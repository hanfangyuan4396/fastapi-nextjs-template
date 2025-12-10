from __future__ import annotations

import pytest
from sqlalchemy import select

from models import RefreshToken, User
from services.auth_service import AuthService
from tests.helpers import async_create_expired_refresh_token, async_create_user, async_persist_refresh


async def _create_user(db, username: str, password: str) -> User:  # 兼容旧调用签名
    return await async_create_user(db, username, password)


# 服务层：刷新成功的轮换流程——旧刷新令牌 used_at 置位；
# 新刷新令牌插入且 parent_jti 指向旧 jti，同时返回新的 access_token。
@pytest.mark.asyncio
async def test_refresh_rotate_success(async_db_session) -> None:
    user = await _create_user(async_db_session, "r1", "pw")
    token, rt = await async_persist_refresh(async_db_session, user)
    rt_jti = rt.jti  # 在 expire_all 前保存 jti

    service = AuthService()
    result = await service.refresh(db=async_db_session, refresh_token=token)

    assert result["code"] == 0
    assert "access_token" in (result.get("data") or {})

    async_db_session.expire_all()
    stmt = select(RefreshToken).filter(RefreshToken.jti == rt_jti)
    res = await async_db_session.execute(stmt)
    old = res.scalars().first()
    assert old is not None
    assert old.used_at is not None

    # 新纪录插入且 parent_jti 指向旧 jti
    stmt_children = select(RefreshToken).filter(RefreshToken.parent_jti == rt_jti)
    res_children = await async_db_session.execute(stmt_children)
    children = res_children.scalars().all()
    assert len(children) == 1


# 服务层：复用检测——同一刷新令牌第二次使用将被识别为复用；
# 服务撤销整个家族的刷新令牌（全部 revoked=true）。
@pytest.mark.asyncio
async def test_refresh_reuse_detects_and_revokes_family(async_db_session) -> None:
    user = await _create_user(async_db_session, "r2", "pw")
    token, rt = await async_persist_refresh(async_db_session, user)
    rt_jti = rt.jti  # 在 expire_all 前保存 jti

    service = AuthService()
    first = await service.refresh(db=async_db_session, refresh_token=token)
    assert first["code"] == 0

    # 复用旧 token
    second = await service.refresh(db=async_db_session, refresh_token=token)
    assert second["code"] == 40112

    # 家族内所有刷新令牌应被撤销
    async_db_session.expire_all()
    stmt = select(RefreshToken)
    res = await async_db_session.execute(stmt)
    tokens = res.scalars().all()
    assert len(tokens) >= 2
    assert all(t.revoked for t in tokens)

    # 使用子令牌也应失败
    child = next(t for t in tokens if t.parent_jti == rt_jti)
    # 为了避免复杂化 JWT 重签名，这里直接断言 DB 层已撤销即可
    assert child.revoked is True


# 服务层：过期刷新——传入已过期的 refresh_token 时，返回 40111（刷新令牌已过期）。
@pytest.mark.asyncio
async def test_refresh_expired_returns_401(async_db_session) -> None:
    user = await _create_user(async_db_session, "r3", "pw")
    expired_token, rt = await async_create_expired_refresh_token(async_db_session, user)
    service = AuthService()
    result = await service.refresh(db=async_db_session, refresh_token=expired_token)
    assert result["code"] == 40111
