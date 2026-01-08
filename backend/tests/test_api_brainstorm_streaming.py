"""Tests for brainstorm streaming endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from app.models.brainstorm import BrainstormSession, MessageRole


class TestStreamBrainstorm:
    """Tests for streaming brainstorm endpoint."""

    @pytest.mark.asyncio
    async def test_stream_endpoint_returns_sse(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that streaming endpoint returns SSE stream."""
        # Create session
        session = BrainstormSession(
            id="session-1",
            title="Test Session",
            description="Test description",
        )
        db_session.add(session)
        await db_session.commit()

        # Mock BrainstormingService
        async def mock_stream(*args, **kwargs):
            yield "Hello "
            yield "world"

        with patch("app.api.brainstorms.BrainstormingService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.stream_brainstorm_message = mock_stream

            response = await async_client.get(
                "/api/v1/brainstorms/session-1/stream",
                params={"message": "Hello Claude"},
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_stream_saves_messages(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that streaming saves user and assistant messages."""
        session = BrainstormSession(
            id="session-2",
            title="Test",
            description="Test",
        )
        db_session.add(session)
        await db_session.commit()

        async def mock_stream(*args, **kwargs):
            yield "Response text"

        with patch("app.api.brainstorms.BrainstormingService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.stream_brainstorm_message = mock_stream

            await async_client.get(
                "/api/v1/brainstorms/session-2/stream",
                params={"message": "User message"},
            )

            # Verify messages were saved
            await db_session.refresh(session)
            assert len(session.messages) == 2
            assert session.messages[0].role == MessageRole.USER
            assert session.messages[0].content == "User message"
            assert session.messages[1].role == MessageRole.ASSISTANT
