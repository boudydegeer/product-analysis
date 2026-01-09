"""Tests for brainstorming service."""
import pytest
from unittest.mock import patch, AsyncMock
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

        # Create async iterator for text_stream
        async def mock_text_stream():
            # Yield text chunks from streaming mode
            for text in ["Key ", "features ", "include..."]:
                yield text

        # Create mock stream context manager
        class MockStream:
            def __init__(self):
                self.text_stream = mock_text_stream()

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        # Mock the Anthropic messages.stream method
        mock_stream = MockStream()

        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            chunks = []
            async for chunk in service.stream_brainstorm_message(messages):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert chunks[0] == "Key "
            assert chunks[1] == "features "
            assert chunks[2] == "include..."

            # Just verify we got the expected chunks
            # (In a real scenario, the API call parameters would be verified via integration tests)
