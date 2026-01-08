"""Tests for brainstorm models."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, BrainstormSession, BrainstormMessage, BrainstormSessionStatus, MessageRole


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


class TestBrainstormSessionModel:
    """Tests for BrainstormSession model."""

    def test_create_session(self, session):
        """Test creating a brainstorm session."""
        brainstorm_session = BrainstormSession(
            id="test-session-1",
            title="Mobile App Redesign",
            description="Reimagine the mobile experience",
            status=BrainstormSessionStatus.ACTIVE,
        )

        session.add(brainstorm_session)
        session.commit()

        assert brainstorm_session.id == "test-session-1"
        assert brainstorm_session.title == "Mobile App Redesign"
        assert brainstorm_session.status == BrainstormSessionStatus.ACTIVE
        assert isinstance(brainstorm_session.created_at, datetime)
        assert isinstance(brainstorm_session.updated_at, datetime)

    def test_session_cascade_delete_messages(self, session):
        """Test that deleting session deletes messages."""
        brainstorm_session = BrainstormSession(
            id="test-session-2",
            title="Test Session",
            description="Test description",
        )
        session.add(brainstorm_session)
        session.commit()

        message = BrainstormMessage(
            id="msg-1",
            session_id=brainstorm_session.id,
            role=MessageRole.USER,
            content="Hello",
        )
        session.add(message)
        session.commit()

        message_id = message.id

        # Delete session
        session.delete(brainstorm_session)
        session.commit()

        # Message should be deleted
        deleted_message = session.get(BrainstormMessage, message_id)
        assert deleted_message is None
