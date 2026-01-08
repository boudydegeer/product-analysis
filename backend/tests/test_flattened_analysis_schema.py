"""Test flattened analysis schema."""
import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import Session
from app.models import Base
from app.models.analysis import Analysis


def test_analysis_has_flattened_columns():
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


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a new database session for testing."""
    with Session(engine) as session:
        yield session


def test_create_analysis_with_flattened_fields(session):
    """Test creating Analysis with flattened fields."""
    from app.models.feature import Feature, FeatureStatus

    # Create feature first
    feature = Feature(
        id="test-feature-123",
        name="Test Feature",
        description="Test description",
        status=FeatureStatus.PENDING,
    )
    session.add(feature)
    session.commit()

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
    session.add(analysis)
    session.commit()
    session.refresh(analysis)

    # Verify
    assert analysis.id is not None
    assert analysis.summary_overview == "This is a test overview"
    assert analysis.summary_key_points == ["Point 1", "Point 2"]
    assert analysis.summary_metrics["complexity"] == "medium"
