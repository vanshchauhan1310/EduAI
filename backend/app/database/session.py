from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _build_engine():
    url = settings.DATABASE_URL
    is_mysql = url.startswith("mysql")

    if is_mysql:
        # MySQL (local dev with aiomysql)
        return create_async_engine(
            url,
            echo=settings.DEBUG,
            pool_recycle=3600,   # prevent MySQL "gone away" error on idle connections
            pool_pre_ping=True,
        )
    else:
        # PostgreSQL (Supabase production with asyncpg)
        return create_async_engine(
            url,
            echo=settings.DEBUG,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
        )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
