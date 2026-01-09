"""Brainstorm session and message schemas."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class BrainstormSessionCreate(BaseModel):
    """Schema for creating a brainstorm session."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)


class BrainstormSessionUpdate(BaseModel):
    """Schema for updating a brainstorm session."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    status: str | None = Field(None, pattern="^(active|paused|completed|archived)$")


class BrainstormMessageResponse(BaseModel):
    """Schema for brainstorm message response."""

    id: str
    session_id: str
    role: str
    content: dict[str, Any]  # Changed from str to dict to match JSONB content with blocks
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BrainstormSessionResponse(BaseModel):
    """Schema for brainstorm session response."""

    id: str
    title: str
    description: str
    status: str
    messages: list[BrainstormMessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BrainstormMessageCreate(BaseModel):
    """Schema for creating a brainstorm message."""

    content: dict[str, Any] = Field(..., description="Message content with blocks structure")
