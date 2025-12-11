import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User


@pytest.mark.asyncio
async def test_create_user_defaults(async_db_session: AsyncSession):
    u = User(username="alice", password_hash="hashed:xxx")
    async_db_session.add(u)
    await async_db_session.commit()

    result = await async_db_session.execute(select(User).where(User.username == "alice"))
    got = result.scalar_one()
    assert got.role == "user"
    assert got.is_active is True
    assert got.token_version == 1


@pytest.mark.asyncio
async def test_username_unique(async_db_session: AsyncSession):
    u1 = User(username="bob", password_hash="hashed:yyy")
    async_db_session.add(u1)
    await async_db_session.commit()

    u2 = User(username="bob", password_hash="hashed:zzz")
    async_db_session.add(u2)
    try:
        await async_db_session.commit()
        # 如果能走到这里，说明唯一约束未生效
        pytest.fail("username unique constraint not enforced")
    except IntegrityError:
        await async_db_session.rollback()
