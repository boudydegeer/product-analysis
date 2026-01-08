"""Tests for idea models."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Idea, IdeaStatus, IdeaPriority


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


class TestIdeaModel:
    """Tests for Idea model."""

    def test_create_idea(self, session):
        """Test creating an idea."""
        idea = Idea(
            id="idea-1",
            title="Dark Mode Feature",
            description="Add dark mode support to the application",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.MEDIUM,
            business_value=8,
            technical_complexity=5,
        )

        session.add(idea)
        session.commit()

        assert idea.id == "idea-1"
        assert idea.title == "Dark Mode Feature"
        assert idea.status == IdeaStatus.BACKLOG
        assert idea.priority == IdeaPriority.MEDIUM
        assert idea.business_value == 8
        assert idea.technical_complexity == 5
        assert isinstance(idea.created_at, datetime)
        assert isinstance(idea.updated_at, datetime)

    def test_idea_nullable_fields(self, session):
        """Test idea with nullable fields."""
        idea = Idea(
            id="idea-2",
            title="Test Idea",
            description="Test description",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.LOW,
        )

        session.add(idea)
        session.commit()

        assert idea.business_value is None
        assert idea.technical_complexity is None
        assert idea.estimated_effort is None
        assert idea.market_fit_analysis is None
        assert idea.risk_assessment is None

    def test_idea_business_value_range(self, session):
        """Test business value must be 1-10."""
        idea = Idea(
            id="idea-3",
            title="Test",
            description="Test",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.LOW,
            business_value=11,  # Invalid
        )

        session.add(idea)

        # Should raise constraint error
        with pytest.raises(Exception):
            session.commit()
