import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fail fast so the developer immediately sees a clear error
    # Example: postgresql+asyncpg://user:pass@host:5432/db
    raise RuntimeError("DATABASE_URL environment variable must be set (e.g. postgresql+asyncpg://user:pass@host:5432/db)")

# Enable SQL echo logging via environment variable
ECHO_SQL = os.getenv("SQL_ECHO", "false").lower() == "true"

engine = create_async_engine(DATABASE_URL, future=True, echo=ECHO_SQL)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI.
    Yields an async SQLAlchemy session.
    """
    async with AsyncSessionLocal() as session:
        yield session