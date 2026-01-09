import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models import Base

# Import all models to ensure they're registered with Base metadata
from app.models.feature import Feature  # noqa: F401
from app.models.analysis import Analysis  # noqa: F401
from app.models.idea import Idea  # noqa: F401
from app.models.brainstorm import BrainstormSession, BrainstormMessage  # noqa: F401
from app.models.tool import Tool  # noqa: F401
from app.models.agent import AgentType, AgentToolConfig, ToolUsageAudit  # noqa: F401


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for anyio."""
    return "asyncio"


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database with tables."""
    # Create async engine for testing with in-memory SQLite
    # Use StaticPool to ensure all connections use the same in-memory database
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    yield async_session_maker

    # Drop tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_db):
    """Create a database session for tests."""
    async with test_db() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
async def test_app(test_db):
    """Create a test FastAPI app instance."""
    # Import the main module to avoid starting scheduler during tests
    from fastapi import FastAPI
    from app.api.features import router as features_router
    from app.api.webhooks import router as webhooks_router
    from app.api.brainstorms import router as brainstorms_router
    from app.api.ideas import router as ideas_router
    from app.api.agents import router as agents_router
    from app.api.tools import router as tools_router
    from app.config import settings

    # Create a test app without lifespan to avoid starting scheduler
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(features_router)
    app.include_router(webhooks_router)
    app.include_router(brainstorms_router)
    app.include_router(ideas_router)
    app.include_router(agents_router)
    app.include_router(tools_router)

    # Add health endpoint for tests
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "app": settings.app_name}

    async def override_get_db():
        async with test_db() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(test_app):
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
