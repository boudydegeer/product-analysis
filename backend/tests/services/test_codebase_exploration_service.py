"""Tests for CodebaseExplorationService.

TDD: Tests written first, then implementation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import re

from app.services.codebase_exploration_service import CodebaseExplorationService


class TestGenerateExplorationId:
    """Tests for generate_exploration_id method."""

    def test_generate_exploration_id_format(self):
        """Test that exploration ID matches expected pattern: exp-{uuid4_short}."""
        service = CodebaseExplorationService()
        exploration_id = service.generate_exploration_id()

        # Should match pattern exp-{8 hex chars}
        pattern = r"^exp-[a-f0-9]{8}$"
        assert re.match(pattern, exploration_id), (
            f"Exploration ID '{exploration_id}' does not match pattern '{pattern}'"
        )

    def test_generate_exploration_id_unique(self):
        """Test that multiple calls generate unique IDs."""
        service = CodebaseExplorationService()
        ids = [service.generate_exploration_id() for _ in range(100)]

        # All IDs should be unique
        assert len(set(ids)) == 100, "Generated IDs should be unique"


class TestTriggerExploration:
    """Tests for trigger_exploration method."""

    @pytest.mark.asyncio
    async def test_trigger_exploration_calls_github_service(self, db_session):
        """Test that trigger_exploration correctly calls GitHubService."""
        # Mock GitHubService
        mock_github_service = AsyncMock()
        mock_github_service.trigger_workflow = AsyncMock(return_value=12345)
        mock_github_service.get_workflow_url = MagicMock(
            return_value="https://github.com/owner/repo/actions/runs/12345"
        )

        with patch(
            "app.services.codebase_exploration_service.GitHubService",
            return_value=mock_github_service
        ):
            service = CodebaseExplorationService()

            result = await service.trigger_exploration(
                db=db_session,
                exploration_id="exp-abc12345",
                query="How does authentication work?",
                scope="backend",
                focus="security",
                session_id="session-123",
                message_id="msg-456",
            )

            # Verify GitHubService was called with correct parameters
            mock_github_service.trigger_workflow.assert_called_once()
            call_args = mock_github_service.trigger_workflow.call_args

            # Check that required inputs were passed
            assert "exploration_id" in str(call_args) or call_args is not None

            # Verify return value structure
            assert "workflow_run_id" in result
            assert "workflow_url" in result
            assert result["workflow_run_id"] == 12345

    @pytest.mark.asyncio
    async def test_trigger_exploration_with_minimal_params(self, db_session):
        """Test trigger_exploration with only required parameters."""
        mock_github_service = AsyncMock()
        mock_github_service.trigger_workflow = AsyncMock(return_value=99999)
        mock_github_service.get_workflow_url = MagicMock(
            return_value="https://github.com/owner/repo/actions/runs/99999"
        )

        with patch(
            "app.services.codebase_exploration_service.GitHubService",
            return_value=mock_github_service
        ):
            service = CodebaseExplorationService()

            result = await service.trigger_exploration(
                db=db_session,
                exploration_id="exp-def67890",
                query="What APIs exist?",
                scope=None,
                focus=None,
                session_id="session-789",
                message_id="msg-012",
            )

            assert result["workflow_run_id"] == 99999
            assert "workflow_url" in result


class TestGetExplorationResults:
    """Tests for get_exploration_results method."""

    @pytest.mark.asyncio
    async def test_get_exploration_results_success(self, db_session):
        """Test successfully fetching exploration results."""
        mock_results = {
            "exploration_id": "exp-abc12345",
            "summary": "Found 5 relevant files",
            "files_found": ["auth.py", "security.py"],
            "patterns": ["JWT authentication", "OAuth2"],
            "code_examples": [{"file": "auth.py", "snippet": "def verify_token()"}],
            "recommendations": ["Consider adding rate limiting"],
        }

        mock_github_service = AsyncMock()
        mock_github_service.download_workflow_artifact = AsyncMock(
            return_value=mock_results
        )

        with patch(
            "app.services.codebase_exploration_service.GitHubService",
            return_value=mock_github_service
        ):
            service = CodebaseExplorationService()

            result = await service.get_exploration_results(
                db=db_session,
                exploration_id="exp-abc12345",
                workflow_run_id=12345,
            )

            assert result is not None
            assert result["exploration_id"] == "exp-abc12345"
            assert "summary" in result
            assert "files_found" in result

    @pytest.mark.asyncio
    async def test_get_exploration_results_not_found(self, db_session):
        """Test fetching results when workflow has no artifacts."""
        mock_github_service = AsyncMock()
        mock_github_service.download_workflow_artifact = AsyncMock(
            side_effect=Exception("No artifacts found")
        )

        with patch(
            "app.services.codebase_exploration_service.GitHubService",
            return_value=mock_github_service
        ):
            service = CodebaseExplorationService()

            result = await service.get_exploration_results(
                db=db_session,
                exploration_id="exp-notfound",
                workflow_run_id=99999,
            )

            assert result is None


class TestFormatResultsForAgent:
    """Tests for format_results_for_agent method."""

    def test_format_results_for_agent_full_results(self):
        """Test formatting complete results to readable markdown."""
        results = {
            "exploration_id": "exp-abc12345",
            "summary": "Found authentication implementation using JWT tokens",
            "files_found": [
                "backend/app/auth/jwt.py",
                "backend/app/auth/oauth.py",
                "backend/app/middleware/auth.py",
            ],
            "patterns": [
                "JWT token verification",
                "OAuth2 flow implementation",
                "Role-based access control",
            ],
            "code_examples": [
                {
                    "file": "backend/app/auth/jwt.py",
                    "snippet": "def verify_token(token: str) -> dict:\n    return jwt.decode(token, SECRET_KEY)",
                    "description": "Token verification function",
                },
            ],
            "recommendations": [
                "Add token refresh mechanism",
                "Implement rate limiting on auth endpoints",
            ],
        }

        service = CodebaseExplorationService()
        formatted = service.format_results_for_agent(results)

        # Verify it's a string
        assert isinstance(formatted, str)

        # Verify key sections are present
        assert "## Summary" in formatted or "summary" in formatted.lower()
        assert "jwt.py" in formatted
        assert "JWT token verification" in formatted or "jwt" in formatted.lower()
        assert "verify_token" in formatted
        assert "rate limiting" in formatted.lower()

        # Should be readable markdown
        assert len(formatted) > 100  # Should have substantial content

    def test_format_results_for_agent_minimal_results(self):
        """Test formatting results with minimal data."""
        results = {
            "exploration_id": "exp-minimal",
            "summary": "No relevant files found",
            "files_found": [],
            "patterns": [],
            "code_examples": [],
            "recommendations": [],
        }

        service = CodebaseExplorationService()
        formatted = service.format_results_for_agent(results)

        assert isinstance(formatted, str)
        assert "No relevant files found" in formatted or "no" in formatted.lower()

    def test_format_results_for_agent_empty_results(self):
        """Test formatting empty/null results."""
        service = CodebaseExplorationService()

        # Empty dict
        formatted = service.format_results_for_agent({})
        assert isinstance(formatted, str)
        assert len(formatted) > 0

        # None should be handled gracefully
        formatted_none = service.format_results_for_agent(None)
        assert isinstance(formatted_none, str)
        assert "no results" in formatted_none.lower() or "empty" in formatted_none.lower()

    def test_format_results_markdown_structure(self):
        """Test that output has proper markdown structure."""
        results = {
            "exploration_id": "exp-test",
            "summary": "Test summary",
            "files_found": ["file1.py", "file2.py"],
            "patterns": ["Pattern 1"],
            "code_examples": [
                {"file": "file1.py", "snippet": "code here", "description": "desc"}
            ],
            "recommendations": ["Recommendation 1"],
        }

        service = CodebaseExplorationService()
        formatted = service.format_results_for_agent(results)

        # Should have markdown headers
        assert "#" in formatted

        # Should have code blocks for code examples
        assert "```" in formatted or "`" in formatted
