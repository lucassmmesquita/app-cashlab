from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from .config import settings


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# Engine kwargs — adapt to database type
_is_postgres = settings.DATABASE_URL.startswith("postgresql")
_engine_kwargs: dict = {
    "echo": settings.DEBUG,
}
if _is_postgres:
    # Supabase pooler handles connection pooling — use NullPool on our side
    # asyncpg needs statement_cache_size=0 for transaction-mode pooler
    _engine_kwargs["poolclass"] = NullPool
    _engine_kwargs["connect_args"] = {"statement_cache_size": 0}

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    **_engine_kwargs,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
