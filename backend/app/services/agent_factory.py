"""Factory for creating Agent SDK clients with dynamic tools."""
import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions

from app.models.agent import AgentType
from app.services.tools_service import ToolsService

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating Agent SDK clients with dynamic tool configuration."""

    def __init__(self, db: AsyncSession, tools_service: ToolsService):
        self.db = db
        self.tools_service = tools_service

    async def create_agent_client(
        self,
        agent_type_name: str,
        api_key: str | None = None
    ) -> ClaudeSDKClient:
        """Create an SDK client for the given agent type.

        Flow:
        1. Load agent type configuration from database
        2. Load tools assigned to this agent via ToolsService
        3. Initialize ClaudeSDKClient with tools
        4. Return ready-to-use client

        Args:
            agent_type_name: Agent type name (e.g., "brainstorm")
            api_key: Optional Anthropic API key (uses env var if not provided)

        Returns:
            Configured ClaudeSDKClient instance
        """
        # Get agent configuration
        result = await self.db.execute(
            select(AgentType).where(AgentType.name == agent_type_name)
        )
        agent_config = result.scalar_one_or_none()

        if not agent_config:
            raise ValueError(f"Agent type '{agent_type_name}' not found")

        if not agent_config.enabled:
            raise ValueError(f"Agent type '{agent_type_name}' is disabled")

        # Load tools for this agent
        tools = await self.tools_service.get_tools_for_agent(
            agent_config.id,
            enabled_only=True
        )

        logger.info(f"Creating SDK client for '{agent_type_name}' with {len(tools)} tools")

        # Extract tool names for SDK (SDK expects list of strings, not full definitions)
        tool_names = [tool["name"] for tool in tools] if tools else None

        # Build SDK options
        options = ClaudeAgentOptions(
            model=agent_config.model,
            system_prompt=agent_config.system_prompt,
            tools=tool_names,  # SDK expects list of tool names (strings)
        )

        # Create and return client
        client = ClaudeSDKClient(options=options)

        return client

    async def get_agent_config(self, agent_type_name: str) -> dict[str, Any]:
        """Get agent configuration including personalization.

        Args:
            agent_type_name: Agent type name

        Returns:
            Dictionary with agent configuration
        """
        result = await self.db.execute(
            select(AgentType).where(AgentType.name == agent_type_name)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            raise ValueError(f"Agent type '{agent_type_name}' not found")

        return {
            "id": agent.id,
            "name": agent.name,
            "display_name": agent.display_name,
            "description": agent.description,
            "avatar_url": agent.avatar_url,
            "avatar_color": agent.avatar_color,
            "personality_traits": agent.personality_traits,
            "model": agent.model,
            "temperature": agent.temperature,
        }

    async def list_available_agents(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        """List all available agent types.

        Args:
            enabled_only: Only return enabled agents

        Returns:
            List of agent configurations
        """
        query = select(AgentType)

        if enabled_only:
            query = query.where(AgentType.enabled.is_(True))

        result = await self.db.execute(query)
        agents = result.scalars().all()

        return [
            {
                "id": agent.id,
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
                "avatar_url": agent.avatar_url,
                "avatar_color": agent.avatar_color,
                "personality_traits": agent.personality_traits,
            }
            for agent in agents
        ]
