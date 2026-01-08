"""Idea schemas for request/response validation."""
from datetime import datetime
from pydantic import BaseModel, Field


class IdeaCreate(BaseModel):
    """Schema for creating an idea."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    priority: str | None = Field(None, pattern="^(low|medium|high|critical)$")


class IdeaUpdate(BaseModel):
    """Schema for updating an idea."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    status: str | None = Field(
        None, pattern="^(backlog|under_review|approved|rejected|implemented)$"
    )
    priority: str | None = Field(None, pattern="^(low|medium|high|critical)$")
    business_value: int | None = Field(None, ge=1, le=10)
    technical_complexity: int | None = Field(None, ge=1, le=10)
    estimated_effort: str | None = Field(None, max_length=100)
    market_fit_analysis: str | None = None
    risk_assessment: str | None = None


class IdeaResponse(BaseModel):
    """Schema for idea response."""

    id: str
    title: str
    description: str
    status: str
    priority: str
    business_value: int | None = None
    technical_complexity: int | None = None
    estimated_effort: str | None = None
    market_fit_analysis: str | None = None
    risk_assessment: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IdeaEvaluationRequest(BaseModel):
    """Schema for requesting AI evaluation of an idea."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    context: str | None = Field(None, description="Additional context for evaluation")


class IdeaEvaluationResponse(BaseModel):
    """Schema for AI evaluation response."""

    business_value: int = Field(
        ..., ge=1, le=10, description="Business value score (1-10)"
    )
    technical_complexity: int = Field(
        ..., ge=1, le=10, description="Technical complexity score (1-10)"
    )
    estimated_effort: str = Field(..., description="Estimated effort (e.g., '2 weeks')")
    market_fit_analysis: str = Field(..., description="Market fit analysis")
    risk_assessment: str = Field(..., description="Risk assessment")
