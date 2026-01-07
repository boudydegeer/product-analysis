"""Polling service for checking GitHub workflow status and downloading results.

This service acts as a fallback mechanism when webhooks are not available
or fail to deliver. It periodically checks workflows in ANALYZING status
and downloads results when complete.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Feature, FeatureStatus, Analysis
from app.services.github_service import GitHubService, GitHubServiceError

logger = logging.getLogger(__name__)


class AnalysisPollingService:
    """Service for polling GitHub workflow status and downloading results."""

    def __init__(self, db: AsyncSession):
        """Initialize polling service.

        Args:
            db: Database session
        """
        self.db = db
        self.timeout_seconds = settings.analysis_polling_timeout_seconds

    async def get_features_needing_polling(self) -> List[Feature]:
        """Get features that need status polling.

        Returns features that are:
        - In ANALYZING status
        - Have not received webhook recently (last 5 minutes)
        - Have not exceeded timeout threshold
        - Have workflow_run_id set

        Returns:
            List of features needing polling
        """
        logger.debug("Querying database for features needing polling")

        cutoff_time = datetime.now(UTC) - timedelta(seconds=self.timeout_seconds)
        webhook_grace_period = datetime.now(UTC) - timedelta(minutes=5)

        query = (
            select(Feature)
            .where(Feature.status == FeatureStatus.ANALYZING)
            .where(Feature.analysis_workflow_run_id.isnot(None))
            .where(Feature.created_at > cutoff_time)  # Not timed out
            .where(
                # Either never received webhook or received long ago
                (Feature.webhook_received_at.is_(None))
                | (Feature.webhook_received_at < webhook_grace_period)
            )
        )

        result = await self.db.execute(query)
        features = result.scalars().all()

        logger.debug(f"Found {len(features)} features needing polling")
        return list(features)

    async def poll_workflow_status(self, feature: Feature) -> None:
        """Poll status for a single feature's workflow.

        Args:
            feature: Feature to poll
        """
        if not feature.analysis_workflow_run_id:
            logger.warning(f"Feature {feature.id} has no workflow_run_id, skipping")
            return

        run_id = int(feature.analysis_workflow_run_id)
        logger.info(f"Polling feature {feature.id}: checking workflow {run_id}")

        try:
            github_service = GitHubService(
                token=settings.github_token,
                repo=settings.github_repo,
            )

            # Update last polled timestamp
            feature.last_polled_at = datetime.now(UTC)

            # Check workflow status
            status = await github_service.get_workflow_run_status(run_id)

            logger.info(f"Polling feature {feature.id}: workflow status is {status}")

            if status == "completed":
                # Download and process results
                logger.info(f"Polling feature {feature.id}: downloading results and updating status")
                await self._process_completed_workflow(feature, run_id, github_service)

            elif status in ["failure", "cancelled", "timed_out"]:
                # Mark feature as failed
                logger.warning(f"Polling feature {feature.id}: workflow {status}, marking as FAILED")
                feature.status = FeatureStatus.FAILED

                # Create error analysis record
                analysis = Analysis(
                    feature_id=feature.id,
                    result={
                        "error": f"Workflow {status}",
                        "workflow_run_id": run_id,
                    },
                    tokens_used=0,
                    model_used="unknown",
                    completed_at=datetime.now(UTC),
                )
                self.db.add(analysis)

            elif status in ["queued", "in_progress"]:
                # Still running, will check again next polling cycle
                logger.debug(f"Polling feature {feature.id}: workflow still {status}, will check again later")

            await self.db.commit()
            await github_service.close()

        except GitHubServiceError as e:
            logger.error(f"Polling feature {feature.id}: GitHub API error - {e}")
            # Don't update feature status on transient errors

        except Exception as e:
            logger.error(f"Polling feature {feature.id}: unexpected error - {e}", exc_info=True)

    async def _process_completed_workflow(
        self, feature: Feature, run_id: int, github_service: GitHubService
    ) -> None:
        """Process completed workflow by downloading artifact and storing results.

        Args:
            feature: Feature being analyzed
            run_id: Workflow run ID
            github_service: GitHub service instance
        """
        try:
            # Download artifact with feature-specific name
            artifact_name = f"feature-analysis-{feature.id}"
            logger.debug(f"Polling feature {feature.id}: downloading artifact '{artifact_name}'")

            result_data = await github_service.download_workflow_artifact(
                run_id, artifact_name=artifact_name
            )

            logger.debug(f"Polling feature {feature.id}: artifact downloaded successfully")

            # Check if analysis had errors
            has_error = "error" in result_data

            # Update feature status
            new_status = FeatureStatus.FAILED if has_error else FeatureStatus.COMPLETED
            feature.status = new_status

            logger.info(
                f"Polling feature {feature.id}: updated status to {new_status.value}"
            )

            # Create analysis record
            analysis = Analysis(
                feature_id=feature.id,
                result=result_data,
                tokens_used=0,  # TODO: Extract from metadata if available
                model_used=result_data.get("metadata", {}).get(
                    "model", "claude-3-5-sonnet-20241022"
                ),
                completed_at=datetime.now(UTC),
            )

            self.db.add(analysis)

            logger.info(
                f"Polling feature {feature.id}: successfully processed completed workflow"
            )

        except GitHubServiceError as e:
            logger.error(
                f"Polling feature {feature.id}: failed to download artifact - {e}"
            )
            feature.status = FeatureStatus.FAILED

            # Create error analysis record
            analysis = Analysis(
                feature_id=feature.id,
                result={
                    "error": f"Failed to download results: {str(e)}",
                    "workflow_run_id": run_id,
                },
                tokens_used=0,
                model_used="unknown",
                completed_at=datetime.now(UTC),
            )
            self.db.add(analysis)

    async def poll_all_analyzing_features(self) -> int:
        """Poll status for all features needing polling.

        Returns:
            Number of features polled
        """
        logger.info("Polling service: Starting to check for features needing updates")

        features = await self.get_features_needing_polling()

        if len(features) == 0:
            logger.info("Polling service: No features needing updates")
        else:
            logger.info(f"Polling service: Found {len(features)} features needing updates")

        for feature in features:
            try:
                await self.poll_workflow_status(feature)
            except Exception as e:
                logger.error(f"Polling service: Error polling feature {feature.id} - {e}", exc_info=True)
                # Continue with other features

        return len(features)
