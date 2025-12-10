import os
import sys
from collections.abc import Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def _ensure_api_dir_on_syspath() -> None:
    """Ensure `api/` directory is on sys.path so `from xx.yy` works.

    Tests live in `api/tests`. Adding the parent directory (`api`) to sys.path
    makes the `xx.yy` package importable from project root.
    """

    tests_dir = os.path.dirname(__file__)
    api_dir = os.path.abspath(os.path.join(tests_dir, os.pardir))
    if api_dir not in sys.path:
        sys.path.insert(0, api_dir)


_ensure_api_dir_on_syspath()

# 现在可以安全导入 api 包内模块
from app import app as fastapi_app  # noqa: E402
from models.base import Base  # noqa: E402
from utils.db import get_async_db, get_db  # noqa: E402


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return fastapi_app


# TODO: sqlite用于测试是否可靠，学习dify或其他项目的测试方案，是否可以使用mock
@pytest.fixture
def test_engine():
    # 使用内存 SQLite + StaticPool 保证同一引擎内多连接共享一个内存库；函数级作用域实现测试隔离
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    testing_session_local = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False
    )
    session: Session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest_asyncio.fixture
async def async_test_engine():
    # 使用内存 aiosqlite；函数级作用域，确保测试隔离
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(async_test_engine) -> AsyncSession:
    async_session_local = async_sessionmaker(bind=async_test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_local() as session:
        yield session


# 提供异步 HTTP 客户端，驱动 ASGI 应用进行端到端异步调用
@pytest_asyncio.fixture
async def async_client(app: FastAPI, test_engine, async_test_engine) -> AsyncClient:
    # 同步会话（用于仍依赖同步 DB 的依赖路径）
    testing_session_local = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False
    )
    # 异步会话（用于 students 等已异步化模块）
    async_session_local = async_sessionmaker(bind=async_test_engine, class_=AsyncSession, expire_on_commit=False)

    def _override_get_db() -> Generator[Session, None, None]:
        session: Session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    async def _override_get_async_db():
        async with async_session_local() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_async_db] = _override_get_async_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_async_db, None)
