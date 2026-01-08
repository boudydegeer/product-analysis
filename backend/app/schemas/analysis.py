"""Pydantic schemas for Analysis model."""

from datetime import datetime
from typing import Any, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisResponse(BaseModel):
    """Schema for Analysis response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    feature_id: UUID
    result: dict[str, Any]
    tokens_used: int
    model_used: str
    completed_at: Optional[datetime] = None
    created_at: datetime


class AnalysisOverviewResponse(BaseModel):
    """Analysis overview section."""
    summary: str = Field(..., description="Executive summary of the feature")
    key_points: list[str] = Field(default_factory=list, description="Key highlights")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Complexity, effort, confidence")


class ArchitectureInfo(BaseModel):
    """Architecture information."""
    pattern: str = Field(..., description="Architecture pattern name")
    components: list[str] = Field(default_factory=list, description="List of components")


class TechnicalDetail(BaseModel):
    """Technical detail item."""
    category: str = Field(..., description="Category of technical detail")
    description: str = Field(..., description="Detailed description")
    code_locations: Optional[list[str]] = Field(None, description="Relevant code paths")


class DataFlow(BaseModel):
    """Data flow information."""
    description: str = Field(..., description="Data flow description")
    steps: list[str] = Field(default_factory=list, description="Sequential steps")


class AnalysisImplementationResponse(BaseModel):
    """Analysis implementation section."""
    architecture: dict[str, Any] = Field(default_factory=dict, description="Architecture details")
    technical_details: list[dict[str, Any]] = Field(default_factory=list, description="Technical implementation details")
    data_flow: dict[str, Any] = Field(default_factory=dict, description="Data flow information")


class AnalysisRisksResponse(BaseModel):
    """Analysis risks section."""
    technical_risks: list[dict[str, Any]] = Field(default_factory=list, description="Technical risks")
    security_concerns: list[dict[str, Any]] = Field(default_factory=list, description="Security issues")
    scalability_issues: list[dict[str, Any]] = Field(default_factory=list, description="Scalability concerns")
    mitigation_strategies: list[str] = Field(default_factory=list, description="Risk mitigation strategies")


class AnalysisRecommendationsResponse(BaseModel):
    """Analysis recommendations section."""
    improvements: list[dict[str, Any]] = Field(default_factory=list, description="Suggested improvements")
    best_practices: list[str] = Field(default_factory=list, description="Best practices to follow")
    next_steps: list[str] = Field(default_factory=list, description="Recommended next steps")


class AnalysisDetailResponse(BaseModel):
    """Complete analysis detail response."""
    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature ID")
    feature_name: str = Field(..., description="Feature name")
    analyzed_at: Optional[str] = Field(None, description="Analysis timestamp")
    status: Literal["completed", "no_analysis", "failed", "analyzing"] = Field(..., description="Analysis status")

    overview: AnalysisOverviewResponse
    implementation: AnalysisImplementationResponse
    risks: AnalysisRisksResponse
    recommendations: AnalysisRecommendationsResponse


class AnalysisErrorResponse(BaseModel):
    """Error response when analysis not available."""
    feature_id: str
    status: Literal["no_analysis", "failed", "analyzing"]
    message: str
    failed_at: Optional[str] = None
    started_at: Optional[str] = None
