from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt

from utils.config import settings


class TokenError(Exception):
    """通用 Token 异常基类"""


class TokenExpiredError(TokenError):
    """令牌已过期"""


class TokenSignatureError(TokenError):
    """令牌签名无效"""


class TokenTypeError(TokenError):
    """令牌类型与预期不符"""


class TokenMissingClaimError(TokenError):
    """必需声明缺失或格式不正确"""


class TokenInvalidError(TokenError):
    """令牌非法或无法解析"""


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _normalize_user_id(user_id: Any) -> str:
    """将入参 user_id 统一为 UUID 字符串，若失败抛出 TokenMissingClaimError。"""
    try:
        # 允许传入 UUID 对象或字符串
        if isinstance(user_id, uuid.UUID):
            return str(user_id)
        return str(uuid.UUID(str(user_id)))
    except Exception as e:
        raise TokenMissingClaimError("`sub`(用户ID) 不是合法 UUID") from e


def _build_common_claims(
    user_id: Any, token_type: Literal["access", "refresh"], expires_delta: timedelta
) -> dict[str, Any]:
    issued_at = _now()
    claims: dict[str, Any] = {
        "sub": _normalize_user_id(user_id),
        "type": token_type,
        "jti": _uuid_str(),
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + expires_delta).timestamp()),
    }
    return claims


def create_access_token(user_id: Any) -> str:
    """签发访问令牌（有效期：settings.ACCESS_TOKEN_EXPIRES_MINUTES）。"""
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES)
    payload = _build_common_claims(user_id, "access", expires)
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM, headers={"typ": "JWT"})
    return token


def create_refresh_token(user_id: Any) -> str:
    """签发刷新令牌（有效期：settings.REFRESH_TOKEN_EXPIRES_MINUTES）。"""
    expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRES_MINUTES)
    payload = _build_common_claims(user_id, "refresh", expires)
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM, headers={"typ": "JWT"})
    return token


def verify_token(token: str, expected_type: Literal["access", "refresh"]) -> dict[str, Any]:
    """
    验证并解析令牌。

    - 校验签名、过期时间（exp）。
    - 校验 `type` 与 expected_type 一致。
    - 校验 `sub`/`jti`/`iat`/`exp` 存在且格式正确。

    Returns: 已验证的 claims 字典
    Raises: TokenExpiredError, TokenSignatureError, TokenTypeError, TokenMissingClaimError, TokenInvalidError
    """
    try:
        # 关闭对 iat/exp 的内建校验，改为在下方进行自定义校验
        claims = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "require": ["exp", "iat", "sub", "jti", "type"],
                "verify_exp": False,
                "verify_iat": False,
            },
        )
    except jwt.ExpiredSignatureError as e:
        # 一般不会触发（已关闭 verify_exp），保底处理
        raise TokenExpiredError("令牌已过期") from e
    except jwt.InvalidSignatureError as e:
        raise TokenSignatureError("令牌签名无效") from e
    except jwt.InvalidTokenError as e:
        # 其他解码错误归并为非法令牌
        raise TokenInvalidError("非法令牌或解析失败") from e

    # 类型校验
    token_type = claims.get("type")
    if token_type != expected_type:
        raise TokenTypeError(f"令牌类型错误：期望 {expected_type}，实际 {token_type}")

    # 必需字段与格式进一步校验
    # sub / jti 必须是 UUID 字符串
    for key in ("sub", "jti"):
        value = claims.get(key)
        if not value:
            raise TokenMissingClaimError(f"缺少必需声明: {key}")
        try:
            uuid.UUID(str(value))
        except Exception as e:
            raise TokenMissingClaimError(f"声明 {key} 不是合法 UUID") from e

    # iat/exp 必须是整数时间戳
    for key in ("iat", "exp"):
        value = claims.get(key)
        if value is None:
            raise TokenMissingClaimError(f"缺少必需声明: {key}")
        if not isinstance(value, int):
            raise TokenMissingClaimError(f"声明 {key} 需要为整数时间戳")

    # 过期校验（因关闭 verify_exp，需要在此处手动判断）
    now_ts = int(_now().timestamp())
    if now_ts >= int(claims["exp"]):
        raise TokenExpiredError("令牌已过期")

    return claims
