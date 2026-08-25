"""测试公共 fixtures。

设计：
- session-scoped init_db：所有测试共用一个 DB（避免每测试都跑 alembic 子进程）
- function-scoped transactional session：每个测试独立回滚，互不影响
- ASGITransport：内存 FastAPI，无真实端口
- 使用 settings 的 admin 凭证（与 init_db 一致）
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import async_session, engine


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """每个测试独立 session：测试结束自动 rollback，干净隔离。"""
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def admin_credentials() -> dict[str, str]:
    """从 settings 读 admin 凭证——避免硬编码用户名/密码。"""
    return {
        "username": settings.INITIAL_ADMIN_USERNAME,
        "password": settings.INITIAL_ADMIN_PASSWORD,
    }


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """提供 httpx AsyncClient 走 ASGI transport；不依赖真实网络端口。

    关键：base_url 用 "testserver" 让 Host 头匹配 settings.TRUSTED_HOSTS
    （默认包含 "testserver"）。否则 TrustedHostMiddleware 会返 400。
    """
    from app.main import app

    # 关键：每个 client fixture 创建前先 init_db 一次（在 ASGI app lifespan 里）
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _final_cleanup() -> AsyncGenerator[None, None]:
    """session 结束：dispose 引擎 + 关 redis。"""
    yield
    await engine.dispose()
    try:
        from app.db.redis_client import redis_client

        await redis_client.close()
    except Exception:
        pass


__all__ = [
    "client",
    "admin_credentials",
    "db_session",
]
