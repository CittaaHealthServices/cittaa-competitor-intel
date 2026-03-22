from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Convert postgresql:// to postgresql+asyncpg:// for async
async_db_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace("postgres://", "postgresql+asyncpg://")

# Sync URL for Alembic migrations
sync_db_url = settings.DATABASE_URL.replace(
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
