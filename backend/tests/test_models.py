"""Tests for database models - Task 2 TDD.

These tests verify:
- Base model has id, created_at, updated_at fields
- FeatureStatus enum has correct values
- Feature model has all required fields
- Analysis model has all required fields
- Feature-Analysis relationship works
"""

import pytest
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Feature, FeatureStatus, Analysis


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a new database session for testing."""
    with Session(engine) as session:
        yield session


class TestFeatureStatusEnum:
    """Tests for FeatureStatus enum."""

    def test_has_pending_value(self):
        """FeatureStatus should have 'pending' value."""
        assert FeatureStatus.PENDING.value == "pending"

    def test_has_analyzing_value(self):
        """FeatureStatus should have 'analyzing' value."""
        assert FeatureStatus.ANALYZING.value == "analyzing"

    def test_has_completed_value(self):
        """FeatureStatus should have 'completed' value."""
        assert FeatureStatus.COMPLETED.value == "completed"

    def test_has_failed_value(self):
        """FeatureStatus should have 'failed' value."""
        assert FeatureStatus.FAILED.value == "failed"

    def test_enum_is_string_enum(self):
        """FeatureStatus should be a string enum."""
        assert isinstance(FeatureStatus.PENDING, str)
        assert FeatureStatus.PENDING == "pending"


class TestFeatureModel:
    """Tests for Feature model."""

    def test_feature_has_id_field(self, session):
        """Feature should have a string id field."""
        feature = Feature(
            id="TEST-001",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        assert feature.id == "TEST-001"

    def test_feature_has_name_field(self, session):
        """Feature should have a name field."""
        feature = Feature(
            id="TEST-002",
            name="My Feature Name",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        assert feature.name == "My Feature Name"

    def test_feature_has_description_field(self, session):
        """Feature should have a description field."""
        feature = Feature(
            id="TEST-003",
            name="Test Feature",
            description="This is a detailed description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        assert feature.description == "This is a detailed description"

    def test_feature_has_status_field(self, session):
        """Feature should have a status field using FeatureStatus enum."""
        feature = Feature(
            id="TEST-004",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.ANALYZING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        assert feature.status == FeatureStatus.ANALYZING

    def test_feature_has_priority_field(self, session):
        """Feature should have a priority field."""
        feature = Feature(
            id="TEST-005",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=5,
        )
        session.add(feature)
        session.commit()

        assert feature.priority == 5

    def test_feature_has_github_issue_url_field(self, session):
        """Feature should have an optional github_issue_url field."""
        feature = Feature(
            id="TEST-006",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
            github_issue_url="https://github.com/org/repo/issues/123",
        )
        session.add(feature)
        session.commit()

        assert feature.github_issue_url == "https://github.com/org/repo/issues/123"

    def test_feature_github_issue_url_is_optional(self, session):
        """Feature github_issue_url should be optional (nullable)."""
        feature = Feature(
            id="TEST-007",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        assert feature.github_issue_url is None

    def test_feature_has_analysis_workflow_run_id_field(self, session):
        """Feature should have an optional analysis_workflow_run_id field."""
        feature = Feature(
            id="TEST-008",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
            analysis_workflow_run_id="12345678",
        )
        session.add(feature)
        session.commit()

        assert feature.analysis_workflow_run_id == "12345678"

    def test_feature_has_created_at_field(self, session):
        """Feature should have a created_at timestamp field."""
        feature = Feature(
            id="TEST-009",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        assert feature.created_at is not None
        assert isinstance(feature.created_at, datetime)

    def test_feature_has_updated_at_field(self, session):
        """Feature should have an updated_at timestamp field."""
        feature = Feature(
            id="TEST-010",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        assert feature.updated_at is not None
        assert isinstance(feature.updated_at, datetime)


class TestAnalysisModel:
    """Tests for Analysis model."""

    def test_analysis_has_auto_increment_id(self, session):
        """Analysis should have an auto-incrementing integer id."""
        feature = Feature(
            id="FEAT-001",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis = Analysis(
            feature_id="FEAT-001",
            result={"summary": "test"},
            tokens_used=1000,
            model_used="claude-3-opus",
        )
        session.add(analysis)
        session.commit()

        assert analysis.id is not None
        assert isinstance(analysis.id, int)

    def test_analysis_has_feature_id_foreign_key(self, session):
        """Analysis should have a feature_id foreign key."""
        feature = Feature(
            id="FEAT-002",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis = Analysis(
            feature_id="FEAT-002",
            result={"summary": "test"},
            tokens_used=1000,
            model_used="claude-3-opus",
        )
        session.add(analysis)
        session.commit()

        assert analysis.feature_id == "FEAT-002"

    def test_analysis_has_result_json_field(self, session):
        """Analysis should have a result JSON field."""
        feature = Feature(
            id="FEAT-003",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        result_data = {
            "summary": "Analysis complete",
            "complexity": "medium",
            "recommendations": ["item1", "item2"],
        }
        analysis = Analysis(
            feature_id="FEAT-003",
            result=result_data,
            tokens_used=1500,
            model_used="claude-3-opus",
        )
        session.add(analysis)
        session.commit()

        assert analysis.result == result_data
        assert analysis.result["summary"] == "Analysis complete"

    def test_analysis_has_tokens_used_field(self, session):
        """Analysis should have a tokens_used integer field."""
        feature = Feature(
            id="FEAT-004",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis = Analysis(
            feature_id="FEAT-004",
            result={"summary": "test"},
            tokens_used=2500,
            model_used="claude-3-opus",
        )
        session.add(analysis)
        session.commit()

        assert analysis.tokens_used == 2500

    def test_analysis_has_model_used_field(self, session):
        """Analysis should have a model_used string field."""
        feature = Feature(
            id="FEAT-005",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis = Analysis(
            feature_id="FEAT-005",
            result={"summary": "test"},
            tokens_used=1000,
            model_used="claude-3-5-sonnet",
        )
        session.add(analysis)
        session.commit()

        assert analysis.model_used == "claude-3-5-sonnet"

    def test_analysis_has_completed_at_field(self, session):
        """Analysis should have an optional completed_at timestamp field."""
        feature = Feature(
            id="FEAT-006",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        completed = datetime.now(UTC)
        analysis = Analysis(
            feature_id="FEAT-006",
            result={"summary": "test"},
            tokens_used=1000,
            model_used="claude-3-opus",
            completed_at=completed,
        )
        session.add(analysis)
        session.commit()

        # SQLite doesn't preserve timezone info, so compare without timezone
        assert analysis.completed_at.replace(tzinfo=None) == completed.replace(
            tzinfo=None
        )

    def test_analysis_has_created_at_field(self, session):
        """Analysis should have a created_at timestamp field."""
        feature = Feature(
            id="FEAT-007",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis = Analysis(
            feature_id="FEAT-007",
            result={"summary": "test"},
            tokens_used=1000,
            model_used="claude-3-opus",
        )
        session.add(analysis)
        session.commit()

        assert analysis.created_at is not None
        assert isinstance(analysis.created_at, datetime)

    def test_analysis_has_updated_at_field(self, session):
        """Analysis should have an updated_at timestamp field."""
        feature = Feature(
            id="FEAT-008",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis = Analysis(
            feature_id="FEAT-008",
            result={"summary": "test"},
            tokens_used=1000,
            model_used="claude-3-opus",
        )
        session.add(analysis)
        session.commit()

        assert analysis.updated_at is not None
        assert isinstance(analysis.updated_at, datetime)


class TestFeatureAnalysisRelationship:
    """Tests for Feature-Analysis relationship."""

    def test_feature_analyses_returns_list(self, session):
        """Feature.analyses should return a list of related Analysis objects."""
        feature = Feature(
            id="REL-001",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis1 = Analysis(
            feature_id="REL-001",
            result={"summary": "First analysis"},
            tokens_used=1000,
            model_used="claude-3-opus",
        )
        analysis2 = Analysis(
            feature_id="REL-001",
            result={"summary": "Second analysis"},
            tokens_used=1500,
            model_used="claude-3-opus",
        )
        session.add_all([analysis1, analysis2])
        session.commit()

        # Refresh to load relationship
        session.refresh(feature)

        assert len(feature.analyses) == 2
        assert all(isinstance(a, Analysis) for a in feature.analyses)

    def test_analysis_feature_returns_parent(self, session):
        """Analysis.feature should return the parent Feature object."""
        feature = Feature(
            id="REL-002",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis = Analysis(
            feature_id="REL-002",
            result={"summary": "test"},
            tokens_used=1000,
            model_used="claude-3-opus",
        )
        session.add(analysis)
        session.commit()

        # Refresh to load relationship
        session.refresh(analysis)

        assert analysis.feature is not None
        assert analysis.feature.id == "REL-002"
        assert isinstance(analysis.feature, Feature)

    def test_cascade_delete_removes_analyses(self, session):
        """Deleting a Feature should cascade delete its Analysis records."""
        feature = Feature(
            id="REL-003",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            priority=1,
        )
        session.add(feature)
        session.commit()

        analysis = Analysis(
            feature_id="REL-003",
            result={"summary": "test"},
            tokens_used=1000,
            model_used="claude-3-opus",
        )
        session.add(analysis)
        session.commit()

        analysis_id = analysis.id

        # Delete the feature
        session.delete(feature)
        session.commit()

        # Verify analysis was also deleted
        deleted_analysis = session.get(Analysis, analysis_id)
        assert deleted_analysis is None


class TestFeatureWebhookFields:
    """Tests for webhook-related fields in Feature model."""

    def test_feature_has_webhook_secret_field(self, session):
        """Feature should have webhook_secret field for validation."""
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
            webhook_secret="secret-abc-123",
        )
        session.add(feature)
        session.commit()

        retrieved = session.get(Feature, "test-123")
        assert retrieved.webhook_secret == "secret-abc-123"

    def test_webhook_secret_is_optional(self, session):
        """Webhook secret should be optional (can be None)."""
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
        )
        session.add(feature)
        session.commit()

        retrieved = session.get(Feature, "test-123")
        assert retrieved.webhook_secret is None

    def test_feature_has_webhook_received_at_field(self, session):
        """Feature should track when webhook was received."""
        now = datetime.now(UTC)
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
            webhook_received_at=now,
        )
        session.add(feature)
        session.commit()

        retrieved = session.get(Feature, "test-123")
        assert retrieved.webhook_received_at is not None
        # SQLite doesn't preserve timezone info, so compare without timezone
        # Use timedelta comparison to avoid microsecond precision issues
        now_naive = now.replace(tzinfo=None)
        retrieved_naive = (
            retrieved.webhook_received_at.replace(tzinfo=None)
            if retrieved.webhook_received_at.tzinfo
            else retrieved.webhook_received_at
        )
        assert abs((retrieved_naive - now_naive).total_seconds()) < 1

    def test_webhook_received_at_is_optional(self, session):
        """Webhook received timestamp should be optional."""
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
        )
        session.add(feature)
        session.commit()

        retrieved = session.get(Feature, "test-123")
        assert retrieved.webhook_received_at is None

    def test_feature_has_last_polled_at_field(self, session):
        """Feature should track when it was last polled."""
        now = datetime.now(UTC)
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
            last_polled_at=now,
        )
        session.add(feature)
        session.commit()

        retrieved = session.get(Feature, "test-123")
        assert retrieved.last_polled_at is not None
        # SQLite doesn't preserve timezone info, so compare without timezone
        now_naive = now.replace(tzinfo=None)
        retrieved_naive = (
            retrieved.last_polled_at.replace(tzinfo=None)
            if retrieved.last_polled_at.tzinfo
            else retrieved.last_polled_at
        )
        assert abs((retrieved_naive - now_naive).total_seconds()) < 1

    def test_last_polled_at_is_optional(self, session):
        """Last polled timestamp should be optional."""
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
        )
        session.add(feature)
        session.commit()

        retrieved = session.get(Feature, "test-123")
        assert retrieved.last_polled_at is None
