from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

# 读取 alembic.ini 的配置对象
config = context.config

# 日志（可选）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---- 目标元数据：来自项目的 Base ----
# 确保可以导入到项目根目录
import sys
from pathlib import Path

# 将 api 目录加入 sys.path（相对于 api/migrations/env.py 向上一级）
API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

# 导入模型与配置（以 api 为根目录）
from models.base import Base  # noqa: E402
from utils.config import settings  # noqa: E402
from utils.db_url import build_database_url  # noqa: E402

target_metadata = Base.metadata

# 使用全局 settings 组装数据库 URL（避免重复日志）
database_url = build_database_url()


def run_migrations_offline() -> None:
    context.configure(
        url=str(database_url),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
