import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool


# Remove custom event_loop fixture - let pytest-asyncio handle it
# Using pytest-asyncio's default event loop with proper scope


@pytest.fixture(scope="session")
def test_engine():
    # Single in-memory DB shared across connections
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    return engine


@pytest.fixture(scope="session")
def session_maker(test_engine):
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture(scope="session", autouse=True)
async def _create_tables(test_engine):
    # Ensure all models are imported/registered before create_all
    import app.models  # noqa: F401
    from app.config.database import Base

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture()
def uploads_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Force uploads into a temp dir for each test
    from app.services.file_service import FileService

    base = tmp_path / "uploads"
    base.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(FileService, "STORAGE_BASE", base)
    return base


@pytest.fixture()
def app(session_maker, test_engine):
    """
    Return FastAPI app wired to the in-memory test DB.
    """
    import app.config.database as db
    from app.main import app as fastapi_app

    # Patch the global engine/sessionmaker used by init_db/get_db
    db.engine = test_engine
    db.AsyncSessionLocal = session_maker

    async def override_get_db():
        async with session_maker() as session:
            yield session

    fastapi_app.dependency_overrides[db.get_db] = override_get_db
    return fastapi_app


@pytest.fixture()
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


