from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.jwt_tokens import create_refresh_token, verify_token
from core.security import hash_password
from models import RefreshToken, User
from utils.config import settings

# ==================== 同步版本（用于同步测试） ====================


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
        "role": user.role,
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


# ==================== 异步版本（用于异步测试） ====================


async def async_create_user(
    db: AsyncSession, username: str, password: str, *, role: str = "user", is_active: bool = True
) -> User:
    user = User(username=username, password_hash=hash_password(password), role=role, is_active=is_active)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def async_persist_refresh(db: AsyncSession, user: User) -> tuple[str, RefreshToken]:
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
    await db.commit()
    return token, rt


async def async_create_expired_refresh_token(db: AsyncSession, user: User) -> tuple[str, RefreshToken]:
    """构造一个已过期但签名合法的 refresh_token，并写入匹配的 DB 记录（异步版本）。"""
    now = int(datetime.now(UTC).timestamp())
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": now - 100,
        "exp": now - 1,
        "role": user.role,
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
    await db.commit()
    return token, rt


class FakeRedis:
    """
    简单的内存版 Redis 实现，用于测试：
    - 支持 incr/expire/hset/hgetall/delete
    - 忽略 TTL，仅用于逻辑校验
    """

    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    async def incr(self, key: str) -> int:
        value = int(self._store.get(key, 0)) + 1
        self._store[key] = value
        return value

    async def expire(self, key: str, _seconds: int) -> None:
        # 为简化测试逻辑，这里不实现真正的过期行为
        return None

    async def hset(self, key: str, mapping: dict[str, str]) -> None:
        # 更新部分字段，保留其他字段（符合真实 Redis 行为）
        if key not in self._store:
            self._store[key] = {}
        if not isinstance(self._store[key], dict):
            self._store[key] = {}
        self._store[key].update(mapping)

    async def hgetall(self, key: str) -> dict[str, str]:
        value = self._store.get(key)
        if isinstance(value, dict):
            return dict(value)
        return {}

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
