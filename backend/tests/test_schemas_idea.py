"""Tests for idea schemas."""
from datetime import datetime
import pytest
from pydantic import ValidationError

from app.schemas.idea import (
    IdeaCreate,
    IdeaUpdate,
    IdeaResponse,
    IdeaEvaluationRequest,
    IdeaEvaluationResponse,
)


def test_idea_create_schema():
    """Test IdeaCreate schema validation."""
    data = {
        "title": "Dark Mode Feature",
        "description": "Add dark mode support to the application",
    }

    schema = IdeaCreate(**data)
    assert schema.title == "Dark Mode Feature"
    assert schema.description == "Add dark mode support to the application"


def test_idea_create_with_priority():
    """Test IdeaCreate with optional priority."""
    data = {
        "title": "Test Idea",
        "description": "Test description",
        "priority": "high",
    }

    schema = IdeaCreate(**data)
    assert schema.priority == "high"


def test_idea_response_schema():
    """Test IdeaResponse schema."""
    data = {
        "id": "idea-1",
        "title": "Test Idea",
        "description": "Test description",
        "status": "backlog",
        "priority": "medium",
        "business_value": 8,
        "technical_complexity": 5,
        "estimated_effort": "2 weeks",
        "market_fit_analysis": "Strong market fit",
        "risk_assessment": "Low risk",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    schema = IdeaResponse(**data)
    assert schema.id == "idea-1"
    assert schema.business_value == 8
    assert schema.technical_complexity == 5


def test_idea_evaluation_request():
    """Test IdeaEvaluationRequest schema."""
    data = {
        "title": "Dark Mode Feature",
        "description": "Add dark mode support",
    }

    schema = IdeaEvaluationRequest(**data)
    assert schema.title == "Dark Mode Feature"


def test_idea_evaluation_response():
    """Test IdeaEvaluationResponse schema."""
    data = {
        "business_value": 8,
        "technical_complexity": 5,
        "estimated_effort": "2 weeks",
        "market_fit_analysis": "Strong market fit based on user requests",
        "risk_assessment": "Low risk - standard UI implementation",
    }

    schema = IdeaEvaluationResponse(**data)
    assert schema.business_value == 8
    assert schema.technical_complexity == 5


def test_business_value_validation():
    """Test business value must be 1-10."""
    with pytest.raises(ValidationError):
        IdeaEvaluationResponse(
            business_value=11,
            technical_complexity=5,
            estimated_effort="2 weeks",
            market_fit_analysis="Test",
            risk_assessment="Test",
        )
