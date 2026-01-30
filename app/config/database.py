"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config.settings import get_settings

settings = get_settings()

# Create async engine
# Use SQLite for simplicity, can be easily switched to PostgreSQL
database_url = settings.database_url or "sqlite+aiosqlite:///./media_mind.db"

# Only echo SQL queries in debug mode AND if explicitly enabled
# For cleaner logs, we'll suppress via logging instead
# Configure SQLite for better async handling with longer timeout
connect_args = {}
if "sqlite" in database_url:
    # SQLite-specific configuration for async operations
    connect_args = {
        "timeout": 30.0,  # Increase timeout to 30 seconds
        "check_same_thread": False,  # Allow multi-threaded access
    }

engine = create_async_engine(
    database_url,
    echo=False,  # Disable echo, use logging level control instead
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

