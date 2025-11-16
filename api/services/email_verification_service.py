from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from typing import Any

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, verify_password
from models import User
from utils.config import settings
from utils.email import EmailNotConfiguredError, send_verification_email
from utils.logging import get_logger
from utils.redis_client import get_redis

logger = get_logger()


class EmailVerificationService:
    """
    邮箱验证码业务逻辑：
    - 生成并发送验证码
    - 按邮箱/IP 做频率限制
    - 将验证码及元数据存入 Redis
    - 提供校验/消费验证码的能力
    """

    # Redis key 前缀
    KEY_PREFIX_CODE = "auth:email_verification:code"
    KEY_PREFIX_RATE_EMAIL = "auth:email_verification:rate:email"
    KEY_PREFIX_RATE_IP = "auth:email_verification:rate:ip"

    # 业务场景常量，预留未来扩展（如 reset_password）
    SCENE_REGISTER = "register"

    # 频控时间窗口（秒）
    RATE_LIMIT_WINDOW_SECONDS = 60

    # 验证码最大允许失败次数
    MAX_ATTEMPTS = 5

    @classmethod
    def _build_code_key(cls, *, scene: str, email: str) -> str:
        return f"{cls.KEY_PREFIX_CODE}:{scene}:{email}"

    @classmethod
    def _build_rate_email_key(cls, email: str) -> str:
        return f"{cls.KEY_PREFIX_RATE_EMAIL}:{email}"

    @classmethod
    def _build_rate_ip_key(cls, ip: str) -> str:
        return f"{cls.KEY_PREFIX_RATE_IP}:{ip}"

    @staticmethod
    def _generate_numeric_code(length: int = 6) -> str:
        # 生成指定位数的数字验证码（0-9）
        # 使用 os.urandom 保证一定的随机性
        digits = []
        for _ in range(length):
            # 生成一个 0-9 的数字
            value = os.urandom(1)[0] % 10
            digits.append(str(value))
        return "".join(digits)

    async def send_register_code(
        self,
        *,
        db: AsyncSession,
        email: str,
        client_ip: str | None = None,
    ) -> dict[str, Any]:
        """
        注册场景：发送邮箱验证码。

        流程：
        - 校验邮箱格式
        - 检查邮箱是否已存在并且为激活状态，如是则返回错误
        - 频率限制（按邮箱 + IP）
        - 生成 6 位数字验证码，计算哈希并写入 Redis（带 TTL）
        - 通过 SMTP 发送验证码邮件
        """
        try:
            # 使用 Pydantic 的 EmailStr + TypeAdapter 进行格式校验（兼容 Pydantic v2 的 Annotated 类型）
            valid_email = TypeAdapter(EmailStr).validate_python(email)
        except ValidationError:
            return {"code": 42201, "message": "邮箱格式不合法"}

        try:
            # 异步查询用户信息
            stmt = select(User).where(User.username == str(valid_email))
            result = await db.execute(stmt)
            existing: User | None = result.scalars().first()
            if existing and existing.is_active:
                return {"code": 40901, "message": "邮箱已注册"}
        except Exception:
            logger.exception("check existing user for email failed")
            return {"code": 50020, "message": "检查邮箱状态失败"}

        r = get_redis()

        # 频率限制：邮箱维度
        email_key = self._build_rate_email_key(str(valid_email))
        try:
            email_count = await r.incr(email_key)
            if email_count == 1:
                # 首次设置过期时间
                await r.expire(email_key, self.RATE_LIMIT_WINDOW_SECONDS)
            if email_count > settings.EMAIL_VERIFICATION_RATE_LIMIT_PER_EMAIL:
                return {"code": 42901, "message": "验证码发送过于频繁，请稍后再试"}
        except Exception:
            logger.exception("email-based rate limit failed")
            return {"code": 50021, "message": "发送验证码失败"}

        # 频率限制：IP 维度（若有 IP）
        if client_ip:
            ip_key = self._build_rate_ip_key(client_ip)
            try:
                ip_count = await r.incr(ip_key)
                if ip_count == 1:
                    await r.expire(ip_key, self.RATE_LIMIT_WINDOW_SECONDS)
                if ip_count > settings.EMAIL_VERIFICATION_RATE_LIMIT_PER_IP:
                    return {"code": 42902, "message": "当前 IP 请求过于频繁，请稍后再试"}
            except Exception:
                logger.exception("ip-based rate limit failed")
                return {"code": 50021, "message": "发送验证码失败"}

        # 生成验证码并写入 Redis
        code = self._generate_numeric_code(6)
        # 复用密码哈希逻辑（argon2），避免自己管理盐值配置
        code_hash = hash_password(code)

        ttl_seconds = settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES * 60
        now = datetime.now(UTC)

        code_key = self._build_code_key(scene=self.SCENE_REGISTER, email=str(valid_email))

        # 存储字段：
        # - code_hash: 验证码哈希
        # - scene: 使用场景
        # - created_at: 创建时间（ISO）
        # - used: 是否已使用（"0"/"1"）
        # - failed_attempts: 当前失败次数
        # - ip: 最后一次请求 IP（可用于风控）
        # 通过 TTL 控制过期，无需单独存储过期时间字段
        # max_attempts 使用类变量 MAX_ATTEMPTS，不存储到 Redis
        try:
            await r.hset(
                code_key,
                mapping={
                    "code_hash": code_hash,
                    "scene": self.SCENE_REGISTER,
                    "created_at": now.isoformat(),
                    "used": "0",
                    "failed_attempts": "0",
                    "ip": client_ip or "",
                },
            )
            await r.expire(code_key, ttl_seconds)
        except Exception:
            logger.exception("store verification code in redis failed")
            return {"code": 50021, "message": "发送验证码失败"}

        # 发送邮件（在线程池中执行，避免阻塞事件循环）
        try:
            await asyncio.to_thread(
                send_verification_email,
                str(valid_email),
                code,
                settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES,
            )
        except EmailNotConfiguredError as err:
            # 配置不完整，属于服务端配置错误
            logger.exception("email verification config not set correctly")
            return {"code": 50022, "message": str(err)}
        except Exception:
            logger.exception("send verification email failed")
            return {"code": 50021, "message": "发送验证码失败"}

        return {"code": 0, "message": "ok", "data": {"expires_in": ttl_seconds}}

    async def verify_and_consume_code(
        self,
        *,
        email: str,
        code: str,
    ) -> dict[str, Any]:
        """
        校验并消费注册场景的验证码（不创建用户，只负责验证码本身的合法性验证）。

        - 验证码不存在 / 已过期：返回错误
        - 已标记为 used：返回错误
        - 失败次数超过上限：返回错误
        - 匹配失败：失败次数 +1，并在超过阈值时视为失效
        - 匹配成功：删除 Redis key，表示验证码已消费
        """
        try:
            valid_email = TypeAdapter(EmailStr).validate_python(email)
        except ValidationError:
            return {"code": 42201, "message": "邮箱格式不合法"}

        if not isinstance(code, str) or not code:
            return {"code": 42202, "message": "验证码格式不合法"}

        r = get_redis()
        code_key = self._build_code_key(scene=self.SCENE_REGISTER, email=str(valid_email))

        try:
            data = await r.hgetall(code_key)
        except Exception:
            logger.exception("read verification code from redis failed")
            return {"code": 50023, "message": "验证码验证失败"}

        if not data:
            return {"code": 40001, "message": "验证码不存在或已过期"}

        # 基本状态检查
        used = data.get("used", "0")
        if used == "1":
            return {"code": 40002, "message": "验证码已使用，请重新获取"}

        failed_attempts_raw = data.get("failed_attempts") or "0"
        try:
            failed_attempts = int(failed_attempts_raw)
        except ValueError:
            failed_attempts = 0

        if failed_attempts >= self.MAX_ATTEMPTS:
            # 已达最大失败次数，视为失效
            try:
                await r.delete(code_key)
            except Exception:
                logger.exception("delete invalid verification code failed")
            return {"code": 40003, "message": "验证码错误次数过多，请重新获取"}

        # 验证哈希：复用密码校验逻辑
        expected_hash = data.get("code_hash") or ""

        if not expected_hash or not verify_password(code, expected_hash):
            # 验证失败：失败次数 +1
            failed_attempts += 1
            try:
                await r.hset(code_key, mapping={"failed_attempts": str(failed_attempts)})
            except Exception:
                logger.exception("update failed_attempts for verification code failed")

            if failed_attempts >= self.MAX_ATTEMPTS:
                try:
                    await r.delete(code_key)
                except Exception:
                    logger.exception("delete verification code after too many failures failed")
                return {"code": 40003, "message": "验证码错误次数过多，请重新获取"}

            return {"code": 40004, "message": "验证码错误"}

        # 匹配成功：删除 key 视为已消费
        try:
            await r.delete(code_key)
        except Exception:
            logger.exception("delete verification code after success failed")

        return {"code": 0, "message": "ok"}
