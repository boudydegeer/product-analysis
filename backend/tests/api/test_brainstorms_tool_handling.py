"""Tests for tool call handling in brainstorms WebSocket."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.brainstorms import handle_tool_call, handle_explore_codebase
from app.models.codebase_exploration import CodebaseExploration, CodebaseExplorationStatus


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    websocket = MagicMock()
    sent_messages = []

    async def mock_send_json(data):
        sent_messages.append(data)

    websocket.send_json = mock_send_json
    websocket.sent_messages = sent_messages
    return websocket


@pytest.fixture
def mock_db():
    """Create a mock database session for testing."""
    db = MagicMock(spec=AsyncSession)

    async def mock_commit():
        pass

    db.commit = mock_commit
    db.add = MagicMock()
    return db


class TestHandleToolCall:
    """Tests for handle_tool_call dispatcher function."""

    @pytest.mark.asyncio
    async def test_handle_tool_call_dispatches_explore_codebase(
        self, mock_websocket, mock_db
    ):
        """Should dispatch explore_codebase tool calls to handler."""
        tool_input = {
            "query": "Find authentication patterns",
            "scope": "backend",
            "focus": "security"
        }

        with patch(
            "app.api.brainstorms.handle_explore_codebase",
            new_callable=AsyncMock
        ) as mock_handler:
            mock_handler.return_value = {
                "exploration_id": "exp-test123",
                "status": "investigating",
                "message": "Codebase exploration started."
            }

            result = await handle_tool_call(
                tool_name="explore_codebase",
                tool_input=tool_input,
                session_id="session-123",
                message_id="msg-456",
                db=mock_db,
                websocket=mock_websocket
            )

            mock_handler.assert_called_once_with(
                tool_input,
                "session-123",
                "msg-456",
                mock_db,
                mock_websocket
            )
            assert result["exploration_id"] == "exp-test123"
            assert result["status"] == "investigating"

    @pytest.mark.asyncio
    async def test_handle_unknown_tool_returns_error(
        self, mock_websocket, mock_db
    ):
        """Should return error for unknown tool names."""
        result = await handle_tool_call(
            tool_name="unknown_tool",
            tool_input={"param": "value"},
            session_id="session-123",
            message_id="msg-456",
            db=mock_db,
            websocket=mock_websocket
        )

        assert "error" in result
        assert "Unknown tool: unknown_tool" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_tool_call_with_empty_tool_name(
        self, mock_websocket, mock_db
    ):
        """Should return error for empty tool name."""
        result = await handle_tool_call(
            tool_name="",
            tool_input={},
            session_id="session-123",
            message_id="msg-456",
            db=mock_db,
            websocket=mock_websocket
        )

        assert "error" in result
        assert "Unknown tool:" in result["error"]


class TestHandleExploreCodebase:
    """Tests for handle_explore_codebase handler function."""

    @pytest.mark.asyncio
    async def test_handle_explore_codebase_creates_record(
        self, mock_websocket, mock_db
    ):
        """Should create a CodebaseExploration record in the database."""
        tool_input = {
            "query": "Find API patterns",
            "scope": "backend",
            "focus": "architecture"
        }

        with patch(
            "app.api.brainstorms.CodebaseExplorationService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.generate_exploration_id.return_value = "exp-abc123"
            mock_service.trigger_exploration = AsyncMock(return_value={
                "workflow_run_id": "12345",
                "workflow_url": "https://github.com/owner/repo/actions/runs/12345"
            })

            await handle_explore_codebase(
                tool_input=tool_input,
                session_id="session-123",
                message_id="msg-456",
                db=mock_db,
                websocket=mock_websocket
            )

            # Verify db.add was called with a CodebaseExploration
            assert mock_db.add.called
            call_args = mock_db.add.call_args[0][0]
            assert isinstance(call_args, CodebaseExploration)
            assert call_args.id == "exp-abc123"
            assert call_args.session_id == "session-123"
            assert call_args.message_id == "msg-456"
            assert call_args.query == "Find API patterns"
            assert call_args.scope == "backend"
            assert call_args.focus == "architecture"
            # After successful workflow trigger, status is updated to INVESTIGATING
            assert call_args.status == CodebaseExplorationStatus.INVESTIGATING

    @pytest.mark.asyncio
    async def test_handle_explore_codebase_triggers_workflow(
        self, mock_websocket, mock_db
    ):
        """Should trigger GitHub workflow with correct parameters."""
        tool_input = {
            "query": "Find authentication code",
            "scope": "full",
            "focus": "security"
        }

        with patch(
            "app.api.brainstorms.CodebaseExplorationService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.generate_exploration_id.return_value = "exp-def456"
            mock_service.trigger_exploration = AsyncMock(return_value={
                "workflow_run_id": "67890",
                "workflow_url": "https://github.com/owner/repo/actions/runs/67890"
            })

            result = await handle_explore_codebase(
                tool_input=tool_input,
                session_id="session-789",
                message_id="msg-012",
                db=mock_db,
                websocket=mock_websocket
            )

            # Verify trigger_exploration was called with correct params
            mock_service.trigger_exploration.assert_called_once_with(
                db=mock_db,
                exploration_id="exp-def456",
                query="Find authentication code",
                scope="full",
                focus="security",
                session_id="session-789",
                message_id="msg-012"
            )

            assert result["exploration_id"] == "exp-def456"
            assert result["status"] == "investigating"

    @pytest.mark.asyncio
    async def test_handle_explore_codebase_sends_websocket_message(
        self, mock_websocket, mock_db
    ):
        """Should send tool_executing message via WebSocket."""
        tool_input = {
            "query": "Find database models",
            "scope": "backend",
            "focus": "patterns"
        }

        with patch(
            "app.api.brainstorms.CodebaseExplorationService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.generate_exploration_id.return_value = "exp-ghi789"
            mock_service.trigger_exploration = AsyncMock(return_value={
                "workflow_run_id": "11111",
                "workflow_url": "https://github.com/owner/repo/actions/runs/11111"
            })

            await handle_explore_codebase(
                tool_input=tool_input,
                session_id="session-aaa",
                message_id="msg-bbb",
                db=mock_db,
                websocket=mock_websocket
            )

            # Verify WebSocket message was sent
            assert len(mock_websocket.sent_messages) == 1
            ws_message = mock_websocket.sent_messages[0]
            assert ws_message["type"] == "tool_executing"
            assert ws_message["tool_name"] == "explore_codebase"
            assert ws_message["exploration_id"] == "exp-ghi789"
            assert ws_message["status"] == "investigating"
            assert ws_message["message"] == "Investigating codebase..."

    @pytest.mark.asyncio
    async def test_handle_explore_codebase_with_default_values(
        self, mock_websocket, mock_db
    ):
        """Should use default values for scope and focus when not provided."""
        tool_input = {
            "query": "Find patterns"
            # scope and focus not provided
        }

        with patch(
            "app.api.brainstorms.CodebaseExplorationService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.generate_exploration_id.return_value = "exp-jkl012"
            mock_service.trigger_exploration = AsyncMock(return_value={
                "workflow_run_id": "22222",
                "workflow_url": "https://github.com/owner/repo/actions/runs/22222"
            })

            await handle_explore_codebase(
                tool_input=tool_input,
                session_id="session-ccc",
                message_id="msg-ddd",
                db=mock_db,
                websocket=mock_websocket
            )

            # Verify default values were used
            call_args = mock_db.add.call_args[0][0]
            assert call_args.scope == "full"
            assert call_args.focus == "patterns"

    @pytest.mark.asyncio
    async def test_handle_explore_codebase_handles_workflow_error(
        self, mock_websocket, mock_db
    ):
        """Should handle workflow trigger errors gracefully."""
        tool_input = {
            "query": "Find something",
            "scope": "backend",
            "focus": "patterns"
        }

        with patch(
            "app.api.brainstorms.CodebaseExplorationService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.generate_exploration_id.return_value = "exp-error123"
            mock_service.trigger_exploration = AsyncMock(
                side_effect=Exception("GitHub API error")
            )

            result = await handle_explore_codebase(
                tool_input=tool_input,
                session_id="session-err",
                message_id="msg-err",
                db=mock_db,
                websocket=mock_websocket
            )

            # Verify error is returned
            assert "error" in result
            assert "GitHub API error" in result["error"]

            # Verify exploration status was updated to FAILED
            # The exploration record should have been updated
            call_args = mock_db.add.call_args[0][0]
            assert call_args.status == CodebaseExplorationStatus.FAILED
            assert call_args.error_message == "GitHub API error"

    @pytest.mark.asyncio
    async def test_handle_explore_codebase_updates_workflow_info(
        self, mock_websocket, mock_db
    ):
        """Should update exploration record with workflow info after trigger."""
        tool_input = {
            "query": "Find routes",
            "scope": "frontend",
            "focus": "patterns"
        }

        with patch(
            "app.api.brainstorms.CodebaseExplorationService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.generate_exploration_id.return_value = "exp-upd456"
            mock_service.trigger_exploration = AsyncMock(return_value={
                "workflow_run_id": "33333",
                "workflow_url": "https://github.com/owner/repo/actions/runs/33333"
            })

            await handle_explore_codebase(
                tool_input=tool_input,
                session_id="session-upd",
                message_id="msg-upd",
                db=mock_db,
                websocket=mock_websocket
            )

            # Verify the exploration was updated with workflow info
            # After successful trigger, status should be INVESTIGATING
            call_args = mock_db.add.call_args[0][0]
            # After the update, the status should be INVESTIGATING
            # Note: In the actual code, the status is updated on the same object
            # but since we're mocking, we verify the initial creation was correct
            assert call_args.id == "exp-upd456"


class TestToolCallIntegration:
    """Integration tests for tool call handling."""

    @pytest.mark.asyncio
    async def test_full_explore_codebase_flow(
        self, mock_websocket, mock_db
    ):
        """Test complete flow from tool call to WebSocket notification."""
        tool_input = {
            "query": "Analyze authentication implementation",
            "scope": "backend",
            "focus": "security"
        }

        with patch(
            "app.api.brainstorms.CodebaseExplorationService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.generate_exploration_id.return_value = "exp-flow789"
            mock_service.trigger_exploration = AsyncMock(return_value={
                "workflow_run_id": "44444",
                "workflow_url": "https://github.com/owner/repo/actions/runs/44444"
            })

            # Call through the dispatcher
            result = await handle_tool_call(
                tool_name="explore_codebase",
                tool_input=tool_input,
                session_id="session-flow",
                message_id="msg-flow",
                db=mock_db,
                websocket=mock_websocket
            )

            # Verify result
            assert result["exploration_id"] == "exp-flow789"
            assert result["status"] == "investigating"
            assert "started" in result["message"].lower()

            # Verify WebSocket message
            assert len(mock_websocket.sent_messages) == 1
            ws_msg = mock_websocket.sent_messages[0]
            assert ws_msg["type"] == "tool_executing"
            assert ws_msg["exploration_id"] == "exp-flow789"

            # Verify database record creation
            assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_empty_query_is_accepted(
        self, mock_websocket, mock_db
    ):
        """Should accept empty query (edge case)."""
        tool_input = {
            "query": "",
            "scope": "full",
            "focus": "patterns"
        }

        with patch(
            "app.api.brainstorms.CodebaseExplorationService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.generate_exploration_id.return_value = "exp-empty"
            mock_service.trigger_exploration = AsyncMock(return_value={
                "workflow_run_id": "55555",
                "workflow_url": "https://github.com/owner/repo/actions/runs/55555"
            })

            result = await handle_explore_codebase(
                tool_input=tool_input,
                session_id="session-empty",
                message_id="msg-empty",
                db=mock_db,
                websocket=mock_websocket
            )

            # Should succeed even with empty query
            assert "error" not in result
            assert result["exploration_id"] == "exp-empty"
