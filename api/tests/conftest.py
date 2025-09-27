import os
import sys
from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
from utils.db import get_db  # noqa: E402


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


@pytest.fixture
def client(app: FastAPI, test_engine) -> Generator[TestClient, None, None]:
    testing_session_local = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False
    )

    def _override_get_db() -> Generator[Session, None, None]:
        session: Session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
