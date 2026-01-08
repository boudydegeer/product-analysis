"""GitHub service for interacting with GitHub Actions API.

This service handles:
- Triggering analysis workflows via GitHub Actions
- Checking workflow run status
- Downloading workflow artifacts with analysis results
"""
import io
import json
import logging
import zipfile
from typing import Any
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class GitHubServiceError(Exception):
    """Exception raised for GitHub service errors."""

    pass


class GitHubService:
    """Service for interacting with GitHub Actions API.

    Uses httpx.AsyncClient for async HTTP calls to the GitHub API.
    Provides methods to trigger workflows, check status, and download artifacts.
    """

    API_BASE_URL = "https://api.github.com"
    WORKFLOW_FILE = "analyze-feature.yml"
    DEFAULT_ARTIFACT_NAME = "analysis-result"

    def __init__(self, token: str, repo: str) -> None:
        """Initialize GitHubService.

        Args:
            token: GitHub personal access token with repo and workflow permissions.
            repo: Repository in format "owner/repo".
        """
        self.token = token
        self.repo = repo
        self.api_base_url = self.API_BASE_URL

        # Parse owner and repo name
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}. Expected 'owner/repo'.")
        self.owner = parts[0]
        self.repo_name = parts[1]

        # Create HTTP client with auth headers
        self._client = httpx.AsyncClient(
            base_url=self.API_BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "GitHubService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def trigger_analysis_workflow(
        self,
        feature_id: UUID,
        feature_description: str,
        callback_url: str | None = None,
        ref: str = "main",
    ) -> int:
        """Trigger the feature analysis workflow.

        Args:
            feature_id: UUID of the feature to analyze.
            feature_description: Description of the feature to analyze.
            callback_url: Optional URL to POST results to.
            ref: Git ref (branch/tag) to run the workflow on.

        Returns:
            The workflow run ID.

        Raises:
            GitHubServiceError: If workflow trigger fails.
        """
        url = f"/repos/{self.owner}/{self.repo_name}/actions/workflows/{self.WORKFLOW_FILE}/dispatches"

        inputs = {
            "feature_id": str(feature_id),
            "feature_description": feature_description,
        }

        # Only include callback_url if provided
        if callback_url:
            inputs["callback_url"] = callback_url

        payload = {
            "ref": ref,
            "inputs": inputs,
        }

        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to trigger workflow: {e}")
            raise GitHubServiceError(
                f"Failed to trigger workflow for feature {feature_id}: {e}"
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error triggering workflow: {e}")
            raise GitHubServiceError(f"Request error triggering workflow: {e}") from e

        # GitHub dispatch returns 204 No Content on success
        # We need to get the run_id by listing recent workflow runs
        run_id = await self._get_latest_workflow_run_id()
        logger.info(
            f"Triggered analysis workflow for feature {feature_id}, run_id={run_id}"
        )
        return run_id

    async def _get_latest_workflow_run_id(self) -> int:
        """Get the ID of the most recent workflow run.

        Returns:
            The workflow run ID.

        Raises:
            GitHubServiceError: If no workflow runs found.
        """
        url = f"/repos/{self.owner}/{self.repo_name}/actions/workflows/{self.WORKFLOW_FILE}/runs"
        params = {
            "per_page": 1,
        }

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("workflow_runs"):
                raise GitHubServiceError("No workflow runs found")

            return int(data["workflow_runs"][0]["id"])

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get workflow runs: {e}")
            raise GitHubServiceError(f"Failed to get workflow runs: {e}") from e

    async def get_workflow_run_status(self, run_id: int) -> str:
        """Get the status of a workflow run.

        Args:
            run_id: The workflow run ID.

        Returns:
            The workflow status: "queued", "in_progress", "completed", or "failure".

        Raises:
            GitHubServiceError: If workflow run not found or API error.
        """
        url = f"/repos/{self.owner}/{self.repo_name}/actions/runs/{run_id}"

        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()

            status = str(data.get("status", "unknown"))
            conclusion = data.get("conclusion")

            # If completed, return the conclusion (success/failure)
            if status == "completed":
                if conclusion == "success":
                    return "completed"
                return str(conclusion) if conclusion else "failure"

            return status

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise GitHubServiceError(f"Workflow run {run_id} not found") from e
            logger.error(f"Failed to get workflow run status: {e}")
            raise GitHubServiceError(
                f"Failed to get workflow run {run_id} status: {e}"
            ) from e

    async def download_workflow_artifact(
        self,
        run_id: int,
        artifact_name: str | None = None,
    ) -> dict[str, Any]:
        """Download and parse workflow artifact.

        Args:
            run_id: The workflow run ID.
            artifact_name: Optional specific artifact name. Defaults to "analysis-result".

        Returns:
            Parsed JSON data from the artifact.

        Raises:
            GitHubServiceError: If artifact not found or parsing fails.
        """
        artifact_name = artifact_name or self.DEFAULT_ARTIFACT_NAME

        # List artifacts for the run
        url = f"/repos/{self.owner}/{self.repo_name}/actions/runs/{run_id}/artifacts"

        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()

            artifacts = data.get("artifacts", [])
            if not artifacts:
                raise GitHubServiceError(f"No artifacts found for run {run_id}")

            # Find the target artifact
            target_artifact = None
            for artifact in artifacts:
                if artifact["name"] == artifact_name:
                    target_artifact = artifact
                    break

            if not target_artifact:
                # Use first artifact if specific name not found
                target_artifact = artifacts[0]
                logger.warning(
                    f"Artifact '{artifact_name}' not found, using '{target_artifact['name']}'"
                )

            # Download the artifact
            artifact_id = target_artifact["id"]
            download_url = f"/repos/{self.owner}/{self.repo_name}/actions/artifacts/{artifact_id}/zip"

            download_response = await self._client.get(
                download_url, follow_redirects=True
            )
            download_response.raise_for_status()

            # Parse ZIP and extract JSON
            return self._parse_artifact_zip(download_response.content)

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to download artifact: {e}")
            raise GitHubServiceError(
                f"Failed to download artifact for run {run_id}: {e}"
            ) from e

    def _parse_artifact_zip(self, content: bytes) -> dict[str, Any]:
        """Parse ZIP artifact content and extract JSON data.

        Args:
            content: ZIP file content as bytes.

        Returns:
            Parsed JSON data.

        Raises:
            GitHubServiceError: If ZIP parsing or JSON parsing fails.
        """
        try:
            buffer = io.BytesIO(content)
            with zipfile.ZipFile(buffer, "r") as zf:
                # Find JSON file in the ZIP
                json_files = [f for f in zf.namelist() if f.endswith(".json")]
                if not json_files:
                    raise GitHubServiceError("No JSON file found in artifact")

                # Read and parse the first JSON file
                json_content = zf.read(json_files[0])
                result: dict[str, Any] = json.loads(json_content)
                return result

        except zipfile.BadZipFile as e:
            raise GitHubServiceError(f"Invalid ZIP file in artifact: {e}") from e
        except json.JSONDecodeError as e:
            raise GitHubServiceError(f"Invalid JSON in artifact: {e}") from e
