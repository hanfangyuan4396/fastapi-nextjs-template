from unittest.mock import MagicMock, Mock

from scripts import ensure_database


def test_build_maintenance_connection_kwargs_uses_configured_database_settings():
    """测试维护库连接参数直接使用当前数据库配置。"""
    kwargs = ensure_database.build_maintenance_connection_kwargs()

    assert kwargs == {
        "dbname": "postgres",
        "user": ensure_database.settings.DB_USERNAME,
        "password": ensure_database.settings.DB_PASSWORD,
        "host": ensure_database.settings.DB_HOST,
        "port": int(ensure_database.settings.DB_PORT),
    }


def test_database_exists_returns_true_when_database_found():
    """测试目标数据库存在时返回 True。"""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)

    result = ensure_database.database_exists(connection, "auto_review_format")

    assert result is True
    cursor.execute.assert_called_once_with("SELECT 1 FROM pg_database WHERE datname = %s", ("auto_review_format",))


def test_database_exists_returns_false_when_database_missing():
    """测试目标数据库不存在时返回 False。"""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = ensure_database.database_exists(connection, "auto_review_format")

    assert result is False


def test_create_database_uses_safe_identifier():
    """测试创建数据库时使用 psycopg Identifier 处理数据库名。"""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value

    ensure_database.create_database(connection, "auto_review_format")

    statement = cursor.execute.call_args.args[0]
    assert statement.as_string(None) == 'CREATE DATABASE "auto_review_format"'


def test_ensure_database_exists_skips_existing_database(monkeypatch):
    """测试数据库已存在时不会执行创建操作。"""
    logger = Mock()
    connection = Mock()
    connect_context = Mock()
    connect_context.__enter__ = Mock(return_value=connection)
    connect_context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(ensure_database.psycopg, "connect", Mock(return_value=connect_context))
    monkeypatch.setattr(ensure_database, "database_exists", Mock(return_value=True))
    monkeypatch.setattr(ensure_database, "create_database", Mock())

    result = ensure_database.ensure_database_exists(logger)

    assert result == "skipped"
    ensure_database.psycopg.connect.assert_called_once_with(
        **ensure_database.build_maintenance_connection_kwargs(),
        autocommit=True,
    )
    ensure_database.create_database.assert_not_called()
    logger.info.assert_called_once_with(
        "database init result=skipped database=%s",
        ensure_database.settings.DB_DATABASE,
    )


def test_ensure_database_exists_creates_missing_database(monkeypatch):
    """测试数据库不存在时会创建目标数据库。"""
    logger = Mock()
    connection = Mock()
    connect_context = Mock()
    connect_context.__enter__ = Mock(return_value=connection)
    connect_context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(ensure_database.psycopg, "connect", Mock(return_value=connect_context))
    monkeypatch.setattr(ensure_database, "database_exists", Mock(return_value=False))
    monkeypatch.setattr(ensure_database, "create_database", Mock())

    result = ensure_database.ensure_database_exists(logger)

    assert result == "created"
    ensure_database.create_database.assert_called_once_with(connection, ensure_database.settings.DB_DATABASE)
    logger.info.assert_called_once_with(
        "database init result=created database=%s",
        ensure_database.settings.DB_DATABASE,
    )
