"""
异步数据库引擎与会话工厂。

使用示例：
    from app.db.session import async_session

    async with async_session() as session:
        result = await session.execute(select(User))
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.base_class import Base

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # 防长连接被 PG / NAT 静默断开
    pool_recycle=settings.DB_POOL_RECYCLE,  # 1 小时回收连接
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：每次请求一个独立 Session。"""
    async with async_session() as session:
        yield session


__all__ = ["Base", "engine", "async_session", "get_session"]
