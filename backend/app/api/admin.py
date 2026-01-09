"""Admin API endpoints for managing agents and tools."""
import logging
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import AgentType, AgentToolConfig
from app.models.tool import Tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ===== Pydantic Schemas =====


class AgentTypeCreate(BaseModel):
    """Schema for creating an agent type."""

    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    avatar_url: str | None = None
    avatar_color: str = "#6366f1"
    personality_traits: list[str] = Field(default_factory=list)
    model: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1)
    streaming_enabled: bool = True
    max_context_tokens: int = 200000
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    enabled: bool = True
    is_default: bool = False
    version: str = "1.0.0"


class AgentTypeUpdate(BaseModel):
    """Schema for updating an agent type."""

    display_name: str | None = None
    description: str | None = None
    avatar_url: str | None = None
    avatar_color: str | None = None
    personality_traits: list[str] | None = None
    model: str | None = None
    system_prompt: str | None = None
    streaming_enabled: bool | None = None
    max_context_tokens: int | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    enabled: bool | None = None
    is_default: bool | None = None
    version: str | None = None


class AgentTypeResponse(BaseModel):
    """Schema for agent type response."""

    id: int
    name: str
    display_name: str
    description: str | None
    avatar_url: str | None
    avatar_color: str
    personality_traits: list[str]
    model: str
    system_prompt: str
    streaming_enabled: bool
    max_context_tokens: int
    temperature: float
    enabled: bool
    is_default: bool
    version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolCreate(BaseModel):
    """Schema for creating a tool."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    tool_type: str = Field(..., pattern="^(builtin|custom|mcp)$")
    definition: dict[str, Any]
    enabled: bool = True
    is_dangerous: bool = False
    requires_approval: bool = False
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)
    example_usage: str | None = None
    created_by: str | None = None


class ToolUpdate(BaseModel):
    """Schema for updating a tool."""

    description: str | None = None
    category: str | None = None
    tool_type: str | None = Field(default=None, pattern="^(builtin|custom|mcp)$")
    definition: dict[str, Any] | None = None
    enabled: bool | None = None
    is_dangerous: bool | None = None
    requires_approval: bool | None = None
    version: str | None = None
    tags: list[str] | None = None
    example_usage: str | None = None


class ToolResponse(BaseModel):
    """Schema for tool response."""

    id: int
    name: str
    description: str
    category: str
    tool_type: str
    definition: dict[str, Any]
    enabled: bool
    is_dangerous: bool
    requires_approval: bool
    version: str
    tags: list[str]
    example_usage: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None

    class Config:
        from_attributes = True


class AgentToolAssignment(BaseModel):
    """Schema for assigning a tool to an agent."""

    tool_id: int
    enabled_for_agent: bool = True
    order_index: int | None = None
    allow_use: bool = True
    requires_approval: bool = False
    usage_limit: int | None = None
    allowed_parameters: dict[str, Any] | None = None
    denied_parameters: dict[str, Any] | None = None
    parameter_defaults: dict[str, Any] | None = None


class AgentToolConfigResponse(BaseModel):
    """Schema for agent tool config response."""

    id: int
    agent_type_id: int
    tool_id: int
    enabled_for_agent: bool
    order_index: int | None
    allow_use: bool
    requires_approval: bool
    usage_limit: int | None
    allowed_parameters: dict[str, Any] | None
    denied_parameters: dict[str, Any] | None
    parameter_defaults: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Agent Type Endpoints =====


@router.post("/agents", response_model=AgentTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentTypeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent type.

    Args:
        data: Agent type data
        db: Database session

    Returns:
        Created agent type

    Raises:
        HTTPException: If agent name already exists
    """
    # Check if name already exists
    result = await db.execute(select(AgentType).where(AgentType.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent with name '{data.name}' already exists",
        )

    # Create agent
    agent = AgentType(**data.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    logger.info(f"Created agent type: {agent.name} (ID: {agent.id})")
    return agent


@router.get("/agents", response_model=list[AgentTypeResponse])
async def list_all_agents(
    db: AsyncSession = Depends(get_db),
):
    """List all agent types (including disabled).

    Args:
        db: Database session

    Returns:
        List of all agent types
    """
    result = await db.execute(select(AgentType).order_by(AgentType.name))
    agents = result.scalars().all()
    return agents


@router.get("/agents/{agent_id}", response_model=AgentTypeResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an agent type by ID.

    Args:
        agent_id: Agent type ID
        db: Database session

    Returns:
        Agent type

    Raises:
        HTTPException: If agent not found
    """
    result = await db.execute(select(AgentType).where(AgentType.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    return agent


@router.put("/agents/{agent_id}", response_model=AgentTypeResponse)
async def update_agent(
    agent_id: int,
    data: AgentTypeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an agent type.

    Args:
        agent_id: Agent type ID
        data: Updated agent data
        db: Database session

    Returns:
        Updated agent type

    Raises:
        HTTPException: If agent not found
    """
    result = await db.execute(select(AgentType).where(AgentType.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)

    logger.info(f"Updated agent type: {agent.name} (ID: {agent.id})")
    return agent


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an agent type.

    Args:
        agent_id: Agent type ID
        db: Database session

    Raises:
        HTTPException: If agent not found
    """
    result = await db.execute(select(AgentType).where(AgentType.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    await db.delete(agent)
    await db.commit()

    logger.info(f"Deleted agent type: {agent.name} (ID: {agent.id})")


# ===== Tool Endpoints =====


@router.post("/tools", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    data: ToolCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tool.

    Args:
        data: Tool data
        db: Database session

    Returns:
        Created tool

    Raises:
        HTTPException: If tool name already exists
    """
    # Check if name already exists
    result = await db.execute(select(Tool).where(Tool.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool with name '{data.name}' already exists",
        )

    # Create tool
    tool = Tool(**data.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    logger.info(f"Created tool: {tool.name} (ID: {tool.id})")
    return tool


@router.get("/tools", response_model=list[ToolResponse])
async def list_all_tools(
    db: AsyncSession = Depends(get_db),
):
    """List all tools (including disabled).

    Args:
        db: Database session

    Returns:
        List of all tools
    """
    result = await db.execute(select(Tool).order_by(Tool.category, Tool.name))
    tools = result.scalars().all()
    return tools


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a tool by ID.

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
            detail=f"Tool with ID {tool_id} not found",
        )

    return tool


@router.put("/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    data: ToolUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a tool.

    Args:
        tool_id: Tool ID
        data: Updated tool data
        db: Database session

    Returns:
        Updated tool

    Raises:
        HTTPException: If tool not found
    """
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with ID {tool_id} not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)

    await db.commit()
    await db.refresh(tool)

    logger.info(f"Updated tool: {tool.name} (ID: {tool.id})")
    return tool


@router.delete("/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
):
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
            detail=f"Tool with ID {tool_id} not found",
        )

    await db.delete(tool)
    await db.commit()

    logger.info(f"Deleted tool: {tool.name} (ID: {tool.id})")


# ===== Agent Tool Assignment Endpoints =====


@router.post(
    "/agents/{agent_id}/tools",
    response_model=AgentToolConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_tool_to_agent(
    agent_id: int,
    data: AgentToolAssignment,
    db: AsyncSession = Depends(get_db),
):
    """Assign a tool to an agent.

    Args:
        agent_id: Agent type ID
        data: Tool assignment data
        db: Database session

    Returns:
        Created tool config

    Raises:
        HTTPException: If agent or tool not found, or assignment already exists
    """
    # Check agent exists
    result = await db.execute(select(AgentType).where(AgentType.id == agent_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    # Check tool exists
    result = await db.execute(select(Tool).where(Tool.id == data.tool_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with ID {data.tool_id} not found",
        )

    # Check if assignment already exists
    result = await db.execute(
        select(AgentToolConfig).where(
            AgentToolConfig.agent_type_id == agent_id,
            AgentToolConfig.tool_id == data.tool_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool {data.tool_id} is already assigned to agent {agent_id}",
        )

    # Create assignment
    config = AgentToolConfig(agent_type_id=agent_id, **data.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)

    logger.info(f"Assigned tool {data.tool_id} to agent {agent_id}")
    return config


@router.get("/agents/{agent_id}/tools", response_model=list[AgentToolConfigResponse])
async def list_agent_tool_assignments(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List all tool assignments for an agent.

    Args:
        agent_id: Agent type ID
        db: Database session

    Returns:
        List of tool configs

    Raises:
        HTTPException: If agent not found
    """
    # Check agent exists
    result = await db.execute(select(AgentType).where(AgentType.id == agent_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    # Get assignments
    result = await db.execute(
        select(AgentToolConfig)
        .where(AgentToolConfig.agent_type_id == agent_id)
        .order_by(AgentToolConfig.order_index, AgentToolConfig.id)
    )
    configs = result.scalars().all()
    return configs


@router.delete("/agents/{agent_id}/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tool_from_agent(
    agent_id: int,
    tool_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove a tool assignment from an agent.

    Args:
        agent_id: Agent type ID
        tool_id: Tool ID
        db: Database session

    Raises:
        HTTPException: If assignment not found
    """
    result = await db.execute(
        select(AgentToolConfig).where(
            AgentToolConfig.agent_type_id == agent_id,
            AgentToolConfig.tool_id == tool_id,
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool assignment not found for agent {agent_id} and tool {tool_id}",
        )

    await db.delete(config)
    await db.commit()

    logger.info(f"Removed tool {tool_id} from agent {agent_id}")
