"""登录频率限制服务 - 使用 Redis 管理登录失败计数与账号锁定。

设计原理：
- 失败窗口：30 分钟内累计失败次数
- 锁定策略：达到 5 次失败后锁定 1 小时
- Redis Key 设计：
  - login:fail:{username} - 失败计数（带 30 分钟 TTL）
  - login:lock:{username} - 锁定标记（带 1 小时 TTL）

优势：
1. 原子操作：INCR 避免并发问题
2. 自动过期：TTL 自动清理，无需定时任务
3. 高性能：Redis 读写比 PostgreSQL 快 10-100 倍
4. 不污染用户表：业务数据与风控数据分离
"""

from __future__ import annotations

from redis import asyncio as aioredis

from utils.logging import get_logger
from utils.redis_client import get_redis

logger = get_logger()


class LoginRateLimitService:
    """登录频率限制服务。"""

    # Key 前缀
    FAIL_KEY_PREFIX = "login:fail:"
    LOCK_KEY_PREFIX = "login:lock:"

    # 策略参数
    MAX_ATTEMPTS = 5  # 最大失败次数
    FAIL_WINDOW_SECONDS = 30 * 60  # 30 分钟失败窗口
    LOCK_DURATION_SECONDS = 60 * 60  # 1 小时锁定期

    def __init__(self, redis: aioredis.Redis | None = None) -> None:
        """初始化服务。

        Args:
            redis: 可选的 Redis 客户端，用于测试注入。默认使用全局单例。
        """
        self._redis = redis

    @property
    def redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = get_redis()
        return self._redis

    def _fail_key(self, username: str) -> str:
        return f"{self.FAIL_KEY_PREFIX}{username}"

    def _lock_key(self, username: str) -> str:
        return f"{self.LOCK_KEY_PREFIX}{username}"

    async def is_locked(self, username: str) -> bool:
        """检查账号是否处于锁定状态。

        Returns:
            True 表示锁定中，False 表示正常。
        """
        try:
            lock_key = self._lock_key(username)
            locked = await self.redis.exists(lock_key)
            return bool(locked)
        except Exception:
            logger.exception("check lock status failed for %s", username)
            # Redis 故障时降级：不阻止登录
            return False

    async def record_failure(self, username: str) -> tuple[int, bool]:
        """记录一次登录失败。

        Returns:
            (当前失败次数, 是否触发锁定)
        """
        try:
            fail_key = self._fail_key(username)

            # 原子递增失败计数
            attempts = await self.redis.incr(fail_key)

            # 首次失败时设置 TTL（30 分钟窗口）
            if attempts == 1:
                await self.redis.expire(fail_key, self.FAIL_WINDOW_SECONDS)

            # 达到阈值则锁定
            if attempts >= self.MAX_ATTEMPTS:
                lock_key = self._lock_key(username)
                await self.redis.setex(lock_key, self.LOCK_DURATION_SECONDS, "1")
                return int(attempts), True

            return int(attempts), False
        except Exception:
            logger.exception("record login failure failed for %s", username)
            # Redis 故障时降级：不计数，不锁定
            return 0, False

    async def reset_on_success(self, username: str) -> None:
        """登录成功后重置失败计数。"""
        try:
            fail_key = self._fail_key(username)
            lock_key = self._lock_key(username)
            # 同时删除失败计数和锁定标记
            await self.redis.delete(fail_key, lock_key)
        except Exception:
            logger.exception("reset login attempts failed for %s", username)
            # Redis 故障时降级：忽略错误

    async def get_attempts(self, username: str) -> int:
        """获取当前失败次数（用于调试/测试）。"""
        try:
            fail_key = self._fail_key(username)
            value = await self.redis.get(fail_key)
            return int(value) if value else 0
        except Exception:
            logger.exception("get login attempts failed for %s", username)
            return 0

    async def get_lock_ttl(self, username: str) -> int:
        """获取锁定剩余秒数（用于调试/测试，-2 表示不存在，-1 表示无过期）。"""
        try:
            lock_key = self._lock_key(username)
            return await self.redis.ttl(lock_key)
        except Exception:
            logger.exception("get lock ttl failed for %s", username)
            return -2


# 单例实例
_service: LoginRateLimitService | None = None


def get_login_rate_limit_service() -> LoginRateLimitService:
    """获取全局单例实例。"""
    global _service
    if _service is None:
        _service = LoginRateLimitService()
    return _service
