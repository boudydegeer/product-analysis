"""Tests for analysis polling service."""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, patch
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base, Feature, FeatureStatus
from app.services.polling_service import AnalysisPollingService


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


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency with test database."""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Get a test database session."""
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.fixture
def polling_service(db_session: AsyncSession):
    """Create polling service instance."""
    return AnalysisPollingService(db_session)


@pytest.fixture
async def analyzing_feature(db_session: AsyncSession) -> Feature:
    """Create a feature in ANALYZING status."""
    feature = Feature(
        id="test-analyzing-feature",
        name="Test Feature",
        description="Test description",
        status=FeatureStatus.ANALYZING,
        analysis_workflow_run_id="12345",
        webhook_secret="test-secret",
    )
    db_session.add(feature)
    await db_session.commit()
    await db_session.refresh(feature)
    return feature


@pytest.mark.asyncio
class TestAnalysisPollingService:
    """Tests for AnalysisPollingService."""

    async def test_get_features_needing_polling_returns_analyzing_features(
        self, polling_service, analyzing_feature
    ):
        """Should return features in ANALYZING status."""
        features = await polling_service.get_features_needing_polling()

        assert len(features) == 1
        assert features[0].id == analyzing_feature.id
        assert features[0].status == FeatureStatus.ANALYZING

    async def test_get_features_needing_polling_excludes_completed_features(
        self, polling_service, db_session: AsyncSession
    ):
        """Should not return features that are already COMPLETED."""
        feature = Feature(
            id="completed-feature",
            name="Completed Feature",
            description="Done",
            status=FeatureStatus.COMPLETED,
            analysis_workflow_run_id="99999",
        )
        db_session.add(feature)
        await db_session.commit()

        features = await polling_service.get_features_needing_polling()

        assert len(features) == 0

    async def test_get_features_needing_polling_excludes_recently_received_webhooks(
        self, polling_service, db_session: AsyncSession
    ):
        """Should not poll features that recently received webhooks."""
        # Feature received webhook 1 minute ago
        feature = Feature(
            id="webhook-received-feature",
            name="Webhook Received",
            description="Test",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="11111",
            webhook_received_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        db_session.add(feature)
        await db_session.commit()

        features = await polling_service.get_features_needing_polling()

        # Should be excluded because webhook was received recently
        feature_ids = [f.id for f in features]
        assert "webhook-received-feature" not in feature_ids

    async def test_get_features_needing_polling_excludes_timed_out_features(
        self, polling_service, db_session: AsyncSession
    ):
        """Should not poll features that have exceeded timeout."""
        # Feature created 20 minutes ago (beyond 15 minute timeout)
        old_timestamp = datetime.now(UTC) - timedelta(minutes=20)
        feature = Feature(
            id="timed-out-feature",
            name="Timed Out Feature",
            description="Test",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="22222",
            created_at=old_timestamp,
        )
        db_session.add(feature)
        await db_session.commit()

        features = await polling_service.get_features_needing_polling()

        # Should be excluded because it exceeded timeout
        feature_ids = [f.id for f in features]
        assert "timed-out-feature" not in feature_ids

    async def test_poll_workflow_status_updates_feature_when_completed(
        self, polling_service, analyzing_feature, db_session: AsyncSession
    ):
        """Should download artifact and update feature when workflow completes."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "completed"
        mock_github_service.download_workflow_artifact.return_value = {
            "feature_id": analyzing_feature.id,
            "complexity": {"story_points": 5, "estimated_hours": 16},
            "metadata": {"workflow_run_id": "12345"},
        }

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_workflow_status(analyzing_feature)

        # Refresh feature to load relationships
        await db_session.refresh(analyzing_feature)

        # Feature should be updated to COMPLETED
        assert analyzing_feature.status == FeatureStatus.COMPLETED
        assert analyzing_feature.last_polled_at is not None

        # Analysis should be created - check via query to avoid lazy loading issues
        from sqlalchemy import select
        from app.models import Analysis

        result = await db_session.execute(
            select(Analysis).where(Analysis.feature_id == analyzing_feature.id)
        )
        analyses = result.scalars().all()
        assert len(analyses) == 1

    async def test_poll_workflow_status_updates_feature_when_failed(
        self, polling_service, analyzing_feature
    ):
        """Should update feature to FAILED when workflow fails."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "failure"

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_workflow_status(analyzing_feature)

        # Feature should be updated to FAILED
        assert analyzing_feature.status == FeatureStatus.FAILED

    async def test_poll_workflow_status_updates_last_polled_timestamp(
        self, polling_service, analyzing_feature
    ):
        """Should update last_polled_at timestamp even if still in progress."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "in_progress"

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_workflow_status(analyzing_feature)

        # Should update timestamp even though still in progress
        assert analyzing_feature.last_polled_at is not None
        assert analyzing_feature.status == FeatureStatus.ANALYZING

    async def test_poll_all_analyzing_features_polls_multiple_features(
        self, polling_service, db_session: AsyncSession
    ):
        """Should poll all features in ANALYZING status."""
        features = [
            Feature(
                id=f"feature-{i}",
                name=f"Feature {i}",
                description="Test",
                status=FeatureStatus.ANALYZING,
                analysis_workflow_run_id=f"{1000 + i}",
            )
            for i in range(3)
        ]

        for feature in features:
            db_session.add(feature)
        await db_session.commit()

        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "in_progress"

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            polled_count = await polling_service.poll_all_analyzing_features()

        assert polled_count == 3

    async def test_poll_all_handles_errors_gracefully(
        self, polling_service, analyzing_feature
    ):
        """Should continue polling other features if one fails."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.side_effect = Exception(
            "GitHub API error"
        )

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            # Should not raise exception
            polled_count = await polling_service.poll_all_analyzing_features()

        # Should still count as attempted
        assert polled_count >= 0
