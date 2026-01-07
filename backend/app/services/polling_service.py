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

        return list(features)

    async def poll_workflow_status(self, feature: Feature) -> None:
        """Poll status for a single feature's workflow.

        Args:
            feature: Feature to poll
        """
        if not feature.analysis_workflow_run_id:
            logger.warning(f"Feature {feature.id} has no workflow_run_id")
            return

        try:
            github_service = GitHubService(
                token=settings.github_token,
                repo=settings.github_repo,
            )

            # Update last polled timestamp
            feature.last_polled_at = datetime.now(UTC)

            # Check workflow status
            run_id = int(feature.analysis_workflow_run_id)
            status = await github_service.get_workflow_run_status(run_id)

            logger.info(
                f"Workflow {run_id} for feature {feature.id} status: {status}"
            )

            if status == "completed":
                # Download and process results
                await self._process_completed_workflow(feature, run_id, github_service)

            elif status in ["failure", "cancelled", "timed_out"]:
                # Mark feature as failed
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

            # If status is "queued" or "in_progress", do nothing (keep polling)

            await self.db.commit()
            await github_service.close()

        except GitHubServiceError as e:
            logger.error(f"GitHub API error polling feature {feature.id}: {e}")
            # Don't update feature status on transient errors

        except Exception as e:
            logger.error(f"Unexpected error polling feature {feature.id}: {e}")

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
            result_data = await github_service.download_workflow_artifact(
                run_id, artifact_name=artifact_name
            )

            # Check if analysis had errors
            has_error = "error" in result_data

            # Update feature status
            feature.status = FeatureStatus.FAILED if has_error else FeatureStatus.COMPLETED

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
                f"Successfully processed completed workflow for feature {feature.id}"
            )

        except GitHubServiceError as e:
            logger.error(
                f"Failed to download artifact for feature {feature.id}: {e}"
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
        features = await self.get_features_needing_polling()

        logger.info(f"Polling {len(features)} features")

        for feature in features:
            try:
                await self.poll_workflow_status(feature)
            except Exception as e:
                logger.error(f"Error polling feature {feature.id}: {e}")
                # Continue with other features

        return len(features)
