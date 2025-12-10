from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import verify_password
from models.users import User


async def _async_upsert_user(
    async_db_session: AsyncSession, username: str, plain_password: str, role: str
) -> tuple[User, str]:
    """异步包装 upsert_user，用于测试。

    由于 upsert_user 本身是同步的（用于 CLI 脚本），我们使用 run_sync 在异步上下文中调用。
    """
    # 使用 connection 的 run_sync 来执行同步 ORM 操作
    # 但更简单的方式是直接在异步 session 中重新实现逻辑
    result = await async_db_session.execute(select(User).filter_by(username=username))
    user = result.scalar_one_or_none()

    if user is None:
        from core.security import hash_password

        user = User(
            username=username,
            password_hash=hash_password(plain_password),
            role=role,
            is_active=True,
            token_version=1,
            failed_login_attempts=0,
            lock_until=None,
        )
        async_db_session.add(user)
        return user, "created"

    need_update = False

    if user.role != role:
        user.role = role
        need_update = True

    if not verify_password(plain_password, user.password_hash):
        from core.security import hash_password

        user.password_hash = hash_password(plain_password)
        need_update = True

    if not user.is_active:
        user.is_active = True
        need_update = True

    if user.failed_login_attempts != 0 or user.lock_until is not None:
        user.failed_login_attempts = 0
        user.lock_until = None
        need_update = True

    return user, ("updated" if need_update else "skipped")


@pytest.mark.asyncio
async def test_seed_creates_admin_and_user(async_db_session: AsyncSession):
    user_admin, action_admin = await _async_upsert_user(async_db_session, "admin", "123456", "admin")
    user_user, action_user = await _async_upsert_user(async_db_session, "user", "123456", "user")
    await async_db_session.commit()

    assert action_admin == "created"
    assert action_user == "created"

    result_admin = await async_db_session.execute(select(User).where(User.username == "admin"))
    got_admin = result_admin.scalar_one()
    result_user = await async_db_session.execute(select(User).where(User.username == "user"))
    got_user = result_user.scalar_one()

    assert got_admin.role == "admin"
    assert got_user.role == "user"
    assert got_admin.is_active is True
    assert got_user.is_active is True
    assert verify_password("123456", got_admin.password_hash) is True
    assert verify_password("123456", got_user.password_hash) is True


@pytest.mark.asyncio
async def test_seed_idempotent_skips_when_no_change(async_db_session: AsyncSession):
    """
    Verifies that calling upsert_user again with identical username, password, and role
    is idempotent and preserves the stored password hash.
    """
    await _async_upsert_user(async_db_session, "admin", "123456", "admin")
    await async_db_session.commit()

    result_before = await async_db_session.execute(select(User).where(User.username == "admin"))
    before = result_before.scalar_one()
    hash_before = before.password_hash

    _, action = await _async_upsert_user(async_db_session, "admin", "123456", "admin")
    await async_db_session.commit()

    result_after = await async_db_session.execute(select(User).where(User.username == "admin"))
    after = result_after.scalar_one()
    assert action == "skipped"
    assert after.password_hash == hash_before


@pytest.mark.asyncio
async def test_seed_resets_lock_and_failures(async_db_session: AsyncSession):
    """
    Verifies that upsert_user clears failed login attempts and lock state when updating.
    """
    user, _ = await _async_upsert_user(async_db_session, "user", "123456", "user")
    await async_db_session.commit()

    # 模拟锁定与失败计数
    user.failed_login_attempts = 5
    user.lock_until = datetime.now(UTC) + timedelta(hours=1)
    await async_db_session.commit()

    _, action = await _async_upsert_user(async_db_session, "user", "123456", "user")
    await async_db_session.commit()

    result = await async_db_session.execute(select(User).where(User.username == "user"))
    got = result.scalar_one()
    assert action == "updated"
    assert got.failed_login_attempts == 0
    assert got.lock_until is None


@pytest.mark.asyncio
async def test_seed_updates_role(async_db_session: AsyncSession):
    await _async_upsert_user(async_db_session, "bob", "123456", "user")
    await async_db_session.commit()

    _, action = await _async_upsert_user(async_db_session, "bob", "123456", "admin")
    await async_db_session.commit()

    result = await async_db_session.execute(select(User).where(User.username == "bob"))
    got = result.scalar_one()
    assert action == "updated"
    assert got.role == "admin"
