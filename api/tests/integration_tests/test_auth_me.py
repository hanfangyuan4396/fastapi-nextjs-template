from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from models import User


@pytest.mark.asyncio
async def test_auth_me_returns_current_user(async_client: AsyncClient, async_db_session: AsyncSession) -> None:
    user = User(username="me@example.com", password_hash=hash_password("pw"), role="user", is_active=True)
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)

    login_resp = await async_client.post("/api/auth/login", json={"username": "me@example.com", "password": "pw"})
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["code"] == 0

    access_token = (body.get("data") or {}).get("access_token")
    assert access_token

    resp = await async_client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    me_body = resp.json()
    assert me_body["code"] == 0
    data = me_body.get("data") or {}
    assert data["username"] == "me@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert data["token_version"] == 1
