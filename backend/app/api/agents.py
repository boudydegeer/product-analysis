"""Agent API endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import AgentType, AgentToolConfig
from app.models.tool import Tool
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    ToolAssignmentConfig,
)
from app.services.agent_factory import AgentFactory
from app.services.tools_service import ToolsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("")
@router.get("/")
async def list_agents(
    enabled_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all available agent types.

    Args:
        enabled_only: Only return enabled agents
        db: Database session

    Returns:
        List of agent configurations
    """
    tools_service = ToolsService(db)
    factory = AgentFactory(db, tools_service)

    agents = await factory.list_available_agents(enabled_only=enabled_only)

    return agents


@router.get("/{agent_name}")
async def get_agent_config(
    agent_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get specific agent configuration.

    Args:
        agent_name: Agent type name
        db: Database session

    Returns:
        Agent configuration

    Raises:
        HTTPException: If agent not found
    """
    tools_service = ToolsService(db)
    factory = AgentFactory(db, tools_service)

    try:
        config = await factory.get_agent_config(agent_name)
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{agent_id}/tools")
async def get_agent_tools(
    agent_id: int,
    enabled_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Get tools assigned to an agent.

    Args:
        agent_id: Agent type ID
        enabled_only: Only return enabled tools
        db: Database session

    Returns:
        List of tools in SDK format
    """
    tools_service = ToolsService(db)

    tools = await tools_service.get_tools_for_agent(
        agent_id,
        enabled_only=enabled_only
    )

    return tools


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent.

    Args:
        agent_data: Agent creation data
        db: Database session

    Returns:
        Created agent

    Raises:
        HTTPException: If agent name already exists
    """
    # Check if agent with same name exists
    result = await db.execute(
        select(AgentType).where(AgentType.name == agent_data.name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with name '{agent_data.name}' already exists"
        )

    # Create new agent
    agent = AgentType(
        name=agent_data.name,
        display_name=agent_data.display_name,
        description=agent_data.description,
        avatar_url=agent_data.avatar_url,
        avatar_color=agent_data.avatar_color,
        personality_traits=agent_data.personality_traits,
        model=agent_data.model,
        system_prompt=agent_data.system_prompt,
        streaming_enabled=agent_data.streaming_enabled,
        max_context_tokens=agent_data.max_context_tokens,
        temperature=agent_data.temperature,
        enabled=agent_data.enabled,
        is_default=agent_data.is_default,
        version=agent_data.version,
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    logger.info(f"Created agent: {agent.name} (id={agent.id})")

    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing agent.

    Args:
        agent_id: Agent ID
        agent_data: Agent update data
        db: Database session

    Returns:
        Updated agent

    Raises:
        HTTPException: If agent not found or name conflict
    """
    # Get existing agent
    result = await db.execute(
        select(AgentType).where(AgentType.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )

    # Check name uniqueness if name is being changed
    if agent_data.name and agent_data.name != agent.name:
        result = await db.execute(
            select(AgentType).where(AgentType.name == agent_data.name)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent with name '{agent_data.name}' already exists"
            )

    # Update fields
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)

    logger.info(f"Updated agent: {agent.name} (id={agent.id})")

    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an agent.

    Args:
        agent_id: Agent ID
        db: Database session

    Raises:
        HTTPException: If agent not found
    """
    # Get agent
    result = await db.execute(
        select(AgentType).where(AgentType.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )

    # Delete agent (cascade will handle tool configs)
    await db.delete(agent)
    await db.commit()

    logger.info(f"Deleted agent: {agent.name} (id={agent_id})")


@router.post(
    "/{agent_id}/tools/{tool_id}",
    status_code=status.HTTP_201_CREATED
)
async def assign_tool_to_agent(
    agent_id: int,
    tool_id: int,
    config: ToolAssignmentConfig = ToolAssignmentConfig(),
    db: AsyncSession = Depends(get_db),
):
    """Assign a tool to an agent with configuration.

    Args:
        agent_id: Agent ID
        tool_id: Tool ID
        config: Tool assignment configuration
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If agent/tool not found or already assigned
    """
    # Verify agent exists
    result = await db.execute(
        select(AgentType).where(AgentType.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )

    # Verify tool exists
    result = await db.execute(
        select(Tool).where(Tool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with id {tool_id} not found"
        )

    # Check if already assigned
    result = await db.execute(
        select(AgentToolConfig).where(
            AgentToolConfig.agent_type_id == agent_id,
            AgentToolConfig.tool_id == tool_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tool {tool_id} already assigned to agent {agent_id}"
        )

    # Create assignment
    assignment = AgentToolConfig(
        agent_type_id=agent_id,
        tool_id=tool_id,
        enabled_for_agent=config.enabled_for_agent,
        order_index=config.order_index,
        allow_use=config.allow_use,
        requires_approval=config.requires_approval,
        usage_limit=config.usage_limit,
        allowed_parameters=config.allowed_parameters,
        denied_parameters=config.denied_parameters,
        parameter_defaults=config.parameter_defaults,
    )

    db.add(assignment)
    await db.commit()

    logger.info(f"Assigned tool {tool_id} to agent {agent_id}")

    return {
        "message": f"Tool {tool.name} assigned to agent {agent.name}",
        "agent_id": agent_id,
        "tool_id": tool_id
    }


@router.delete(
    "/{agent_id}/tools/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def remove_tool_from_agent(
    agent_id: int,
    tool_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove a tool assignment from an agent.

    Args:
        agent_id: Agent ID
        tool_id: Tool ID
        db: Database session

    Raises:
        HTTPException: If assignment not found
    """
    # Get assignment
    result = await db.execute(
        select(AgentToolConfig).where(
            AgentToolConfig.agent_type_id == agent_id,
            AgentToolConfig.tool_id == tool_id
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not assigned to agent {agent_id}"
        )

    # Delete assignment
    await db.delete(assignment)
    await db.commit()

    logger.info(f"Removed tool {tool_id} from agent {agent_id}")
