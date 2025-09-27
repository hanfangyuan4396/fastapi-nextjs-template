import logging
import os

_INITIALIZED = False


def init_logging(level: str | None = None) -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return
    log_level_name = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=log_level,
            # 显示具体打印日志的文件和行号
            format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
        )
    else:
        logging.getLogger().setLevel(log_level)
    _INITIALIZED = True


def get_logger() -> logging.Logger:
    """获取 root logger（统一使用全局格式，包含文件名与行号）。"""
    return logging.getLogger()
