"""
限流（slowapi）。

仅在 ENABLE_REDIS=true 时启用；无 Redis 时装饰器 no-op，不报错。
"""

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
except ImportError:

    class _NoopLimiter:
        def limit(self, *_args, **_kwargs):
            def deco(f):
                return f

            return deco

    limiter = _NoopLimiter()
