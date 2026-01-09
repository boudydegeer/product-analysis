"""Tools API endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tool import Tool
from app.schemas.tool import ToolCreate, ToolUpdate, ToolResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_in: ToolCreate,
    db: AsyncSession = Depends(get_db),
) -> Tool:
    """Create a new tool.

    Args:
        tool_in: Tool data
        db: Database session

    Returns:
        Created tool

    Raises:
        HTTPException: If tool with same name already exists
    """
    # Check for duplicate name
    result = await db.execute(select(Tool).where(Tool.name == tool_in.name))
    existing_tool = result.scalar_one_or_none()

    if existing_tool:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tool with name '{tool_in.name}' already exists",
        )

    # Create new tool
    tool = Tool(
        name=tool_in.name,
        description=tool_in.description,
        category=tool_in.category,
        tool_type=tool_in.tool_type,
        definition=tool_in.definition,
        enabled=tool_in.enabled,
        is_dangerous=tool_in.is_dangerous,
        requires_approval=tool_in.requires_approval,
        version=tool_in.version,
        tags=tool_in.tags,
        example_usage=tool_in.example_usage,
        created_by=tool_in.created_by,
    )

    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    logger.info(f"Created tool: {tool.id} ({tool.name})")
    return tool


@router.get("", response_model=list[ToolResponse])
@router.get("/", response_model=list[ToolResponse])
async def list_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: str | None = None,
    tool_type: str | None = Query(None, pattern="^(builtin|custom|mcp)$"),
    enabled_only: bool = Query(True, description="Filter to show only enabled tools"),
    db: AsyncSession = Depends(get_db),
) -> list[Tool]:
    """List all tools with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        category: Filter by category
        tool_type: Filter by tool type
        enabled_only: If True, only return enabled tools
        db: Database session

    Returns:
        List of tools
    """
    query = select(Tool).offset(skip).limit(limit).order_by(Tool.created_at.desc())

    # Apply filters
    if category:
        query = query.where(Tool.category == category)
    if tool_type:
        query = query.where(Tool.tool_type == tool_type)
    if enabled_only:
        query = query.where(Tool.enabled == True)  # noqa: E712

    result = await db.execute(query)
    tools = result.scalars().all()
    return list(tools)


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
) -> Tool:
    """Get a specific tool by ID.

    Args:
        tool_id: Tool ID
        db: Database session

    Returns:
        Tool

    Raises:
        HTTPException: If tool not found
    """
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found",
        )

    return tool


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    tool_update: ToolUpdate,
    db: AsyncSession = Depends(get_db),
) -> Tool:
    """Update a tool.

    Args:
        tool_id: Tool ID
        tool_update: Update data
        db: Database session

    Returns:
        Updated tool

    Raises:
        HTTPException: If tool not found or duplicate name conflict
    """
    # Get existing tool
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found",
        )

    # Check for duplicate name if name is being updated
    update_data = tool_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != tool.name:
        result = await db.execute(
            select(Tool).where(Tool.name == update_data["name"])
        )
        existing_tool = result.scalar_one_or_none()
        if existing_tool:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tool with name '{update_data['name']}' already exists",
            )

    # Update fields
    for field, value in update_data.items():
        setattr(tool, field, value)

    await db.commit()
    await db.refresh(tool)

    logger.info(f"Updated tool: {tool_id}")
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a tool.

    Args:
        tool_id: Tool ID
        db: Database session

    Raises:
        HTTPException: If tool not found
    """
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found",
        )

    await db.delete(tool)
    await db.commit()

    logger.info(f"Deleted tool: {tool_id}")
