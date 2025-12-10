from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import RefreshToken, User
from tests.helpers import async_create_expired_refresh_token, async_create_user


async def _create_user(db: AsyncSession, username: str, password: str, *, is_active: bool = True) -> User:
    return await async_create_user(db, username, password, is_active=is_active)


# 正常刷新：仅依赖 Cookie 中的 refresh_token，返回新 access 并轮换出新的 refresh；
# 旧刷新记录 used_at 应置位，新刷新写入 Cookie（值变化）。
@pytest.mark.asyncio
async def test_refresh_endpoint_success_sets_new_cookie(
    async_client: AsyncClient, async_db_session: AsyncSession
) -> None:
    await _create_user(async_db_session, "eve", "pw")

    r1 = await async_client.post("/api/auth/login", json={"username": "eve", "password": "pw"})
    assert r1.status_code == 200
    old_cookie = r1.cookies.get("refresh_token")
    assert old_cookie

    # 设置 cookie 进行刷新
    async_client.cookies.set("refresh_token", old_cookie)
    r2 = await async_client.post("/api/auth/refresh")
    assert r2.status_code == 200
    body = r2.json()
    assert body["code"] == 0
    assert "access_token" in (body.get("data") or {})

    new_cookie = r2.cookies.get("refresh_token")
    assert new_cookie
    assert isinstance(new_cookie, str)
    assert new_cookie != old_cookie

    # DB 状态：旧记录 used_at 置位 + 新记录插入
    stmt = select(RefreshToken)
    result = await async_db_session.execute(stmt)
    tokens = result.scalars().all()
    assert len(tokens) == 2
    old = next(t for t in tokens if t.parent_jti is None)
    child = next(t for t in tokens if t.parent_jti == old.jti)
    assert old.used_at is not None
    assert child is not None


# 复用检测：同一旧 refresh 再次使用，服务应撤销该家族全部刷新令牌，
# 接口返回 40112；随后即便携带较新的 refresh 也应失败。
@pytest.mark.asyncio
async def test_refresh_endpoint_reuse_revokes_family(async_client: AsyncClient, async_db_session: AsyncSession) -> None:
    await _create_user(async_db_session, "frank", "pw")

    r1 = await async_client.post("/api/auth/login", json={"username": "frank", "password": "pw"})
    assert r1.status_code == 200
    cookie_initial = r1.cookies.get("refresh_token")
    assert cookie_initial

    # 第一次刷新（正常）
    async_client.cookies.set("refresh_token", cookie_initial)
    r2 = await async_client.post("/api/auth/refresh")
    assert r2.json()["code"] == 0
    cookie_after = r2.cookies.get("refresh_token")
    assert cookie_after

    # 复用最初的旧 cookie 进行第二次刷新
    async_client.cookies.set("refresh_token", cookie_initial)
    r3 = await async_client.post("/api/auth/refresh")
    assert r3.status_code == 200
    assert r3.json()["code"] == 40112

    # 家族全部撤销：随后即便使用较新的 cookie 也应失败
    async_client.cookies.set("refresh_token", cookie_after)
    r4 = await async_client.post("/api/auth/refresh")
    assert r4.status_code == 200
    assert r4.json()["code"] != 0

    async_db_session.expire_all()
    stmt = select(RefreshToken)
    result = await async_db_session.execute(stmt)
    tokens = result.scalars().all()
    assert len(tokens) >= 2
    assert all(t.revoked for t in tokens)


# 过期刷新：携带已过期的 refresh_token 时，接口返回 40111，刷新失败。
@pytest.mark.asyncio
async def test_refresh_endpoint_with_expired_token_returns_401(
    async_client: AsyncClient, async_db_session: AsyncSession
) -> None:
    user = await _create_user(async_db_session, "gina", "pw")
    expired_token, _ = await async_create_expired_refresh_token(async_db_session, user)

    async_client.cookies.set("refresh_token", expired_token)
    r = await async_client.post("/api/auth/refresh")
    assert r.status_code == 200
    assert r.json()["code"] == 40111
