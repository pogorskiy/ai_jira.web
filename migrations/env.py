# migrations/env.py
"""
Alembic environment file, adapted for SQLAlchemy 2.x and async engine.
Runs DDL online via asyncpg, but keeps the offline mode synchronous.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import DATABASE_URL            # pulled from .env at import time
from app.models import Base                      # all ORM models

# ------------------------------------------------------------------------------
# Alembic configuration
# ------------------------------------------------------------------------------

config = context.config
fileConfig(config.config_file_name)              # integrate alembic.ini logging

target_metadata = Base.metadata                  # for autogenerate


# ------------------------------------------------------------------------------
# Offline migrations (generate SQL only)
# ------------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Emit the DDL to stdout/SQL file without an active DB connection."""
    url = DATABASE_URL.replace("+asyncpg", "")   # use sync dialect for offline SQL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------------------------
# Online migrations (apply directly to DB)
# ------------------------------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    """Helper to configure a sync context inside an async connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Connect to the database with an async engine and run migrations."""
    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as async_conn:
        await async_conn.run_sync(do_run_migrations)

    await connectable.dispose()


# ------------------------------------------------------------------------------
# Entrypoint selection
# ------------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())