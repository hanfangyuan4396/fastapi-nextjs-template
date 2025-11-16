from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from models import RefreshToken, User
from services.registration_service import RegistrationService


@pytest.mark.asyncio
async def test_registration_success(async_db_session, monkeypatch):
    # mock 掉验证码校验，专注于注册与令牌逻辑
    async def _ok_verify(self, *, email: str, code: str):
        return {"code": 0, "message": "ok"}

    monkeypatch.setattr(
        "services.email_verification_service.EmailVerificationService.verify_and_consume_code",
        _ok_verify,
    )

    service = RegistrationService()
    now_ts = int(datetime.now(UTC).timestamp())

    resp = await service.register_with_email_code(
        db=async_db_session,
        email="reg@example.com",
        code="123456",
        password="StrongPass123",
        client_ip="127.0.0.1",
        user_agent="pytest",
    )

    assert resp["code"] == 0
    assert resp["message"] == "ok"
    assert "access_token" in resp["data"]
    assert "refresh_token" in resp["data"]
    assert resp["data"]["refresh_expires_at"] >= now_ts

    # 验证用户已创建
    stmt_user = select(User).where(User.username == "reg@example.com")
    result_user = await async_db_session.execute(stmt_user)
    user = result_user.scalars().first()
    assert user is not None
    assert user.is_active is True
    assert user.role == "user"

    # 验证刷新令牌记录已创建
    stmt_rt = select(RefreshToken).where(RefreshToken.user_id == user.id)
    result_rt = await async_db_session.execute(stmt_rt)
    tokens = result_rt.scalars().all()
    assert len(tokens) == 1
    rt = tokens[0]
    assert rt.revoked is False
    assert rt.parent_jti is None
    assert rt.ip == "127.0.0.1"
    assert rt.user_agent == "pytest"


@pytest.mark.asyncio
async def test_registration_email_already_registered(async_db_session, monkeypatch):
    # 先插入一个已激活用户
    user = User(username="dup-reg@example.com", password_hash="x", role="user", is_active=True)
    async_db_session.add(user)
    await async_db_session.commit()

    # mock 验证码通过
    async def _ok_verify(self, *, email: str, code: str):
        return {"code": 0, "message": "ok"}

    monkeypatch.setattr(
        "services.email_verification_service.EmailVerificationService.verify_and_consume_code",
        _ok_verify,
    )

    service = RegistrationService()
    resp = await service.register_with_email_code(
        db=async_db_session,
        email="dup-reg@example.com",
        code="123456",
        password="StrongPass123",
        client_ip=None,
        user_agent=None,
    )

    assert resp["code"] == 40901
    assert "邮箱已注册" in resp["message"]


@pytest.mark.asyncio
async def test_registration_otp_failed(async_db_session, monkeypatch):
    # mock 验证码失败
    async def _fail_verify(self, *, email: str, code: str):
        return {"code": 40004, "message": "验证码错误"}

    monkeypatch.setattr(
        "services.email_verification_service.EmailVerificationService.verify_and_consume_code",
        _fail_verify,
    )

    service = RegistrationService()
    resp = await service.register_with_email_code(
        db=async_db_session,
        email="any@example.com",
        code="000000",
        password="StrongPass123",
        client_ip=None,
        user_agent=None,
    )

    # 应直接透传验证码错误，不创建用户/令牌
    assert resp["code"] == 40004
    assert "验证码错误" in resp["message"]
