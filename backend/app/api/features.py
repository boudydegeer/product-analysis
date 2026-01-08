"""Feature API endpoints.

Provides CRUD operations for features and analysis workflow triggering.
"""

from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Feature, FeatureStatus, Analysis
from app.schemas import FeatureCreate, FeatureUpdate, FeatureResponse
from app.schemas.analysis import AnalysisDetailResponse, AnalysisErrorResponse
from app.services.github_service import GitHubService
from app.utils.webhook_security import generate_webhook_secret

router = APIRouter(prefix="/api/v1/features", tags=["features"])


def get_github_service() -> GitHubService:
    """Dependency for GitHub service."""
    return GitHubService(
        token=settings.github_token,
        repo=settings.github_repo,
    )


@router.post("", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    feature_in: FeatureCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new feature request.

    Args:
        feature_in: Feature creation data
        db: Database session

    Returns:
        The created feature
    """
    feature = Feature(
        id=str(uuid4()),
        name=feature_in.name,
        description=feature_in.description or "",
        priority=feature_in.priority,
        status=FeatureStatus.PENDING,
        webhook_secret=generate_webhook_secret(),  # Generate unique webhook secret
    )

    db.add(feature)
    await db.commit()
    await db.refresh(feature)

    return feature


@router.get("", response_model=List[FeatureResponse])
@router.get("/", response_model=List[FeatureResponse])
async def list_features(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all features with optional pagination.

    Args:
        skip: Number of features to skip
        limit: Maximum number of features to return
        db: Database session

    Returns:
        List of features
    """
    result = await db.execute(
        select(Feature).offset(skip).limit(limit).order_by(Feature.created_at.desc())
    )
    features = result.scalars().all()
    return features


@router.get("/{feature_id}", response_model=FeatureResponse)
async def get_feature(
    feature_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific feature by ID.

    Args:
        feature_id: UUID of the feature
        db: Database session

    Returns:
        The feature

    Raises:
        HTTPException: If feature not found
    """
    result = await db.execute(select(Feature).where(Feature.id == str(feature_id)))
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found",
        )

    return feature


@router.put("/{feature_id}", response_model=FeatureResponse)
async def update_feature(
    feature_id: UUID,
    feature_in: FeatureUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a feature.

    Args:
        feature_id: UUID of the feature
        feature_in: Feature update data
        db: Database session

    Returns:
        The updated feature

    Raises:
        HTTPException: If feature not found
    """
    result = await db.execute(select(Feature).where(Feature.id == str(feature_id)))
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found",
        )

    # Update only provided fields
    update_data = feature_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feature, field, value)

    await db.commit()
    await db.refresh(feature)

    return feature


@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(
    feature_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a feature.

    Args:
        feature_id: UUID of the feature
        db: Database session

    Raises:
        HTTPException: If feature not found
    """
    result = await db.execute(select(Feature).where(Feature.id == str(feature_id)))
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found",
        )

    await db.delete(feature)
    await db.commit()


@router.post("/{feature_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def trigger_analysis(
    feature_id: UUID,
    db: AsyncSession = Depends(get_db),
    github_service: GitHubService = Depends(get_github_service),
):
    """Trigger GitHub Actions workflow to analyze a feature.

    Args:
        feature_id: UUID of the feature to analyze
        db: Database session
        github_service: GitHub service for API calls

    Returns:
        Dict with workflow run_id and feature_id

    Raises:
        HTTPException: If feature not found or GitHub API fails
    """
    result = await db.execute(select(Feature).where(Feature.id == str(feature_id)))
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found",
        )

    try:
        # Construct callback URL if webhook_base_url is configured
        callback_url = None
        if settings.webhook_base_url:
            callback_url = f"{settings.webhook_base_url}/api/v1/webhooks/analysis-result"

        # Trigger the analysis workflow with callback URL
        run_id = await github_service.trigger_analysis_workflow(
            feature_id=feature_id,
            feature_description=feature.description,
            callback_url=callback_url,
        )

        # Update feature status and store workflow run ID
        feature.status = FeatureStatus.ANALYZING
        feature.analysis_workflow_run_id = str(run_id)

        await db.commit()
        await db.refresh(feature)

        return {
            "run_id": run_id,
            "feature_id": str(feature_id),
            "status": "analyzing",
            "callback_url": callback_url,  # Include in response for debugging
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger analysis workflow: {str(e)}",
        )


@router.get("/{feature_id}/analysis", response_model=AnalysisDetailResponse | AnalysisErrorResponse)
async def get_feature_analysis(
    feature_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get analysis details for a feature.

    Args:
        feature_id: UUID of the feature
        db: Database session

    Returns:
        Complete analysis with overview, implementation, risks, and recommendations

    Raises:
        HTTPException: If feature not found
    """
    # Get feature
    result = await db.execute(select(Feature).where(Feature.id == str(feature_id)))
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found",
        )

    # Get most recent analysis
    result = await db.execute(
        select(Analysis)
        .where(Analysis.feature_id == str(feature_id))
        .order_by(Analysis.created_at.desc())
        .limit(1)
    )
    analysis = result.scalar_one_or_none()

    # Handle no analysis case
    if not analysis:
        return AnalysisErrorResponse(
            feature_id=str(feature_id),
            status="no_analysis",
            message="No analysis available for this feature",
        )

    # Handle analyzing state
    if feature.status == FeatureStatus.ANALYZING:
        return AnalysisErrorResponse(
            feature_id=str(feature_id),
            status="analyzing",
            message="Analysis in progress...",
            started_at=feature.updated_at.isoformat() if feature.updated_at else None,
        )

    # Handle failed state
    if feature.status == FeatureStatus.FAILED:
        return AnalysisErrorResponse(
            feature_id=str(feature_id),
            status="failed",
            message="Analysis failed",
            failed_at=analysis.completed_at.isoformat() if analysis.completed_at else None,
        )

    # Return successful analysis
    return AnalysisDetailResponse(
        feature_id=str(feature_id),
        feature_name=feature.name,
        analyzed_at=analysis.completed_at.isoformat() if analysis.completed_at else None,
        status="completed",
        overview={
            "summary": analysis.summary_overview or "",
            "key_points": analysis.summary_key_points or [],
            "metrics": analysis.summary_metrics or {},
        },
        implementation={
            "architecture": analysis.implementation_architecture or {},
            "technical_details": analysis.implementation_technical_details or [],
            "data_flow": analysis.implementation_data_flow or {},
        },
        risks={
            "technical_risks": analysis.risks_technical_risks or [],
            "security_concerns": analysis.risks_security_concerns or [],
            "scalability_issues": analysis.risks_scalability_issues or [],
            "mitigation_strategies": analysis.risks_mitigation_strategies or [],
        },
        recommendations={
            "improvements": analysis.recommendations_improvements or [],
            "best_practices": analysis.recommendations_best_practices or [],
            "next_steps": analysis.recommendations_next_steps or [],
        },
    )
