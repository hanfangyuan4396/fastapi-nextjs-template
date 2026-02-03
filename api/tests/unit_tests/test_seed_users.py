import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import verify_password
from models.users import User


async def _async_create_user_if_missing(
    async_db_session: AsyncSession, username: str, plain_password: str, role: str
) -> tuple[User, str]:
    """异步实现 create_user_if_missing，用于测试。"""
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
        )
        async_db_session.add(user)
        return user, "created"

    return user, "skipped"


@pytest.mark.asyncio
async def test_seed_creates_admin_and_user(async_db_session: AsyncSession):
    user_admin, action_admin = await _async_create_user_if_missing(async_db_session, "admin", "123456", "admin")
    user_user, action_user = await _async_create_user_if_missing(async_db_session, "user", "123456", "user")
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
    """重复初始化时跳过，不更新密码。"""
    await _async_create_user_if_missing(async_db_session, "admin", "123456", "admin")
    await async_db_session.commit()

    result_before = await async_db_session.execute(select(User).where(User.username == "admin"))
    before = result_before.scalar_one()
    hash_before = before.password_hash

    _, action = await _async_create_user_if_missing(async_db_session, "admin", "123456", "admin")
    await async_db_session.commit()

    result_after = await async_db_session.execute(select(User).where(User.username == "admin"))
    after = result_after.scalar_one()
    assert action == "skipped"
    assert after.password_hash == hash_before


@pytest.mark.asyncio
async def test_seed_skip_does_not_update_existing_user(async_db_session: AsyncSession):
    await _async_create_user_if_missing(async_db_session, "bob", "123456", "user")
    await async_db_session.commit()

    _, action = await _async_create_user_if_missing(async_db_session, "bob", "newpass", "admin")
    await async_db_session.commit()

    result = await async_db_session.execute(select(User).where(User.username == "bob"))
    got = result.scalar_one()
    assert action == "skipped"
    assert got.role == "user"
    assert verify_password("123456", got.password_hash) is True
