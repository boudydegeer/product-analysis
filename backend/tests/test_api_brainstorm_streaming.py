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
        from contextlib import asynccontextmanager

        session = BrainstormSession(
            id="session-2",
            title="Test",
            description="Test",
        )
        db_session.add(session)
        await db_session.commit()

        async def mock_stream(*args, **kwargs):
            yield "Response text"

        # Mock async_session_maker to use the test db_session
        @asynccontextmanager
        async def mock_session_maker():
            yield db_session

        with patch("app.api.brainstorms.BrainstormingService") as MockService, patch(
            "app.database.async_session_maker", mock_session_maker
        ):
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.stream_brainstorm_message = mock_stream

            # Need to consume the stream for the generator to execute
            response = await async_client.get(
                "/api/v1/brainstorms/session-2/stream",
                params={"message": "User message"},
            )

            # Consume all stream chunks to ensure generator completes
            async for _ in response.aiter_bytes():
                pass

            # Verify messages were saved - need fresh session to see changes
            from sqlalchemy import select

            result = await db_session.execute(
                select(BrainstormSession).where(BrainstormSession.id == "session-2")
            )
            session = result.scalar_one()

            assert len(session.messages) == 2
            assert session.messages[0].role == MessageRole.USER
            assert session.messages[0].content == "User message"
            assert session.messages[1].role == MessageRole.ASSISTANT
            assert session.messages[1].content == "Response text"

    @pytest.mark.asyncio
    async def test_stream_returns_done_event_with_saved_status(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that stream returns 'done' event with saved status."""
        from contextlib import asynccontextmanager

        session = BrainstormSession(
            id="session-3",
            title="Test",
            description="Test",
        )
        db_session.add(session)
        await db_session.commit()

        async def mock_stream(*args, **kwargs):
            yield "Test response"

        @asynccontextmanager
        async def mock_session_maker():
            yield db_session

        with patch("app.api.brainstorms.BrainstormingService") as MockService, patch(
            "app.database.async_session_maker", mock_session_maker
        ):
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.stream_brainstorm_message = mock_stream

            response = await async_client.get(
                "/api/v1/brainstorms/session-3/stream",
                params={"message": "Test"},
            )

            # Collect all events
            raw_events = []
            async for chunk in response.aiter_bytes():
                raw_events.append(chunk.decode())

            # Parse SSE events - they may be combined in one chunk
            import json
            found_done_with_saved = False

            # Combine all chunks and split by "data: " prefix
            full_response = ''.join(raw_events)
            event_lines = [line.strip() for line in full_response.split('data: ') if line.strip()]

            for event_line in event_lines:
                # Remove any trailing newlines
                event_line = event_line.split('\n')[0]
                try:
                    event_data = json.loads(event_line)
                    if event_data.get('type') == 'done':
                        assert 'saved' in event_data, "Done event should include 'saved' status"
                        assert event_data['saved'] is True, "Assistant message should have been saved"
                        found_done_with_saved = True
                        break
                except json.JSONDecodeError:
                    continue

            assert found_done_with_saved, "No done event with 'saved' status found"
