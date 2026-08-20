"""
异步 Redis 客户端封装。

使用示例：
    from app.db.redis_client import redis_client

    await redis_client.set("foo", "bar", ex=60)
    value = await redis_client.get("foo")
"""

import redis.asyncio as redis

from app.core.config import settings


class RedisClient:
    """封装 redis.asyncio，提供全局单例风格的接口。"""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            try:
                await self._client.ping()
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    f"无法连接 Redis ({settings.REDIS_URL}): {exc}"
                ) from exc

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis 客户端未初始化，请先调用 connect()")
        return self._client

    # ---------- 常用快捷方法 ----------
    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self.client.set(key, value, ex=ex)

    async def delete(self, *keys: str) -> int:
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    async def expire(self, key: str, seconds: int) -> bool:
        return bool(await self.client.expire(key, seconds))


redis_client = RedisClient()
