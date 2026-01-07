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
from app.models import Feature, FeatureStatus
from app.schemas import FeatureCreate, FeatureUpdate, FeatureResponse
from app.services.github_service import GitHubService

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
        # Construct callback URL (optional - can be None)
        callback_url = None  # TODO: Set this if you want to receive results via callback

        # Trigger the analysis workflow with required parameters
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
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger analysis workflow: {str(e)}",
        )
