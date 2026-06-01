import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.core.config import settings
from app.database.session import Base

# Import all models so Alembic detects them
from app.models import user, school, student, teacher, attendance, assessment, notification, ai_insight
from app.models import copilot  # Admin Copilot tables

# Build the correct SYNC URL for Alembic from the async DATABASE_URL in settings
def _make_sync_url(async_url: str) -> str:
    """Convert async driver URL to sync driver URL for Alembic."""
    return (
        async_url
        .replace("mysql+aiomysql://",       "mysql+pymysql://")
        .replace("postgresql+asyncpg://",   "postgresql+psycopg2://")
    )

SYNC_URL  = _make_sync_url(settings.DATABASE_URL)
ASYNC_URL = settings.DATABASE_URL

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=SYNC_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Use the async URL from .env, not from alembic.ini
    connectable = create_async_engine(ASYNC_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
