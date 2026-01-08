"""Tests for brainstorming service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.brainstorming_service import BrainstormingService


class TestBrainstormingService:
    """Tests for BrainstormingService."""

    @pytest.mark.asyncio
    async def test_stream_message(self):
        """Test streaming a brainstorm message."""
        service = BrainstormingService(api_key="test-key")

        messages = [
            {"role": "user", "content": "What are key features of a mobile app?"}
        ]

        # Mock the Anthropic client
        with patch.object(service, 'client') as mock_client:
            # Create an async iterator that yields text chunks
            async def mock_text_stream():
                for text in ["Key ", "features ", "include..."]:
                    yield text

            mock_stream = MagicMock()
            mock_stream.text_stream = mock_text_stream()
            mock_client.messages.stream.return_value.__aenter__.return_value = mock_stream

            chunks = []
            async for chunk in service.stream_brainstorm_message(messages):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert chunks[0] == "Key "
            assert chunks[1] == "features "

    def test_format_messages(self):
        """Test message formatting."""
        service = BrainstormingService(api_key="test-key")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        formatted = service._format_messages(messages)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello"
