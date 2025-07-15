import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fail fast so the developer immediately sees a clear error
    raise RuntimeError("DATABASE_URL environment variable must be set (e.g. postgresql+asyncpg://user:pass@host:5432/db)")

engine = create_async_engine(DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_session() -> AsyncSession:  # Dependency
    async with AsyncSessionLocal() as session:
        yield session