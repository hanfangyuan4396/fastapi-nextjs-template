# 使用方法: python -m scripts.ensure_database

from __future__ import annotations

import os

import psycopg
from psycopg import sql
from sqlalchemy import URL

from utils.config import settings
from utils.logging import get_logger, init_logging


def build_maintenance_database_url() -> URL:
    """Build a PostgreSQL URL that connects to the maintenance database."""
    return URL.create(
        "postgresql",
        username=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        database=os.getenv("DB_MAINTENANCE_DATABASE", "postgres"),
    )


def database_exists(connection: psycopg.Connection, database_name: str) -> bool:
    """Return whether the target database already exists."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        return cursor.fetchone() is not None


def create_database(connection: psycopg.Connection, database_name: str) -> None:
    """Create a PostgreSQL database using a safely quoted identifier."""
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))


def ensure_database_exists(logger) -> str:
    """
    Create the configured application database if it is missing.

    Returns:
        str: `created` if the database was created, or `skipped` if it already exists.
    """
    database_name = settings.DB_DATABASE
    maintenance_url = build_maintenance_database_url()

    with psycopg.connect(str(maintenance_url), autocommit=True) as connection:
        if database_exists(connection, database_name):
            logger.info("database init result=skipped database=%s", database_name)
            return "skipped"

        create_database(connection, database_name)
        logger.info("database init result=created database=%s", database_name)
        return "created"


def main() -> None:
    """Ensure the configured application database exists before migrations run."""
    init_logging(os.getenv("LOG_LEVEL"))
    logger = get_logger()
    ensure_database_exists(logger)


if __name__ == "__main__":
    main()
