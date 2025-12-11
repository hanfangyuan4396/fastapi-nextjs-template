from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from core.jwt_tokens import create_refresh_token, verify_token
from core.security import hash_password
from models import RefreshToken, User
from utils.config import settings


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
    await db.commit()
    return token, rt


class FakeRedis:
    """
    简单的内存版 Redis 实现，用于测试：
    - 支持 incr/expire/hset/hgetall/delete/get/set/setex/exists/ttl
    - 忽略 TTL，仅用于逻辑校验（除非明确设置 _ttl 字典）
    """

    def __init__(self) -> None:
        self._store: dict[str, object] = {}
        self._ttl: dict[str, int] = {}  # key -> ttl seconds（仅用于测试验证）

    async def incr(self, key: str) -> int:
        value = int(self._store.get(key, 0)) + 1
        self._store[key] = value
        return value

    async def expire(self, key: str, seconds: int) -> None:
        # 记录 TTL 供测试验证
        self._ttl[key] = seconds

    async def get(self, key: str) -> str | None:
        value = self._store.get(key)
        if value is None:
            return None
        return str(value)

    async def set(self, key: str, value: str) -> None:
        self._store[key] = value

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self._store[key] = value
        self._ttl[key] = seconds

    async def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    async def ttl(self, key: str) -> int:
        if key not in self._store:
            return -2  # key 不存在
        return self._ttl.get(key, -1)  # -1 表示无过期

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

    async def delete(self, *keys: str) -> None:
        for key in keys:
            self._store.pop(key, None)
            self._ttl.pop(key, None)
