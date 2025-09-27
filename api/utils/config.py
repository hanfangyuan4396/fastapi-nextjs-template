import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _load_env_file() -> None:
    """在模块导入时加载 .env（不覆盖系统环境变量）。"""
    env_path = Path(__file__).with_name("..").resolve().joinpath(".env")
    if not env_path.exists():
        env_path = Path(__file__).with_name("..").resolve().joinpath(".env.example")
    load_dotenv(dotenv_path=env_path, override=False)


# 提前加载 .env，确保 LOG_LEVEL 等环境变量可用于日志初始化
_load_env_file()

# 初始化日志，使 Settings 初始化期间的 DEBUG 日志可见
from utils.logging import init_logging  # noqa: E402

init_logging(os.getenv("LOG_LEVEL"))

# 模块级 logger（具体输出行为取决于外部 logging 配置）
logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """配置校验异常"""

    pass


class Settings:
    """
    应用配置项（来源于环境变量 .env 或系统环境）。仅保留与 `api/.env.example` 对齐的配置：

    基础
    - ENABLE_DOCS: 是否启用接口文档（true/false）。默认 false
    - LOG_LEVEL: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）。默认 INFO

    数据库（PostgreSQL）
    - DB_USERNAME: 数据库用户名。默认 postgres
    - DB_PASSWORD: 数据库密码。默认 postgres
    - DB_HOST: 数据库主机。默认 localhost
    - DB_PORT: 数据库端口。默认 5432
    - DB_DATABASE: 数据库名。默认 fastapi-nextjs
    """

    def __init__(self) -> None:
        # 基础运行环境
        self.ENABLE_DOCS: bool = os.getenv("ENABLE_DOCS", "false").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

        # 数据库连接配置
        self.DB_USERNAME: str = os.getenv("DB_USERNAME", "postgres")
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
        self.DB_HOST: str = os.getenv("DB_HOST", "localhost")
        self.DB_PORT: str = os.getenv("DB_PORT", "5432")
        self.DB_DATABASE: str = os.getenv("DB_DATABASE", "fastapi-nextjs")

        # 构造函数不打印日志，避免多次实例化导致重复日志

        # 配置完整性校验
        self._validate_config()

    def _validate_config(self) -> None:
        """
        验证配置完整性

        Raises:
            ConfigValidationError: 当配置不完整时抛出异常
        """
        # 开发环境不强制做严格校验；在实际使用对应配置的功能处再做必要字段校验
        return

    def _to_safe_dict(self) -> dict[str, Any]:
        """
        返回屏蔽敏感字段后的配置字典，仅用于调试日志输出。
        """
        return {
            "ENABLE_DOCS": self.ENABLE_DOCS,
            "LOG_LEVEL": self.LOG_LEVEL,
            "DB_USERNAME": self.DB_USERNAME,
            "DB_PASSWORD": "***" if self.DB_PASSWORD else "",
            "DB_HOST": self.DB_HOST,
            "DB_PORT": self.DB_PORT,
            "DB_DATABASE": self.DB_DATABASE,
        }


settings = Settings()
# 创建单例后打印一次配置（已脱敏）
logger.debug("Loaded settings: %s", settings._to_safe_dict())
