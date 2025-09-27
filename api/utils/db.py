from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .db_url import build_database_url

# 初始化数据库引擎与会话工厂（复用全局 settings，避免重复日志）
_database_url = build_database_url()

engine = create_engine(
    _database_url,
    pool_size=8,  # 连接池常驻连接数：每个 worker 保持 8 个连接
    max_overflow=4,  # 溢出连接数：突发时最多额外创建 4 个连接（总计 worker*(8+4)=48 连接）
    pool_timeout=10,  # 连接超时：等待可用连接的最长时间（秒），超过抛异常
    pool_recycle=1800,  # 连接回收：连接存活时间（秒），防止云环境/代理的空闲断链
    pool_pre_ping=True,  # 连接预检：取用前探测连接有效性，降低首查错误率
    echo=settings.LOG_LEVEL.upper() == "DEBUG",  # SQL 日志：仅在 DEBUG 模式下输出 SQL 语句
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 可复用的依赖别名，便于在控制器中注入
DbSession = Annotated[Session, Depends(get_db)]
