"""Tests for brainstorm schemas."""
from datetime import datetime
from app.schemas.brainstorm import (
    BrainstormSessionCreate,
    BrainstormSessionResponse,
    BrainstormMessageResponse,
)


def test_session_create_schema():
    """Test BrainstormSessionCreate schema validation."""
    data = {
        "title": "Mobile App Redesign",
        "description": "Reimagine the mobile experience",
    }

    schema = BrainstormSessionCreate(**data)
    assert schema.title == "Mobile App Redesign"
    assert schema.description == "Reimagine the mobile experience"


def test_session_response_schema():
    """Test BrainstormSessionResponse schema."""
    data = {
        "id": "session-1",
        "title": "Test Session",
        "description": "Test description",
        "status": "active",
        "messages": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    schema = BrainstormSessionResponse(**data)
    assert schema.id == "session-1"
    assert schema.status == "active"


def test_message_response_schema():
    """Test BrainstormMessageResponse schema."""
    data = {
        "id": "msg-1",
        "session_id": "session-1",
        "role": "user",
        "content": "Hello",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    schema = BrainstormMessageResponse(**data)
    assert schema.role == "user"
    assert schema.content == "Hello"
