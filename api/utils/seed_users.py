# 使用方法: python -m utils.seed_users

from __future__ import annotations

import os

from sqlalchemy.orm import Session

from models.base import Base
from models.users import User
from utils.db import SessionLocal, engine
from utils.logging import get_logger, init_logging
from utils.security import hash_password, verify_password


def ensure_tables() -> None:
    """确保需要的表已创建(dev/test 便捷使用)."""
    Base.metadata.create_all(bind=engine)


def upsert_user(session: Session, username: str, plain_password: str, role: str) -> tuple[User, str]:
    """插入或更新用户，返回 (user, action). action ∈ {created, updated, skipped}."""
    user = session.query(User).filter_by(username=username).one_or_none()
    if user is None:
        user = User(
            username=username,
            password_hash=hash_password(plain_password),
            role=role,
            is_active=True,
            token_version=1,
            failed_login_attempts=0,
            lock_until=None,
        )
        session.add(user)
        return user, "created"

    need_update = False

    # 角色
    if user.role != role:
        user.role = role
        need_update = True

    # 密码（若不匹配，则重置为指定默认密码）
    if not verify_password(plain_password, user.password_hash):
        user.password_hash = hash_password(plain_password)
        need_update = True

    # 状态与风控字段重置
    if not user.is_active:
        user.is_active = True
        need_update = True
    if user.failed_login_attempts != 0 or user.lock_until is not None:
        user.failed_login_attempts = 0
        user.lock_until = None
        need_update = True

    return user, ("updated" if need_update else "skipped")


def main() -> None:
    # 初始化日志
    init_logging(os.getenv("LOG_LEVEL"))
    logger = get_logger()

    logger.warning("运行开发/测试种子脚本，仅用于 dev/test 环境。目标数据库：%s", str(engine.url))

    ensure_tables()

    session: Session = SessionLocal()
    # TODO: 支持从环境变量中读取用户名和密码，放到boot.sh中执行
    try:
        targets = [
            ("admin", "123456", "admin"),
            ("user", "123456", "user"),
        ]

        results: list[tuple[str, str, str]] = []
        for username, password, role in targets:
            user, action = upsert_user(session, username, password, role)
            results.append((username, action, user.role))

        session.commit()

        for username, action, role in results:
            logger.info("user=%s action=%s role=%s", username, action, role)

    except Exception:  # pragma: no cover - 脚本运行时错误记录
        session.rollback()
        logger.exception("seed users failed")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
