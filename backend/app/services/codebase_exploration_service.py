"""Codebase Exploration Service.

Service for triggering and managing codebase exploration workflows via GitHub Actions.
Used by the brainstorming agent to explore the target codebase and gather context.
"""
import logging
import uuid
from typing import Any

from app.config import settings
from app.services.github_service import GitHubService, GitHubServiceError

logger = logging.getLogger(__name__)


class CodebaseExplorationServiceError(Exception):
    """Exception raised for codebase exploration service errors."""

    pass


class CodebaseExplorationService:
    """Service for managing codebase exploration via GitHub Actions.

    Provides methods to:
    - Generate unique exploration IDs
    - Trigger exploration workflows
    - Fetch and format exploration results
    """

    WORKFLOW_FILE = "explore-codebase.yml"
    ARTIFACT_NAME = "exploration-result"

    def __init__(self) -> None:
        """Initialize CodebaseExplorationService."""
        pass

    def generate_exploration_id(self) -> str:
        """Generate a unique exploration ID.

        Returns:
            A unique ID in format "exp-{uuid4_short}" (8 hex chars).
        """
        short_uuid = uuid.uuid4().hex[:8]
        return f"exp-{short_uuid}"

    async def trigger_exploration(
        self,
        db: Any,
        exploration_id: str,
        query: str,
        scope: str | None,
        focus: str | None,
        session_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Trigger a codebase exploration workflow.

        Args:
            db: Database session (for future use with exploration tracking).
            exploration_id: Unique ID for this exploration.
            query: The exploration query/question.
            scope: Optional scope filter (e.g., "backend", "frontend").
            focus: Optional focus area (e.g., "security", "performance").
            session_id: ID of the brainstorming session.
            message_id: ID of the message that triggered exploration.

        Returns:
            Dict containing workflow_run_id and workflow_url.

        Raises:
            CodebaseExplorationServiceError: If workflow trigger fails.
        """
        try:
            github_service = GitHubService(
                token=settings.github_token,
                repo=settings.github_repo,
            )

            # Build workflow inputs
            inputs = {
                "exploration_id": exploration_id,
                "query": query,
                "session_id": session_id,
                "message_id": message_id,
            }

            if scope:
                inputs["scope"] = scope
            if focus:
                inputs["focus"] = focus

            # Trigger the exploration workflow
            workflow_run_id = await github_service.trigger_workflow(
                workflow_file=self.WORKFLOW_FILE,
                inputs=inputs,
            )

            workflow_url = github_service.get_workflow_url(workflow_run_id)

            logger.info(
                f"Triggered exploration workflow: exploration_id={exploration_id}, "
                f"run_id={workflow_run_id}"
            )

            return {
                "workflow_run_id": workflow_run_id,
                "workflow_url": workflow_url,
            }

        except GitHubServiceError as e:
            logger.error(f"Failed to trigger exploration workflow: {e}")
            raise CodebaseExplorationServiceError(
                f"Failed to trigger exploration: {e}"
            ) from e

    async def get_exploration_results(
        self,
        db: Any,
        exploration_id: str,
        workflow_run_id: int,
    ) -> dict[str, Any] | None:
        """Fetch exploration results from completed workflow.

        Args:
            db: Database session (for future use).
            exploration_id: The exploration ID to fetch results for.
            workflow_run_id: The GitHub workflow run ID.

        Returns:
            Dict containing exploration results, or None if not available.
        """
        try:
            github_service = GitHubService(
                token=settings.github_token,
                repo=settings.github_repo,
            )

            results = await github_service.download_workflow_artifact(
                run_id=workflow_run_id,
                artifact_name=self.ARTIFACT_NAME,
            )

            logger.info(
                f"Retrieved exploration results: exploration_id={exploration_id}"
            )

            return results

        except GitHubServiceError as e:
            logger.warning(
                f"Failed to get exploration results for {exploration_id}: {e}"
            )
            return None
        except Exception as e:
            logger.warning(
                f"Unexpected error getting exploration results for {exploration_id}: {e}"
            )
            return None

    def format_results_for_agent(self, results: dict[str, Any] | None) -> str:
        """Format exploration results as readable markdown for agent injection.

        Args:
            results: The exploration results dict, or None.

        Returns:
            Formatted markdown string suitable for agent conversation.
        """
        if not results:
            return "## Codebase Exploration Results\n\nNo results available or exploration returned empty results."

        sections = []

        # Header
        exploration_id = results.get("exploration_id", "unknown")
        sections.append(f"## Codebase Exploration Results\n\n**Exploration ID:** {exploration_id}")

        # Summary
        summary = results.get("summary", "")
        if summary:
            sections.append(f"### Summary\n\n{summary}")

        # Files Found
        files_found = results.get("files_found", [])
        if files_found:
            files_list = "\n".join([f"- `{f}`" for f in files_found])
            sections.append(f"### Files Found ({len(files_found)})\n\n{files_list}")
        else:
            sections.append("### Files Found\n\nNo relevant files found.")

        # Patterns
        patterns = results.get("patterns", [])
        if patterns:
            patterns_list = "\n".join([f"- {p}" for p in patterns])
            sections.append(f"### Patterns Identified\n\n{patterns_list}")

        # Code Examples
        code_examples = results.get("code_examples", [])
        if code_examples:
            examples_content = []
            for example in code_examples:
                file_name = example.get("file", "unknown")
                snippet = example.get("snippet", "")
                description = example.get("description", "")

                example_text = f"**{file_name}**"
                if description:
                    example_text += f"\n\n{description}"
                if snippet:
                    example_text += f"\n\n```python\n{snippet}\n```"

                examples_content.append(example_text)

            sections.append("### Code Examples\n\n" + "\n\n---\n\n".join(examples_content))

        # Recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            rec_list = "\n".join([f"- {r}" for r in recommendations])
            sections.append(f"### Recommendations\n\n{rec_list}")

        return "\n\n".join(sections)
