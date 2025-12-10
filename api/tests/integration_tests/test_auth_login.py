from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.jwt_tokens import verify_token
from core.security import hash_password
from models import RefreshToken, User
from services.auth_service import AuthService


async def _create_user(db: AsyncSession, username: str, password: str, *, is_active: bool = True) -> User:
    user = User(username=username, password_hash=hash_password(password), role="user", is_active=is_active)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_login_success_sets_refresh_cookie_and_returns_access(
    async_client: AsyncClient, async_db_session: AsyncSession
) -> None:
    await _create_user(async_db_session, "alice", "secret")

    resp = await async_client.post("/api/auth/login", json={"username": "alice", "password": "secret"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert "access_token" in (body.get("data") or {})

    # 刷新令牌应写入 Cookie
    cookie_val = resp.cookies.get("refresh_token")
    assert cookie_val is not None
    assert isinstance(cookie_val, str)
    assert len(cookie_val) > 10

    # DB 中应有一条 RefreshToken 记录
    stmt = select(RefreshToken)
    result = await async_db_session.execute(stmt)
    tokens = result.scalars().all()
    assert len(tokens) == 1

    # access_token 与 refresh_token 均应包含 role
    access_token = (body.get("data") or {}).get("access_token")
    claims = verify_token(access_token, "access")
    assert claims.get("role") == "user"
    cookie_val = resp.cookies.get("refresh_token")
    refresh_claims = verify_token(cookie_val, "refresh")
    assert refresh_claims.get("role") == "user"


@pytest.mark.asyncio
async def test_login_wrong_password_increments_attempts(
    async_client: AsyncClient, async_db_session: AsyncSession
) -> None:
    user = await _create_user(async_db_session, "bob", "pw")
    user_id = user.id  # 在 expire_all 前保存 id

    resp = await async_client.post("/api/auth/login", json={"username": "bob", "password": "oops"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40101

    # 刷新用户状态（避免会话缓存返回旧对象）
    async_db_session.expire_all()
    stmt = select(User).filter(User.id == user_id)
    result = await async_db_session.execute(stmt)
    refreshed = result.scalars().first()
    assert refreshed is not None
    assert int(refreshed.failed_login_attempts or 0) == 1
    assert refreshed.lock_until is not None  # 开启30分钟窗口


@pytest.mark.asyncio
async def test_login_lock_after_five_failures_returns_403(
    async_client: AsyncClient, async_db_session: AsyncSession
) -> None:
    user = await _create_user(async_db_session, "carol", "pw")
    user_id = user.id  # 在 expire_all 前保存 id

    for _i in range(4):
        r = await async_client.post("/api/auth/login", json={"username": "carol", "password": "wrong"})
        assert r.json()["code"] == 40101

    # 第5次触发锁定
    r5 = await async_client.post("/api/auth/login", json={"username": "carol", "password": "wrong"})
    assert r5.status_code == 200
    assert r5.json()["code"] == 40301

    async_db_session.expire_all()
    stmt = select(User).filter(User.id == user_id)
    result = await async_db_session.execute(stmt)
    refreshed = result.scalars().first()
    assert refreshed is not None
    assert int(refreshed.failed_login_attempts or 0) >= 5
    assert refreshed.lock_until is not None
    assert datetime.now(UTC) < AuthService._normalize_utc(refreshed.lock_until)  # 仍处于锁定期


@pytest.mark.asyncio
async def test_login_disabled_user_returns_403(async_client: AsyncClient, async_db_session: AsyncSession) -> None:
    await _create_user(async_db_session, "dave", "pw", is_active=False)

    resp = await async_client.post("/api/auth/login", json={"username": "dave", "password": "pw"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40302

    # 不应写入 refresh_token Cookie
    assert resp.cookies.get("refresh_token") is None

    # 不应产生刷新令牌记录
    stmt = select(RefreshToken)
    result = await async_db_session.execute(stmt)
    count = len(result.scalars().all())
    assert count == 0
