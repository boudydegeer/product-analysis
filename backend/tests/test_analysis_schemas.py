"""Test analysis response schemas."""
import pytest
from pydantic import ValidationError
from app.schemas.analysis import (
    AnalysisOverviewResponse,
    AnalysisImplementationResponse,
    AnalysisRisksResponse,
    AnalysisRecommendationsResponse,
    AnalysisDetailResponse,
)


def test_analysis_overview_response_schema():
    """Test AnalysisOverviewResponse schema."""
    data = {
        "summary": "Test summary",
        "key_points": ["Point 1", "Point 2"],
        "metrics": {
            "complexity": "medium",
            "estimated_effort": "3-5 days",
            "confidence": 0.85,
        },
    }
    response = AnalysisOverviewResponse(**data)
    assert response.summary == "Test summary"
    assert len(response.key_points) == 2
    assert response.metrics["complexity"] == "medium"


def test_analysis_implementation_response_schema():
    """Test AnalysisImplementationResponse schema."""
    data = {
        "architecture": {
            "pattern": "MVC",
            "components": ["Component1", "Component2"],
        },
        "technical_details": [
            {
                "category": "Backend",
                "description": "Test description",
                "code_locations": ["/path/to/file.py"],
            }
        ],
        "data_flow": {
            "description": "Flow description",
            "steps": ["Step 1", "Step 2"],
        },
    }
    response = AnalysisImplementationResponse(**data)
    assert response.architecture["pattern"] == "MVC"
    assert len(response.technical_details) == 1


def test_analysis_detail_response_schema():
    """Test complete AnalysisDetailResponse schema."""
    data = {
        "feature_id": "test-123",
        "feature_name": "Test Feature",
        "analyzed_at": "2026-01-08T10:30:00Z",
        "status": "completed",
        "overview": {
            "summary": "Test summary",
            "key_points": ["Point 1"],
            "metrics": {"complexity": "low", "estimated_effort": "1 day", "confidence": 0.9},
        },
        "implementation": {
            "architecture": {"pattern": "MVC", "components": []},
            "technical_details": [],
            "data_flow": {"description": "Flow", "steps": []},
        },
        "risks": {
            "technical_risks": [],
            "security_concerns": [],
            "scalability_issues": [],
            "mitigation_strategies": [],
        },
        "recommendations": {
            "improvements": [],
            "best_practices": [],
            "next_steps": [],
        },
    }
    response = AnalysisDetailResponse(**data)
    assert response.feature_id == "test-123"
    assert response.status == "completed"
