# 使用方法: python -m utils.seed_users

from __future__ import annotations

import os

from sqlalchemy.orm import Session

from core.security import hash_password
from models.users import User
from utils.db import SessionLocal
from utils.logging import get_logger, init_logging


def create_user_if_missing(
    session: Session,
    username: str,
    plain_password: str,
    role: str,
) -> tuple[User, str]:
    """
    Insert a new user if missing; do not update existing accounts.

    If a user with the given username does not exist, a new User is created with the
    provided password (hashed) and role. If the user exists, the function does not
    modify the user. The function does not commit the session; the caller is responsible
    for committing.

    Parameters:
        username (str): The username to create or update.
        plain_password (str): The plaintext password to verify against or store (will be hashed).
        role (str): The role to assign to the user.

    Returns:
        tuple[User, str]: A tuple containing the User instance and an action string:
            `'created'` if a new user was added, or `'skipped'` if no changes were necessary.
    """
    user = session.query(User).filter_by(username=username).one_or_none()
    if user is None:
        user = User(
            username=username,
            password_hash=hash_password(plain_password),
            role=role,
            is_active=True,
            token_version=1,
        )
        session.add(user)
        return user, "created"

    return user, "skipped"


def create_admin_if_missing(
    session: Session,
    *,
    username: str,
    plain_password: str,
) -> str:
    """Create admin user if missing; do not update existing accounts."""
    existing = session.query(User).filter_by(username=username).one_or_none()
    if existing is not None:
        return "skipped"

    user = User(
        username=username,
        password_hash=hash_password(plain_password),
        role="admin",
        is_active=True,
        token_version=1,
    )
    session.add(user)
    return "created"


def _get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"missing required environment variable: {key}")
    return value


def _run_init_admin(session: Session, logger) -> None:
    username = _get_required_env("DEFAULT_ADMIN_USERNAME")
    password = _get_required_env("DEFAULT_ADMIN_PASSWORD")

    try:
        action = create_admin_if_missing(session, username=username, plain_password=password)
        session.commit()
        logger.info("init admin result=%s username=%s", action, username)
    except Exception:  # pragma: no cover - 脚本运行时错误记录
        session.rollback()
        logger.exception("init admin failed")
        raise
    finally:
        session.close()


def main() -> None:
    # 初始化日志
    """
    Initialize default admin from environment variables.
    """
    init_logging(os.getenv("LOG_LEVEL"))
    logger = get_logger()

    session: Session = SessionLocal()
    _run_init_admin(session, logger)


if __name__ == "__main__":
    main()
