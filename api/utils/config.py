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

    鉴权（JWT）
    - JWT_SECRET: 签名密钥（HS256）。默认 dev-secret-change-me（请在生产环境中覆盖）
    - JWT_ALGORITHM: 签名算法。固定 HS256
    - ACCESS_TOKEN_EXPIRES_MINUTES: 访问令牌有效期（分钟）。默认 60
    - REFRESH_TOKEN_EXPIRES_DAYS: 刷新令牌有效期（天）。默认 7
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

        # JWT 配置
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        # 允许字符串或数字，统一转为 int
        self.ACCESS_TOKEN_EXPIRES_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
        self.REFRESH_TOKEN_EXPIRES_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", "7"))

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
            "JWT_SECRET": "***" if self.JWT_SECRET else "",
            "JWT_ALGORITHM": self.JWT_ALGORITHM,
            "ACCESS_TOKEN_EXPIRES_MINUTES": self.ACCESS_TOKEN_EXPIRES_MINUTES,
            "REFRESH_TOKEN_EXPIRES_DAYS": self.REFRESH_TOKEN_EXPIRES_DAYS,
        }


settings = Settings()
# 创建单例后打印一次配置（已脱敏）
logger.debug("Loaded settings: %s", settings._to_safe_dict())
