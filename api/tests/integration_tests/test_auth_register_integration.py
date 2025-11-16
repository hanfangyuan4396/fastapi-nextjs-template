from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import RefreshToken, User
from tests.helpers import FakeRedis
from utils.config import settings

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_register_flow_success(async_client: AsyncClient, async_db_session: AsyncSession, monkeypatch):
    """
    端到端测试注册流程：
    1. /auth/register/send-code 发送验证码
    2. /auth/register/verify-and-create 使用验证码创建用户并完成“注册即登录”
    """

    # 使用 FakeRedis 替代真实 Redis
    fake_redis = FakeRedis()

    def _get_fake_redis():
        return fake_redis

    monkeypatch.setattr("services.email_verification_service.get_redis", _get_fake_redis)

    # 安装一个空实现的验证码邮件发送函数，记录发送的验证码
    sent: list[tuple[str, str, int]] = []

    def _send_verification_email(email: str, code: str, expires_in_minutes: int) -> None:
        sent.append((email, code, expires_in_minutes))

    monkeypatch.setattr(
        "services.email_verification_service.send_verification_email",
        _send_verification_email,
    )

    email = "reg-int@example.com"

    # 1) 调用发送验证码接口
    resp_send = await async_client.post(
        f"{API_PREFIX}/auth/register/send-code",
        json={"email": email},
    )
    assert resp_send.status_code == 200
    body_send = resp_send.json()
    assert body_send["code"] == 0
    assert body_send["message"] == "ok"
    assert body_send["data"]["expires_in"] == settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES * 60

    # 验证邮件发送函数被调用了一次，并拿到真实验证码
    assert len(sent) == 1
    sent_email, real_code, expires_in_minutes = sent[0]
    assert sent_email == email
    assert expires_in_minutes == settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES

    # 2) 使用验证码完成注册
    password = "StrongPass123"
    resp_reg = await async_client.post(
        f"{API_PREFIX}/auth/register/verify-and-create",
        json={"email": email, "code": real_code, "password": password},
    )

    assert resp_reg.status_code == 200
    body_reg = resp_reg.json()
    assert body_reg["code"] == 0
    assert body_reg["message"] == "ok"
    assert "access_token" in (body_reg.get("data") or {})

    # 成功后应设置 refresh_token Cookie
    cookie_val = async_client.cookies.get("refresh_token")
    assert cookie_val is not None
    assert isinstance(cookie_val, str)
    assert len(cookie_val) > 10

    # DB 中应已创建用户与刷新令牌记录（使用异步会话查询）
    stmt_user = select(User).where(User.username == email)
    result_user = await async_db_session.execute(stmt_user)
    user = result_user.scalars().first()
    assert user is not None
    assert user.is_active is True
    assert user.role == "user"

    stmt_rt = select(RefreshToken).where(RefreshToken.user_id == user.id)
    result_rt = await async_db_session.execute(stmt_rt)
    tokens = result_rt.scalars().all()
    assert len(tokens) == 1
    rt = tokens[0]
    assert rt.revoked is False
    assert rt.parent_jti is None


@pytest.mark.asyncio
async def test_register_with_wrong_code_does_not_create_user(
    async_client: AsyncClient,
    async_db_session: AsyncSession,
    monkeypatch,
):
    """
    使用错误验证码尝试注册：
    - 接口返回验证码错误
    - 不应创建用户，也不应产生刷新令牌记录
    """

    fake_redis = FakeRedis()

    def _get_fake_redis():
        return fake_redis

    monkeypatch.setattr("services.email_verification_service.get_redis", _get_fake_redis)

    sent: list[tuple[str, str, int]] = []

    def _send_verification_email(email: str, code: str, expires_in_minutes: int) -> None:
        sent.append((email, code, expires_in_minutes))

    monkeypatch.setattr(
        "services.email_verification_service.send_verification_email",
        _send_verification_email,
    )

    email = "reg-int-wrong@example.com"

    # 先正常发送一次验证码
    resp_send = await async_client.post(
        f"{API_PREFIX}/auth/register/send-code",
        json={"email": email},
    )
    assert resp_send.status_code == 200
    assert resp_send.json()["code"] == 0

    # 确认已发送验证码
    assert len(sent) == 1
    sent_email, real_code, _expires_in_minutes = sent[0]
    assert sent_email == email

    # 构造错误验证码
    wrong_code = "000000" if real_code != "000000" else "111111"

    # 使用错误验证码尝试注册
    resp_reg = await async_client.post(
        f"{API_PREFIX}/auth/register/verify-and-create",
        json={"email": email, "code": wrong_code, "password": "StrongPass123"},
    )

    assert resp_reg.status_code == 200
    body_reg = resp_reg.json()
    assert body_reg["code"] == 40004
    assert "验证码错误" in body_reg["message"]

    # 不应设置 refresh_token Cookie
    assert async_client.cookies.get("refresh_token") is None

    # DB 中不应创建用户与刷新令牌记录
    stmt_user = select(User).where(User.username == email)
    result_user = await async_db_session.execute(stmt_user)
    user = result_user.scalars().first()
    assert user is None

    stmt_rt = select(RefreshToken).where(RefreshToken.user_id == (user.id if user else -1))
    result_rt = await async_db_session.execute(stmt_rt)
    tokens = result_rt.scalars().all()
    assert tokens == []
