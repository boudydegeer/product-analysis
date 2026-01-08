"""Tests for GitHub service - TDD RED phase.

Tests for GitHubService class that interacts with GitHub Actions API
to trigger workflows, check status, and download artifacts.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import httpx
import pytest

from app.services.github_service import GitHubService, GitHubServiceError


@pytest.fixture
def github_service():
    """Create GitHubService instance with test configuration."""
    return GitHubService(
        token="test_github_token",
        repo="owner/test-repo",
    )


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.AsyncClient."""
    return AsyncMock(spec=httpx.AsyncClient)


class TestGitHubServiceInit:
    """Tests for GitHubService initialization."""

    def test_init_takes_token_and_repo(self):
        """GitHubService should accept token and repo in __init__."""
        service = GitHubService(
            token="my_token",
            repo="owner/repo",
        )
        assert service.token == "my_token"
        assert service.repo == "owner/repo"

    def test_init_parses_owner_and_repo_name(self):
        """GitHubService should parse owner and repo name from repo string."""
        service = GitHubService(
            token="my_token",
            repo="smith-ai/product-analysis",
        )
        assert service.owner == "smith-ai"
        assert service.repo_name == "product-analysis"

    def test_init_sets_api_base_url(self):
        """GitHubService should set the GitHub API base URL."""
        service = GitHubService(
            token="my_token",
            repo="owner/repo",
        )
        assert service.api_base_url == "https://api.github.com"


class TestTriggerAnalysisWorkflow:
    """Tests for trigger_analysis_workflow method."""

    @pytest.mark.asyncio
    async def test_trigger_analysis_workflow_success(self, github_service):
        """Successful workflow trigger should return run_id."""
        feature_id = UUID("12345678-1234-5678-1234-567812345678")

        # Mock the HTTP response for workflow dispatch
        mock_dispatch_response = MagicMock()
        mock_dispatch_response.status_code = 204
        mock_dispatch_response.raise_for_status = MagicMock()

        # Mock the response for listing workflow runs to get the run_id
        mock_runs_response = MagicMock()
        mock_runs_response.status_code = 200
        mock_runs_response.json.return_value = {
            "workflow_runs": [
                {
                    "id": 12345,
                    "status": "queued",
                    "created_at": "2024-01-07T10:00:00Z",
                }
            ]
        }
        mock_runs_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.post.return_value = mock_dispatch_response
            mock_client.get.return_value = mock_runs_response

            run_id = await github_service.trigger_analysis_workflow(feature_id)

            assert run_id == 12345
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_analysis_workflow_failure_raises_exception(
        self, github_service
    ):
        """Failed workflow trigger should raise GitHubServiceError."""
        feature_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unprocessable Entity",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.post.return_value = mock_response

            with pytest.raises(GitHubServiceError) as exc_info:
                await github_service.trigger_analysis_workflow(feature_id)

            assert "Failed to trigger workflow" in str(exc_info.value)


class TestGetWorkflowRunStatus:
    """Tests for get_workflow_run_status method."""

    @pytest.mark.asyncio
    async def test_get_workflow_run_status_queued(self, github_service):
        """Should return 'queued' status for queued workflow run."""
        run_id = 12345

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": run_id,
            "status": "queued",
            "conclusion": None,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.return_value = mock_response

            status = await github_service.get_workflow_run_status(run_id)

            assert status == "queued"

    @pytest.mark.asyncio
    async def test_get_workflow_run_status_in_progress(self, github_service):
        """Should return 'in_progress' status for running workflow."""
        run_id = 12345

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": run_id,
            "status": "in_progress",
            "conclusion": None,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.return_value = mock_response

            status = await github_service.get_workflow_run_status(run_id)

            assert status == "in_progress"

    @pytest.mark.asyncio
    async def test_get_workflow_run_status_completed(self, github_service):
        """Should return 'completed' for successfully finished workflow."""
        run_id = 12345

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": run_id,
            "status": "completed",
            "conclusion": "success",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.return_value = mock_response

            status = await github_service.get_workflow_run_status(run_id)

            assert status == "completed"

    @pytest.mark.asyncio
    async def test_get_workflow_run_status_failure(self, github_service):
        """Should return 'failure' for failed workflow."""
        run_id = 12345

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": run_id,
            "status": "completed",
            "conclusion": "failure",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.return_value = mock_response

            status = await github_service.get_workflow_run_status(run_id)

            assert status == "failure"

    @pytest.mark.asyncio
    async def test_get_workflow_run_status_not_found(self, github_service):
        """Should raise exception for non-existent workflow run."""
        run_id = 99999

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.return_value = mock_response

            with pytest.raises(GitHubServiceError) as exc_info:
                await github_service.get_workflow_run_status(run_id)

            assert "not found" in str(exc_info.value).lower()


class TestDownloadWorkflowArtifact:
    """Tests for download_workflow_artifact method."""

    @pytest.mark.asyncio
    async def test_download_workflow_artifact_success(self, github_service):
        """Should return parsed JSON data from artifact."""
        run_id = 12345
        expected_data = {
            "feature_id": "TEST-001",
            "complexity": {
                "story_points": 5,
                "estimated_hours": 16,
            },
            "recommendations": ["Use async/await", "Add unit tests"],
        }

        # Mock listing artifacts
        mock_artifacts_response = MagicMock()
        mock_artifacts_response.status_code = 200
        mock_artifacts_response.json.return_value = {
            "artifacts": [
                {
                    "id": 98765,
                    "name": "analysis-result",
                    "archive_download_url": "https://api.github.com/repos/owner/repo/actions/artifacts/98765/zip",
                }
            ]
        }
        mock_artifacts_response.raise_for_status = MagicMock()

        # Mock downloading artifact (returns zip with JSON)
        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = _create_mock_zip_with_json(expected_data)
        mock_download_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.side_effect = [
                mock_artifacts_response,
                mock_download_response,
            ]

            result = await github_service.download_workflow_artifact(run_id)

            assert result == expected_data
            assert result["feature_id"] == "TEST-001"
            assert result["complexity"]["story_points"] == 5

    @pytest.mark.asyncio
    async def test_download_workflow_artifact_no_artifacts(self, github_service):
        """Should raise exception when no artifacts found."""
        run_id = 12345

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"artifacts": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.return_value = mock_response

            with pytest.raises(GitHubServiceError) as exc_info:
                await github_service.download_workflow_artifact(run_id)

            assert "No artifacts found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_workflow_artifact_specific_name(self, github_service):
        """Should download artifact with specific name when provided."""
        run_id = 12345
        artifact_name = "feature-analysis-report"
        expected_data = {"report": "data"}

        mock_artifacts_response = MagicMock()
        mock_artifacts_response.status_code = 200
        mock_artifacts_response.json.return_value = {
            "artifacts": [
                {"id": 111, "name": "other-artifact"},
                {"id": 222, "name": "feature-analysis-report"},
            ]
        }
        mock_artifacts_response.raise_for_status = MagicMock()

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = _create_mock_zip_with_json(expected_data)
        mock_download_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.side_effect = [
                mock_artifacts_response,
                mock_download_response,
            ]

            result = await github_service.download_workflow_artifact(
                run_id, artifact_name=artifact_name
            )

            assert result == expected_data

    @pytest.mark.asyncio
    async def test_download_workflow_artifact_follows_redirects(self, github_service):
        """Should follow 302 redirects when downloading artifacts from Azure Blob Storage."""
        run_id = 12345
        expected_data = {"analysis": "complete"}

        # Mock listing artifacts
        mock_artifacts_response = MagicMock()
        mock_artifacts_response.status_code = 200
        mock_artifacts_response.json.return_value = {
            "artifacts": [
                {
                    "id": 5050220102,
                    "name": "analysis-result",
                    "archive_download_url": "https://api.github.com/repos/owner/repo/actions/artifacts/5050220102/zip",
                }
            ]
        }
        mock_artifacts_response.raise_for_status = MagicMock()

        # Mock downloading artifact - should follow 302 redirect to Azure Blob Storage
        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = _create_mock_zip_with_json(expected_data)
        mock_download_response.raise_for_status = MagicMock()

        with patch.object(
            github_service, "_client", new_callable=AsyncMock
        ) as mock_client:
            mock_client.get.side_effect = [
                mock_artifacts_response,
                mock_download_response,
            ]

            result = await github_service.download_workflow_artifact(run_id)

            assert result == expected_data

            # Verify that the download was called with follow_redirects=True
            artifact_download_call = mock_client.get.call_args_list[1]
            assert artifact_download_call.kwargs.get("follow_redirects") is True


def _create_mock_zip_with_json(data: dict) -> bytes:
    """Create a mock ZIP file containing JSON data.

    GitHub Actions artifacts are downloaded as ZIP files.
    """
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("analysis.json", json.dumps(data))
    return buffer.getvalue()
