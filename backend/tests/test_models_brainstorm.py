"""Tests for brainstorm models with JSONB content."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    Base,
    BrainstormSession,
    BrainstormMessage,
    BrainstormSessionStatus,
    MessageRole,
)


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


def test_message_accepts_jsonb_content(session):
    """Message should accept JSONB block structure."""
    brainstorm_session = BrainstormSession(
        id="test-session",
        title="Test",
        description="Test session",
        status="active"
    )
    session.add(brainstorm_session)
    session.commit()

    message = BrainstormMessage(
        id="test-msg",
        session_id="test-session",
        role="user",
        content={
            "blocks": [
                {
                    "id": "block-1",
                    "type": "text",
                    "text": "Hello"
                }
            ]
        }
    )
    session.add(message)
    session.commit()

    # Retrieve and verify
    retrieved = session.query(BrainstormMessage).filter_by(id="test-msg").first()
    assert retrieved.content["blocks"][0]["text"] == "Hello"
    assert retrieved.content["blocks"][0]["type"] == "text"


def test_message_supports_button_group_block(session):
    """Message should support button_group block type."""
    brainstorm_session = BrainstormSession(
        id="test-session-2",
        title="Test",
        description="Test session",
        status="active"
    )
    session.add(brainstorm_session)
    session.commit()

    message = BrainstormMessage(
        id="test-msg-2",
        session_id="test-session-2",
        role="assistant",
        content={
            "blocks": [
                {
                    "id": "block-1",
                    "type": "text",
                    "text": "Choose platform:"
                },
                {
                    "id": "block-2",
                    "type": "button_group",
                    "label": "Platform",
                    "buttons": [
                        {"label": "iOS", "value": "ios"},
                        {"label": "Android", "value": "android"}
                    ]
                }
            ],
            "metadata": {}
        }
    )
    session.add(message)
    session.commit()

    retrieved = session.query(BrainstormMessage).filter_by(id="test-msg-2").first()
    assert retrieved.content["blocks"][1]["type"] == "button_group"
    assert len(retrieved.content["blocks"][1]["buttons"]) == 2
