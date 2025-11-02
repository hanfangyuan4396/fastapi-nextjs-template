from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from models import User

from .auth_dependency import CurrentUser, get_current_user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    if not allowed_roles:
        raise ValueError("require_roles 至少需要一个角色")

    def _guard(user: CurrentUser) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": f"权限不足，需要角色: {','.join(allowed_roles)}"},
            )
        return user

    # 返回一个依赖：先注入 current_user，再进行角色校验
    return Depends(_guard)  # type: ignore[return-value]


# 便捷别名
Admin = Annotated[User, require_roles("admin")]
UserOrAdmin = Annotated[User, require_roles("user", "admin")]

__all__ = [
    "Admin",
    "CurrentUser",
    "UserOrAdmin",
    "get_current_user",
    "require_roles",
]
