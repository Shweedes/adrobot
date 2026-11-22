"""Движок и фабрика сессий."""

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


def build_engine(url: str) -> AsyncEngine:
    """Создаёт async-движок по URL базы."""
    return create_async_engine(url)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker:
    """Создаёт фабрику сессий; объекты остаются доступны после commit."""
    return async_sessionmaker(engine, expire_on_commit=False)
