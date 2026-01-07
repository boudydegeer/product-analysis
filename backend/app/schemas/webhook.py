"""Webhook schemas for receiving analysis results."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class AnalysisResultWebhook(BaseModel):
    """Schema for analysis result webhook payload from GitHub workflow.

    This matches the JSON structure sent by the analyze-feature.yml workflow.
    """

    feature_id: str = Field(..., description="Feature ID that was analyzed")

    # Analysis result fields (all optional as structure may vary)
    warnings: Optional[list[dict[str, Any]]] = Field(
        None, description="Warnings about missing infrastructure or risks"
    )
    repository_state: Optional[dict[str, Any]] = Field(
        None, description="State of the repository"
    )
    complexity: Optional[dict[str, Any]] = Field(
        None, description="Complexity estimation"
    )
    affected_modules: Optional[list[dict[str, Any]]] = Field(
        None, description="Modules affected by the feature"
    )
    implementation_tasks: Optional[list[dict[str, Any]]] = Field(
        None, description="List of implementation tasks"
    )
    technical_risks: Optional[list[dict[str, Any]]] = Field(
        None, description="Technical risks identified"
    )
    recommendations: Optional[dict[str, Any]] = Field(
        None, description="Implementation recommendations"
    )

    # Error handling
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    stack: Optional[str] = Field(None, description="Stack trace if analysis failed")
    raw_output: Optional[str] = Field(
        None, description="Raw output if structured parsing failed"
    )

    # Metadata
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Workflow metadata (run_id, timestamp, etc.)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "feature_id": "feat-12345",
                "complexity": {
                    "story_points": 5,
                    "estimated_hours": 16,
                    "level": "Medium",
                },
                "metadata": {
                    "workflow_run_id": "98765",
                    "analyzed_at": "2026-01-07T10:30:00Z",
                },
            }
        }
