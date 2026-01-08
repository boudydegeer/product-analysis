"""Webhook endpoints for receiving analysis results from GitHub workflows."""

from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.feature import Feature, FeatureStatus
from app.models.analysis import Analysis
from app.schemas.webhook import AnalysisResultWebhook
from app.utils.webhook_security import verify_webhook_signature
from app.utils.analysis_mapper import extract_flattened_fields

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/analysis-result")
async def receive_analysis_result(
    request: Request,
    webhook_data: AnalysisResultWebhook,
    x_webhook_signature: str = Header(..., alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """Receive analysis results from GitHub workflow via webhook.

    This endpoint:
    1. Validates the webhook signature to ensure authenticity
    2. Looks up the feature by feature_id
    3. Creates an Analysis record with the results
    4. Updates the feature status to COMPLETED or FAILED
    5. Records the webhook_received_at timestamp

    Args:
        request: FastAPI request object (to access raw body)
        webhook_data: Validated webhook payload
        x_webhook_signature: HMAC signature in X-Webhook-Signature header
        db: Database session

    Returns:
        Success message with feature_id

    Raises:
        HTTPException 401: Invalid signature
        HTTPException 404: Feature not found
    """
    # Get raw request body for signature verification
    body = await request.body()
    payload_str = body.decode("utf-8")

    # Look up the feature
    result = await db.execute(
        select(Feature).where(Feature.id == webhook_data.feature_id)
    )
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=404,
            detail=f"Feature {webhook_data.feature_id} not found",
        )

    # Verify webhook signature using feature's secret
    if not feature.webhook_secret:
        raise HTTPException(
            status_code=401,
            detail="Feature has no webhook secret configured",
        )

    is_valid = verify_webhook_signature(
        payload_str,
        x_webhook_signature,
        feature.webhook_secret,
    )

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    # Update feature status based on result
    if webhook_data.error:
        feature.status = FeatureStatus.FAILED
    else:
        feature.status = FeatureStatus.COMPLETED

    # Record when webhook was received
    feature.webhook_received_at = datetime.now(UTC)

    # Create Analysis record with the results
    # Store all webhook data as JSON in the result field
    result_data = {
        "complexity": webhook_data.complexity,
        "warnings": webhook_data.warnings,
        "repository_state": webhook_data.repository_state,
        "affected_modules": webhook_data.affected_modules,
        "implementation_tasks": webhook_data.implementation_tasks,
        "technical_risks": webhook_data.technical_risks,
        "recommendations": webhook_data.recommendations,
        "error": webhook_data.error,
        "raw_output": webhook_data.raw_output,
        "metadata": webhook_data.metadata,
    }

    # Extract flattened fields from result using shared mapper
    flattened_fields = extract_flattened_fields(result_data)

    # Create Analysis record with flattened fields
    analysis = Analysis(
        feature_id=feature.id,
        result=result_data,  # Keep full data for backward compatibility
        tokens_used=0,
        model_used="github-workflow",
        completed_at=datetime.now(UTC),
        # Flattened fields
        **flattened_fields,
    )

    db.add(analysis)
    await db.commit()
    await db.refresh(feature)

    return {
        "status": "success",
        "feature_id": webhook_data.feature_id,
        "message": "Analysis result received and stored",
    }
