from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from core.jwt_tokens import TokenError, TokenExpiredError, TokenTypeError, verify_token
from models import User
from utils.db import AsyncDbSession


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not isinstance(authorization, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "缺少 Authorization 头"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer" or not parts[1]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Authorization 格式错误，期望 'Bearer <token>'"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1]


async def get_current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    db: AsyncDbSession = None,
) -> User:
    """基于访问令牌(access)的认证依赖，返回当前活跃用户。

    校验项：
    - Authorization: Bearer <access>
    - token 类型为 access，且未过期
    - 用户存在且 is_active 为 True
    """

    token = _extract_bearer_token(authorization)

    try:
        claims = verify_token(token, "access")
    except TokenExpiredError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "访问令牌已过期"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except TokenTypeError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "令牌类型错误，必须为 access"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except TokenError as err:
        # 其他令牌错误，例如签名无效、缺少声明、非法令牌等
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "访问令牌无效"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    user_id_str = str(claims.get("sub"))
    try:
        user_uuid = UUID(user_id_str)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "访问令牌载荷非法"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    user = await db.get(User, user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "用户不存在"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "用户已禁用"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# 便捷别名：在路由函数中可写作 `current_user: CurrentUser`
CurrentUser = Annotated[User, Depends(get_current_user)]

__all__ = ["CurrentUser", "get_current_user"]
