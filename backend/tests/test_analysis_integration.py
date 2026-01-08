"""Integration test for analysis endpoint and webhook flow."""
import pytest
import json
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base, Feature, FeatureStatus
from app.utils.webhook_security import compute_webhook_signature


# Test database setup - SQLite in-memory with async
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestingAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db():
    """Override the get_db dependency for tests."""
    async with TestingAsyncSessionLocal() as session:
        yield session


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_session():
    """Get a test database session."""
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.mark.anyio
async def test_full_analysis_flow(async_client: AsyncClient, db_session: AsyncSession):
    """Test complete flow: webhook receives data, endpoint returns it."""
    # Use a valid UUID format for feature_id
    feature_id = "550e8400-e29b-41d4-a716-446655440000"

    # 1. Create feature
    feature = Feature(
        id=feature_id,
        name="Flow Test Feature",
        description="Testing full flow",
        status=FeatureStatus.ANALYZING,
        webhook_secret="flow-secret",
    )
    db_session.add(feature)
    await db_session.commit()

    # 2. Simulate webhook receiving analysis result (using real workflow structure)
    webhook_payload = {
        "feature_id": feature_id,
        "complexity": {
            "story_points": 3,
            "estimated_hours": 8,
            "prerequisite_hours": 0,
            "total_hours": 8,
            "level": "Medium",
            "rationale": "Test flow overview",
        },
        "warnings": [],
        "repository_state": {},
        "affected_modules": [
            {"path": "/test/file.py", "change_type": "modify", "reason": "Test"}
        ],
        "implementation_tasks": [],
        "technical_risks": [],
        "recommendations": {
            "improvements": [
                {
                    "priority": "high",
                    "title": "Test improvement",
                    "description": "Test improvement description",
                    "effort": "1 day",
                }
            ],
            "best_practices": ["Best practice 1"],
            "next_steps": ["Next step 1"],
        },
        "error": None,
        "raw_output": "",
        "metadata": {},
    }

    payload_str = json.dumps(webhook_payload)
    signature = compute_webhook_signature(payload_str, "flow-secret")

    webhook_response = await async_client.post(
        "/api/v1/webhooks/analysis-result",
        json=webhook_payload,
        headers={"X-Webhook-Signature": signature},
    )
    assert webhook_response.status_code == 200

    # 3. Fetch analysis via endpoint
    analysis_response = await async_client.get(
        f"/api/v1/features/{feature_id}/analysis"
    )
    assert analysis_response.status_code == 200

    data = analysis_response.json()
    assert data["feature_id"] == feature_id
    assert data["status"] == "completed"
    # Overview data comes from complexity
    assert data["overview"]["summary"] == "Test flow overview"  # complexity.rationale
    assert data["overview"]["key_points"] == ["Test flow overview"]  # complexity.rationale
    assert data["overview"]["metrics"]["complexity"] == "medium"  # complexity.level.lower()
    assert "days" in data["overview"]["metrics"]["estimated_effort"] or "hours" in data["overview"]["metrics"]["estimated_effort"]
    # Recommendations should include the improvement
    assert len(data["recommendations"]["improvements"]) == 1
    assert data["recommendations"]["improvements"][0]["title"] == "Test improvement"
    assert data["recommendations"]["improvements"][0]["priority"] == "high"
    assert data["recommendations"]["improvements"][0]["effort"] == "1 day"
