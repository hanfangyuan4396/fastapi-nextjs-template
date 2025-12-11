from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.jwt_tokens import verify_token
from core.security import hash_password
from models import RefreshToken, User
from services.login_rate_limit_service import LoginRateLimitService
from tests.helpers import FakeRedis


async def _create_user(db: AsyncSession, username: str, password: str, *, is_active: bool = True) -> User:
    user = User(username=username, password_hash=hash_password(password), role="user", is_active=is_active)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def fake_redis_for_rate_limit(monkeypatch) -> FakeRedis:
    """为登录频率限制服务注入 FakeRedis。"""
    fake = FakeRedis()

    # 重置全局单例以便注入 FakeRedis
    import services.login_rate_limit_service as rate_limit_module

    monkeypatch.setattr(rate_limit_module, "_service", None)

    # 替换 get_redis 函数
    def _get_fake_redis():
        return fake

    monkeypatch.setattr("services.login_rate_limit_service.get_redis", _get_fake_redis)
    return fake


@pytest.mark.asyncio
async def test_login_success_sets_refresh_cookie_and_returns_access(
    async_client: AsyncClient, async_db_session: AsyncSession, fake_redis_for_rate_limit: FakeRedis
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
    async_client: AsyncClient, async_db_session: AsyncSession, fake_redis_for_rate_limit: FakeRedis
) -> None:
    await _create_user(async_db_session, "bob", "pw")

    resp = await async_client.post("/api/auth/login", json={"username": "bob", "password": "oops"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40101

    # 验证 Redis 中的失败计数
    fail_key = f"{LoginRateLimitService.FAIL_KEY_PREFIX}bob"
    attempts = await fake_redis_for_rate_limit.get(fail_key)
    assert int(attempts or 0) == 1

    # 验证已设置 TTL（30 分钟窗口）
    ttl = fake_redis_for_rate_limit._ttl.get(fail_key)
    assert ttl == LoginRateLimitService.FAIL_WINDOW_SECONDS


@pytest.mark.asyncio
async def test_login_lock_after_five_failures_returns_403(
    async_client: AsyncClient, async_db_session: AsyncSession, fake_redis_for_rate_limit: FakeRedis
) -> None:
    await _create_user(async_db_session, "carol", "pw")

    for _i in range(4):
        r = await async_client.post("/api/auth/login", json={"username": "carol", "password": "wrong"})
        assert r.json()["code"] == 40101

    # 第5次触发锁定
    r5 = await async_client.post("/api/auth/login", json={"username": "carol", "password": "wrong"})
    assert r5.status_code == 200
    assert r5.json()["code"] == 40301

    # 验证 Redis 中存在锁定标记
    lock_key = f"{LoginRateLimitService.LOCK_KEY_PREFIX}carol"
    locked = await fake_redis_for_rate_limit.exists(lock_key)
    assert locked == 1

    # 验证锁定 TTL（1 小时）
    ttl = fake_redis_for_rate_limit._ttl.get(lock_key)
    assert ttl == LoginRateLimitService.LOCK_DURATION_SECONDS


@pytest.mark.asyncio
async def test_login_locked_user_rejected_immediately(
    async_client: AsyncClient, async_db_session: AsyncSession, fake_redis_for_rate_limit: FakeRedis
) -> None:
    """测试已锁定用户直接被拒绝，无需查库。"""
    await _create_user(async_db_session, "locked_user", "pw")

    # 手动设置锁定状态
    lock_key = f"{LoginRateLimitService.LOCK_KEY_PREFIX}locked_user"
    await fake_redis_for_rate_limit.setex(lock_key, 3600, "1")

    resp = await async_client.post("/api/auth/login", json={"username": "locked_user", "password": "pw"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_login_success_resets_attempts(
    async_client: AsyncClient, async_db_session: AsyncSession, fake_redis_for_rate_limit: FakeRedis
) -> None:
    """测试登录成功后重置失败计数。"""
    await _create_user(async_db_session, "reset_user", "pw")

    # 先失败几次
    for _ in range(3):
        await async_client.post("/api/auth/login", json={"username": "reset_user", "password": "wrong"})

    fail_key = f"{LoginRateLimitService.FAIL_KEY_PREFIX}reset_user"
    attempts_before = await fake_redis_for_rate_limit.get(fail_key)
    assert int(attempts_before or 0) == 3

    # 成功登录
    resp = await async_client.post("/api/auth/login", json={"username": "reset_user", "password": "pw"})
    assert resp.json()["code"] == 0

    # 失败计数应被清除
    attempts_after = await fake_redis_for_rate_limit.get(fail_key)
    assert attempts_after is None


@pytest.mark.asyncio
async def test_login_nonexistent_user_also_records_failure(
    async_client: AsyncClient, async_db_session: AsyncSession, fake_redis_for_rate_limit: FakeRedis
) -> None:
    """测试不存在的用户也会记录失败（防止用户名枚举）。"""
    resp = await async_client.post("/api/auth/login", json={"username": "nonexistent", "password": "any"})
    assert resp.json()["code"] == 40101

    fail_key = f"{LoginRateLimitService.FAIL_KEY_PREFIX}nonexistent"
    attempts = await fake_redis_for_rate_limit.get(fail_key)
    assert int(attempts or 0) == 1


@pytest.mark.asyncio
async def test_login_disabled_user_returns_403(
    async_client: AsyncClient, async_db_session: AsyncSession, fake_redis_for_rate_limit: FakeRedis
) -> None:
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
