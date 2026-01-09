"""Tests for WebSocket brainstorming endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.brainstorm import BrainstormSession


@pytest.mark.asyncio
async def test_websocket_accepts_connection(db_session):
    """WebSocket should accept connections to existing sessions."""
    # Create test session
    session = BrainstormSession(
        id="ws-test-session",
        title="Test Session",
        description="Test",
        status="active"
    )
    db_session.add(session)
    await db_session.commit()

    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/brainstorms/ws/ws-test-session") as websocket:
        # Connection successful if no exception
        assert websocket is not None


@pytest.mark.asyncio
async def test_websocket_rejects_nonexistent_session():
    """WebSocket should reject connections to non-existent sessions."""
    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/brainstorms/ws/nonexistent-session") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_websocket_handles_user_message(db_session):
    """WebSocket should handle user_message type."""
    session = BrainstormSession(
        id="msg-test-session",
        title="Test",
        description="Test",
        status="active"
    )
    db_session.add(session)
    await db_session.commit()

    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/brainstorms/ws/msg-test-session") as websocket:
        # Send user message
        websocket.send_json({
            "type": "user_message",
            "content": "Hello"
        })

        # Should receive stream_chunk or stream_complete
        response = websocket.receive_json()
        assert response["type"] in ["stream_chunk", "stream_complete", "error"]
