from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.jwt_tokens import create_access_token, create_refresh_token, verify_token
from core.security import hash_password
from models import RefreshToken, User
from services.email_verification_service import EmailVerificationService
from utils.logging import get_logger

logger = get_logger()


class RegistrationService:
    """
    注册相关业务逻辑：
    - 校验邮箱验证码
    - 创建新用户（邮箱即用户名）
    - 签发 access/refresh 令牌并持久化刷新令牌，实现“注册即登录”
    """

    async def register_with_email_code(
        self,
        *,
        db: AsyncSession,
        email: str,
        code: str,
        password: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        email_service = EmailVerificationService()

        # 1) 校验并消费验证码
        otp_result = await email_service.verify_and_consume_code(email=email, code=code)
        if otp_result.get("code") != 0:
            # 验证码不通过，直接返回
            return otp_result

        # 2) 再次检查邮箱是否已被注册（防并发）
        try:
            stmt = select(User).where(User.username == email)
            result = await db.execute(stmt)
            existing: User | None = result.scalars().first()
            if existing and existing.is_active:
                return {"code": 40901, "message": "邮箱已注册"}
        except Exception:
            logger.exception("check existing user before registration failed")
            return {"code": 50024, "message": "注册失败"}

        # 3) 创建新用户记录
        try:
            password_hash = hash_password(password)
            user = User(
                username=email,
                password_hash=password_hash,
                role="user",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        except Exception:
            await db.rollback()
            logger.exception("create user in registration failed")
            return {"code": 50024, "message": "注册失败"}

        # 4) 注册即登录：签发令牌并持久化刷新令牌记录（与登录保持一致数据结构）
        try:
            from datetime import UTC, datetime

            # 签发 access / refresh 令牌
            access_token = create_access_token(user.id, user.role)
            refresh_token = create_refresh_token(user.id, user.role)

            # 从 refresh token 提取 jti/iat/exp
            claims = verify_token(refresh_token, "refresh")
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
                ip=client_ip,
                user_agent=user_agent,
            )
            db.add(rt)
            await db.commit()

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
            await db.rollback()
            logger.exception("issue tokens in registration failed")
            return {"code": 50025, "message": "注册成功但登录状态创建失败，请稍后手动登录"}
