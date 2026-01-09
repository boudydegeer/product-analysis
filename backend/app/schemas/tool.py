"""Tool schemas for request/response validation."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator


class ToolCreate(BaseModel):
    """Schema for creating a tool."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    tool_type: str = Field(..., pattern="^(builtin|custom|mcp)$")
    definition: dict[str, Any] = Field(..., description="Tool definition matching Claude SDK format")
    enabled: bool = Field(default=True)
    is_dangerous: bool = Field(default=False)
    requires_approval: bool = Field(default=False)
    version: str = Field(default="1.0.0", max_length=20)
    tags: list[str] = Field(default_factory=list)
    example_usage: str | None = Field(None, description="Example usage of the tool")
    created_by: str | None = Field(None, max_length=255)

    @field_validator("definition")
    @classmethod
    def validate_definition(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate tool definition structure.

        Claude SDK expects tools to have specific structure.
        For custom tools, we expect at minimum: name, description, input_schema.
        """
        if not isinstance(v, dict):
            raise ValueError("Definition must be a dictionary")

        # For custom tools, validate required fields
        if "input_schema" not in v and "parameters" not in v:
            raise ValueError("Tool definition must include 'input_schema' or 'parameters'")

        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags are non-empty strings."""
        if not all(isinstance(tag, str) and tag.strip() for tag in v):
            raise ValueError("All tags must be non-empty strings")
        return v


class ToolUpdate(BaseModel):
    """Schema for updating a tool."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    category: str | None = Field(None, min_length=1, max_length=100)
    tool_type: str | None = Field(None, pattern="^(builtin|custom|mcp)$")
    definition: dict[str, Any] | None = Field(None, description="Tool definition matching Claude SDK format")
    enabled: bool | None = None
    is_dangerous: bool | None = None
    requires_approval: bool | None = None
    version: str | None = Field(None, max_length=20)
    tags: list[str] | None = None
    example_usage: str | None = None
    created_by: str | None = Field(None, max_length=255)

    @field_validator("definition")
    @classmethod
    def validate_definition(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate tool definition structure if provided."""
        if v is None:
            return v

        if not isinstance(v, dict):
            raise ValueError("Definition must be a dictionary")

        # For custom tools, validate required fields
        if "input_schema" not in v and "parameters" not in v:
            raise ValueError("Tool definition must include 'input_schema' or 'parameters'")

        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Validate tags are non-empty strings if provided."""
        if v is None:
            return v

        if not all(isinstance(tag, str) and tag.strip() for tag in v):
            raise ValueError("All tags must be non-empty strings")
        return v


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

    model_config = {"from_attributes": True}
