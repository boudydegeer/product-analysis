"""Tests for brainstorming service."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.brainstorming_service import (
    BrainstormingService,
    StreamChunk,
    ToolUseRequest,
    TOOL_CALL_PATTERN,
)


class TestBrainstormingService:
    """Tests for BrainstormingService."""

    @pytest.mark.asyncio
    async def test_stream_message(self):
        """Test streaming a brainstorm message."""
        messages = [
            {"role": "user", "content": "What are key features of a mobile app?"}
        ]

        # Create mock TextBlock that matches claude_agent_sdk.types.TextBlock
        class MockTextBlock:
            def __init__(self, text):
                self.text = text

        # Create mock AssistantMessage that matches claude_agent_sdk.types.AssistantMessage
        class MockAssistantMessage:
            def __init__(self, texts):
                self.content = [MockTextBlock(t) for t in texts]

        # Create async iterator for receive_response()
        async def mock_receive_response():
            # Yield AssistantMessage objects with TextBlock content
            for text in ["Key ", "features ", "include..."]:
                yield MockAssistantMessage([text])

        # Mock the claude-agent-sdk client
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.query = AsyncMock()
        mock_client.receive_response = MagicMock(return_value=mock_receive_response())

        # Mock ClaudeSDKClient to return our mock client
        # Also mock AssistantMessage and TextBlock type checks
        with patch("app.services.brainstorming_service.ClaudeSDKClient", return_value=mock_client), \
             patch("app.services.brainstorming_service.AssistantMessage", MockAssistantMessage), \
             patch("app.services.brainstorming_service.TextBlock", MockTextBlock):
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

    @pytest.mark.asyncio
    async def test_stream_with_tool_detection_no_tools(self):
        """Test streaming with tool detection when no tools are called."""
        messages = [
            {"role": "user", "content": "Tell me about the project."}
        ]

        # Create mock types
        class MockTextBlock:
            def __init__(self, text):
                self.text = text

        class MockAssistantMessage:
            def __init__(self, texts):
                self.content = [MockTextBlock(t) for t in texts]

        async def mock_receive_response():
            # Normal response without tool calls
            yield MockAssistantMessage(["Here is some ", "information about the project."])

        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.query = AsyncMock()
        mock_client.receive_response = MagicMock(return_value=mock_receive_response())

        with patch("app.services.brainstorming_service.ClaudeSDKClient", return_value=mock_client), \
             patch("app.services.brainstorming_service.AssistantMessage", MockAssistantMessage), \
             patch("app.services.brainstorming_service.TextBlock", MockTextBlock):
            service = BrainstormingService(api_key="test-key")

            chunks = []
            async for chunk in service.stream_with_tool_detection(messages):
                chunks.append(chunk)

            # Should have text chunks and complete
            text_chunks = [c for c in chunks if c.type == "text"]
            complete_chunks = [c for c in chunks if c.type == "complete"]
            tool_chunks = [c for c in chunks if c.type == "tool_use"]

            assert len(text_chunks) == 2
            assert len(complete_chunks) == 1
            assert len(tool_chunks) == 0

    @pytest.mark.asyncio
    async def test_stream_with_tool_detection_tool_call(self):
        """Test streaming with tool detection when a tool is called."""
        messages = [
            {"role": "user", "content": "How is authentication implemented?"}
        ]

        # Create mock types
        class MockTextBlock:
            def __init__(self, text):
                self.text = text

        class MockAssistantMessage:
            def __init__(self, texts):
                self.content = [MockTextBlock(t) for t in texts]

        async def mock_receive_response():
            # Response with tool call JSON embedded
            tool_json = '{"tool_call": "explore_codebase", "query": "authentication implementation", "scope": "backend", "focus": "patterns"}'
            yield MockAssistantMessage([tool_json])

        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.query = AsyncMock()
        mock_client.receive_response = MagicMock(return_value=mock_receive_response())

        with patch("app.services.brainstorming_service.ClaudeSDKClient", return_value=mock_client), \
             patch("app.services.brainstorming_service.AssistantMessage", MockAssistantMessage), \
             patch("app.services.brainstorming_service.TextBlock", MockTextBlock):
            service = BrainstormingService(api_key="test-key")

            chunks = []
            async for chunk in service.stream_with_tool_detection(messages):
                chunks.append(chunk)

            # Should detect tool call
            tool_chunks = [c for c in chunks if c.type == "tool_use"]
            assert len(tool_chunks) == 1

            tool_use = tool_chunks[0].tool_use
            assert tool_use.tool_name == "explore_codebase"
            assert tool_use.tool_input["query"] == "authentication implementation"
            assert tool_use.tool_input["scope"] == "backend"
            assert tool_use.tool_input["focus"] == "patterns"

    def test_detect_tool_call(self):
        """Test _detect_tool_call method."""
        service = BrainstormingService(api_key="test-key")

        # Valid tool call
        text = 'Some text {"tool_call": "explore_codebase", "query": "test"} more text'
        result = service._detect_tool_call(text)
        assert result is not None
        assert result["tool_call"] == "explore_codebase"
        assert result["query"] == "test"

        # No tool call
        text = "Just regular text without tool calls"
        result = service._detect_tool_call(text)
        assert result is None

        # Invalid JSON
        text = '{"tool_call": "explore_codebase" invalid'
        result = service._detect_tool_call(text)
        assert result is None

    def test_extract_tool_calls(self):
        """Test _extract_tool_calls method."""
        service = BrainstormingService(api_key="test-key")

        # Text with tool call
        text = 'Before {"tool_call": "explore_codebase", "query": "test"} After'
        tool_calls, cleaned = service._extract_tool_calls(text)

        assert len(tool_calls) == 1
        assert tool_calls[0]["query"] == "test"
        assert "tool_call" not in cleaned
        assert "Before" in cleaned
        assert "After" in cleaned

        # Text without tool call
        text = "Just regular text"
        tool_calls, cleaned = service._extract_tool_calls(text)
        assert len(tool_calls) == 0
        assert cleaned == "Just regular text"
