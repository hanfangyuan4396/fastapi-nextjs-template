from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class User(Base):
    """用户表模型"""

    __tablename__ = "users"

    # 使用 PostgreSQL 原生 UUID 作为主键
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        comment="用户ID(UUID)",
        default=uuid4,
    )

    # 基本账号信息
    username = Column(String(50), unique=True, nullable=False, comment="用户名(唯一)")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")

    # 角色与状态
    role = Column(String(10), nullable=False, default="user", server_default="user", comment="角色：admin/user")
    is_active = Column(Boolean, nullable=False, default=True, server_default="1", comment="是否启用")

    # 令牌版本与风控字段
    token_version = Column(Integer, nullable=False, default=1, server_default="1", comment="令牌版本")
    failed_login_attempts = Column(
        Integer, nullable=False, default=0, server_default="0", comment="30分钟内连续失败次数"
    )
    lock_until = Column(DateTime, nullable=True, comment="账号锁定到期时间")

    def __repr__(self) -> str:  # pragma: no cover - 调试友好
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_safe_dict(self) -> dict[str, str | int | bool | None]:
        """脱敏后的字典，不包含敏感字段。"""
        return {
            "id": str(self.id),
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "token_version": self.token_version,
            "failed_login_attempts": self.failed_login_attempts,
            "lock_until": self.lock_until.isoformat() if isinstance(self.lock_until, datetime) else None,
        }
