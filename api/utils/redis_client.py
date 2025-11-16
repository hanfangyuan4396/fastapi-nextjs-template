from __future__ import annotations

from redis import asyncio as aioredis

from utils.config import settings
from utils.logging import get_logger

logger = get_logger()

_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """
    获取全局 Redis 客户端实例。

    - 使用简单的懒加载单例，避免在应用启动时就建立连接。
    - decode_responses=True：统一返回 str，便于后续 JSON/业务处理。
    """
    global _redis_client
    if _redis_client is None:
        logger.debug("Initializing async Redis client")
        _redis_client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
        )
    return _redis_client
