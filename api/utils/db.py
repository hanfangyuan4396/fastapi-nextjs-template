# TODO: 数据库文件单独整理一个目录

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .db_url import build_async_database_url, build_database_url

# 同步引擎与会话工厂（仅用于 CLI 脚本如 seed_users.py）
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

# 异步引擎与会话（用于 FastAPI 控制器和服务）
_async_database_url = build_async_database_url()
async_engine = create_async_engine(
    _async_database_url,
    pool_size=8,
    max_overflow=4,
    pool_timeout=10,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=settings.LOG_LEVEL.upper() == "DEBUG",
)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# 可复用的依赖别名，便于在控制器中注入
AsyncDbSession = Annotated[AsyncSession, Depends(get_async_db)]
