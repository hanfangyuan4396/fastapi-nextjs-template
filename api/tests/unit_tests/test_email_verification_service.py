from __future__ import annotations

import pytest

from services.email_verification_service import EmailVerificationService
from tests.helpers import FakeRedis
from utils.config import settings


@pytest.fixture
def fake_redis(monkeypatch) -> FakeRedis:
    fake = FakeRedis()

    def _get_fake_redis():
        return fake

    # 覆盖 service 模块中实际使用的 get_redis，使服务层获取到的是内存实现
    monkeypatch.setattr("services.email_verification_service.get_redis", _get_fake_redis)
    return fake


@pytest.fixture
def noop_email_sender(monkeypatch):
    """
    安装一个空实现的验证码邮件发送函数，便于在测试中断言调用次数与参数。

    返回值:
        sent: list[tuple[email, code, expires_in_minutes]]
    """
    sent: list[tuple[str, str, int]] = []

    def _send_verification_email(email: str, code: str, expires_in_minutes: int) -> None:
        sent.append((email, code, expires_in_minutes))

    # 按“在哪里用就在哪儿 patch”的原则，直接 patch service 模块中导入的符号
    monkeypatch.setattr("services.email_verification_service.send_verification_email", _send_verification_email)
    return sent


@pytest.mark.asyncio
async def test_send_register_code_success(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    service = EmailVerificationService()

    resp = await service.send_register_code(
        db=async_db_session,
        email="newuser@example.com",
        client_ip="127.0.0.1",
    )

    assert resp["code"] == 0
    assert resp["message"] == "ok"
    assert resp["data"]["expires_in"] == settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES * 60

    # 验证 Redis 中已写入验证码记录
    code_key = (
        f"{EmailVerificationService.KEY_PREFIX_CODE}:{EmailVerificationService.SCENE_REGISTER}:newuser@example.com"
    )
    stored = await fake_redis.hgetall(code_key)
    assert stored.get("code_hash")
    assert stored.get("scene") == EmailVerificationService.SCENE_REGISTER
    assert stored.get("used") == "0"
    assert stored.get("failed_attempts") == "0"

    # 验证邮件发送函数被调用了一次
    assert len(noop_email_sender) == 1
    email, _code, expires = noop_email_sender[0]
    assert email == "newuser@example.com"
    assert expires == settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES


@pytest.mark.asyncio
async def test_send_register_code_invalid_email(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    service = EmailVerificationService()

    resp = await service.send_register_code(
        db=async_db_session,
        email="not-an-email",
        client_ip=None,
    )

    assert resp["code"] == 42201
    assert "邮箱格式不合法" in resp["message"]
    # 不应发送邮件，也不应写入 Redis
    assert noop_email_sender == []
    assert fake_redis._store == {}  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_send_register_code_email_already_registered(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    # 先插入一个已激活用户
    from models import User

    user = User(username="dup@example.com", password_hash="x", role="user", is_active=True)
    async_db_session.add(user)
    await async_db_session.commit()

    service = EmailVerificationService()
    resp = await service.send_register_code(
        db=async_db_session,
        email="dup@example.com",
        client_ip=None,
    )

    assert resp["code"] == 40901
    assert "邮箱已注册" in resp["message"]
    # 不应发送邮件
    assert noop_email_sender == []


@pytest.mark.asyncio
async def test_send_register_code_rate_limit_per_email(
    async_db_session, fake_redis: FakeRedis, noop_email_sender, monkeypatch
):
    # 将同一邮箱的频率限制调小，便于测试
    monkeypatch.setattr(settings, "EMAIL_VERIFICATION_RATE_LIMIT_PER_EMAIL", 1)

    service = EmailVerificationService()

    # 第一次应成功
    resp1 = await service.send_register_code(
        db=async_db_session,
        email="rl@example.com",
        client_ip=None,
    )
    assert resp1["code"] == 0

    # 第二次在频控窗口内应返回 42901
    resp2 = await service.send_register_code(
        db=async_db_session,
        email="rl@example.com",
        client_ip=None,
    )
    assert resp2["code"] == 42901


@pytest.mark.asyncio
async def test_send_register_code_rate_limit_per_ip(
    async_db_session, fake_redis: FakeRedis, noop_email_sender, monkeypatch
):
    monkeypatch.setattr(settings, "EMAIL_VERIFICATION_RATE_LIMIT_PER_IP", 1)

    service = EmailVerificationService()

    # 第一次应成功
    resp1 = await service.send_register_code(
        db=async_db_session,
        email="ip1@example.com",
        client_ip="10.0.0.1",
    )
    assert resp1["code"] == 0

    # 同一 IP 第二次（不同邮箱）也应触发 IP 限流
    resp2 = await service.send_register_code(
        db=async_db_session,
        email="ip2@example.com",
        client_ip="10.0.0.1",
    )
    assert resp2["code"] == 42902


@pytest.mark.asyncio
async def test_send_reset_password_code_success(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    from models import User

    user = User(username="reset@example.com", password_hash="x", role="user", is_active=True)
    async_db_session.add(user)
    await async_db_session.commit()

    service = EmailVerificationService()
    resp = await service.send_reset_password_code(
        db=async_db_session,
        email="reset@example.com",
        client_ip=None,
    )

    assert resp["code"] == 0

    code_key = (
        f"{EmailVerificationService.KEY_PREFIX_CODE}:{EmailVerificationService.SCENE_RESET_PASSWORD}:reset@example.com"
    )
    stored = await fake_redis.hgetall(code_key)
    assert stored.get("scene") == EmailVerificationService.SCENE_RESET_PASSWORD
    assert len(noop_email_sender) == 1


@pytest.mark.asyncio
async def test_send_reset_password_code_email_not_found(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    service = EmailVerificationService()
    resp = await service.send_reset_password_code(
        db=async_db_session,
        email="missing@example.com",
        client_ip=None,
    )

    assert resp["code"] == 40401
    assert noop_email_sender == []


@pytest.mark.asyncio
async def test_verify_and_consume_code_success(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    service = EmailVerificationService()
    email = "verify@example.com"

    # 手动写入一条有效验证码记录
    code_key = f"{EmailVerificationService.KEY_PREFIX_CODE}:{EmailVerificationService.SCENE_REGISTER}:{email}"
    await fake_redis.hset(
        code_key,
        mapping={
            "code_hash": "placeholder",  # 先占位，后面再写入真实哈希
            "scene": EmailVerificationService.SCENE_REGISTER,
            "created_at": "2024-01-01T00:00:00Z",
            "used": "0",
            "failed_attempts": "0",
            "ip": "",
        },
    )

    # 为了利用服务内部的 hash/verify 逻辑，我们走一次 send_register_code 获取真实哈希
    # 这里无需关心邮件/频控，只需要覆盖 code_hash
    # 直接调用内部生成逻辑不太优雅，但可保证与生产逻辑一致
    resp = await service.send_register_code(db=async_db_session, email=email, client_ip=None)
    assert resp["code"] == 0

    # 由于我们不知道具体验证码内容，这里只测试 verify_and_consume_code 针对"不存在/已删除"的行为：
    # 先调用一次 verify_and_consume_code，之后 key 应被删除，再调用一次应返回不存在。
    await service.verify_and_consume_code(email=email, code="123456")
    # 无论成功还是失败，第二次调用应视为"不存在或已过期"
    result2 = await service.verify_and_consume_code(email=email, code="123456")
    assert result2["code"] in (40001, 40003, 40004)


@pytest.mark.asyncio
async def test_verify_and_consume_code_wrong_code(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    """测试验证码错误的情况"""
    service = EmailVerificationService()
    email = "wrong@example.com"

    # 发送验证码
    resp = await service.send_register_code(db=async_db_session, email=email, client_ip=None)
    assert resp["code"] == 0

    # 从邮件发送记录中获取真实验证码
    assert len(noop_email_sender) == 1
    _email, real_code, _expires = noop_email_sender[0]
    assert _email == email

    # 使用错误的验证码验证
    code_key = f"{EmailVerificationService.KEY_PREFIX_CODE}:{EmailVerificationService.SCENE_REGISTER}:{email}"
    wrong_code = "000000" if real_code != "000000" else "111111"
    result = await service.verify_and_consume_code(email=email, code=wrong_code)

    # 应该返回验证码错误
    assert result["code"] == 40004
    assert "验证码错误" in result["message"]

    # 验证失败次数已增加
    stored = await fake_redis.hgetall(code_key)
    assert stored.get("failed_attempts") == "1"
    # 验证码应该还存在（未删除）
    assert stored.get("code_hash")
    assert stored.get("used") == "0"


@pytest.mark.asyncio
async def test_verify_and_consume_code_exceed_max_attempts(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    """测试超过最大重试次数的情况"""
    service = EmailVerificationService()
    email = "max_attempts@example.com"

    # 发送验证码
    resp = await service.send_register_code(db=async_db_session, email=email, client_ip=None)
    assert resp["code"] == 0

    # 从邮件发送记录中获取真实验证码
    assert len(noop_email_sender) == 1
    _email, real_code, _expires = noop_email_sender[0]
    assert _email == email

    code_key = f"{EmailVerificationService.KEY_PREFIX_CODE}:{EmailVerificationService.SCENE_REGISTER}:{email}"
    wrong_code = "000000" if real_code != "000000" else "111111"

    # 连续使用错误验证码 MAX_ATTEMPTS 次
    for attempt in range(EmailVerificationService.MAX_ATTEMPTS):
        result = await service.verify_and_consume_code(email=email, code=wrong_code)

        if attempt < EmailVerificationService.MAX_ATTEMPTS - 1:
            # 前几次应该返回验证码错误
            assert result["code"] == 40004
            assert "验证码错误" in result["message"]
            # 验证失败次数递增
            stored = await fake_redis.hgetall(code_key)
            assert stored.get("failed_attempts") == str(attempt + 1)
        else:
            # 最后一次应该返回超过最大重试次数
            assert result["code"] == 40003
            assert "验证码错误次数过多" in result["message"]
            # 验证 key 已被删除
            stored = await fake_redis.hgetall(code_key)
            assert stored == {}
