import os
import sys
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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
from utils.db import get_async_db  # noqa: E402


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return fastapi_app


@pytest_asyncio.fixture
async def async_test_engine():
    # 使用内存 aiosqlite + StaticPool；函数级作用域，确保测试隔离
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        echo=False,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(async_test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_local = async_sessionmaker(bind=async_test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_local() as session:
        yield session


# 提供异步 HTTP 客户端，驱动 ASGI 应用进行端到端异步调用
@pytest_asyncio.fixture
async def async_client(app: FastAPI, async_test_engine) -> AsyncGenerator[AsyncClient, None]:
    # 异步会话（统一使用单一异步引擎）
    async_session_local = async_sessionmaker(bind=async_test_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_async_db():
        async with async_session_local() as session:
            yield session

    app.dependency_overrides[get_async_db] = _override_get_async_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_async_db, None)
