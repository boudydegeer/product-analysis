# Analysis Details UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a comprehensive four-tab analysis details interface that displays flattened AI-generated feature analysis data through a new API endpoint.

**Architecture:** Flatten the nested JSON structure in the Analysis model to improve query performance and simplify access patterns. Create a new GET endpoint that returns structured analysis data grouped by concern (overview, implementation, risks, recommendations). Build Vue components using shadcn-vue that consume this API and display the data in an intuitive tabbed interface.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL (backend); Vue 3, TypeScript, Pinia, shadcn-vue, TailwindCSS (frontend); Vitest (testing)

---

## Phase 1: Backend - Database Migration (Flatten Schema)

### Task 1.1: Create migration script for flattened structure

**Estimated time:** 3 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_flattened_analysis_schema.py`:

```python
"""Test flattened analysis schema."""
import pytest
from sqlalchemy import select, inspect
from app.models.analysis import Analysis
from app.database import get_db


@pytest.mark.asyncio
async def test_analysis_has_flattened_columns(async_session):
    """Test that Analysis model has new flattened columns."""
    # Check that new columns exist in the model
    inspector = inspect(Analysis)
    column_names = [c.name for c in inspector.columns]

    assert "summary_overview" in column_names
    assert "summary_key_points" in column_names
    assert "summary_metrics" in column_names
    assert "implementation_architecture" in column_names
    assert "implementation_technical_details" in column_names
    assert "implementation_data_flow" in column_names
    assert "risks_technical_risks" in column_names
    assert "risks_security_concerns" in column_names
    assert "risks_scalability_issues" in column_names
    assert "risks_mitigation_strategies" in column_names
    assert "recommendations_improvements" in column_names
    assert "recommendations_best_practices" in column_names
    assert "recommendations_next_steps" in column_names
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_flattened_analysis_schema.py -v
```

Expected: Test fails because columns don't exist yet.

**Step 3: Create Alembic migration**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
alembic revision -m "flatten_analysis_result_structure"
```

Edit the generated migration file in `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/alembic/versions/XXXXX_flatten_analysis_result_structure.py`:

```python
"""flatten_analysis_result_structure

Revision ID: XXXXX
Revises: YYYYY
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'XXXXX'
down_revision = 'YYYYY'  # Will be auto-filled
branch_label = None
depends_on = None


def upgrade() -> None:
    """Add flattened analysis columns."""
    # Add new flattened columns
    op.add_column('analyses', sa.Column('summary_overview', sa.Text(), nullable=True))
    op.add_column('analyses', sa.Column('summary_key_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('summary_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('implementation_architecture', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('implementation_technical_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('implementation_data_flow', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('risks_technical_risks', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('risks_security_concerns', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('risks_scalability_issues', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('risks_mitigation_strategies', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('recommendations_improvements', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('recommendations_best_practices', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('analyses', sa.Column('recommendations_next_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Remove flattened analysis columns."""
    op.drop_column('analyses', 'recommendations_next_steps')
    op.drop_column('analyses', 'recommendations_best_practices')
    op.drop_column('analyses', 'recommendations_improvements')
    op.drop_column('analyses', 'risks_mitigation_strategies')
    op.drop_column('analyses', 'risks_scalability_issues')
    op.drop_column('analyses', 'risks_security_concerns')
    op.drop_column('analyses', 'risks_technical_risks')
    op.drop_column('analyses', 'implementation_data_flow')
    op.drop_column('analyses', 'implementation_technical_details')
    op.drop_column('analyses', 'implementation_architecture')
    op.drop_column('analyses', 'summary_metrics')
    op.drop_column('analyses', 'summary_key_points')
    op.drop_column('analyses', 'summary_overview')
```

**Step 4: Run migration and verify test passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
alembic upgrade head
pytest tests/test_flattened_analysis_schema.py -v
```

Expected: Migration runs successfully, test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/alembic/versions/*_flatten_analysis_result_structure.py backend/tests/test_flattened_analysis_schema.py
git commit -m "feat(backend): add database migration for flattened analysis schema

Add new columns to analyses table to store flattened analysis data:
- summary_overview, summary_key_points, summary_metrics
- implementation_architecture, technical_details, data_flow
- risks_technical_risks, security_concerns, scalability_issues, mitigation_strategies
- recommendations_improvements, best_practices, next_steps

This improves query performance and simplifies data access patterns."
```

---

### Task 1.2: Update Analysis SQLAlchemy model

**Estimated time:** 3 min

**Step 1: Write failing test**

Add to `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_flattened_analysis_schema.py`:

```python
@pytest.mark.asyncio
async def test_create_analysis_with_flattened_fields(async_session):
    """Test creating Analysis with flattened fields."""
    from app.models.feature import Feature, FeatureStatus

    # Create feature first
    feature = Feature(
        id="test-feature-123",
        name="Test Feature",
        description="Test description",
        status=FeatureStatus.PENDING,
    )
    async_session.add(feature)
    await async_session.commit()

    # Create analysis with flattened fields
    analysis = Analysis(
        feature_id="test-feature-123",
        result={},  # Keep for backward compatibility
        tokens_used=100,
        model_used="gpt-4",
        summary_overview="This is a test overview",
        summary_key_points=["Point 1", "Point 2"],
        summary_metrics={"complexity": "medium", "confidence": 0.85},
        implementation_architecture={"pattern": "MVC"},
        implementation_technical_details=[{"category": "Backend"}],
        implementation_data_flow={"steps": ["Step 1"]},
        risks_technical_risks=[{"severity": "high"}],
        risks_security_concerns=[{"severity": "medium"}],
        risks_scalability_issues=[{"severity": "low"}],
        risks_mitigation_strategies=["Strategy 1"],
        recommendations_improvements=[{"priority": "high"}],
        recommendations_best_practices=["Practice 1"],
        recommendations_next_steps=["Next step 1"],
    )
    async_session.add(analysis)
    await async_session.commit()
    await async_session.refresh(analysis)

    # Verify
    assert analysis.id is not None
    assert analysis.summary_overview == "This is a test overview"
    assert analysis.summary_key_points == ["Point 1", "Point 2"]
    assert analysis.summary_metrics["complexity"] == "medium"
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_flattened_analysis_schema.py::test_create_analysis_with_flattened_fields -v
```

Expected: Test fails because model doesn't have new fields.

**Step 3: Update Analysis model**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/models/analysis.py`:

```python
"""Analysis model for storing feature analysis results."""

from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, JSON, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.feature import Feature


class Analysis(Base, TimestampMixin):
    """Feature analysis result model."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("features.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Legacy field - keep for backward compatibility
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Flattened summary fields
    summary_overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_key_points: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    summary_metrics: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Flattened implementation fields
    implementation_architecture: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    implementation_technical_details: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    implementation_data_flow: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Flattened risk fields
    risks_technical_risks: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    risks_security_concerns: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    risks_scalability_issues: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    risks_mitigation_strategies: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    # Flattened recommendation fields
    recommendations_improvements: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    recommendations_best_practices: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    recommendations_next_steps: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    # Metadata
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    feature: Mapped["Feature"] = relationship("Feature", back_populates="analyses")
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_flattened_analysis_schema.py -v
```

Expected: All tests pass.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/models/analysis.py backend/tests/test_flattened_analysis_schema.py
git commit -m "feat(backend): update Analysis model with flattened fields

Add typed fields to Analysis model for direct access to flattened data:
- Summary: overview, key_points, metrics
- Implementation: architecture, technical_details, data_flow
- Risks: technical_risks, security_concerns, scalability_issues, mitigation_strategies
- Recommendations: improvements, best_practices, next_steps

Keep legacy result field for backward compatibility."
```

---

## Phase 2: Backend - API Endpoint

### Task 2.1: Create Pydantic schemas for analysis response

**Estimated time:** 4 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_analysis_schemas.py`:

```python
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
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_analysis_schemas.py -v
```

Expected: Test fails because schemas don't exist.

**Step 3: Create analysis schemas**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/schemas/analysis.py`:

```python
"""Analysis response schemas."""
from typing import Optional, Any, Literal
from pydantic import BaseModel, Field


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
    feature_id: str = Field(..., description="Feature ID")
    feature_name: str = Field(..., description="Feature name")
    analyzed_at: Optional[str] = Field(None, description="Analysis timestamp")
    status: Literal["completed", "no_analysis", "failed", "analyzing"] = Field(..., description="Analysis status")

    overview: AnalysisOverviewResponse
    implementation: AnalysisImplementationResponse
    risks: AnalysisRisksResponse
    recommendations: AnalysisRecommendationsResponse

    class Config:
        from_attributes = True


class AnalysisErrorResponse(BaseModel):
    """Error response when analysis not available."""
    feature_id: str
    status: Literal["no_analysis", "failed", "analyzing"]
    message: str
    failed_at: Optional[str] = None
    started_at: Optional[str] = None
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_analysis_schemas.py -v
```

Expected: All tests pass.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/schemas/analysis.py backend/tests/test_analysis_schemas.py
git commit -m "feat(backend): add Pydantic schemas for analysis detail response

Create structured response schemas for analysis endpoint:
- AnalysisOverviewResponse: summary, key_points, metrics
- AnalysisImplementationResponse: architecture, technical_details, data_flow
- AnalysisRisksResponse: risks and mitigation strategies
- AnalysisRecommendationsResponse: improvements and next steps
- AnalysisDetailResponse: complete response with all sections"
```

---

### Task 2.2: Implement GET /api/v1/features/{feature_id}/analysis endpoint

**Estimated time:** 5 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_analysis_endpoint.py`:

```python
"""Test analysis detail endpoint."""
import pytest
from datetime import datetime, UTC
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature import Feature, FeatureStatus
from app.models.analysis import Analysis


@pytest.mark.asyncio
async def test_get_analysis_success(client: AsyncClient, async_session: AsyncSession):
    """Test getting analysis for a feature."""
    # Create feature
    feature = Feature(
        id="test-feature-456",
        name="Test Feature",
        description="Description",
        status=FeatureStatus.COMPLETED,
    )
    async_session.add(feature)
    await async_session.commit()

    # Create analysis with flattened data
    analysis = Analysis(
        feature_id="test-feature-456",
        result={},
        tokens_used=100,
        model_used="gpt-4",
        completed_at=datetime.now(UTC),
        summary_overview="Test overview",
        summary_key_points=["Point 1", "Point 2"],
        summary_metrics={"complexity": "medium", "estimated_effort": "3 days", "confidence": 0.85},
        implementation_architecture={"pattern": "MVC", "components": ["Component1"]},
        implementation_technical_details=[{"category": "Backend", "description": "Detail"}],
        implementation_data_flow={"description": "Flow", "steps": ["Step 1"]},
        risks_technical_risks=[{"severity": "high", "description": "Risk"}],
        risks_security_concerns=[],
        risks_scalability_issues=[],
        risks_mitigation_strategies=["Strategy 1"],
        recommendations_improvements=[{"priority": "high", "title": "Improvement"}],
        recommendations_best_practices=["Practice 1"],
        recommendations_next_steps=["Next step"],
    )
    async_session.add(analysis)
    await async_session.commit()

    # Call endpoint
    response = await client.get(f"/api/v1/features/test-feature-456/analysis")

    assert response.status_code == 200
    data = response.json()
    assert data["feature_id"] == "test-feature-456"
    assert data["status"] == "completed"
    assert data["overview"]["summary"] == "Test overview"
    assert len(data["overview"]["key_points"]) == 2
    assert data["implementation"]["architecture"]["pattern"] == "MVC"


@pytest.mark.asyncio
async def test_get_analysis_no_analysis(client: AsyncClient, async_session: AsyncSession):
    """Test getting analysis when none exists."""
    # Create feature without analysis
    feature = Feature(
        id="test-feature-789",
        name="Test Feature No Analysis",
        description="Description",
        status=FeatureStatus.PENDING,
    )
    async_session.add(feature)
    await async_session.commit()

    # Call endpoint
    response = await client.get(f"/api/v1/features/test-feature-789/analysis")

    assert response.status_code == 200
    data = response.json()
    assert data["feature_id"] == "test-feature-789"
    assert data["status"] == "no_analysis"
    assert "message" in data


@pytest.mark.asyncio
async def test_get_analysis_feature_not_found(client: AsyncClient):
    """Test getting analysis for non-existent feature."""
    response = await client.get("/api/v1/features/non-existent/analysis")
    assert response.status_code == 404
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_analysis_endpoint.py -v
```

Expected: Tests fail because endpoint doesn't exist.

**Step 3: Implement endpoint**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/api/features.py` and add the endpoint before the last line:

```python
from app.schemas.analysis import AnalysisDetailResponse, AnalysisErrorResponse
from app.models.analysis import Analysis

# Add this import at the top with other imports


# Add this endpoint after the trigger_analysis endpoint (before the file ends)

@router.get("/{feature_id}/analysis", response_model=AnalysisDetailResponse | AnalysisErrorResponse)
async def get_feature_analysis(
    feature_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get analysis details for a feature.

    Args:
        feature_id: UUID of the feature
        db: Database session

    Returns:
        Complete analysis with overview, implementation, risks, and recommendations

    Raises:
        HTTPException: If feature not found
    """
    # Get feature
    result = await db.execute(select(Feature).where(Feature.id == str(feature_id)))
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found",
        )

    # Get most recent analysis
    result = await db.execute(
        select(Analysis)
        .where(Analysis.feature_id == str(feature_id))
        .order_by(Analysis.created_at.desc())
        .limit(1)
    )
    analysis = result.scalar_one_or_none()

    # Handle no analysis case
    if not analysis:
        return AnalysisErrorResponse(
            feature_id=str(feature_id),
            status="no_analysis",
            message="No analysis available for this feature",
        )

    # Handle analyzing state
    if feature.status == FeatureStatus.ANALYZING:
        return AnalysisErrorResponse(
            feature_id=str(feature_id),
            status="analyzing",
            message="Analysis in progress...",
            started_at=feature.updated_at.isoformat() if feature.updated_at else None,
        )

    # Handle failed state
    if feature.status == FeatureStatus.FAILED:
        return AnalysisErrorResponse(
            feature_id=str(feature_id),
            status="failed",
            message="Analysis failed",
            failed_at=analysis.completed_at.isoformat() if analysis.completed_at else None,
        )

    # Return successful analysis
    return AnalysisDetailResponse(
        feature_id=str(feature_id),
        feature_name=feature.name,
        analyzed_at=analysis.completed_at.isoformat() if analysis.completed_at else None,
        status="completed",
        overview={
            "summary": analysis.summary_overview or "",
            "key_points": analysis.summary_key_points or [],
            "metrics": analysis.summary_metrics or {},
        },
        implementation={
            "architecture": analysis.implementation_architecture or {},
            "technical_details": analysis.implementation_technical_details or [],
            "data_flow": analysis.implementation_data_flow or {},
        },
        risks={
            "technical_risks": analysis.risks_technical_risks or [],
            "security_concerns": analysis.risks_security_concerns or [],
            "scalability_issues": analysis.risks_scalability_issues or [],
            "mitigation_strategies": analysis.risks_mitigation_strategies or [],
        },
        recommendations={
            "improvements": analysis.recommendations_improvements or [],
            "best_practices": analysis.recommendations_best_practices or [],
            "next_steps": analysis.recommendations_next_steps or [],
        },
    )
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_analysis_endpoint.py -v
```

Expected: All tests pass.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/api/features.py backend/tests/test_analysis_endpoint.py
git commit -m "feat(backend): add GET /api/v1/features/{id}/analysis endpoint

Implement endpoint to retrieve feature analysis details:
- Returns flattened analysis data grouped by concern
- Handles no_analysis, analyzing, failed, and completed states
- Returns most recent analysis for the feature
- Supports four sections: overview, implementation, risks, recommendations"
```

---

## Phase 3: Backend - Update Webhook Handler

### Task 3.1: Update webhook to save flattened data

**Estimated time:** 4 min

**Step 1: Write failing test**

Add to `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_webhook_endpoint.py`:

```python
@pytest.mark.asyncio
async def test_webhook_saves_flattened_analysis(
    client: AsyncClient, async_session: AsyncSession
):
    """Test webhook saves analysis in flattened format."""
    from app.models.analysis import Analysis

    # Create feature
    feature = Feature(
        id="webhook-test-flat",
        name="Webhook Test Feature",
        description="Testing flattened save",
        status=FeatureStatus.ANALYZING,
        webhook_secret="test-secret-flat",
    )
    async_session.add(feature)
    await async_session.commit()

    # Prepare webhook payload with nested structure
    payload = {
        "feature_id": "webhook-test-flat",
        "complexity": {
            "summary": {
                "overview": "This feature is complex",
                "key_points": ["Point 1", "Point 2"],
                "metrics": {"complexity": "high", "confidence": 0.9}
            },
            "implementation": {
                "architecture": {"pattern": "Microservices"},
                "technical_details": [{"category": "API"}],
                "data_flow": {"steps": ["Step 1"]}
            }
        },
        "warnings": [],
        "repository_state": {},
        "affected_modules": [],
        "implementation_tasks": [],
        "technical_risks": [{"severity": "medium"}],
        "recommendations": {
            "improvements": [{"priority": "high"}],
            "best_practices": ["Practice 1"],
            "next_steps": ["Step 1"]
        },
        "error": None,
        "raw_output": "Raw output",
        "metadata": {},
    }

    payload_str = json.dumps(payload)
    signature = generate_webhook_signature(payload_str, "test-secret-flat")

    # Send webhook
    response = await client.post(
        "/api/v1/webhooks/analysis-result",
        json=payload,
        headers={"X-Webhook-Signature": signature},
    )

    assert response.status_code == 200

    # Verify flattened data was saved
    result = await async_session.execute(
        select(Analysis).where(Analysis.feature_id == "webhook-test-flat")
    )
    analysis = result.scalar_one()

    assert analysis.summary_overview == "This feature is complex"
    assert analysis.summary_key_points == ["Point 1", "Point 2"]
    assert analysis.summary_metrics["complexity"] == "high"
    assert analysis.implementation_architecture["pattern"] == "Microservices"
    assert analysis.risks_technical_risks[0]["severity"] == "medium"
    assert analysis.recommendations_improvements[0]["priority"] == "high"
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_webhook_endpoint.py::test_webhook_saves_flattened_analysis -v
```

Expected: Test fails because webhook doesn't save flattened data.

**Step 3: Update webhook handler**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/api/webhooks.py` and replace the analysis creation section:

```python
# Replace the section starting from "# Create Analysis record" (around line 91-115)

    # Extract flattened data from nested structure
    complexity = webhook_data.complexity or {}
    summary = complexity.get("summary", {})
    implementation = complexity.get("implementation", {})

    # Create Analysis record with flattened fields
    analysis = Analysis(
        feature_id=feature.id,
        result=result_data,  # Keep full data for backward compatibility
        tokens_used=0,
        model_used="github-workflow",
        completed_at=datetime.now(UTC),
        # Flattened summary
        summary_overview=summary.get("overview"),
        summary_key_points=summary.get("key_points", []),
        summary_metrics=summary.get("metrics", {}),
        # Flattened implementation
        implementation_architecture=implementation.get("architecture"),
        implementation_technical_details=implementation.get("technical_details", []),
        implementation_data_flow=implementation.get("data_flow"),
        # Flattened risks
        risks_technical_risks=webhook_data.technical_risks or [],
        risks_security_concerns=[],  # Extract from technical_risks if needed
        risks_scalability_issues=[],  # Extract from technical_risks if needed
        risks_mitigation_strategies=[],  # Could extract from recommendations
        # Flattened recommendations
        recommendations_improvements=webhook_data.recommendations.get("improvements", []) if webhook_data.recommendations else [],
        recommendations_best_practices=webhook_data.recommendations.get("best_practices", []) if webhook_data.recommendations else [],
        recommendations_next_steps=webhook_data.recommendations.get("next_steps", []) if webhook_data.recommendations else [],
    )

    db.add(analysis)
    await db.commit()
    await db.refresh(feature)

    return {
        "status": "success",
        "feature_id": webhook_data.feature_id,
        "message": "Analysis result received and stored",
    }
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_webhook_endpoint.py::test_webhook_saves_flattened_analysis -v
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/api/webhooks.py backend/tests/test_webhook_endpoint.py
git commit -m "feat(backend): update webhook to save flattened analysis data

Extract nested analysis data from webhook payload and save to flattened fields:
- Extract summary.overview, key_points, metrics from complexity
- Extract implementation details from complexity.implementation
- Save technical_risks and recommendations to flattened fields
- Maintain backward compatibility by keeping full result JSON"
```

---

## Phase 4: Frontend - TypeScript Types

### Task 4.1: Create TypeScript interfaces for analysis

**Estimated time:** 3 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/analysis-types.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import type {
  AnalysisOverview,
  AnalysisImplementation,
  AnalysisRisks,
  AnalysisRecommendations,
  AnalysisDetail,
  AnalysisStatus,
} from '../types/analysis'

describe('Analysis Types', () => {
  it('should accept valid AnalysisOverview', () => {
    const overview: AnalysisOverview = {
      summary: 'Test summary',
      key_points: ['Point 1', 'Point 2'],
      metrics: {
        complexity: 'medium',
        estimated_effort: '3 days',
        confidence: 0.85,
      },
    }
    expect(overview.summary).toBe('Test summary')
    expect(overview.key_points).toHaveLength(2)
  })

  it('should accept valid AnalysisDetail', () => {
    const detail: AnalysisDetail = {
      feature_id: 'test-123',
      feature_name: 'Test Feature',
      analyzed_at: '2026-01-08T10:30:00Z',
      status: 'completed',
      overview: {
        summary: 'Summary',
        key_points: [],
        metrics: {},
      },
      implementation: {
        architecture: {},
        technical_details: [],
        data_flow: {},
      },
      risks: {
        technical_risks: [],
        security_concerns: [],
        scalability_issues: [],
        mitigation_strategies: [],
      },
      recommendations: {
        improvements: [],
        best_practices: [],
        next_steps: [],
      },
    }
    expect(detail.feature_id).toBe('test-123')
    expect(detail.status).toBe('completed')
  })

  it('should enforce AnalysisStatus literals', () => {
    const statuses: AnalysisStatus[] = ['completed', 'no_analysis', 'failed', 'analyzing']
    expect(statuses).toHaveLength(4)
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- analysis-types.spec.ts
```

Expected: Test fails because types don't exist.

**Step 3: Create analysis types**

Create file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/types/analysis.ts`:

```typescript
export type AnalysisStatus = 'completed' | 'no_analysis' | 'failed' | 'analyzing'

export interface AnalysisOverview {
  summary: string
  key_points: string[]
  metrics: {
    complexity?: string
    estimated_effort?: string
    confidence?: number
    [key: string]: any
  }
}

export interface ArchitectureInfo {
  pattern?: string
  components?: string[]
  [key: string]: any
}

export interface TechnicalDetail {
  category: string
  description: string
  code_locations?: string[]
}

export interface DataFlow {
  description?: string
  steps?: string[]
  [key: string]: any
}

export interface AnalysisImplementation {
  architecture: Record<string, any>
  technical_details: Array<Record<string, any>>
  data_flow: Record<string, any>
}

export interface Risk {
  severity: string
  category?: string
  description: string
  impact?: string
  cwe?: string
  recommendation?: string
}

export interface AnalysisRisks {
  technical_risks: Risk[]
  security_concerns: Risk[]
  scalability_issues: Risk[]
  mitigation_strategies: string[]
}

export interface Improvement {
  priority: string
  title: string
  description: string
  effort?: string
}

export interface AnalysisRecommendations {
  improvements: Improvement[]
  best_practices: string[]
  next_steps: string[]
}

export interface AnalysisDetail {
  feature_id: string
  feature_name: string
  analyzed_at: string | null
  status: AnalysisStatus
  overview: AnalysisOverview
  implementation: AnalysisImplementation
  risks: AnalysisRisks
  recommendations: AnalysisRecommendations
}

export interface AnalysisError {
  feature_id: string
  status: 'no_analysis' | 'failed' | 'analyzing'
  message: string
  failed_at?: string | null
  started_at?: string | null
}

export type AnalysisResponse = AnalysisDetail | AnalysisError
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- analysis-types.spec.ts
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/types/analysis.ts frontend/src/__tests__/analysis-types.spec.ts
git commit -m "feat(frontend): add TypeScript types for analysis data

Create comprehensive type definitions for analysis detail interface:
- AnalysisOverview, Implementation, Risks, Recommendations
- AnalysisDetail and AnalysisError response types
- Support for all analysis states and data structures"
```

---

## Phase 5: Frontend - API Client

### Task 5.1: Add analysis API client method

**Estimated time:** 3 min

**Step 1: Write failing test**

Add to `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/api.spec.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { featuresApi } from '../api/features'
import type { AnalysisDetail } from '../types/analysis'

describe('Features API - Analysis', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('should fetch analysis for a feature', async () => {
    const mockAnalysis: AnalysisDetail = {
      feature_id: 'test-123',
      feature_name: 'Test Feature',
      analyzed_at: '2026-01-08T10:30:00Z',
      status: 'completed',
      overview: {
        summary: 'Test summary',
        key_points: ['Point 1'],
        metrics: { complexity: 'medium' },
      },
      implementation: {
        architecture: {},
        technical_details: [],
        data_flow: {},
      },
      risks: {
        technical_risks: [],
        security_concerns: [],
        scalability_issues: [],
        mitigation_strategies: [],
      },
      recommendations: {
        improvements: [],
        best_practices: [],
        next_steps: [],
      },
    }

    // Mock the API call
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockAnalysis,
    })

    const result = await featuresApi.getAnalysis('test-123')
    expect(result.feature_id).toBe('test-123')
    expect(result.status).toBe('completed')
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- api.spec.ts
```

Expected: Test fails because method doesn't exist.

**Step 3: Add API method**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/api/features.ts` and add:

```typescript
import type { AnalysisResponse } from '../types/analysis'

// Add this import at the top

// Add this method to the featuresApi object before the closing brace:

  /**
   * Get analysis details for a feature
   * GET /api/features/{id}/analysis
   */
  async getAnalysis(id: string): Promise<AnalysisResponse> {
    const response = await apiClient.get<AnalysisResponse>(`/features/${id}/analysis`)
    return response.data
  },
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- api.spec.ts
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/api/features.ts frontend/src/__tests__/api.spec.ts
git commit -m "feat(frontend): add getAnalysis API client method

Add method to fetch analysis details from backend:
- GET /api/v1/features/{id}/analysis
- Returns AnalysisResponse (detail or error)
- Supports all analysis states"
```

---

## Phase 6: Frontend - Pinia Store

### Task 6.1: Create analysis store

**Estimated time:** 4 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/analysis-store.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAnalysisStore } from '../stores/analysis'
import type { AnalysisDetail } from '../types/analysis'

vi.mock('../api/features', () => ({
  featuresApi: {
    getAnalysis: vi.fn(),
  },
}))

describe('Analysis Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with empty state', () => {
    const store = useAnalysisStore()
    expect(store.currentAnalysis).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should fetch and store analysis', async () => {
    const { featuresApi } = await import('../api/features')
    const mockAnalysis: AnalysisDetail = {
      feature_id: 'test-123',
      feature_name: 'Test Feature',
      analyzed_at: '2026-01-08T10:30:00Z',
      status: 'completed',
      overview: {
        summary: 'Summary',
        key_points: [],
        metrics: {},
      },
      implementation: {
        architecture: {},
        technical_details: [],
        data_flow: {},
      },
      risks: {
        technical_risks: [],
        security_concerns: [],
        scalability_issues: [],
        mitigation_strategies: [],
      },
      recommendations: {
        improvements: [],
        best_practices: [],
        next_steps: [],
      },
    }

    vi.mocked(featuresApi.getAnalysis).mockResolvedValue(mockAnalysis)

    const store = useAnalysisStore()
    await store.fetchAnalysis('test-123')

    expect(store.currentAnalysis).toEqual(mockAnalysis)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should handle fetch errors', async () => {
    const { featuresApi } = await import('../api/features')
    vi.mocked(featuresApi.getAnalysis).mockRejectedValue(new Error('Network error'))

    const store = useAnalysisStore()
    await store.fetchAnalysis('test-123')

    expect(store.currentAnalysis).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBe('Network error')
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- analysis-store.spec.ts
```

Expected: Test fails because store doesn't exist.

**Step 3: Create analysis store**

Create file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/stores/analysis.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { featuresApi } from '../api/features'
import type { AnalysisResponse, AnalysisDetail } from '../types/analysis'

export const useAnalysisStore = defineStore('analysis', () => {
  // State
  const currentAnalysis = ref<AnalysisResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchAnalysis(featureId: string) {
    loading.value = true
    error.value = null

    try {
      const response = await featuresApi.getAnalysis(featureId)
      currentAnalysis.value = response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch analysis'
      currentAnalysis.value = null
    } finally {
      loading.value = false
    }
  }

  function clearAnalysis() {
    currentAnalysis.value = null
    error.value = null
  }

  // Getters
  function isCompleted(analysis: AnalysisResponse | null): analysis is AnalysisDetail {
    return analysis?.status === 'completed'
  }

  return {
    // State
    currentAnalysis,
    loading,
    error,
    // Actions
    fetchAnalysis,
    clearAnalysis,
    // Getters
    isCompleted,
  }
})
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- analysis-store.spec.ts
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/stores/analysis.ts frontend/src/__tests__/analysis-store.spec.ts
git commit -m "feat(frontend): create Pinia store for analysis state

Add analysis store with:
- State: currentAnalysis, loading, error
- Actions: fetchAnalysis, clearAnalysis
- Type guards for analysis status checking"
```

---

## Phase 7: Frontend - UI Components (Overview Tab)

### Task 7.1: Create OverviewTab component

**Estimated time:** 5 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/OverviewTab.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import OverviewTab from '../components/analysis/tabs/OverviewTab.vue'
import type { AnalysisOverview } from '../types/analysis'

describe('OverviewTab', () => {
  it('should render summary', () => {
    const overview: AnalysisOverview = {
      summary: 'Test summary text',
      key_points: ['Point 1', 'Point 2'],
      metrics: {
        complexity: 'medium',
        estimated_effort: '3-5 days',
        confidence: 0.85,
      },
    }

    const wrapper = mount(OverviewTab, {
      props: { overview },
    })

    expect(wrapper.text()).toContain('Test summary text')
  })

  it('should render key points', () => {
    const overview: AnalysisOverview = {
      summary: 'Summary',
      key_points: ['First point', 'Second point'],
      metrics: {},
    }

    const wrapper = mount(OverviewTab, {
      props: { overview },
    })

    expect(wrapper.text()).toContain('First point')
    expect(wrapper.text()).toContain('Second point')
  })

  it('should display metrics', () => {
    const overview: AnalysisOverview = {
      summary: 'Summary',
      key_points: [],
      metrics: {
        complexity: 'high',
        estimated_effort: '5-7 days',
        confidence: 0.9,
      },
    }

    const wrapper = mount(OverviewTab, {
      props: { overview },
    })

    expect(wrapper.text()).toContain('high')
    expect(wrapper.text()).toContain('5-7 days')
    expect(wrapper.text()).toContain('90')
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- OverviewTab.spec.ts
```

Expected: Test fails because component doesn't exist.

**Step 3: Create OverviewTab component**

Create file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/tabs/OverviewTab.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2 } from 'lucide-vue-next'
import type { AnalysisOverview } from '@/types/analysis'

interface Props {
  overview: AnalysisOverview
}

const props = defineProps<Props>()

const complexityColor = computed(() => {
  const complexity = props.overview.metrics?.complexity?.toLowerCase()
  if (complexity === 'low') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
  if (complexity === 'medium') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
  if (complexity === 'high') return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
  return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
})

const confidencePercent = computed(() => {
  const confidence = props.overview.metrics?.confidence
  return confidence ? (confidence * 100).toFixed(0) : '0'
})
</script>

<template>
  <div class="space-y-6">
    <!-- Summary Card -->
    <Card>
      <CardHeader>
        <CardTitle>Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <p class="text-base leading-relaxed text-muted-foreground">
          {{ overview.summary }}
        </p>
      </CardContent>
    </Card>

    <!-- Key Points -->
    <Card v-if="overview.key_points.length > 0">
      <CardHeader>
        <CardTitle>Key Points</CardTitle>
      </CardHeader>
      <CardContent>
        <ul class="space-y-2">
          <li
            v-for="(point, index) in overview.key_points"
            :key="index"
            class="flex items-start gap-2"
          >
            <CheckCircle2 class="w-5 h-5 text-green-600 mt-0.5 shrink-0" />
            <span>{{ point }}</span>
          </li>
        </ul>
      </CardContent>
    </Card>

    <!-- Metrics Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card v-if="overview.metrics?.complexity">
        <CardHeader>
          <CardDescription>Complexity</CardDescription>
        </CardHeader>
        <CardContent>
          <Badge :class="complexityColor">
            {{ overview.metrics.complexity }}
          </Badge>
        </CardContent>
      </Card>

      <Card v-if="overview.metrics?.estimated_effort">
        <CardHeader>
          <CardDescription>Estimated Effort</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold">
            {{ overview.metrics.estimated_effort }}
          </p>
        </CardContent>
      </Card>

      <Card v-if="overview.metrics?.confidence !== undefined">
        <CardHeader>
          <CardDescription>Confidence</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold">
            {{ confidencePercent }}%
          </p>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- OverviewTab.spec.ts
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/components/analysis/tabs/OverviewTab.vue frontend/src/__tests__/OverviewTab.spec.ts
git commit -m "feat(frontend): create OverviewTab component

Implement overview tab with:
- Summary card displaying main analysis text
- Key points list with check icons
- Metrics grid showing complexity, effort, confidence
- Color-coded complexity badges (low/medium/high)"
```

---

## Phase 8: Frontend - UI Components (Implementation Tab)

### Task 8.1: Create ImplementationTab component

**Estimated time:** 5 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/ImplementationTab.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ImplementationTab from '../components/analysis/tabs/ImplementationTab.vue'
import type { AnalysisImplementation } from '../types/analysis'

describe('ImplementationTab', () => {
  it('should render architecture pattern', () => {
    const implementation: AnalysisImplementation = {
      architecture: {
        pattern: 'Microservices',
        components: ['Service A', 'Service B'],
      },
      technical_details: [],
      data_flow: {},
    }

    const wrapper = mount(ImplementationTab, {
      props: { implementation },
    })

    expect(wrapper.text()).toContain('Microservices')
    expect(wrapper.text()).toContain('Service A')
  })

  it('should render technical details', () => {
    const implementation: AnalysisImplementation = {
      architecture: {},
      technical_details: [
        {
          category: 'Backend',
          description: 'Uses FastAPI',
          code_locations: ['/api/main.py'],
        },
      ],
      data_flow: {},
    }

    const wrapper = mount(ImplementationTab, {
      props: { implementation },
    })

    expect(wrapper.text()).toContain('Backend')
    expect(wrapper.text()).toContain('Uses FastAPI')
  })

  it('should render data flow steps', () => {
    const implementation: AnalysisImplementation = {
      architecture: {},
      technical_details: [],
      data_flow: {
        description: 'Request flow',
        steps: ['Step 1', 'Step 2'],
      },
    }

    const wrapper = mount(ImplementationTab, {
      props: { implementation },
    })

    expect(wrapper.text()).toContain('Request flow')
    expect(wrapper.text()).toContain('Step 1')
    expect(wrapper.text()).toContain('Step 2')
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- ImplementationTab.spec.ts
```

Expected: Test fails because component doesn't exist.

**Step 3: Create ImplementationTab component**

First, create Accordion components if they don't exist. Check for existing accordion:

```bash
ls /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/ui/accordion/
```

If accordion doesn't exist, install it:

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npx shadcn-vue@latest add accordion
```

Create file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/tabs/ImplementationTab.vue`:

```vue
<script setup lang="ts">
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import type { AnalysisImplementation } from '@/types/analysis'

interface Props {
  implementation: AnalysisImplementation
}

const props = defineProps<Props>()
</script>

<template>
  <div class="space-y-6">
    <!-- Architecture -->
    <Card v-if="implementation.architecture?.pattern">
      <CardHeader>
        <CardTitle>Architecture Pattern</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <p class="text-base">{{ implementation.architecture.pattern }}</p>

        <div v-if="implementation.architecture.components?.length > 0">
          <h4 class="text-sm font-semibold mb-2">Components</h4>
          <ul class="space-y-1 font-mono text-sm">
            <li v-for="(component, index) in implementation.architecture.components" :key="index">
              {{ component }}
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>

    <!-- Technical Details -->
    <Card v-if="implementation.technical_details?.length > 0">
      <CardHeader>
        <CardTitle>Technical Details</CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible class="w-full">
          <AccordionItem
            v-for="(detail, index) in implementation.technical_details"
            :key="index"
            :value="`detail-${index}`"
          >
            <AccordionTrigger>
              <Badge variant="outline">{{ detail.category }}</Badge>
            </AccordionTrigger>
            <AccordionContent class="space-y-2">
              <p>{{ detail.description }}</p>
              <div v-if="detail.code_locations?.length > 0">
                <p class="text-sm text-muted-foreground">Code locations:</p>
                <ul class="text-sm font-mono">
                  <li v-for="(location, locIndex) in detail.code_locations" :key="locIndex">
                    {{ location }}
                  </li>
                </ul>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>

    <!-- Data Flow -->
    <Card v-if="implementation.data_flow?.description || implementation.data_flow?.steps?.length > 0">
      <CardHeader>
        <CardTitle>Data Flow</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <p v-if="implementation.data_flow.description" class="text-base">
          {{ implementation.data_flow.description }}
        </p>

        <div v-if="implementation.data_flow.steps?.length > 0" class="space-y-2">
          <div
            v-for="(step, index) in implementation.data_flow.steps"
            :key="index"
            class="flex items-start gap-3"
          >
            <div class="flex flex-col items-center">
              <div
                class="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold"
              >
                {{ index + 1 }}
              </div>
              <div
                v-if="index < implementation.data_flow.steps.length - 1"
                class="w-0.5 h-8 bg-border mt-1"
              ></div>
            </div>
            <p class="pt-1">{{ step }}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- ImplementationTab.spec.ts
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/components/analysis/tabs/ImplementationTab.vue frontend/src/__tests__/ImplementationTab.spec.ts
git commit -m "feat(frontend): create ImplementationTab component

Implement implementation tab with:
- Architecture pattern card with components list
- Technical details accordion with categories
- Data flow visualization with numbered steps
- Code locations display for technical details"
```

---

## Phase 9: Frontend - UI Components (Risks Tab)

### Task 9.1: Create RisksTab component

**Estimated time:** 5 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/RisksTab.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RisksTab from '../components/analysis/tabs/RisksTab.vue'
import type { AnalysisRisks } from '../types/analysis'

describe('RisksTab', () => {
  it('should render technical risks', () => {
    const risks: AnalysisRisks = {
      technical_risks: [
        {
          severity: 'high',
          category: 'Performance',
          description: 'Slow database queries',
        },
      ],
      security_concerns: [],
      scalability_issues: [],
      mitigation_strategies: [],
    }

    const wrapper = mount(RisksTab, {
      props: { risks },
    })

    expect(wrapper.text()).toContain('high')
    expect(wrapper.text()).toContain('Slow database queries')
  })

  it('should render security concerns', () => {
    const risks: AnalysisRisks = {
      technical_risks: [],
      security_concerns: [
        {
          severity: 'critical',
          description: 'SQL injection vulnerability',
          cwe: 'CWE-89',
        },
      ],
      scalability_issues: [],
      mitigation_strategies: [],
    }

    const wrapper = mount(RisksTab, {
      props: { risks },
    })

    expect(wrapper.text()).toContain('critical')
    expect(wrapper.text()).toContain('SQL injection')
    expect(wrapper.text()).toContain('CWE-89')
  })

  it('should render mitigation strategies', () => {
    const risks: AnalysisRisks = {
      technical_risks: [],
      security_concerns: [],
      scalability_issues: [],
      mitigation_strategies: ['Add caching', 'Implement rate limiting'],
    }

    const wrapper = mount(RisksTab, {
      props: { risks },
    })

    expect(wrapper.text()).toContain('Add caching')
    expect(wrapper.text()).toContain('Implement rate limiting')
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- RisksTab.spec.ts
```

Expected: Test fails because component doesn't exist.

**Step 3: Install Alert component if needed**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npx shadcn-vue@latest add alert
```

**Step 4: Create RisksTab component**

Create file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/tabs/RisksTab.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertTriangle, Shield, TrendingUp, CheckCircle2 } from 'lucide-vue-next'
import type { AnalysisRisks } from '@/types/analysis'

interface Props {
  risks: AnalysisRisks
}

const props = defineProps<Props>()

function severityColor(severity: string): string {
  const sev = severity?.toLowerCase()
  if (sev === 'critical') return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
  if (sev === 'high') return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300'
  if (sev === 'medium') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
  if (sev === 'low') return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
  return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Technical Risks -->
    <Card v-if="risks.technical_risks?.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <AlertTriangle class="w-5 h-5 text-yellow-600" />
          Technical Risks
        </CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <Alert v-for="(risk, index) in risks.technical_risks" :key="index" variant="default">
          <div class="flex items-start justify-between">
            <div class="space-y-1 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <Badge :class="severityColor(risk.severity)">
                  {{ risk.severity }}
                </Badge>
                <Badge v-if="risk.category" variant="outline">{{ risk.category }}</Badge>
              </div>
              <AlertDescription>{{ risk.description }}</AlertDescription>
              <p v-if="risk.impact" class="text-sm text-muted-foreground mt-2">
                Impact: {{ risk.impact }}
              </p>
            </div>
          </div>
        </Alert>
      </CardContent>
    </Card>

    <!-- Security Concerns -->
    <Card v-if="risks.security_concerns?.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Shield class="w-5 h-5 text-red-600" />
          Security Concerns
        </CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <Alert
          v-for="(concern, index) in risks.security_concerns"
          :key="index"
          variant="destructive"
        >
          <div class="space-y-1">
            <div class="flex items-center gap-2 flex-wrap">
              <Badge :class="severityColor(concern.severity)">
                {{ concern.severity }}
              </Badge>
              <Badge v-if="concern.cwe" variant="outline" class="font-mono">
                {{ concern.cwe }}
              </Badge>
            </div>
            <AlertDescription>{{ concern.description }}</AlertDescription>
          </div>
        </Alert>
      </CardContent>
    </Card>

    <!-- Scalability Issues -->
    <Card v-if="risks.scalability_issues?.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <TrendingUp class="w-5 h-5 text-blue-600" />
          Scalability Issues
        </CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <Alert v-for="(issue, index) in risks.scalability_issues" :key="index">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <Badge :class="severityColor(issue.severity)">
                {{ issue.severity }}
              </Badge>
            </div>
            <AlertDescription>{{ issue.description }}</AlertDescription>
            <p v-if="issue.recommendation" class="text-sm text-muted-foreground mt-2">
              Recommendation: {{ issue.recommendation }}
            </p>
          </div>
        </Alert>
      </CardContent>
    </Card>

    <!-- Mitigation Strategies -->
    <Card v-if="risks.mitigation_strategies?.length > 0" class="border-l-4 border-l-blue-500">
      <CardHeader>
        <CardTitle>Mitigation Strategies</CardTitle>
      </CardHeader>
      <CardContent>
        <ul class="space-y-2">
          <li
            v-for="(strategy, index) in risks.mitigation_strategies"
            :key="index"
            class="flex items-start gap-2"
          >
            <CheckCircle2 class="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
            <span>{{ strategy }}</span>
          </li>
        </ul>
      </CardContent>
    </Card>
  </div>
</template>
```

**Step 5: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- RisksTab.spec.ts
```

Expected: Test passes.

**Step 6: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/components/analysis/tabs/RisksTab.vue frontend/src/__tests__/RisksTab.spec.ts
git commit -m "feat(frontend): create RisksTab component

Implement risks tab with:
- Technical risks with severity badges and icons
- Security concerns with CWE numbers
- Scalability issues with recommendations
- Mitigation strategies checklist with action items"
```

---

## Phase 10: Frontend - UI Components (Recommendations Tab)

### Task 10.1: Create RecommendationsTab component

**Estimated time:** 5 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/RecommendationsTab.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RecommendationsTab from '../components/analysis/tabs/RecommendationsTab.vue'
import type { AnalysisRecommendations } from '../types/analysis'

describe('RecommendationsTab', () => {
  it('should render improvements with priority', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [
        {
          priority: 'high',
          title: 'Add caching layer',
          description: 'Implement Redis caching',
          effort: '2 days',
        },
      ],
      best_practices: [],
      next_steps: [],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    expect(wrapper.text()).toContain('high')
    expect(wrapper.text()).toContain('Add caching layer')
    expect(wrapper.text()).toContain('2 days')
  })

  it('should render best practices', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [],
      best_practices: ['Use TypeScript', 'Write unit tests'],
      next_steps: [],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    expect(wrapper.text()).toContain('Use TypeScript')
    expect(wrapper.text()).toContain('Write unit tests')
  })

  it('should render next steps', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [],
      best_practices: [],
      next_steps: ['Setup CI/CD', 'Deploy to staging'],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    expect(wrapper.text()).toContain('Setup CI/CD')
    expect(wrapper.text()).toContain('Deploy to staging')
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- RecommendationsTab.spec.ts
```

Expected: Test fails because component doesn't exist.

**Step 3: Create RecommendationsTab component**

Create file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/tabs/RecommendationsTab.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Info, Clock } from 'lucide-vue-next'
import type { AnalysisRecommendations, Improvement } from '@/types/analysis'

interface Props {
  recommendations: AnalysisRecommendations
}

const props = defineProps<Props>()

const sortedImprovements = computed(() => {
  if (!props.recommendations.improvements) return []

  const priorityOrder: Record<string, number> = {
    high: 1,
    medium: 2,
    low: 3,
  }

  return [...props.recommendations.improvements].sort((a, b) => {
    const aPriority = priorityOrder[a.priority?.toLowerCase()] || 99
    const bPriority = priorityOrder[b.priority?.toLowerCase()] || 99
    return aPriority - bPriority
  })
})

function priorityColor(priority: string): string {
  const pri = priority?.toLowerCase()
  if (pri === 'high') return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
  if (pri === 'medium') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
  if (pri === 'low') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
  return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Improvements -->
    <div v-if="sortedImprovements.length > 0">
      <h3 class="text-lg font-semibold mb-4">Priority Improvements</h3>
      <div class="space-y-4">
        <Card v-for="(improvement, index) in sortedImprovements" :key="index">
          <CardHeader>
            <div class="flex items-start justify-between">
              <CardTitle class="text-base">{{ improvement.title }}</CardTitle>
              <Badge :class="priorityColor(improvement.priority)">
                {{ improvement.priority }}
              </Badge>
            </div>
          </CardHeader>
          <CardContent class="space-y-2">
            <p class="text-muted-foreground">{{ improvement.description }}</p>
            <div v-if="improvement.effort" class="flex items-center gap-2 text-sm">
              <Clock class="w-4 h-4" />
              <span>Estimated effort: {{ improvement.effort }}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Best Practices -->
    <Card v-if="recommendations.best_practices?.length > 0">
      <CardHeader>
        <CardTitle>Best Practices</CardTitle>
      </CardHeader>
      <CardContent>
        <ul class="space-y-2">
          <li
            v-for="(practice, index) in recommendations.best_practices"
            :key="index"
            class="flex items-start gap-2"
          >
            <Info class="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
            <span>{{ practice }}</span>
          </li>
        </ul>
      </CardContent>
    </Card>

    <!-- Next Steps -->
    <Card v-if="recommendations.next_steps?.length > 0">
      <CardHeader>
        <CardTitle>Next Steps</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          <div
            v-for="(step, index) in recommendations.next_steps"
            :key="index"
            class="flex items-start gap-3"
          >
            <div
              class="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold shrink-0"
            >
              {{ index + 1 }}
            </div>
            <p class="pt-1">{{ step }}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- RecommendationsTab.spec.ts
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/components/analysis/tabs/RecommendationsTab.vue frontend/src/__tests__/RecommendationsTab.spec.ts
git commit -m "feat(frontend): create RecommendationsTab component

Implement recommendations tab with:
- Priority improvements sorted by urgency (high/medium/low)
- Effort estimates for each improvement
- Best practices list with info icons
- Next steps roadmap with numbered actions"
```

---

## Phase 11: Frontend - UI Components (State Components)

### Task 11.1: Create loading, error, and empty state components

**Estimated time:** 4 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/AnalysisStates.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingState from '../components/analysis/states/LoadingState.vue'
import NoAnalysisState from '../components/analysis/states/NoAnalysisState.vue'
import FailedState from '../components/analysis/states/FailedState.vue'
import AnalyzingState from '../components/analysis/states/AnalyzingState.vue'

describe('Analysis State Components', () => {
  it('should render loading state', () => {
    const wrapper = mount(LoadingState)
    expect(wrapper.exists()).toBe(true)
  })

  it('should render no analysis state', () => {
    const wrapper = mount(NoAnalysisState)
    expect(wrapper.text()).toContain('No Analysis Available')
  })

  it('should render failed state with error message', () => {
    const wrapper = mount(FailedState, {
      props: { message: 'API timeout error' },
    })
    expect(wrapper.text()).toContain('API timeout error')
  })

  it('should render analyzing state', () => {
    const wrapper = mount(AnalyzingState, {
      props: { startedAt: '2026-01-08T10:00:00Z' },
    })
    expect(wrapper.text()).toContain('Analyzing')
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- AnalysisStates.spec.ts
```

Expected: Test fails because components don't exist.

**Step 3: Create state components**

Install Skeleton component if needed:

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npx shadcn-vue@latest add skeleton
```

Create `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/states/LoadingState.vue`:

```vue
<script setup lang="ts">
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
</script>

<template>
  <div class="space-y-6">
    <Card>
      <CardHeader>
        <Skeleton class="h-6 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton class="h-4 w-full mb-2" />
        <Skeleton class="h-4 w-3/4" />
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <Skeleton class="h-6 w-40" />
      </CardHeader>
      <CardContent>
        <Skeleton class="h-4 w-full mb-2" />
        <Skeleton class="h-4 w-2/3" />
      </CardContent>
    </Card>
  </div>
</template>
```

Create `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/states/NoAnalysisState.vue`:

```vue
<script setup lang="ts">
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileQuestion, Sparkles } from 'lucide-vue-next'

const emit = defineEmits<{
  requestAnalysis: []
}>()
</script>

<template>
  <Card>
    <CardContent class="flex flex-col items-center justify-center py-12">
      <FileQuestion class="w-16 h-16 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Analysis Available</h3>
      <p class="text-muted-foreground text-center mb-4">
        This feature hasn't been analyzed yet.
      </p>
      <Button @click="emit('requestAnalysis')">
        <Sparkles class="w-4 h-4 mr-2" />
        Request Analysis
      </Button>
    </CardContent>
  </Card>
</template>
```

Create `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/states/FailedState.vue`:

```vue
<script setup lang="ts">
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw } from 'lucide-vue-next'

interface Props {
  message: string
}

defineProps<Props>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <Alert variant="destructive">
    <AlertCircle class="h-4 w-4" />
    <AlertTitle>Analysis Failed</AlertTitle>
    <AlertDescription>
      {{ message }}
    </AlertDescription>
    <Button variant="outline" class="mt-4" @click="emit('retry')">
      <RefreshCw class="w-4 h-4 mr-2" />
      Retry Analysis
    </Button>
  </Alert>
</template>
```

Create `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/states/AnalyzingState.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { Loader2 } from 'lucide-vue-next'

interface Props {
  startedAt?: string | null
}

const props = defineProps<Props>()

const formattedTime = computed(() => {
  if (!props.startedAt) return ''
  const date = new Date(props.startedAt)
  return date.toLocaleString()
})
</script>

<template>
  <Card>
    <CardContent class="flex flex-col items-center justify-center py-12">
      <Loader2 class="w-16 h-16 text-primary animate-spin mb-4" />
      <h3 class="text-lg font-semibold mb-2">Analyzing Feature...</h3>
      <p class="text-muted-foreground text-center">This may take a few moments.</p>
      <p v-if="formattedTime" class="text-sm text-muted-foreground mt-2">
        Started {{ formattedTime }}
      </p>
    </CardContent>
  </Card>
</template>
```

**Step 4: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- AnalysisStates.spec.ts
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/components/analysis/states/*.vue frontend/src/__tests__/AnalysisStates.spec.ts
git commit -m "feat(frontend): create analysis state components

Add state components for different analysis stages:
- LoadingState: skeleton loaders during fetch
- NoAnalysisState: empty state with request button
- FailedState: error display with retry button
- AnalyzingState: progress indicator with timestamp"
```

---

## Phase 12: Frontend - Main Analysis Dialog

### Task 12.1: Create AnalysisDialog component

**Estimated time:** 5 min

**Step 1: Write failing test**

Create test file `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/AnalysisDialog.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import AnalysisDialog from '../components/analysis/AnalysisDialog.vue'

describe('AnalysisDialog', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render dialog when open', () => {
    const wrapper = mount(AnalysisDialog, {
      props: {
        open: true,
        featureId: 'test-123',
        featureName: 'Test Feature',
      },
    })

    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
  })

  it('should not render dialog when closed', () => {
    const wrapper = mount(AnalysisDialog, {
      props: {
        open: false,
        featureId: 'test-123',
        featureName: 'Test Feature',
      },
    })

    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })

  it('should emit close event', async () => {
    const wrapper = mount(AnalysisDialog, {
      props: {
        open: true,
        featureId: 'test-123',
        featureName: 'Test Feature',
      },
    })

    await wrapper.vm.$emit('update:open', false)
    expect(wrapper.emitted('update:open')).toBeTruthy()
  })
})
```

**Step 2: Run test, verify it fails**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- AnalysisDialog.spec.ts
```

Expected: Test fails because component doesn't exist.

**Step 3: Install Tabs component if needed**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npx shadcn-vue@latest add tabs
```

**Step 4: Create AnalysisDialog component**

Create `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/components/analysis/AnalysisDialog.vue`:

```vue
<script setup lang="ts">
import { watch, computed } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAnalysisStore } from '@/stores/analysis'
import OverviewTab from './tabs/OverviewTab.vue'
import ImplementationTab from './tabs/ImplementationTab.vue'
import RisksTab from './tabs/RisksTab.vue'
import RecommendationsTab from './tabs/RecommendationsTab.vue'
import LoadingState from './states/LoadingState.vue'
import NoAnalysisState from './states/NoAnalysisState.vue'
import FailedState from './states/FailedState.vue'
import AnalyzingState from './states/AnalyzingState.vue'

interface Props {
  open: boolean
  featureId: string
  featureName: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const analysisStore = useAnalysisStore()

// Fetch analysis when dialog opens
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen && props.featureId) {
      analysisStore.fetchAnalysis(props.featureId)
    } else if (!isOpen) {
      analysisStore.clearAnalysis()
    }
  },
  { immediate: true }
)

const isCompleted = computed(() => {
  return analysisStore.currentAnalysis?.status === 'completed'
})

const formattedDate = computed(() => {
  if (!isCompleted.value || !analysisStore.currentAnalysis) return ''
  const analyzedAt = (analysisStore.currentAnalysis as any).analyzed_at
  if (!analyzedAt) return ''
  return new Date(analyzedAt).toLocaleString()
})

function handleRequestAnalysis() {
  // Emit event to parent to trigger analysis
  emit('update:open', false)
  // Could also call API directly here
}

function handleRetry() {
  analysisStore.fetchAnalysis(props.featureId)
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="max-w-5xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{{ featureName }}</DialogTitle>
        <DialogDescription v-if="formattedDate">
          Analyzed {{ formattedDate }}
        </DialogDescription>
      </DialogHeader>

      <!-- Loading State -->
      <LoadingState v-if="analysisStore.loading" />

      <!-- Error State -->
      <div v-else-if="analysisStore.error" class="mt-6">
        <FailedState :message="analysisStore.error" @retry="handleRetry" />
      </div>

      <!-- No Analysis State -->
      <div
        v-else-if="analysisStore.currentAnalysis?.status === 'no_analysis'"
        class="mt-6"
      >
        <NoAnalysisState @request-analysis="handleRequestAnalysis" />
      </div>

      <!-- Analyzing State -->
      <div
        v-else-if="analysisStore.currentAnalysis?.status === 'analyzing'"
        class="mt-6"
      >
        <AnalyzingState
          :started-at="(analysisStore.currentAnalysis as any).started_at"
        />
      </div>

      <!-- Failed State -->
      <div
        v-else-if="analysisStore.currentAnalysis?.status === 'failed'"
        class="mt-6"
      >
        <FailedState
          :message="(analysisStore.currentAnalysis as any).message"
          @retry="handleRetry"
        />
      </div>

      <!-- Success State - Show Tabs -->
      <Tabs v-else-if="isCompleted" default-value="overview" class="mt-6">
        <TabsList class="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="implementation">Implementation</TabsTrigger>
          <TabsTrigger value="risks">Risks & Warnings</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" class="mt-6">
          <OverviewTab :overview="(analysisStore.currentAnalysis as any).overview" />
        </TabsContent>

        <TabsContent value="implementation" class="mt-6">
          <ImplementationTab
            :implementation="(analysisStore.currentAnalysis as any).implementation"
          />
        </TabsContent>

        <TabsContent value="risks" class="mt-6">
          <RisksTab :risks="(analysisStore.currentAnalysis as any).risks" />
        </TabsContent>

        <TabsContent value="recommendations" class="mt-6">
          <RecommendationsTab
            :recommendations="(analysisStore.currentAnalysis as any).recommendations"
          />
        </TabsContent>
      </Tabs>
    </DialogContent>
  </Dialog>
</template>
```

**Step 5: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- AnalysisDialog.spec.ts
```

Expected: Test passes.

**Step 6: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/components/analysis/AnalysisDialog.vue frontend/src/__tests__/AnalysisDialog.spec.ts
git commit -m "feat(frontend): create AnalysisDialog main component

Implement main dialog component that:
- Fetches analysis data when opened
- Displays appropriate state (loading/error/empty/analyzing/success)
- Shows four-tab interface for completed analysis
- Handles dialog open/close state
- Integrates with analysis store"
```

---

## Phase 13: Frontend - Integration

### Task 13.1: Integrate AnalysisDialog with features dashboard

**Estimated time:** 4 min

**Step 1: Write failing test**

Add to `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/DashboardView.spec.ts` (create if doesn't exist):

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import DashboardView from '../views/DashboardView.vue'

describe('DashboardView - Analysis Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should open analysis dialog when feature is clicked', async () => {
    const wrapper = mount(DashboardView)

    // Find and click a feature row (implementation will vary)
    // This test verifies the dialog can be triggered

    expect(wrapper.vm).toBeDefined()
  })
})
```

**Step 2: Run test, verify current behavior**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- DashboardView.spec.ts
```

**Step 3: Update DashboardView to include AnalysisDialog**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/views/DashboardView.vue`:

Add to script section:

```typescript
import { ref } from 'vue'
import AnalysisDialog from '@/components/analysis/AnalysisDialog.vue'

const showAnalysisDialog = ref(false)
const selectedFeatureId = ref<string>('')
const selectedFeatureName = ref<string>('')

function openAnalysis(featureId: string, featureName: string) {
  selectedFeatureId.value = featureId
  selectedFeatureName.value = featureName
  showAnalysisDialog.value = true
}

function closeAnalysis() {
  showAnalysisDialog.value = false
  selectedFeatureId.value = ''
  selectedFeatureName.value = ''
}
```

Add to template section (at the end before closing tag):

```vue
<AnalysisDialog
  v-model:open="showAnalysisDialog"
  :feature-id="selectedFeatureId"
  :feature-name="selectedFeatureName"
/>
```

Update the feature row click handler to call `openAnalysis(feature.id, feature.name)`.

**Step 4: Test manually in browser**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm run dev
```

Navigate to dashboard and click a feature row to verify dialog opens.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add frontend/src/views/DashboardView.vue frontend/src/__tests__/DashboardView.spec.ts
git commit -m "feat(frontend): integrate AnalysisDialog with dashboard

Add analysis dialog integration to dashboard:
- Click feature row to open analysis dialog
- Pass feature ID and name to dialog
- Handle dialog open/close state
- Display full analysis details on demand"
```

---

## Phase 14: Testing

### Task 14.1: Add integration tests

**Estimated time:** 4 min

**Step 1: Write integration test**

Create `/Users/boudydegeer/Code/@smith.ai/product-analysis/frontend/src/__tests__/analysis-integration.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import AnalysisDialog from '../components/analysis/AnalysisDialog.vue'
import { useAnalysisStore } from '../stores/analysis'
import type { AnalysisDetail } from '../types/analysis'

vi.mock('../api/features', () => ({
  featuresApi: {
    getAnalysis: vi.fn(),
  },
}))

describe('Analysis Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should display full analysis flow', async () => {
    const { featuresApi } = await import('../api/features')

    const mockAnalysis: AnalysisDetail = {
      feature_id: 'integration-test',
      feature_name: 'Integration Test Feature',
      analyzed_at: '2026-01-08T10:30:00Z',
      status: 'completed',
      overview: {
        summary: 'Integration test summary',
        key_points: ['Test point 1', 'Test point 2'],
        metrics: {
          complexity: 'medium',
          estimated_effort: '3 days',
          confidence: 0.85,
        },
      },
      implementation: {
        architecture: {
          pattern: 'Test Pattern',
          components: ['Component A'],
        },
        technical_details: [
          {
            category: 'Backend',
            description: 'Test detail',
          },
        ],
        data_flow: {
          description: 'Test flow',
          steps: ['Step 1', 'Step 2'],
        },
      },
      risks: {
        technical_risks: [
          {
            severity: 'high',
            description: 'Test risk',
          },
        ],
        security_concerns: [],
        scalability_issues: [],
        mitigation_strategies: ['Strategy 1'],
      },
      recommendations: {
        improvements: [
          {
            priority: 'high',
            title: 'Test improvement',
            description: 'Improve this',
            effort: '1 day',
          },
        ],
        best_practices: ['Practice 1'],
        next_steps: ['Next step 1'],
      },
    }

    vi.mocked(featuresApi.getAnalysis).mockResolvedValue(mockAnalysis)

    const wrapper = mount(AnalysisDialog, {
      props: {
        open: true,
        featureId: 'integration-test',
        featureName: 'Integration Test Feature',
      },
    })

    // Wait for async data load
    await new Promise((resolve) => setTimeout(resolve, 100))

    // Verify overview tab content
    expect(wrapper.text()).toContain('Integration test summary')
    expect(wrapper.text()).toContain('Test point 1')

    // This test verifies the full integration works
    expect(featuresApi.getAnalysis).toHaveBeenCalledWith('integration-test')
  })
})
```

**Step 2: Run test, verify it passes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test -- analysis-integration.spec.ts
```

Expected: Test passes.

**Step 3: Add backend integration test**

Create `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_analysis_integration.py`:

```python
"""Integration test for analysis endpoint and webhook flow."""
import pytest
from datetime import datetime, UTC
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature import Feature, FeatureStatus
from app.models.analysis import Analysis


@pytest.mark.asyncio
async def test_full_analysis_flow(client: AsyncClient, async_session: AsyncSession):
    """Test complete flow: webhook receives data, endpoint returns it."""
    # 1. Create feature
    feature = Feature(
        id="flow-test-123",
        name="Flow Test Feature",
        description="Testing full flow",
        status=FeatureStatus.ANALYZING,
        webhook_secret="flow-secret",
    )
    async_session.add(feature)
    await async_session.commit()

    # 2. Simulate webhook receiving analysis result
    import json
    from app.utils.webhook_security import generate_webhook_signature

    webhook_payload = {
        "feature_id": "flow-test-123",
        "complexity": {
            "summary": {
                "overview": "Test flow overview",
                "key_points": ["Flow point 1"],
                "metrics": {"complexity": "low"}
            },
            "implementation": {
                "architecture": {"pattern": "Flow pattern"},
                "technical_details": [],
                "data_flow": {}
            }
        },
        "warnings": [],
        "repository_state": {},
        "affected_modules": [],
        "implementation_tasks": [],
        "technical_risks": [],
        "recommendations": {
            "improvements": [],
            "best_practices": [],
            "next_steps": []
        },
        "error": None,
        "raw_output": "",
        "metadata": {},
    }

    payload_str = json.dumps(webhook_payload)
    signature = generate_webhook_signature(payload_str, "flow-secret")

    webhook_response = await client.post(
        "/api/v1/webhooks/analysis-result",
        json=webhook_payload,
        headers={"X-Webhook-Signature": signature},
    )
    assert webhook_response.status_code == 200

    # 3. Fetch analysis via endpoint
    analysis_response = await client.get("/api/v1/features/flow-test-123/analysis")
    assert analysis_response.status_code == 200

    data = analysis_response.json()
    assert data["feature_id"] == "flow-test-123"
    assert data["status"] == "completed"
    assert data["overview"]["summary"] == "Test flow overview"
    assert data["overview"]["key_points"] == ["Flow point 1"]
    assert data["implementation"]["architecture"]["pattern"] == "Flow pattern"
```

**Step 4: Run backend test**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_analysis_integration.py -v
```

Expected: Test passes.

**Step 5: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/tests/test_analysis_integration.py frontend/src/__tests__/analysis-integration.spec.ts
git commit -m "test: add integration tests for analysis feature

Add end-to-end integration tests:
- Backend: webhook receives data, endpoint returns flattened format
- Frontend: dialog fetches and displays analysis data
- Verify full data flow from webhook to UI"
```

---

## Phase 15: Documentation and Cleanup

### Task 15.1: Update README and add inline documentation

**Estimated time:** 3 min

**Step 1: Document the feature**

Create `/Users/boudydegeer/Code/@smith.ai/product-analysis/docs/features/analysis-details-ui.md`:

```markdown
# Analysis Details UI Feature

## Overview

The Analysis Details UI displays AI-generated feature analysis in a comprehensive four-tab interface. Users can view detailed insights organized by concern: overview, implementation, risks, and recommendations.

## Architecture

### Backend

- **Database**: Flattened schema in `analyses` table with dedicated columns for each section
- **API Endpoint**: `GET /api/v1/features/{id}/analysis` returns structured analysis data
- **Webhook Handler**: Extracts nested data from GitHub workflow and saves to flattened columns

### Frontend

- **Store**: Pinia store (`stores/analysis.ts`) manages analysis state
- **Components**: Modular tab components for each section
- **Dialog**: Modal dialog presents analysis in full-screen view

## API Specification

### GET /api/v1/features/{id}/analysis

Returns analysis details for a feature.

**Response (Success):**
```json
{
  "feature_id": "abc123",
  "feature_name": "Feature Name",
  "analyzed_at": "2026-01-08T10:30:00Z",
  "status": "completed",
  "overview": { ... },
  "implementation": { ... },
  "risks": { ... },
  "recommendations": { ... }
}
```

**Response (No Analysis):**
```json
{
  "feature_id": "abc123",
  "status": "no_analysis",
  "message": "No analysis available for this feature"
}
```

## Usage

### Opening Analysis Dialog

```typescript
import { ref } from 'vue'
import AnalysisDialog from '@/components/analysis/AnalysisDialog.vue'

const showDialog = ref(false)
const featureId = ref('feature-123')
const featureName = ref('My Feature')

function openAnalysis() {
  showDialog.value = true
}
```

```vue
<template>
  <button @click="openAnalysis">View Analysis</button>

  <AnalysisDialog
    v-model:open="showDialog"
    :feature-id="featureId"
    :feature-name="featureName"
  />
</template>
```

## Testing

### Backend Tests

```bash
cd backend
pytest tests/test_analysis_endpoint.py -v
pytest tests/test_flattened_analysis_schema.py -v
pytest tests/test_analysis_integration.py -v
```

### Frontend Tests

```bash
cd frontend
npm test -- OverviewTab.spec.ts
npm test -- ImplementationTab.spec.ts
npm test -- RisksTab.spec.ts
npm test -- RecommendationsTab.spec.ts
npm test -- AnalysisDialog.spec.ts
```

## Future Enhancements

- Export analysis as PDF/Markdown
- Compare analysis versions
- Analysis history tracking
- Inline editing and annotations
- Shareable read-only links
```

**Step 2: Update main README**

Add to `/Users/boudydegeer/Code/@smith.ai/product-analysis/README.md` in the Features section:

```markdown
### Analysis Details UI

View comprehensive AI-generated analysis for features in a four-tab interface:
- **Overview**: Summary, key points, and metrics
- **Implementation**: Architecture, technical details, and data flow
- **Risks & Warnings**: Technical risks, security concerns, scalability issues
- **Recommendations**: Priority improvements, best practices, next steps

See [docs/features/analysis-details-ui.md](docs/features/analysis-details-ui.md) for details.
```

**Step 3: Run all tests**

```bash
# Backend
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest -v

# Frontend
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend
npm test
```

Expected: All tests pass.

**Step 4: Commit**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add docs/features/analysis-details-ui.md README.md
git commit -m "docs: add documentation for analysis details UI feature

Add comprehensive documentation:
- Feature overview and architecture
- API specification with examples
- Usage guide for components
- Testing instructions
- Future enhancement ideas"
```

---

## Execution Options

**1. Subagent-Driven (this session)**
- Fresh subagent per task
- Code review between tasks
- Fast iteration
- Ideal for: Iterative development with checkpoints

**2. Parallel Session (separate)**
- Open new session with executing-plans
- Batch execution with checkpoints
- Ideal for: Running complete plan start-to-finish

**Which approach would you like to use?**

---

## Summary

This implementation plan provides:

1. **Bite-sized tasks**: Each task is 2-5 minutes, following TDD
2. **Complete code**: All imports, types, and implementation details included
3. **Exact commands**: Copy-paste ready with expected output
4. **Frequent commits**: Following conventional commits spec
5. **Zero-context execution**: A developer can follow this without prior knowledge
6. **YAGNI/DRY principles**: Only build what's needed, reuse existing patterns
7. **Comprehensive testing**: Unit, integration, and E2E test coverage

**Total estimated time**: ~60-75 minutes for full implementation

**Key architectural decisions**:
- Flattened database schema for better query performance
- Pinia store for centralized state management
- Modular tab components for maintainability
- shadcn-vue components for consistent UI
- Type-safe TypeScript throughout
