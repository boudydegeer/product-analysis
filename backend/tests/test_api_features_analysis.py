"""Tests for Feature Analysis API endpoint.

Tests cover the GET /api/v1/features/{id}/analysis endpoint which returns
analysis details or error responses based on analysis status.
"""

import pytest
from datetime import datetime, UTC
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feature, FeatureStatus, Analysis


class TestGetFeatureAnalysis:
    """Tests for GET /api/v1/features/{id}/analysis endpoint."""

    @pytest.mark.asyncio
    async def test_get_analysis_feature_not_found(self, async_client: AsyncClient):
        """Test getting analysis for non-existent feature returns 404."""
        non_existent_id = str(uuid4())
        response = await async_client.get(
            f"/api/v1/features/{non_existent_id}/analysis"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_analysis_no_analysis_available(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting analysis when no analysis exists returns no_analysis error."""
        # Create feature without analysis
        feature_id = str(uuid4())
        feature = Feature(
            id=feature_id,
            name="Test Feature",
            description="Description",
            status=FeatureStatus.PENDING,
        )
        db_session.add(feature)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/features/{feature_id}/analysis")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no_analysis"
        assert "no analysis available" in data["message"].lower()
        assert data["feature_id"] == feature_id

    @pytest.mark.asyncio
    async def test_get_analysis_analyzing_state(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting analysis when feature is analyzing returns analyzing status."""
        # Create feature with analyzing status
        feature_id = str(uuid4())
        feature = Feature(
            id=feature_id,
            name="Test Feature",
            description="Description",
            status=FeatureStatus.ANALYZING,
        )
        db_session.add(feature)

        # Create analysis (even though it's not complete)
        analysis = Analysis(
            feature_id=feature_id,
            result={},
            tokens_used=0,
            model_used="gpt-4",
        )
        db_session.add(analysis)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/features/{feature_id}/analysis")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "analyzing"
        assert "in progress" in data["message"].lower()
        assert data["feature_id"] == feature_id
        assert "started_at" in data

    @pytest.mark.asyncio
    async def test_get_analysis_failed_state(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting analysis when feature analysis failed returns failed status."""
        # Create feature with failed status
        feature_id = str(uuid4())
        feature = Feature(
            id=feature_id,
            name="Test Feature",
            description="Description",
            status=FeatureStatus.FAILED,
        )
        db_session.add(feature)

        # Create analysis with completed_at timestamp
        analysis = Analysis(
            feature_id=feature_id,
            result={},
            tokens_used=0,
            model_used="gpt-4",
            completed_at=datetime.now(UTC),
        )
        db_session.add(analysis)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/features/{feature_id}/analysis")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "failed" in data["message"].lower()
        assert data["feature_id"] == feature_id
        assert "failed_at" in data

    @pytest.mark.asyncio
    async def test_get_analysis_completed_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting analysis for completed feature returns full analysis."""
        # Generate a valid UUID for testing
        feature_id = str(uuid4())

        # Create feature with completed status
        feature = Feature(
            id=feature_id,
            name="Test Feature",
            description="Description",
            status=FeatureStatus.COMPLETED,
        )
        db_session.add(feature)

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
        assert data["status"] == "completed"
        assert data["feature_id"] == feature_id
        assert data["feature_name"] == "Test Feature"
        assert "analyzed_at" in data

        # Verify overview structure
        assert "overview" in data
        assert data["overview"]["summary"] == "Test overview"
        assert len(data["overview"]["key_points"]) == 2

        # Verify implementation structure
        assert "implementation" in data
        assert "architecture" in data["implementation"]
        assert "technical_details" in data["implementation"]

        # Verify risks structure
        assert "risks" in data
        assert len(data["risks"]["technical_risks"]) == 1

        # Verify recommendations structure
        assert "recommendations" in data
        assert len(data["recommendations"]["improvements"]) == 2
        assert data["recommendations"]["improvements"][0]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_get_analysis_handles_none_fields(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting analysis handles None fields gracefully."""
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

        # Create analysis with minimal data (all optional fields as None)
        analysis = Analysis(
            feature_id=feature_id,
            result={},
            tokens_used=100,
            model_used="gpt-4",
            completed_at=datetime.now(UTC),
            # All optional fields None
            summary_overview=None,
            summary_key_points=None,
            summary_metrics=None,
            implementation_architecture=None,
            implementation_technical_details=None,
            implementation_data_flow=None,
            risks_technical_risks=None,
            risks_security_concerns=None,
            risks_scalability_issues=None,
            risks_mitigation_strategies=None,
            recommendations_improvements=None,
            recommendations_best_practices=None,
            recommendations_next_steps=None,
        )
        db_session.add(analysis)
        await db_session.commit()

        # Call endpoint
        response = await async_client.get(f"/api/v1/features/{feature_id}/analysis")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

        # Verify None fields are handled as empty defaults
        assert data["overview"]["summary"] == ""
        assert data["overview"]["key_points"] == []
        assert data["overview"]["metrics"] == {}
        assert data["implementation"]["architecture"] == {}
        assert data["implementation"]["technical_details"] == []
        assert data["risks"]["technical_risks"] == []
        assert data["recommendations"]["improvements"] == []

    @pytest.mark.asyncio
    async def test_get_analysis_with_empty_optional_fields(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting analysis with empty lists and dicts works correctly."""
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

        # Create analysis with empty collections
        analysis = Analysis(
            feature_id=feature_id,
            result={},
            tokens_used=100,
            model_used="gpt-4",
            completed_at=datetime.now(UTC),
            summary_overview="Test analysis",
            summary_key_points=[],  # Empty list
            summary_metrics={},  # Empty dict
            implementation_architecture={},
            implementation_technical_details=[],
            risks_technical_risks=[],
            recommendations_improvements=[],
        )
        db_session.add(analysis)
        await db_session.commit()

        # Call endpoint
        response = await async_client.get(f"/api/v1/features/{feature_id}/analysis")

        assert response.status_code == 200
        data = response.json()

        # Verify empty collections are properly returned
        assert data["overview"]["summary"] == "Test analysis"
        assert data["overview"]["key_points"] == []
        assert data["overview"]["metrics"] == {}
        assert data["implementation"]["architecture"] == {}
        assert data["recommendations"]["improvements"] == []
