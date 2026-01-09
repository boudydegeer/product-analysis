"""Tests for brainstorming service."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.brainstorming_service import BrainstormingService


class TestBrainstormingService:
    """Tests for BrainstormingService."""

    @pytest.mark.asyncio
    async def test_stream_message(self):
        """Test streaming a brainstorm message."""
        messages = [
            {"role": "user", "content": "What are key features of a mobile app?"}
        ]

        # Create message objects with delta.text attribute
        class MockDelta:
            def __init__(self, text):
                self.text = text

        class MockMessage:
            def __init__(self, text):
                self.delta = MockDelta(text)
                # Don't have content or text attributes
                self._content = None
                self._text = None

        # Create async iterator for receive_messages()
        async def mock_receive_messages():
            # Yield message objects with delta.text attribute (streaming mode)
            for text in ["Key ", "features ", "include..."]:
                yield MockMessage(text)

        # Mock the claude-agent-sdk client
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.query = AsyncMock()
        mock_client.receive_messages = MagicMock(return_value=mock_receive_messages())

        # Mock ClaudeSDKClient to return our mock client
        with patch("app.services.brainstorming_service.ClaudeSDKClient", return_value=mock_client):
            service = BrainstormingService(api_key="test-key")

            chunks = []
            async for chunk in service.stream_brainstorm_message(messages):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert chunks[0] == "Key "
            assert chunks[1] == "features "
            assert chunks[2] == "include..."

            # Verify client methods were called
            mock_client.connect.assert_awaited_once()
            mock_client.query.assert_awaited_once()
