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
    with client.websocket_connect("/api/v1/brainstorms/ws/ws-test-session") as websocket:
        # Connection successful if no exception
        assert websocket is not None


@pytest.mark.asyncio
async def test_websocket_rejects_nonexistent_session():
    """WebSocket should reject connections to non-existent sessions."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/brainstorms/ws/nonexistent-session") as websocket:
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
    with client.websocket_connect("/api/v1/brainstorms/ws/msg-test-session") as websocket:
        # Send user message
        websocket.send_json({
            "type": "user_message",
            "content": "Hello"
        })

        # Should receive stream_chunk or stream_complete
        response = websocket.receive_json()
        assert response["type"] in ["stream_chunk", "stream_complete", "error"]


@pytest.mark.asyncio
async def test_handles_malformed_json_gracefully():
    """Should fallback to text block when Claude returns invalid JSON."""
    from unittest.mock import AsyncMock, MagicMock, patch

    # Test the JSON parsing logic directly
    from app.api.brainstorms import stream_claude_response

    # Create mock websocket
    mock_websocket = MagicMock()
    sent_messages = []

    async def mock_send_json(data):
        sent_messages.append(data)

    mock_websocket.send_json = mock_send_json

    # Create mock database with session and message
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []

    async def mock_execute(*args, **kwargs):
        return mock_result

    async def mock_commit():
        pass

    mock_db.execute = mock_execute
    mock_db.commit = mock_commit
    mock_db.add = MagicMock()

    # Mock BrainstormingService to return malformed JSON
    async def mock_stream_generator(conversation):
        yield "This is not JSON, just plain text"

    mock_service_instance = MagicMock()
    mock_service_instance.stream_brainstorm_message = mock_stream_generator
    mock_service_instance.__aenter__ = AsyncMock(return_value=mock_service_instance)
    mock_service_instance.__aexit__ = AsyncMock(return_value=None)

    # Create mock agent factory
    mock_agent_factory = MagicMock()

    with patch('app.api.brainstorms.BrainstormingService', return_value=mock_service_instance):
        # Call the function directly
        await stream_claude_response(mock_websocket, mock_db, "test-session", mock_agent_factory)

    # Verify fallback text block was sent
    assert len(sent_messages) >= 1
    chunk_message = sent_messages[0]
    assert chunk_message["type"] == "stream_chunk"
    assert chunk_message["block"]["type"] == "text"
    assert "not JSON" in chunk_message["block"]["text"]

    # Verify stream_complete was sent
    assert any(msg["type"] == "stream_complete" for msg in sent_messages)


@pytest.mark.asyncio
async def test_handles_dict_in_text_block():
    """Should handle message blocks with dict values in text field."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.api.brainstorms import stream_claude_response
    from app.models.brainstorm import BrainstormMessage

    # Create mock websocket
    mock_websocket = MagicMock()
    sent_messages = []

    async def mock_send_json(data):
        sent_messages.append(data)

    mock_websocket.send_json = mock_send_json

    # Create mock database with message containing dict in text field
    mock_db = MagicMock()
    mock_result = MagicMock()

    # Create a message with dict in text field (the bug we're fixing)
    mock_message = MagicMock(spec=BrainstormMessage)
    mock_message.role = "user"
    mock_message.content = {
        "blocks": [
            {
                "type": "text",
                "text": {"error": "unexpected dict"}  # This caused the bug
            }
        ]
    }

    mock_result.scalars().all.return_value = [mock_message]

    async def mock_execute(*args, **kwargs):
        return mock_result

    async def mock_commit():
        pass

    mock_db.execute = mock_execute
    mock_db.commit = mock_commit
    mock_db.add = MagicMock()

    # Mock BrainstormingService
    async def mock_stream_generator(conversation):
        # Verify dict was converted to string in conversation
        assert len(conversation) == 1
        assert isinstance(conversation[0]["content"], str)
        # The dict should have been converted to JSON string
        assert "error" in conversation[0]["content"]
        yield '{"blocks": [{"type": "text", "text": "Response"}]}'

    mock_service_instance = MagicMock()
    mock_service_instance.stream_brainstorm_message = mock_stream_generator
    mock_service_instance.__aenter__ = AsyncMock(return_value=mock_service_instance)
    mock_service_instance.__aexit__ = AsyncMock(return_value=None)

    mock_agent_factory = MagicMock()

    with patch('app.api.brainstorms.BrainstormingService', return_value=mock_service_instance):
        # This should not raise "expected str instance, dict found" error
        await stream_claude_response(mock_websocket, mock_db, "test-session", mock_agent_factory)

    # Verify response was sent successfully
    assert len(sent_messages) >= 1
