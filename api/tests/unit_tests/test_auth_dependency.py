from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.auth_dependency import get_current_user
from core.jwt_tokens import create_access_token
from tests.helpers import create_user
from utils.config import settings


def test_get_current_user_missing_token_401(db_session: Session):
    with pytest.raises(HTTPException) as ei:
        get_current_user(authorization=None, db=db_session)
    assert ei.value.status_code == 401


def test_get_current_user_signature_invalid_401(db_session: Session):
    user = create_user(db_session, "alice", "123456")
    token = create_access_token(user.id, user.role)
    # 直接篡改 JWT 的签名段首字符，确保解码后的字节发生变化
    parts = token.split(".")
    assert len(parts) == 3
    header, payload, signature = parts
    mutated_sig = ("A" if signature and signature[0] != "A" else "B") + signature[1:]
    bad = ".".join([header, payload, mutated_sig])
    with pytest.raises(HTTPException) as ei:
        get_current_user(authorization=f"Bearer {bad}", db=db_session)
    assert ei.value.status_code == 401


def test_get_current_user_expired_401(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    user = create_user(db_session, "bob", "123456")
    token = create_access_token(user.id, user.role)

    future = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES + 1)
    from core import jwt_tokens as jwt_mod

    monkeypatch.setattr(jwt_mod, "_now", lambda: future)

    with pytest.raises(HTTPException) as ei:
        get_current_user(authorization=f"Bearer {token}", db=db_session)
    assert ei.value.status_code == 401


def test_get_current_user_success_returns_user(db_session: Session):
    user = create_user(db_session, "carol", "123456")
    token = create_access_token(user.id, user.role)

    got = get_current_user(authorization=f"Bearer {token}", db=db_session)
    assert got.id == user.id
    assert got.username == user.username
