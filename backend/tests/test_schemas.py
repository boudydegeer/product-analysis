"""Tests for Pydantic schemas."""

import pytest
from datetime import datetime, UTC
from uuid import UUID, uuid4

from pydantic import ValidationError


class TestFeatureBase:
    """Tests for FeatureBase schema."""

    def test_has_name_field_required(self):
        """FeatureBase should have name as a required string field."""
        from app.schemas.feature import FeatureBase

        # Valid: name provided
        feature = FeatureBase(name="Test Feature")
        assert feature.name == "Test Feature"
        assert isinstance(feature.name, str)

    def test_name_is_required(self):
        """FeatureBase should require name field."""
        from app.schemas.feature import FeatureBase

        with pytest.raises(ValidationError) as exc_info:
            FeatureBase()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) and e["type"] == "missing" for e in errors)

    def test_has_description_field_optional(self):
        """FeatureBase should have description as an optional string field."""
        from app.schemas.feature import FeatureBase

        # Without description
        feature = FeatureBase(name="Test Feature")
        assert feature.description is None

        # With description
        feature_with_desc = FeatureBase(
            name="Test Feature", description="A test description"
        )
        assert feature_with_desc.description == "A test description"
        assert isinstance(feature_with_desc.description, str)

    def test_has_priority_field_default_zero(self):
        """FeatureBase should have priority as int with default 0."""
        from app.schemas.feature import FeatureBase

        # Default priority
        feature = FeatureBase(name="Test Feature")
        assert feature.priority == 0
        assert isinstance(feature.priority, int)

        # Custom priority
        feature_with_priority = FeatureBase(name="Test Feature", priority=5)
        assert feature_with_priority.priority == 5


class TestFeatureCreate:
    """Tests for FeatureCreate schema."""

    def test_inherits_from_feature_base(self):
        """FeatureCreate should inherit from FeatureBase."""
        from app.schemas.feature import FeatureCreate, FeatureBase

        assert issubclass(FeatureCreate, FeatureBase)

    def test_validates_name_is_required(self):
        """FeatureCreate should require name."""
        from app.schemas.feature import FeatureCreate

        with pytest.raises(ValidationError) as exc_info:
            FeatureCreate()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_accepts_optional_description(self):
        """FeatureCreate should accept optional description."""
        from app.schemas.feature import FeatureCreate

        # Without description
        feature = FeatureCreate(name="Test Feature")
        assert feature.description is None

        # With description
        feature_with_desc = FeatureCreate(
            name="Test Feature", description="A description"
        )
        assert feature_with_desc.description == "A description"

    def test_accepts_optional_priority(self):
        """FeatureCreate should accept optional priority with default 0."""
        from app.schemas.feature import FeatureCreate

        # Default priority
        feature = FeatureCreate(name="Test Feature")
        assert feature.priority == 0

        # Custom priority
        feature_with_priority = FeatureCreate(name="Test Feature", priority=10)
        assert feature_with_priority.priority == 10


class TestFeatureUpdate:
    """Tests for FeatureUpdate schema."""

    def test_all_fields_optional(self):
        """FeatureUpdate should have all fields optional."""
        from app.schemas.feature import FeatureUpdate

        # Empty update is valid
        update = FeatureUpdate()
        assert update.name is None
        assert update.description is None
        assert update.priority is None
        assert update.status is None

    def test_can_update_name_only(self):
        """FeatureUpdate should allow updating just name."""
        from app.schemas.feature import FeatureUpdate

        update = FeatureUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.description is None
        assert update.priority is None
        assert update.status is None

    def test_can_update_description_only(self):
        """FeatureUpdate should allow updating just description."""
        from app.schemas.feature import FeatureUpdate

        update = FeatureUpdate(description="New description")
        assert update.description == "New description"
        assert update.name is None

    def test_can_update_priority_only(self):
        """FeatureUpdate should allow updating just priority."""
        from app.schemas.feature import FeatureUpdate

        update = FeatureUpdate(priority=5)
        assert update.priority == 5
        assert update.name is None

    def test_can_update_status_only(self):
        """FeatureUpdate should allow updating just status."""
        from app.schemas.feature import FeatureUpdate
        from app.models.feature import FeatureStatus

        update = FeatureUpdate(status=FeatureStatus.ANALYZING)
        assert update.status == FeatureStatus.ANALYZING
        assert update.name is None

    def test_can_update_multiple_fields(self):
        """FeatureUpdate should allow updating multiple fields."""
        from app.schemas.feature import FeatureUpdate
        from app.models.feature import FeatureStatus

        update = FeatureUpdate(
            name="Updated Name",
            description="Updated description",
            priority=3,
            status=FeatureStatus.COMPLETED,
        )
        assert update.name == "Updated Name"
        assert update.description == "Updated description"
        assert update.priority == 3
        assert update.status == FeatureStatus.COMPLETED


class TestFeatureResponse:
    """Tests for FeatureResponse schema."""

    def test_inherits_from_feature_base(self):
        """FeatureResponse should inherit from FeatureBase."""
        from app.schemas.feature import FeatureResponse, FeatureBase

        assert issubclass(FeatureResponse, FeatureBase)

    def test_has_id_as_uuid(self):
        """FeatureResponse should have id as UUID."""
        from app.schemas.feature import FeatureResponse
        from app.models.feature import FeatureStatus

        test_uuid = uuid4()
        now = datetime.now(UTC)
        response = FeatureResponse(
            id=test_uuid,
            name="Test Feature",
            status=FeatureStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        assert response.id == test_uuid
        assert isinstance(response.id, UUID)

    def test_has_status_as_feature_status(self):
        """FeatureResponse should have status as FeatureStatus enum."""
        from app.schemas.feature import FeatureResponse
        from app.models.feature import FeatureStatus

        test_uuid = uuid4()
        now = datetime.now(UTC)
        response = FeatureResponse(
            id=test_uuid,
            name="Test Feature",
            status=FeatureStatus.ANALYZING,
            created_at=now,
            updated_at=now,
        )
        assert response.status == FeatureStatus.ANALYZING
        assert isinstance(response.status, FeatureStatus)

    def test_has_created_at_as_datetime(self):
        """FeatureResponse should have created_at as datetime."""
        from app.schemas.feature import FeatureResponse
        from app.models.feature import FeatureStatus

        test_uuid = uuid4()
        now = datetime.now(UTC)
        response = FeatureResponse(
            id=test_uuid,
            name="Test Feature",
            status=FeatureStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        assert response.created_at == now
        assert isinstance(response.created_at, datetime)

    def test_has_updated_at_as_datetime(self):
        """FeatureResponse should have updated_at as datetime."""
        from app.schemas.feature import FeatureResponse
        from app.models.feature import FeatureStatus

        test_uuid = uuid4()
        now = datetime.now(UTC)
        response = FeatureResponse(
            id=test_uuid,
            name="Test Feature",
            status=FeatureStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        assert response.updated_at == now
        assert isinstance(response.updated_at, datetime)

    def test_has_github_issue_url_optional(self):
        """FeatureResponse should have github_issue_url as optional str."""
        from app.schemas.feature import FeatureResponse
        from app.models.feature import FeatureStatus

        test_uuid = uuid4()
        now = datetime.now(UTC)

        # Without github_issue_url
        response = FeatureResponse(
            id=test_uuid,
            name="Test Feature",
            status=FeatureStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        assert response.github_issue_url is None

        # With github_issue_url
        response_with_url = FeatureResponse(
            id=test_uuid,
            name="Test Feature",
            status=FeatureStatus.PENDING,
            created_at=now,
            updated_at=now,
            github_issue_url="https://github.com/org/repo/issues/1",
        )
        assert response_with_url.github_issue_url == "https://github.com/org/repo/issues/1"

    def test_has_analysis_workflow_run_id_optional(self):
        """FeatureResponse should have analysis_workflow_run_id as optional str."""
        from app.schemas.feature import FeatureResponse
        from app.models.feature import FeatureStatus

        test_uuid = uuid4()
        now = datetime.now(UTC)

        # Without analysis_workflow_run_id
        response = FeatureResponse(
            id=test_uuid,
            name="Test Feature",
            status=FeatureStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        assert response.analysis_workflow_run_id is None

        # With analysis_workflow_run_id
        response_with_id = FeatureResponse(
            id=test_uuid,
            name="Test Feature",
            status=FeatureStatus.PENDING,
            created_at=now,
            updated_at=now,
            analysis_workflow_run_id="12345",
        )
        assert response_with_id.analysis_workflow_run_id == "12345"

    def test_has_from_attributes_config(self):
        """FeatureResponse should have ConfigDict with from_attributes=True."""
        from app.schemas.feature import FeatureResponse

        assert hasattr(FeatureResponse, "model_config")
        config = FeatureResponse.model_config
        assert config.get("from_attributes") is True


class TestAnalysisResponse:
    """Tests for AnalysisResponse schema."""

    def test_has_id_as_int(self):
        """AnalysisResponse should have id as int."""
        from app.schemas.analysis import AnalysisResponse

        now = datetime.now(UTC)
        test_uuid = uuid4()
        response = AnalysisResponse(
            id=1,
            feature_id=test_uuid,
            result={"key": "value"},
            tokens_used=100,
            model_used="claude-3-opus",
            created_at=now,
        )
        assert response.id == 1
        assert isinstance(response.id, int)

    def test_has_feature_id_as_uuid(self):
        """AnalysisResponse should have feature_id as UUID."""
        from app.schemas.analysis import AnalysisResponse

        now = datetime.now(UTC)
        test_uuid = uuid4()
        response = AnalysisResponse(
            id=1,
            feature_id=test_uuid,
            result={"key": "value"},
            tokens_used=100,
            model_used="claude-3-opus",
            created_at=now,
        )
        assert response.feature_id == test_uuid
        assert isinstance(response.feature_id, UUID)

    def test_has_result_as_dict(self):
        """AnalysisResponse should have result as dict."""
        from app.schemas.analysis import AnalysisResponse

        now = datetime.now(UTC)
        test_uuid = uuid4()
        result_data = {"complexity": "high", "estimate": 40}
        response = AnalysisResponse(
            id=1,
            feature_id=test_uuid,
            result=result_data,
            tokens_used=100,
            model_used="claude-3-opus",
            created_at=now,
        )
        assert response.result == result_data
        assert isinstance(response.result, dict)

    def test_has_tokens_used_as_int(self):
        """AnalysisResponse should have tokens_used as int."""
        from app.schemas.analysis import AnalysisResponse

        now = datetime.now(UTC)
        test_uuid = uuid4()
        response = AnalysisResponse(
            id=1,
            feature_id=test_uuid,
            result={"key": "value"},
            tokens_used=1500,
            model_used="claude-3-opus",
            created_at=now,
        )
        assert response.tokens_used == 1500
        assert isinstance(response.tokens_used, int)

    def test_has_model_used_as_str(self):
        """AnalysisResponse should have model_used as str."""
        from app.schemas.analysis import AnalysisResponse

        now = datetime.now(UTC)
        test_uuid = uuid4()
        response = AnalysisResponse(
            id=1,
            feature_id=test_uuid,
            result={"key": "value"},
            tokens_used=100,
            model_used="claude-3-opus",
            created_at=now,
        )
        assert response.model_used == "claude-3-opus"
        assert isinstance(response.model_used, str)

    def test_has_completed_at_optional_datetime(self):
        """AnalysisResponse should have completed_at as optional datetime."""
        from app.schemas.analysis import AnalysisResponse

        now = datetime.now(UTC)
        test_uuid = uuid4()

        # Without completed_at
        response = AnalysisResponse(
            id=1,
            feature_id=test_uuid,
            result={"key": "value"},
            tokens_used=100,
            model_used="claude-3-opus",
            created_at=now,
        )
        assert response.completed_at is None

        # With completed_at
        completed = datetime.now(UTC)
        response_completed = AnalysisResponse(
            id=1,
            feature_id=test_uuid,
            result={"key": "value"},
            tokens_used=100,
            model_used="claude-3-opus",
            created_at=now,
            completed_at=completed,
        )
        assert response_completed.completed_at == completed
        assert isinstance(response_completed.completed_at, datetime)

    def test_has_created_at_as_datetime(self):
        """AnalysisResponse should have created_at as datetime."""
        from app.schemas.analysis import AnalysisResponse

        now = datetime.now(UTC)
        test_uuid = uuid4()
        response = AnalysisResponse(
            id=1,
            feature_id=test_uuid,
            result={"key": "value"},
            tokens_used=100,
            model_used="claude-3-opus",
            created_at=now,
        )
        assert response.created_at == now
        assert isinstance(response.created_at, datetime)

    def test_has_from_attributes_config(self):
        """AnalysisResponse should have ConfigDict with from_attributes=True."""
        from app.schemas.analysis import AnalysisResponse

        assert hasattr(AnalysisResponse, "model_config")
        config = AnalysisResponse.model_config
        assert config.get("from_attributes") is True
