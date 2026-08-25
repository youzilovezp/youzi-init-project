"""
异步 Redis 客户端封装。

使用示例：
    from app.db.redis_client import redis_client

    await redis_client.set("foo", "bar", ex=60)
    value = await redis_client.get("foo")
"""

import asyncio

import redis.asyncio as redis

from app.core.config import settings


class RedisClient:
    """封装 redis.asyncio，提供全局单例风格的接口。

    重要：Redis 连接采用**惰性初始化**——第一次调用业务方法时才尝试连接。
    原因：启动期主动 connect() 即便在 catch 里 swallow 异常，
    redis.from_url 内部的 connection_pool 仍会持有 asyncio 引用，
    导致 lifespan 阶段不能正常 yield（uvicorn 持续返回 502）。
    """

    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._connect_lock: asyncio.Lock | None = None  # 延迟到第一次 await 时创建

    async def _ensure_client(self) -> redis.Redis:
        if self._client is not None:
            return self._client
        # 首次调用时建锁——必须发生在事件循环内，所以放这里
        if self._connect_lock is None:
            self._connect_lock = asyncio.Lock()
        async with self._connect_lock:
            if self._client is not None:
                return self._client
            client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await client.ping()  # type: ignore[attr-defined]
            self._client = client
        return self._client

    async def connect(self) -> None:
        """兼容旧 API：尝试预热连接。失败仅记录警告，不阻塞应用。"""
        if self._client is not None:
            return
        try:
            await self._ensure_client()
        except Exception as exc:  # noqa: BLE001
            from loguru import logger

            logger.warning(
                f"⚠️ Redis 暂时不可达 ({settings.REDIS_URL}): {exc}；"
                "应用继续启动，业务调用时会感知"
            )

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()  # type: ignore[attr-defined]
            except Exception:
                pass
            self._client = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis 客户端未初始化，请先调用 connect()")
        return self._client

    # ---------- 常用快捷方法 ----------
    async def ping(self) -> bool:
        """K8s readiness 探针用：检查 Redis 是否在线。"""
        result = await self.client.ping()  # type: ignore[union-attr]
        return bool(result)

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self.client.set(key, value, ex=ex)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        await self.client.setex(key, ttl, value)

    async def delete(self, *keys: str) -> int:
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """检查 key 是否存在（包装 await，避免调用方 await bool）。"""
        result = await self.client.exists(key)
        return bool(result)

    async def expire(self, key: str, seconds: int) -> bool:
        result = await self.client.expire(key, seconds)
        return bool(result)


redis_client = RedisClient()
