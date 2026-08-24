"""
测试公共 fixtures。

设计：
- 使用 ASGI transport 跑内存 FastAPI，不依赖真实网络端口
- 使用 settings 的 admin 凭证（与 init_db 一致）
- pytest-asyncio ≥0.23 不再接受手动 event_loop fixture——每个测试函数各自的事件循环
- 测试前自动调用 init_db 建表 + 种子（依赖 .env 中的真实 DB 配置）
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import engine


@pytest_asyncio.fixture(autouse=True)
async def _setup_database() -> AsyncGenerator[None, None]:
    """每个测试前保证表存在 + 种子已写入。autouse=True 对每个测试自动调用。

    注意：必须 function-scoped，否则 session-scoped 会持有 event loop 的连接，
    与后续测试的 loop 冲突。
    """
    await init_db()
    yield


@pytest.fixture
def admin_credentials() -> dict[str, str]:
    """从 settings 读 admin 凭证——避免硬编码用户名/密码。"""
    return {
        "username": settings.INITIAL_ADMIN_USERNAME,
        "password": settings.INITIAL_ADMIN_PASSWORD,
    }


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """每个测试一个干净的 session；通过依赖覆盖使用同一 session。"""
    from app.db.session import async_session

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """提供 httpx AsyncClient 走 ASGI transport；不依赖真实网络端口。

    同时把 app 的 get_session 依赖替换为 db_session，避免异步引擎跨事件循环。
    """
    from app.db.session import get_session
    from app.main import app

    async def _override_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_engine() -> AsyncGenerator[None, None]:
    """每次测试结束释放 engine 持有的连接，避免 "attached to a different loop"。"""
    yield
    await engine.dispose()


__all__ = [
    "client",
    "admin_credentials",
    "db_session",
    "_setup_database",
    "_cleanup_engine",
]
