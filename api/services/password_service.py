from __future__ import annotations

from typing import Any

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, verify_password
from models import User
from services.email_verification_service import EmailVerificationService
from utils.logging import get_logger

logger = get_logger()


class PasswordService:
    """密码相关业务逻辑：修改密码、忘记密码重置。"""

    async def change_password(
        self,
        *,
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str,
        confirm_password: str,
    ) -> dict[str, Any]:
        if not old_password or not new_password or not confirm_password:
            return {"code": 42203, "message": "密码不能为空"}

        if new_password != confirm_password:
            return {"code": 42204, "message": "两次新密码不一致"}

        if len(new_password) < 6:
            return {"code": 42205, "message": "新密码长度至少 6 位"}

        if not verify_password(old_password, user.password_hash):
            return {"code": 40010, "message": "旧密码错误"}

        try:
            user.password_hash = hash_password(new_password)
            db.add(user)
            await db.commit()
            return {"code": 0, "message": "ok"}
        except Exception:
            await db.rollback()
            logger.exception("change password failed")
            return {"code": 50030, "message": "修改密码失败"}

    async def reset_password(
        self,
        *,
        db: AsyncSession,
        email: str,
        code: str,
        new_password: str,
        confirm_password: str,
    ) -> dict[str, Any]:
        try:
            valid_email = TypeAdapter(EmailStr).validate_python(email)
        except ValidationError:
            return {"code": 42201, "message": "邮箱格式不合法"}

        if not code:
            return {"code": 42202, "message": "验证码格式不合法"}

        if not new_password or not confirm_password:
            return {"code": 42203, "message": "密码不能为空"}

        if new_password != confirm_password:
            return {"code": 42204, "message": "两次新密码不一致"}

        if len(new_password) < 6:
            return {"code": 42205, "message": "新密码长度至少 6 位"}

        email_service = EmailVerificationService()
        otp_result = await email_service.verify_and_consume_code(
            email=str(valid_email),
            code=code,
            scene=EmailVerificationService.SCENE_RESET_PASSWORD,
        )
        if otp_result.get("code") != 0:
            return otp_result

        try:
            stmt = select(User).where(User.username == str(valid_email))
            result = await db.execute(stmt)
            user: User | None = result.scalars().first()
            if user is None or not user.is_active:
                return {"code": 40401, "message": "邮箱不存在"}
        except Exception:
            logger.exception("check user for reset password failed")
            return {"code": 50031, "message": "重置密码失败"}

        try:
            user.password_hash = hash_password(new_password)
            db.add(user)
            await db.commit()
            return {"code": 0, "message": "ok"}
        except Exception:
            await db.rollback()
            logger.exception("reset password failed")
            return {"code": 50031, "message": "重置密码失败"}
