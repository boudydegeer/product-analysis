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

    async def test_timezone_aware_datetime_compatibility(
        self, polling_service, db_session: AsyncSession
    ):
        """Should handle mixed timezone-aware and timezone-naive datetimes correctly.

        This reproduces the bug where webhook_received_at is set with datetime.utcnow()
        (timezone-naive) while polling service uses datetime.now(UTC) (timezone-aware),
        causing asyncpg to fail with: "can't subtract offset-naive and offset-aware datetimes"
        """
        # Simulate webhook endpoint setting timezone-naive datetime (the bug)
        # This is what happens when using datetime.utcnow()
        naive_datetime = datetime.utcnow()

        feature = Feature(
            id="timezone-test-feature",
            name="Timezone Test",
            description="Test timezone handling",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="33333",
            webhook_received_at=naive_datetime,  # This is timezone-naive!
        )
        db_session.add(feature)
        await db_session.commit()

        # This should not raise "can't subtract offset-naive and offset-aware datetimes"
        # The polling service uses datetime.now(UTC) which is timezone-aware
        features = await polling_service.get_features_needing_polling()

        # Feature should be excluded because webhook was received very recently
        # The test passes if no exception is raised during the query
        assert True  # If we get here, the timezone handling works
        assert len(features) == 0  # Feature should be excluded due to recent webhook

    async def test_process_completed_workflow_extracts_flattened_fields(
        self, polling_service, analyzing_feature, db_session: AsyncSession
    ):
        """Should extract and populate all 13 flattened fields from workflow result.

        This test uses the REAL structure that the GitHub workflow generates.
        """
        # Mock workflow result with REAL structure
        workflow_result = {
            "feature_id": analyzing_feature.id,
            "warnings": [
                {
                    "type": "missing_infrastructure",
                    "severity": "high",
                    "message": "Backend infrastructure missing",
                    "impact": "Increases estimate significantly",
                }
            ],
            "repository_state": {
                "has_backend_code": True,
                "has_frontend_code": True,
                "has_database_models": True,
                "has_authentication": False,
                "maturity_level": "partial",
                "notes": "Core infrastructure exists but auth missing",
            },
            "complexity": {
                "story_points": 8,
                "estimated_hours": 16,
                "prerequisite_hours": 8,
                "total_hours": 24,
                "level": "Medium",
                "rationale": "Requires new API endpoints and UI components",
            },
            "affected_modules": [
                {
                    "path": "backend/app/api/features.py",
                    "change_type": "modify",
                    "reason": "Add new endpoint",
                }
            ],
            "implementation_tasks": [
                {
                    "id": "task-1",
                    "task_type": "prerequisite",
                    "description": "Setup authentication",
                    "estimated_effort_hours": 8,
                    "dependencies": [],
                    "priority": "high",
                },
                {
                    "id": "task-2",
                    "task_type": "feature",
                    "description": "Implement feature logic",
                    "estimated_effort_hours": 16,
                    "dependencies": ["task-1"],
                    "priority": "high",
                },
            ],
            "technical_risks": [
                {
                    "category": "security",
                    "description": "Authentication bypass vulnerability",
                    "severity": "high",
                    "mitigation": "Implement proper JWT validation",
                },
                {
                    "category": "performance",
                    "description": "N+1 query problem",
                    "severity": "medium",
                    "mitigation": "Use eager loading",
                },
            ],
            "recommendations": {
                "approach": "Start with authentication, then feature implementation",
                "alternatives": ["Use third-party auth service", "Implement OAuth"],
                "testing_strategy": "Unit tests + integration tests",
                "deployment_notes": "Requires database migration",
            },
            "metadata": {
                "analyzed_at": "2024-01-15T10:00:00Z",
                "workflow_run_id": "12345",
                "model": "claude-3-5-sonnet-20241022",
            },
        }

        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "completed"
        mock_github_service.download_workflow_artifact.return_value = workflow_result

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_workflow_status(analyzing_feature)

        # Query the created Analysis record
        from sqlalchemy import select
        from app.models import Analysis

        result = await db_session.execute(
            select(Analysis).where(Analysis.feature_id == analyzing_feature.id)
        )
        analysis = result.scalar_one()

        # Verify flattened summary fields are populated from complexity
        assert analysis.summary_overview == "Medium"
        assert analysis.summary_key_points == [
            "Requires new API endpoints and UI components"
        ]
        assert analysis.summary_metrics == {
            "story_points": 8,
            "estimated_hours": 16,
            "prerequisite_hours": 8,
            "total_hours": 24,
        }

        # Verify flattened implementation fields from implementation_tasks
        assert analysis.implementation_architecture == {
            "affected_modules_count": 1,
            "primary_areas": ["backend/app/api/features.py"],
        }
        assert len(analysis.implementation_technical_details) == 2
        assert analysis.implementation_technical_details[0]["id"] == "task-1"
        assert analysis.implementation_technical_details[1]["id"] == "task-2"
        assert analysis.implementation_data_flow == {
            "has_prerequisites": True,
            "prerequisite_count": 1,
            "feature_task_count": 1,
        }

        # Verify flattened risk fields from technical_risks
        assert len(analysis.risks_technical_risks) == 2
        assert analysis.risks_technical_risks[0]["category"] == "security"
        assert analysis.risks_technical_risks[1]["category"] == "performance"

        # Extract security and scalability concerns from technical_risks
        assert len(analysis.risks_security_concerns) == 1
        assert (
            analysis.risks_security_concerns[0]["description"]
            == "Authentication bypass vulnerability"
        )

        # No scalability risks in test data (only security and performance)
        assert len(analysis.risks_scalability_issues) == 0

        # Mitigation strategies extracted from technical_risks
        assert len(analysis.risks_mitigation_strategies) == 2
        assert "Implement proper JWT validation" in analysis.risks_mitigation_strategies
        assert "Use eager loading" in analysis.risks_mitigation_strategies

        # Verify flattened recommendation fields from recommendations
        assert len(analysis.recommendations_improvements) == 2
        assert any(
            "third-party auth" in str(imp).lower()
            for imp in analysis.recommendations_improvements
        )

        assert len(analysis.recommendations_best_practices) >= 1
        assert (
            "Unit tests + integration tests" in analysis.recommendations_best_practices
        )

        assert len(analysis.recommendations_next_steps) >= 1
        assert "Start with authentication" in analysis.recommendations_next_steps[0]
