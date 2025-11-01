from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from models import RefreshToken, User
from utils.jwt_tokens import create_access_token, create_refresh_token, verify_token
from utils.logging import get_logger
from utils.security import verify_password

logger = get_logger()


class AuthService:
    @staticmethod
    def _normalize_utc(dt: datetime | None) -> datetime | None:
        """将 datetime 统一规范为 UTC 以便进行安全比较。"""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    def login(
        self,
        *,
        db: Session,
        username: str,
        password: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        """
        登录校验：
        - 检查用户是否存在、是否锁定、是否启用
        - 验证密码，成功则签发 access/refresh 令牌
        - 持久化刷新令牌记录（含 jti/生命周期/客户端信息）
        - 成功后重置失败次数

        注意：失败计数与锁定策略的窗口计算在 6.1 中扩展，这里只做基础读写与锁定检查。
        """
        try:
            user: User | None = db.query(User).filter(User.username == username).first()
            if user is None:
                # 匿名报错，不泄露用户名是否存在
                return {"code": 40101, "message": "用户名或密码错误"}

            # 锁定检查与窗口清理：
            # - 30 分钟窗口：失败次数在窗口外自动重置
            # - 连续 5 次失败：设置锁定 1 小时
            now = datetime.now(UTC)

            lock_cmp = self._normalize_utc(user.lock_until) if isinstance(user.lock_until, datetime) else None
            if lock_cmp is not None:
                # 处于锁定状态：当失败次数达到阈值并且未到解锁时间
                if int(user.failed_login_attempts or 0) >= 5 and now < lock_cmp:
                    return {"code": 40301, "message": "账号已锁定，请稍后再试"}
                # 若窗口/锁定已过期，重置状态
                if now >= lock_cmp and int(user.failed_login_attempts or 0) > 0:
                    user.failed_login_attempts = 0
                    user.lock_until = None
                    try:
                        db.add(user)
                        db.commit()
                    except Exception:
                        db.rollback()
                        logger.exception("reset failed attempts window failed")

            if not user.is_active:
                return {"code": 40302, "message": "账号已禁用"}

            if not verify_password(password, user.password_hash):
                # 失败计数 + 窗口策略（30 分钟；达到 5 次锁 1 小时）
                try:
                    attempts = int(user.failed_login_attempts or 0)
                    # 重新计算窗口是否有效
                    lock_cmp = self._normalize_utc(user.lock_until) if isinstance(user.lock_until, datetime) else None
                    window_active = lock_cmp is not None and now < lock_cmp and attempts > 0
                    # 若未在窗口内（空/已过/未计数），开启新窗口
                    if not window_active:
                        user.failed_login_attempts = 1
                        user.lock_until = now + timedelta(minutes=30)

                    else:
                        # 相当于：user.lock_until is not None and now < user.lock_until and attempts > 0
                        # 窗口内累加
                        attempts += 1
                        user.failed_login_attempts = attempts
                        if attempts >= 5:
                            # 达到阈值：锁定 1 小时
                            user.lock_until = now + timedelta(hours=1)
                        else:
                            # 仍在窗口内：窗口结束时间保持不变
                            pass

                    db.add(user)
                    db.commit()
                except Exception:
                    db.rollback()
                    logger.exception("update failed attempts with window failed")

                # 达到阈值并处于锁定期，直接返回 403
                lock_cmp = self._normalize_utc(user.lock_until) if isinstance(user.lock_until, datetime) else None
                if int(user.failed_login_attempts or 0) >= 5 and lock_cmp is not None and now < lock_cmp:
                    return {"code": 40301, "message": "账号已锁定，请稍后再试"}
                return {"code": 40101, "message": "用户名或密码错误"}

            # 密码通过：签发令牌
            access_token = create_access_token(user.id)
            refresh_token = create_refresh_token(user.id)

            # 解析刷新令牌以获取 jti/iat/exp（保证与 JWT 完全一致）
            claims = verify_token(refresh_token, "refresh")
            issued_at = datetime.fromtimestamp(int(claims["iat"]), UTC)
            expires_at = datetime.fromtimestamp(int(claims["exp"]), UTC)

            # 持久化刷新令牌记录
            rt = RefreshToken(
                jti=str(claims["jti"]),
                parent_jti=None,
                user_id=user.id,
                issued_at=issued_at,
                expires_at=expires_at,
                revoked=False,
                revoked_reason=None,
                device_id=device_id,
                ip=client_ip,
                user_agent=user_agent,
            )
            db.add(rt)
            # 成功登录重置失败次数
            user.failed_login_attempts = 0
            db.add(user)
            db.commit()

            # 返回 access_token；refresh_token 由控制器写入 Cookie
            return {
                "code": 0,
                "message": "ok",
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "refresh_expires_at": int(expires_at.timestamp()),
                },
            }
        except Exception:
            db.rollback()
            logger.exception("Login failed")
            return {"code": 50010, "message": "登录失败"}
