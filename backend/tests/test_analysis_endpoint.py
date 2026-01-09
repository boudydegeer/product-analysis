"""Test analysis detail endpoint."""
import pytest
from datetime import datetime, UTC
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feature, FeatureStatus, Analysis


@pytest.mark.asyncio
async def test_get_analysis_success(
    async_client: AsyncClient, db_session: AsyncSession
):
    """Test getting analysis for a feature."""
    # Generate a valid UUID for testing
    feature_id = str(uuid4())

    # Create feature
    feature = Feature(
        id=feature_id,
        name="Test Feature",
        description="Description",
        status=FeatureStatus.COMPLETED,
    )
    db_session.add(feature)
    await db_session.commit()

    # Create analysis with flattened data
    analysis = Analysis(
        feature_id=feature_id,
        result={},
        tokens_used=100,
        model_used="gpt-4",
        completed_at=datetime.now(UTC),
        summary_overview="Test overview",
        summary_key_points=["Point 1", "Point 2"],
        summary_metrics={
            "complexity": "medium",
            "estimated_effort": "3 days",
            "confidence": 0.85,
        },
        implementation_architecture={"pattern": "MVC", "components": ["Component1"]},
        implementation_technical_details=[
            {"category": "Backend", "description": "Detail"}
        ],
        implementation_data_flow={"description": "Flow", "steps": ["Step 1"]},
        risks_technical_risks=[{"severity": "high", "description": "Risk"}],
        risks_security_concerns=[],
        risks_scalability_issues=[],
        risks_mitigation_strategies=["Strategy 1"],
        recommendations_improvements=[
            {
                "priority": "high",
                "title": "Improvement suggestion 1",
                "description": "Detailed description for improvement 1",
                "effort": "2 days",
            },
            {
                "priority": "medium",
                "title": "Improvement suggestion 2",
                "description": "Detailed description for improvement 2",
                "effort": "1 day",
            },
        ],
        recommendations_best_practices=["Practice 1"],
        recommendations_next_steps=["Next step"],
    )
    db_session.add(analysis)
    await db_session.commit()

    # Call endpoint
    response = await async_client.get(f"/api/v1/features/{feature_id}/analysis")

    assert response.status_code == 200
    data = response.json()
    assert data["feature_id"] == feature_id
    assert data["status"] == "completed"
    assert data["overview"]["summary"] == "Test overview"
    assert len(data["overview"]["key_points"]) == 2
    assert data["implementation"]["architecture"]["pattern"] == "MVC"


@pytest.mark.asyncio
async def test_get_analysis_no_analysis(
    async_client: AsyncClient, db_session: AsyncSession
):
    """Test getting analysis when none exists."""
    # Generate a valid UUID for testing
    feature_id = str(uuid4())

    # Create feature without analysis
    feature = Feature(
        id=feature_id,
        name="Test Feature No Analysis",
        description="Description",
        status=FeatureStatus.PENDING,
    )
    db_session.add(feature)
    await db_session.commit()

    # Call endpoint
    response = await async_client.get(f"/api/v1/features/{feature_id}/analysis")

    assert response.status_code == 200
    data = response.json()
    assert data["feature_id"] == feature_id
    assert data["status"] == "no_analysis"
    assert "message" in data


@pytest.mark.asyncio
async def test_get_analysis_feature_not_found(async_client: AsyncClient):
    """Test getting analysis for non-existent feature."""
    # Use a valid UUID that doesn't exist in the database
    non_existent_id = str(uuid4())
    response = await async_client.get(f"/api/v1/features/{non_existent_id}/analysis")
    assert response.status_code == 404
