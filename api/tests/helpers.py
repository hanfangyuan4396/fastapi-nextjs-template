from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import jwt
from sqlalchemy.orm import Session

from core.jwt_tokens import create_refresh_token, verify_token
from core.security import hash_password
from models import RefreshToken, User
from utils.config import settings


def create_user(db: Session, username: str, password: str, *, role: str = "user", is_active: bool = True) -> User:
    user = User(username=username, password_hash=hash_password(password), role=role, is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def persist_refresh(db: Session, user: User) -> tuple[str, RefreshToken]:
    token = create_refresh_token(user.id, user.role)
    claims = verify_token(token, "refresh")
    issued_at = datetime.fromtimestamp(int(claims["iat"]), UTC)
    expires_at = datetime.fromtimestamp(int(claims["exp"]), UTC)
    rt = RefreshToken(
        jti=str(claims["jti"]),
        parent_jti=None,
        user_id=user.id,
        issued_at=issued_at,
        expires_at=expires_at,
        revoked=False,
        revoked_reason=None,
        device_id=None,
        ip=None,
        user_agent=None,
    )
    db.add(rt)
    db.commit()
    return token, rt


def create_expired_refresh_token(db: Session, user: User) -> tuple[str, RefreshToken]:
    """构造一个已过期但签名合法的 refresh_token，并写入匹配的 DB 记录。"""
    now = int(datetime.now(UTC).timestamp())
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": now - 100,
        "exp": now - 1,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    rt = RefreshToken(
        jti=payload["jti"],
        parent_jti=None,
        user_id=user.id,
        issued_at=datetime.fromtimestamp(payload["iat"], UTC),
        expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        revoked=False,
        revoked_reason=None,
        device_id=None,
        ip=None,
        user_agent=None,
    )
    db.add(rt)
    db.commit()
    return token, rt
