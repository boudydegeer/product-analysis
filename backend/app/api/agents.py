"""Agent API endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
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
