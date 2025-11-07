from __future__ import annotations

import uuid
from datetime import UTC, datetime

import jwt
import pytest

from core.jwt_tokens import (
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingClaimError,
    TokenSignatureError,
    TokenTypeError,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from utils.config import settings


def _now_ts() -> int:
    return int(datetime.now(UTC).timestamp())


def test_create_and_verify_access_refresh_tokens() -> None:
    user_id = uuid.uuid4()
    role = "user"
    access = create_access_token(user_id, role)
    refresh = create_refresh_token(user_id, role)

    access_claims = verify_token(access, "access")
    refresh_claims = verify_token(refresh, "refresh")

    # 基本字段 + 角色
    for claims, expected_type in [(access_claims, "access"), (refresh_claims, "refresh")]:
        assert claims["type"] == expected_type
        # sub/jti 为合法 UUID
        uuid.UUID(str(claims["sub"]))
        uuid.UUID(str(claims["jti"]))
        assert isinstance(claims["iat"], int)
        assert isinstance(claims["exp"], int)
        assert claims["role"] == role

    # 有效期校验：exp - iat 与配置一致
    assert access_claims["exp"] - access_claims["iat"] == settings.ACCESS_TOKEN_EXPIRES_MINUTES * 60
    assert refresh_claims["exp"] - refresh_claims["iat"] == settings.REFRESH_TOKEN_EXPIRES_MINUTES * 60


def test_verify_token_type_mismatch_raises() -> None:
    token = create_access_token(uuid.uuid4(), "user")
    with pytest.raises(TokenTypeError):
        verify_token(token, "refresh")


def test_create_token_with_empty_role_raises() -> None:
    user_id = uuid.uuid4()
    with pytest.raises(TokenMissingClaimError):
        _ = create_access_token(user_id, "")
    with pytest.raises(TokenMissingClaimError):
        _ = create_refresh_token(user_id, "")


def test_verify_token_expired_raises() -> None:
    # 构造一个已过期的 access token（exp 在过去）
    now = _now_ts()
    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now - 10,
        "exp": now - 1,
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenExpiredError):
        verify_token(expired_token, "access")


def test_verify_token_signature_error_raises() -> None:
    # 使用错误密钥签名
    now = _now_ts()
    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + 60,
    }
    wrong_secret_token = jwt.encode(payload, "other-secret", algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenSignatureError):
        verify_token(wrong_secret_token, "access")


def test_verify_token_missing_required_claim_raises_invalid() -> None:
    # 缺少 jti，decode 阶段因 require 检查触发 InvalidTokenError → TokenInvalidError
    now = _now_ts()
    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        # "jti" 缺失
        "iat": now,
        "exp": now + 60,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenInvalidError):
        verify_token(token, "access")


def test_verify_token_malformed_uuid_claims_raises_missing_claim_error() -> None:
    # jti 与 sub 存在但不是合法 UUID
    now = _now_ts()
    payload = {
        "sub": "not-a-uuid",
        "type": "access",
        "jti": "also-not-a-uuid",
        "iat": now,
        "exp": now + 60,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenMissingClaimError):
        verify_token(token, "access")


def test_verify_token_malformed_timestamps_raises_missing_claim_error() -> None:
    # iat/exp 必须为整数
    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": "not-int",
        "exp": "not-int",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenMissingClaimError):
        verify_token(token, "access")
