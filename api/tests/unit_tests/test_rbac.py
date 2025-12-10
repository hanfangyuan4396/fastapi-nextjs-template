from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.rbac import require_roles
from tests.helpers import async_create_user


def _guard_callable_for(*roles: str):
    dep = require_roles(*roles)
    # require_roles 返回 fastapi.Depends，取其内部的依赖函数以便单测直接调用
    assert hasattr(dep, "dependency")
    return dep.dependency  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_require_roles_admin_denies_user(async_db_session: AsyncSession):
    user = await async_create_user(async_db_session, "user1", "123456", role="user")
    guard = _guard_callable_for("admin")
    with pytest.raises(HTTPException) as ei:
        guard(user)
    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_require_roles_admin_allows_admin(async_db_session: AsyncSession):
    admin = await async_create_user(async_db_session, "admin1", "123456", role="admin")
    guard = _guard_callable_for("admin")
    got = guard(admin)
    assert got.id == admin.id


@pytest.mark.asyncio
async def test_require_roles_multiple_allows_user_and_admin(async_db_session: AsyncSession):
    u = await async_create_user(async_db_session, "user2", "123456", role="user")
    a = await async_create_user(async_db_session, "admin2", "123456", role="admin")
    guard = _guard_callable_for("admin", "user")
    assert guard(u).id == u.id
    assert guard(a).id == a.id


def test_require_roles_empty_raises() -> None:
    with pytest.raises(ValueError, match="至少需要一个角色"):
        require_roles()
