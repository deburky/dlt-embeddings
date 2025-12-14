"""Database session management for SQLAlchemy (sync and async)."""

import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from dlt_embeddings.models import Base


def get_database_url(
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    username: str | None = None,
    password: str | None = None,
    async_driver: bool = False,
) -> str:
    """Get database URL from environment variables or parameters.

    Args:
        host: Database host (default: from env or localhost)
        port: Database port (default: from env or 5432)
        database: Database name (default: from env or dlt_dev)
        username: Database username (default: from env or dlt_user)
        password: Database password (default: from env or dlt_password)
        async_driver: Whether to use async driver (asyncpg)

    Returns:
        Database URL string
    """
    host = host or os.getenv("POSTGRES_HOST", "localhost")
    port = port or int(os.getenv("POSTGRES_PORT", "5432"))
    database = database or os.getenv("POSTGRES_DATABASE", "dlt_dev")
    username = username or os.getenv("POSTGRES_USER", "dlt_user")
    password = password or os.getenv("POSTGRES_PASSWORD", "dlt_password")

    driver = "asyncpg" if async_driver else "psycopg2"
    return f"postgresql+{driver}://{username}:{password}@{host}:{port}/{database}"


# Global engines and session factories
_sync_engine = None
_async_engine = None
_SyncSessionLocal = None
_AsyncSessionLocal = None


def get_sync_engine():
    """Get or create sync SQLAlchemy engine."""
    global _sync_engine
    if _sync_engine is None:
        database_url = get_database_url(async_driver=False)
        _sync_engine = create_engine(database_url, echo=False, pool_pre_ping=True)
    return _sync_engine


def get_async_engine():
    """Get or create async SQLAlchemy engine."""
    global _async_engine
    if _async_engine is None:
        database_url = get_database_url(async_driver=True)
        _async_engine = create_async_engine(
            database_url, echo=False, pool_pre_ping=True, future=True
        )
    return _async_engine


def get_sync_session_factory():
    """Get or create sync session factory."""
    global _SyncSessionLocal
    if _SyncSessionLocal is None:
        engine = get_sync_engine()
        _SyncSessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    return _SyncSessionLocal


def get_async_session_factory():
    """Get or create async session factory."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        engine = get_async_engine()
        _AsyncSessionLocal = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
    return _AsyncSessionLocal


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Get a sync database session (context manager).

    Yields:
        SQLAlchemy Session object

    Example:
        ```python
        with get_sync_session() as session:
            results = session.query(Conversation).limit(10).all()
        ```
    """
    SessionLocal = get_sync_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session (context manager).

    Yields:
        SQLAlchemy AsyncSession object

    Example:
        ```python
        async with get_async_session() as session:
            result = await session.execute(select(Conversation).limit(10))
            results = result.scalars().all()
        ```
    """
    AsyncSessionLocal = get_async_session_factory()
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def ensure_pgvector_extension(session: AsyncSession) -> None:
    """Ensure pgvector extension is enabled in the database.

    Args:
        session: Async database session
    """
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await session.commit()


def init_db(schema: str = "dlt_dev") -> None:
    """Initialize database schema (create tables if they don't exist).

    Args:
        schema: Schema name to create if it doesn't exist
    """
    engine = get_sync_engine()

    # Create schema if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()

    # Create all tables
    Base.metadata.create_all(bind=engine)

