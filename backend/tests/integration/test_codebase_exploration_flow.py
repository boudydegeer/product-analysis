"""Integration tests for codebase exploration flow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC

from app.models.codebase_exploration import CodebaseExploration, CodebaseExplorationStatus
from app.services.codebase_exploration_service import CodebaseExplorationService


class TestCodebaseExplorationFlow:
    """Test the complete codebase exploration flow."""

    @pytest.fixture
    def exploration_service(self):
        """Create an exploration service instance."""
        return CodebaseExplorationService()

    @pytest.fixture
    def sample_exploration_results(self):
        """Sample exploration results matching expected workflow output format."""
        return {
            "exploration_id": "exp-test123",
            "query": "How is authentication implemented?",
            "scope": "backend",
            "focus": "patterns",
            "status": "completed",
            "summary": "Authentication uses JWT tokens with refresh mechanism.",
            "files_found": [
                "backend/app/auth/jwt.py",
                "backend/app/auth/middleware.py"
            ],
            "patterns": [
                "JWT token validation",
                "Refresh token rotation"
            ],
            "code_examples": [
                {
                    "file": "backend/app/auth/jwt.py",
                    "snippet": "def validate_token(token: str)...",
                    "description": "Token validation logic"
                }
            ],
            "recommendations": ["Add token blacklist"],
            "metadata": {
                "model": "claude-sonnet-4-20250514",
                "tokens_used": {"input": 1000, "output": 500},
                "tool_calls_made": 5,
                "workflow_run_id": "12345",
                "completed_at": "2024-01-09T10:00:00Z"
            }
        }

    @pytest.mark.asyncio
    async def test_trigger_to_completion_flow(
        self, db_session, exploration_service, sample_exploration_results
    ):
        """Test complete flow: trigger -> poll -> results."""
        # 1. Trigger exploration
        with patch.object(
            exploration_service, 'trigger_exploration',
            new_callable=AsyncMock
        ) as mock_trigger:
            mock_trigger.return_value = {
                "workflow_run_id": "12345",
                "workflow_url": "https://github.com/owner/repo/actions/runs/12345"
            }

            # Create exploration record
            exploration_id = exploration_service.generate_exploration_id()
            exploration = CodebaseExploration(
                id=exploration_id,
                session_id="session-123",
                message_id="msg-456",
                query="How is authentication implemented?",
                scope="backend",
                focus="patterns",
                status=CodebaseExplorationStatus.PENDING
            )
            db_session.add(exploration)
            await db_session.commit()

            # Trigger workflow
            result = await exploration_service.trigger_exploration(
                db=db_session,
                exploration_id=exploration_id,
                query="How is authentication implemented?",
                scope="backend",
                focus="patterns",
                session_id="session-123",
                message_id="msg-456"
            )

            assert result["workflow_run_id"] == "12345"

        # 2. Simulate polling - update to INVESTIGATING status
        exploration.workflow_run_id = "12345"
        exploration.status = CodebaseExplorationStatus.INVESTIGATING
        await db_session.commit()

        # 3. Simulate completion - update results
        exploration.results = {
            "summary": sample_exploration_results["summary"],
            "files_found": sample_exploration_results["files_found"],
            "patterns": sample_exploration_results["patterns"],
            "code_examples": sample_exploration_results["code_examples"],
            "recommendations": sample_exploration_results["recommendations"],
        }
        exploration.formatted_context = exploration_service.format_results_for_agent(
            sample_exploration_results
        )
        exploration.status = CodebaseExplorationStatus.COMPLETED
        exploration.completed_at = datetime.now(UTC)
        await db_session.commit()

        # 4. Verify results
        await db_session.refresh(exploration)
        assert exploration.status == CodebaseExplorationStatus.COMPLETED
        assert exploration.formatted_context is not None
        assert "authentication" in exploration.formatted_context.lower()
        assert exploration.completed_at is not None

    @pytest.mark.asyncio
    async def test_format_results_produces_readable_output(
        self, exploration_service, sample_exploration_results
    ):
        """Test that formatted results are readable markdown."""
        formatted = exploration_service.format_results_for_agent(sample_exploration_results)

        # Should contain key sections
        assert "## " in formatted or "### " in formatted  # Has markdown headers
        assert "JWT" in formatted or "authentication" in formatted.lower()

        # Should mention relevant files
        assert "jwt.py" in formatted or "Files Found" in formatted

        # Should be reasonable length (not too short, not too long)
        assert len(formatted) > 100
        assert len(formatted) < 10000

    @pytest.mark.asyncio
    async def test_exploration_status_transitions(self, db_session):
        """Test that exploration status transitions correctly."""
        exploration = CodebaseExploration(
            id="exp-status-test",
            query="Test query",
            status=CodebaseExplorationStatus.PENDING
        )
        db_session.add(exploration)
        await db_session.commit()

        # PENDING -> INVESTIGATING
        exploration.status = CodebaseExplorationStatus.INVESTIGATING
        exploration.workflow_run_id = "12345"
        await db_session.commit()

        await db_session.refresh(exploration)
        assert exploration.status == CodebaseExplorationStatus.INVESTIGATING

        # INVESTIGATING -> COMPLETED
        exploration.status = CodebaseExplorationStatus.COMPLETED
        exploration.completed_at = datetime.now(UTC)
        await db_session.commit()

        await db_session.refresh(exploration)
        assert exploration.status == CodebaseExplorationStatus.COMPLETED
        assert exploration.completed_at is not None

    @pytest.mark.asyncio
    async def test_exploration_failure_handling(self, db_session):
        """Test that exploration failures are handled correctly."""
        exploration = CodebaseExploration(
            id="exp-fail-test",
            query="Test query",
            status=CodebaseExplorationStatus.INVESTIGATING,
            workflow_run_id="12345"
        )
        db_session.add(exploration)
        await db_session.commit()

        # Simulate failure
        exploration.status = CodebaseExplorationStatus.FAILED
        exploration.error_message = "Workflow timed out"
        await db_session.commit()

        await db_session.refresh(exploration)
        assert exploration.status == CodebaseExplorationStatus.FAILED
        assert exploration.error_message == "Workflow timed out"

    @pytest.mark.asyncio
    async def test_exploration_with_all_fields(self, db_session, exploration_service):
        """Test exploration with all optional fields populated."""
        exploration_id = exploration_service.generate_exploration_id()

        exploration = CodebaseExploration(
            id=exploration_id,
            session_id="session-full",
            message_id="msg-full",
            query="Full exploration query with all options",
            scope="backend",
            focus="security",
            status=CodebaseExplorationStatus.PENDING,
            workflow_run_id=None,
            workflow_url=None,
        )
        db_session.add(exploration)
        await db_session.commit()

        # Verify all fields saved correctly
        await db_session.refresh(exploration)
        assert exploration.id == exploration_id
        assert exploration.session_id == "session-full"
        assert exploration.message_id == "msg-full"
        assert exploration.scope == "backend"
        assert exploration.focus == "security"
        assert exploration.status == CodebaseExplorationStatus.PENDING

    @pytest.mark.asyncio
    async def test_exploration_results_storage(self, db_session, sample_exploration_results):
        """Test that exploration results are stored and retrieved correctly."""
        exploration = CodebaseExploration(
            id="exp-results-test",
            query="Test query for results",
            status=CodebaseExplorationStatus.COMPLETED,
            results=sample_exploration_results,
            completed_at=datetime.now(UTC)
        )
        db_session.add(exploration)
        await db_session.commit()

        await db_session.refresh(exploration)

        # Verify JSON results stored correctly
        assert exploration.results is not None
        assert exploration.results["summary"] == sample_exploration_results["summary"]
        assert "files_found" in exploration.results
        assert exploration.results["files_found"] == sample_exploration_results["files_found"]

    @pytest.mark.asyncio
    async def test_formatted_context_storage(self, db_session, exploration_service):
        """Test that formatted context is stored correctly."""
        results = {
            "exploration_id": "exp-format-test",
            "summary": "Test summary for formatting",
            "files_found": ["test.py"],
            "patterns": ["Test pattern"],
            "code_examples": [],
            "recommendations": [],
        }

        formatted = exploration_service.format_results_for_agent(results)

        exploration = CodebaseExploration(
            id="exp-format-test",
            query="Format test query",
            status=CodebaseExplorationStatus.COMPLETED,
            results=results,
            formatted_context=formatted,
            completed_at=datetime.now(UTC)
        )
        db_session.add(exploration)
        await db_session.commit()

        await db_session.refresh(exploration)

        assert exploration.formatted_context is not None
        assert "Test summary" in exploration.formatted_context
        assert len(exploration.formatted_context) > 50

    @pytest.mark.asyncio
    async def test_multiple_explorations_same_session(self, db_session):
        """Test multiple explorations can exist for the same session."""
        session_id = "session-multi"

        explorations = []
        for i in range(3):
            exp = CodebaseExploration(
                id=f"exp-multi-{i}",
                session_id=session_id,
                message_id=f"msg-{i}",
                query=f"Query {i}",
                status=CodebaseExplorationStatus.COMPLETED if i < 2 else CodebaseExplorationStatus.INVESTIGATING,
            )
            db_session.add(exp)
            explorations.append(exp)

        await db_session.commit()

        # Verify all explorations saved
        for exp in explorations:
            await db_session.refresh(exp)
            assert exp.session_id == session_id

    @pytest.mark.asyncio
    async def test_exploration_workflow_integration(self, db_session, exploration_service):
        """Test the complete exploration workflow with mocked GitHub service."""
        exploration_id = exploration_service.generate_exploration_id()

        # Create exploration in PENDING state
        exploration = CodebaseExploration(
            id=exploration_id,
            session_id="session-workflow",
            message_id="msg-workflow",
            query="How does the API routing work?",
            scope="backend",
            focus="patterns",
            status=CodebaseExplorationStatus.PENDING
        )
        db_session.add(exploration)
        await db_session.commit()

        # Mock GitHub service for triggering workflow
        mock_github_service = AsyncMock()
        mock_github_service.trigger_workflow = AsyncMock(return_value=67890)
        mock_github_service.get_workflow_url = MagicMock(
            return_value="https://github.com/owner/repo/actions/runs/67890"
        )

        with patch(
            "app.services.codebase_exploration_service.GitHubService",
            return_value=mock_github_service
        ):
            result = await exploration_service.trigger_exploration(
                db=db_session,
                exploration_id=exploration_id,
                query="How does the API routing work?",
                scope="backend",
                focus="patterns",
                session_id="session-workflow",
                message_id="msg-workflow"
            )

        # Verify trigger returned workflow info
        assert result["workflow_run_id"] == 67890
        assert "github.com" in result["workflow_url"]

        # Update exploration with workflow info
        exploration.workflow_run_id = str(result["workflow_run_id"])
        exploration.workflow_url = result["workflow_url"]
        exploration.status = CodebaseExplorationStatus.INVESTIGATING
        await db_session.commit()

        await db_session.refresh(exploration)
        assert exploration.status == CodebaseExplorationStatus.INVESTIGATING
        assert exploration.workflow_run_id == "67890"

    @pytest.mark.asyncio
    async def test_format_empty_results(self, exploration_service):
        """Test formatting handles empty/None results gracefully."""
        # None results
        formatted_none = exploration_service.format_results_for_agent(None)
        assert isinstance(formatted_none, str)
        assert len(formatted_none) > 0
        assert "no results" in formatted_none.lower() or "empty" in formatted_none.lower()

        # Empty dict
        formatted_empty = exploration_service.format_results_for_agent({})
        assert isinstance(formatted_empty, str)
        assert len(formatted_empty) > 0

    @pytest.mark.asyncio
    async def test_format_partial_results(self, exploration_service):
        """Test formatting handles partial results (missing fields)."""
        partial_results = {
            "exploration_id": "exp-partial",
            "summary": "Only summary provided",
            # Missing: files_found, patterns, code_examples, recommendations
        }

        formatted = exploration_service.format_results_for_agent(partial_results)

        assert isinstance(formatted, str)
        assert "Only summary provided" in formatted
        assert len(formatted) > 50

    @pytest.mark.asyncio
    async def test_exploration_id_uniqueness(self, exploration_service):
        """Test that generated exploration IDs are unique."""
        ids = set()
        for _ in range(100):
            exp_id = exploration_service.generate_exploration_id()
            assert exp_id not in ids, f"Duplicate ID generated: {exp_id}"
            ids.add(exp_id)

        assert len(ids) == 100

    @pytest.mark.asyncio
    async def test_exploration_id_format(self, exploration_service):
        """Test that exploration IDs follow expected format."""
        import re

        for _ in range(10):
            exp_id = exploration_service.generate_exploration_id()
            # Should match: exp-{8 hex characters}
            assert re.match(r"^exp-[a-f0-9]{8}$", exp_id), f"Invalid ID format: {exp_id}"
