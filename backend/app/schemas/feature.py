"""Pydantic schemas for Feature model."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.feature import FeatureStatus


class FeatureBase(BaseModel):
    """Base schema for Feature with common fields."""

    name: str
    description: Optional[str] = None
    priority: int = 0


class FeatureCreate(FeatureBase):
    """Schema for creating a new Feature."""

    pass


class FeatureUpdate(BaseModel):
    """Schema for updating a Feature. All fields are optional."""

    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[FeatureStatus] = None


class FeatureResponse(FeatureBase):
    """Schema for Feature response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: FeatureStatus
    created_at: datetime
    updated_at: datetime
    github_issue_url: Optional[str] = None
    analysis_workflow_run_id: Optional[str] = None
