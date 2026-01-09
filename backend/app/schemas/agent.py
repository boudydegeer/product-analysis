"""Pydantic schemas for Agent model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentBase(BaseModel):
    """Base schema for Agent with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Unique identifier name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Display name for UI")
    description: Optional[str] = Field(None, description="Agent description")


class AgentCreate(AgentBase):
    """Schema for creating a new Agent."""

    # Personalization
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar image URL")
    avatar_color: str = Field("#6366f1", max_length=7, description="Hex color code for avatar")
    personality_traits: list[str] = Field(default_factory=list, description="Personality traits")

    # Configuration
    model: str = Field(..., min_length=1, max_length=100, description="Claude model to use")
    system_prompt: str = Field(..., min_length=1, description="System prompt for the agent")

    # Behavior
    streaming_enabled: bool = Field(True, description="Enable streaming responses")
    max_context_tokens: int = Field(200000, ge=1000, le=500000, description="Maximum context tokens")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Model temperature")

    # Status
    enabled: bool = Field(True, description="Whether agent is enabled")
    is_default: bool = Field(False, description="Whether this is the default agent")

    # Metadata
    version: str = Field("1.0.0", max_length=20, description="Agent version")


class AgentUpdate(BaseModel):
    """Schema for updating an Agent. All fields are optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None

    # Personalization
    avatar_url: Optional[str] = Field(None, max_length=500)
    avatar_color: Optional[str] = Field(None, max_length=7)
    personality_traits: Optional[list[str]] = None

    # Configuration
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    system_prompt: Optional[str] = Field(None, min_length=1)

    # Behavior
    streaming_enabled: Optional[bool] = None
    max_context_tokens: Optional[int] = Field(None, ge=1000, le=500000)
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Status
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None

    # Metadata
    version: Optional[str] = Field(None, max_length=20)


class AgentResponse(AgentBase):
    """Schema for Agent response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    avatar_url: Optional[str] = None
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


class ToolAssignmentConfig(BaseModel):
    """Schema for configuring tool assignment to agent."""

    enabled_for_agent: bool = Field(True, description="Whether tool is enabled for this agent")
    order_index: Optional[int] = Field(None, description="Display order")
    allow_use: bool = Field(True, description="Allow agent to use this tool")
    requires_approval: bool = Field(False, description="Require approval before use")
    usage_limit: Optional[int] = Field(None, ge=0, description="Max uses per session")
    allowed_parameters: Optional[dict] = Field(None, description="Allowed parameters")
    denied_parameters: Optional[dict] = Field(None, description="Denied parameters")
    parameter_defaults: Optional[dict] = Field(None, description="Default parameter values")
