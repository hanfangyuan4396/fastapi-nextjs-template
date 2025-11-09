from __future__ import annotations

from sqlalchemy import URL

from .config import settings


def build_database_url() -> URL:
    return URL.create(
        "postgresql+psycopg",
        username=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        database=settings.DB_DATABASE,
    )


def build_async_database_url() -> URL:
    return URL.create(
        "postgresql+psycopg_async",
        username=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        database=settings.DB_DATABASE,
    )
