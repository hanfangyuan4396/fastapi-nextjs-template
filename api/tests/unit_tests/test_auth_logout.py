from __future__ import annotations

import pytest
from sqlalchemy import select

from models import RefreshToken, User
from services.auth_service import AuthService
from tests.helpers import async_create_expired_refresh_token, async_create_user, async_persist_refresh


async def _create_user(db, username: str, password: str) -> User:  # 兼容旧签名
    return await async_create_user(db, username, password)


async def _persist_refresh(db, user: User) -> tuple[str, RefreshToken]:
    return await async_persist_refresh(db, user)


# 服务层：logout 撤销整个家族（从根令牌测试）
@pytest.mark.asyncio
async def test_logout_revokes_family_from_root(async_db_session) -> None:
    user = await _create_user(async_db_session, "lo1", "pw")
    token, rt = await _persist_refresh(async_db_session, user)
    rt_jti = rt.jti  # 在 expire_all 前保存 jti

    service = AuthService()
    result = await service.logout(db=async_db_session, refresh_token=token)

    assert result["code"] == 0

    async_db_session.expire_all()
    stmt = select(RefreshToken).filter(RefreshToken.jti == rt_jti)
    res = await async_db_session.execute(stmt)
    stored = res.scalars().first()
    assert stored is not None
    assert stored.revoked is True


# 服务层：无效/缺失令牌时登出为幂等成功
@pytest.mark.asyncio
async def test_logout_is_idempotent_on_invalid_or_missing_token(async_db_session) -> None:
    service = AuthService()
    ok1 = await service.logout(db=async_db_session, refresh_token=None)
    ok2 = await service.logout(db=async_db_session, refresh_token="this-is-not-jwt")
    assert ok1["code"] == 0
    assert ok2["code"] == 0


# 服务层：过期但签名正确的 refresh 也应能定位并撤销家族
@pytest.mark.asyncio
async def test_logout_with_expired_token_still_revokes_family(async_db_session) -> None:
    user = await _create_user(async_db_session, "lo2", "pw")
    user_id = user.id  # 在 expire_all 前保存 id
    expired_token, _ = await async_create_expired_refresh_token(async_db_session, user)
    service = AuthService()
    result = await service.logout(db=async_db_session, refresh_token=expired_token)
    assert result["code"] == 0

    async_db_session.expire_all()
    stmt = select(RefreshToken).filter(RefreshToken.user_id == user_id)
    res = await async_db_session.execute(stmt)
    stored = res.scalars().first()
    assert stored is not None
    assert stored.revoked is True
