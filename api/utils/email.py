from __future__ import annotations

import smtplib
from email.message import EmailMessage

from utils.config import settings
from utils.logging import get_logger

logger = get_logger()


class EmailNotConfiguredError(RuntimeError):
    """邮箱发送配置缺失时抛出的异常。"""

    pass


def _ensure_email_config() -> None:
    """
    校验邮箱验证码发送必需的配置是否存在。

    这些配置来自 `.env`，包括：
    - EMAIL_VERIFICATION_SMTP_HOST
    - EMAIL_VERIFICATION_SMTP_PORT
    - EMAIL_VERIFICATION_SMTP_USER
    - EMAIL_VERIFICATION_SMTP_PASSWORD
    """
    if not settings.EMAIL_VERIFICATION_SMTP_HOST:
        raise EmailNotConfiguredError("EMAIL_VERIFICATION_SMTP_HOST 未配置")
    if not settings.EMAIL_VERIFICATION_SMTP_USER:
        raise EmailNotConfiguredError("EMAIL_VERIFICATION_SMTP_USER 未配置")
    if not settings.EMAIL_VERIFICATION_SMTP_PASSWORD:
        raise EmailNotConfiguredError("EMAIL_VERIFICATION_SMTP_PASSWORD 未配置")


def send_verification_email(email: str, code: str, expires_in_minutes: int) -> None:
    """
    发送邮箱验证码邮件。

    当前实现：
    - 仅支持 SMTP 协议
    - 端口 465 使用 SSL，其它端口使用 STARTTLS
    - 文本内容简单描述验证码与有效期，方便后续扩展为模板
    """
    _ensure_email_config()

    msg = EmailMessage()
    msg["Subject"] = "邮箱验证码 / Email Verification Code"
    # 部分邮箱服务商（如 163/QQ 邮箱）要求 MAIL FROM 必须与认证用户名保持一致，
    # 因此这里直接使用 SMTP 认证用户名作为发件人地址，避免配置错误导致 501 等错误。
    msg["From"] = settings.EMAIL_VERIFICATION_SMTP_USER
    msg["To"] = email

    msg.set_content(
        f"您的验证码为：{code}\n\n"
        f"验证码有效期为 {expires_in_minutes} 分钟，请尽快完成验证。\n"
        "如果这不是您的操作，请忽略此邮件。\n"
    )

    host = settings.EMAIL_VERIFICATION_SMTP_HOST
    port = settings.EMAIL_VERIFICATION_SMTP_PORT
    user = settings.EMAIL_VERIFICATION_SMTP_USER
    password = settings.EMAIL_VERIFICATION_SMTP_PASSWORD

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)

        logger.info("Verification email sent to %s", email)
    except Exception:
        logger.exception("Failed to send verification email to %s", email)
        # 往上抛出异常，由上层统一处理错误码与提示信息
        raise
