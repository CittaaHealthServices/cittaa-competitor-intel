from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine
from app.config import settings
import logging
import sys

logger = logging.getLogger(__name__)

# Validate that POSTGRES_URL is actually a PostgreSQL URL
_raw_url = settings.POSTGRES_URL
if not (_raw_url.startswith("postgresql") or _raw_url.startswith("postgres")):
    logger.error(
        f"POSTGRES_URL does not look like a PostgreSQL URL: {_raw_url[:40]}...\n"
        "Make sure POSTGRES_URL is set to your Railway PostgreSQL connection string, "
        "not a MongoDB or other URI."
    )
    sys.exit(1)

# Convert postgresql:// to postgresql+asyncpg:// for async
async_db_url = _raw_url.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace("postgres://", "postgresql+asyncpg://")

# Sync URL for Alembic migrations
sync_db_url = _raw_url.replace(
    "postgresql+asyncpg://", "postgresql://"
).replace("postgres://", "postgresql://")

engine = create_async_engine(
    async_db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        from app import models  # noqa
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")
