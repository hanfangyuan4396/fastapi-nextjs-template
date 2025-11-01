from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class RefreshToken(Base):
    """刷新令牌持久化记录。

    支持令牌家族（parent_jti）、轮换、撤销与审计。
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, comment="自增ID")

    # JWT 唯一 ID 与父链
    jti = Column(String(36), unique=True, nullable=False, comment="当前刷新令牌 JTI(唯一)")
    parent_jti = Column(String(36), nullable=True, comment="父刷新令牌 JTI，用于家族/链追踪")

    # 归属用户（PostgreSQL 原生 UUID）
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")

    # 生命周期
    issued_at = Column(DateTime, nullable=False, comment="签发时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    used_at = Column(DateTime, nullable=True, comment="已使用时间（轮换时置位）")

    # 撤销与元信息
    revoked = Column(Boolean, nullable=False, default=False, server_default="0", comment="是否撤销")
    revoked_reason = Column(String(200), nullable=True, comment="撤销原因")
    device_id = Column(String(100), nullable=True, comment="设备ID")
    ip = Column(String(64), nullable=True, comment="IP 地址")
    user_agent = Column(String(255), nullable=True, comment="User-Agent")

    __table_args__ = (
        # 常用查询字段索引
        Index("refresh_tokens_user_id_idx", "user_id"),
        Index("refresh_tokens_parent_jti_idx", "parent_jti"),
        Index("refresh_tokens_expires_at_idx", "expires_at"),
    )

    def _as_utc(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    def is_expired(self, now: datetime | None = None) -> bool:
        ref = self._as_utc(now) if isinstance(now, datetime) else datetime.now(UTC)
        exp = self._as_utc(self.expires_at)
        return ref >= exp

    def mark_used(self, when: datetime | None = None) -> None:
        self.used_at = when or datetime.now(UTC)

    def mark_revoked(self, reason: str | None = None) -> None:
        self.revoked = True
        self.revoked_reason = reason or self.revoked_reason
