"""Ideas API endpoints."""
import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.idea import Idea, IdeaStatus, IdeaPriority
from app.schemas.idea import IdeaCreate, IdeaUpdate, IdeaResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ideas", tags=["ideas"])


@router.post("", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
async def create_idea(
    idea_in: IdeaCreate,
    db: AsyncSession = Depends(get_db),
) -> Idea:
    """Create a new idea.

    Args:
        idea_in: Idea data
        db: Database session

    Returns:
        Created idea
    """
    idea = Idea(
        id=str(uuid4()),
        title=idea_in.title,
        description=idea_in.description,
        status=IdeaStatus.BACKLOG,
        priority=IdeaPriority(idea_in.priority) if idea_in.priority else IdeaPriority.MEDIUM,
    )

    db.add(idea)
    await db.commit()
    await db.refresh(idea)

    logger.info(f"Created idea: {idea.id}")
    return idea


@router.get("", response_model=list[IdeaResponse])
@router.get("/", response_model=list[IdeaResponse])
async def list_ideas(
    skip: int = 0,
    limit: int = 100,
    status: str | None = Query(None, pattern="^(backlog|under_review|approved|rejected|implemented)$"),
    priority: str | None = Query(None, pattern="^(low|medium|high|critical)$"),
    db: AsyncSession = Depends(get_db),
) -> list[Idea]:
    """List all ideas with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status
        priority: Filter by priority
        db: Database session

    Returns:
        List of ideas
    """
    query = select(Idea).offset(skip).limit(limit).order_by(Idea.created_at.desc())

    # Apply filters
    if status:
        query = query.where(Idea.status == IdeaStatus(status))
    if priority:
        query = query.where(Idea.priority == IdeaPriority(priority))

    result = await db.execute(query)
    ideas = result.scalars().all()
    return list(ideas)


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
) -> Idea:
    """Get a specific idea.

    Args:
        idea_id: Idea ID
        db: Database session

    Returns:
        Idea

    Raises:
        HTTPException: If idea not found
    """
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Idea {idea_id} not found",
        )

    return idea


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: str,
    idea_update: IdeaUpdate,
    db: AsyncSession = Depends(get_db),
) -> Idea:
    """Update an idea.

    Args:
        idea_id: Idea ID
        idea_update: Update data
        db: Database session

    Returns:
        Updated idea

    Raises:
        HTTPException: If idea not found
    """
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Idea {idea_id} not found",
        )

    # Update fields
    update_data = idea_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status":
            value = IdeaStatus(value)
        elif field == "priority":
            value = IdeaPriority(value)
        setattr(idea, field, value)

    await db.commit()
    await db.refresh(idea)

    logger.info(f"Updated idea: {idea_id}")
    return idea


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an idea.

    Args:
        idea_id: Idea ID
        db: Database session

    Raises:
        HTTPException: If idea not found
    """
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Idea {idea_id} not found",
        )

    await db.delete(idea)
    await db.commit()

    logger.info(f"Deleted idea: {idea_id}")
