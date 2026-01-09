"""Service for managing tools and agent-tool configurations."""
import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig, ToolUsageAudit

logger = logging.getLogger(__name__)


class ToolsService:
    """Service for managing tools and their assignments to agents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tools_for_agent(
        self,
        agent_type_id: int,
        enabled_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get all tools assigned to an agent type.

        Args:
            agent_type_id: Agent type ID
            enabled_only: Only return enabled tools

        Returns:
            List of tool definitions ready for Claude SDK
        """
        query = (
            select(Tool)
            .join(AgentToolConfig)
            .where(AgentToolConfig.agent_type_id == agent_type_id)
        )

        if enabled_only:
            query = query.where(
                Tool.enabled == True,
                AgentToolConfig.enabled_for_agent == True
            )

        query = query.order_by(AgentToolConfig.order_index)

        result = await self.db.execute(query)
        tools = result.scalars().all()

        # Convert to SDK format
        return [self._tool_to_sdk_format(tool) for tool in tools]

    def _tool_to_sdk_format(self, tool: Tool) -> dict[str, Any]:
        """Convert Tool model to Claude SDK tool format."""
        return {
            "name": tool.name,
            "description": tool.description,
            **tool.definition  # Spread the definition (includes input_schema, etc.)
        }

    async def register_tool(self, tool_data: dict[str, Any]) -> Tool:
        """Register a new tool.

        Args:
            tool_data: Tool definition dictionary

        Returns:
            Created Tool instance
        """
        tool = Tool(**tool_data)
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)

        logger.info(f"Registered tool: {tool.name}")
        return tool

    async def get_tool_by_name(self, name: str) -> Tool | None:
        """Get tool by name."""
        result = await self.db.execute(
            select(Tool).where(Tool.name == name)
        )
        return result.scalar_one_or_none()

    async def assign_tool_to_agent(
        self,
        agent_type_id: int,
        tool_id: int,
        config: dict[str, Any] | None = None
    ) -> AgentToolConfig:
        """Assign a tool to an agent type.

        Args:
            agent_type_id: Agent type ID
            tool_id: Tool ID
            config: Optional configuration overrides

        Returns:
            Created AgentToolConfig instance
        """
        config_data = {
            "agent_type_id": agent_type_id,
            "tool_id": tool_id,
            **(config or {})
        }

        agent_tool_config = AgentToolConfig(**config_data)
        self.db.add(agent_tool_config)
        await self.db.commit()
        await self.db.refresh(agent_tool_config)

        logger.info(f"Assigned tool {tool_id} to agent {agent_type_id}")
        return agent_tool_config

    async def check_tool_allowed(
        self,
        agent_type_id: int,
        tool_name: str,
        parameters: dict | None = None
    ) -> bool:
        """Check if a tool is allowed for an agent.

        Args:
            agent_type_id: Agent type ID
            tool_name: Tool name
            parameters: Optional parameters to validate

        Returns:
            True if tool is allowed, False otherwise
        """
        result = await self.db.execute(
            select(AgentToolConfig)
            .join(Tool)
            .where(
                AgentToolConfig.agent_type_id == agent_type_id,
                Tool.name == tool_name,
                AgentToolConfig.enabled_for_agent == True,
                AgentToolConfig.allow_use == True
            )
        )

        config = result.scalar_one_or_none()

        if not config:
            return False

        # TODO: Add parameter validation against allowed/denied parameters

        return True

    async def audit_tool_usage(
        self,
        session_id: str,
        agent_type_id: int,
        tool_name: str,
        parameters: dict,
        result: dict,
        status: str,
        execution_time_ms: int,
        error_message: str | None = None
    ) -> ToolUsageAudit:
        """Log tool usage for audit trail.

        Args:
            session_id: Session ID
            agent_type_id: Agent type ID
            tool_name: Tool name
            parameters: Tool input parameters
            result: Tool output result
            status: Execution status (success/failed/denied)
            execution_time_ms: Execution time in milliseconds
            error_message: Optional error message

        Returns:
            Created ToolUsageAudit instance
        """
        # Get tool_id
        tool = await self.get_tool_by_name(tool_name)

        audit = ToolUsageAudit(
            session_id=session_id,
            agent_type_id=agent_type_id,
            tool_id=tool.id if tool else None,
            parameters=parameters,
            result=result,
            status=status,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )

        self.db.add(audit)
        await self.db.commit()

        return audit
