import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.models.brainstorm import BrainstormSession
from app.models.feature import Feature
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db():
    mock = AsyncMock(spec=AsyncSession)
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.add = MagicMock()
    mock.refresh = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_complete_validation_flow_with_approval(mock_db):
    """
    Test complete flow:
    1. Agent generates Feature Brief
    2. PM clicks 'Accept Brief'
    3. PM clicks 'Create Feature'
    4. Feature is created in database
    """
    from app.api.brainstorms import (
        handle_brief_approval,
        handle_feature_creation
    )

    brainstorm_id = "test-brainstorm-123"
    brief_text = """# Feature Brief: Dark Mode Toggle

## Problem Statement
Users need the ability to switch between light and dark themes.

## Core Functionality
- Toggle button in settings
- Persists preference across sessions
"""

    # Step 1: PM approves brief
    approval_response = await handle_brief_approval(
        brainstorm_id=brainstorm_id,
        brief_text=brief_text,
        db=mock_db
    )

    assert "blocks" in approval_response
    button_group = next(
        b for b in approval_response["blocks"]
        if b["type"] == "button_group"
    )
    assert any(btn["id"] == "create_feature" for btn in button_group["buttons"])

    # Step 2: PM creates feature
    creation_response = await handle_feature_creation(
        brainstorm_id=brainstorm_id,
        brief_text=brief_text,
        db=mock_db
    )

    # Verify feature was created
    assert mock_db.add.called
    feature_arg = mock_db.add.call_args[0][0]
    assert isinstance(feature_arg, Feature)
    assert feature_arg.name == "Dark Mode Toggle"
    assert "dark themes" in feature_arg.description

    # Verify response
    assert "created successfully" in creation_response["blocks"][0]["text"]


@pytest.mark.asyncio
async def test_complete_validation_flow_with_changes(mock_db):
    """
    Test flow with changes:
    1. Agent generates Feature Brief
    2. PM clicks 'Request Changes'
    3. PM provides feedback
    4. Agent iterates
    """
    from app.api.brainstorms import handle_brief_changes_request

    brainstorm_id = "test-brainstorm-123"

    # PM requests changes
    response = await handle_brief_changes_request(
        brainstorm_id=brainstorm_id,
        db=mock_db
    )

    assert "blocks" in response
    text_block = response["blocks"][0]
    assert "change" in text_block["text"].lower()


@pytest.mark.asyncio
async def test_complete_validation_flow_with_discard(mock_db):
    """
    Test flow with discard:
    1. Agent generates Feature Brief
    2. PM clicks 'Discard'
    3. Agent asks what to explore instead
    """
    from app.api.brainstorms import handle_brief_discard

    brainstorm_id = "test-brainstorm-123"

    response = await handle_brief_discard(
        brainstorm_id=brainstorm_id,
        db=mock_db
    )

    assert "blocks" in response
    text_block = response["blocks"][0]
    assert len(text_block["text"]) > 0


@pytest.mark.asyncio
async def test_validation_flow_saves_draft(mock_db):
    """
    Test draft saving:
    1. Agent generates Feature Brief
    2. PM clicks 'Accept Brief'
    3. PM clicks 'Save as Draft'
    4. Brief saved in brainstorm metadata
    """
    from app.api.brainstorms import (
        handle_brief_approval,
        handle_save_draft
    )
    from sqlalchemy import select

    brainstorm_id = "test-brainstorm-123"
    brief_text = "# Feature Brief: Test"

    # Mock brainstorm lookup
    mock_brainstorm = MagicMock()
    mock_brainstorm.id = brainstorm_id
    mock_brainstorm.metadata_ = None  # Start with None to test initialization

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_brainstorm
    mock_db.execute.return_value = mock_result

    # PM approves
    await handle_brief_approval(
        brainstorm_id=brainstorm_id,
        brief_text=brief_text,
        db=mock_db
    )

    # PM saves draft
    response = await handle_save_draft(
        brainstorm_id=brainstorm_id,
        brief_text=brief_text,
        db=mock_db
    )

    # Verify draft saved - check the mock object's metadata_ attribute directly
    assert mock_brainstorm.metadata_ is not None
    assert mock_brainstorm.metadata_["draft_brief"] == brief_text
    assert mock_db.commit.called
    assert "saved" in response["blocks"][0]["text"].lower()


@pytest.mark.asyncio
async def test_parser_integration_with_feature_creation(mock_db):
    """Test that BriefParser correctly extracts data for Feature creation"""
    from app.api.brainstorms import handle_feature_creation

    brief_text = """# Feature Brief: Advanced Search

## Problem Statement
Users struggle to find specific items in large datasets.

## Target Users
- Data analysts
- Power users

## Core Functionality
- Full-text search
- Filter by multiple criteria
- Export results

## Success Metrics
- 80% of searches return results in <2s
- 60% of users use advanced filters

## Technical Considerations
- Elasticsearch integration
- Query caching
"""

    response = await handle_feature_creation(
        brainstorm_id="test-123",
        brief_text=brief_text,
        db=mock_db
    )

    # Get the feature that was added
    feature = mock_db.add.call_args[0][0]

    assert feature.name == "Advanced Search"
    assert "large datasets" in feature.description
    assert feature.metadata_["brief"]["target_users"] == ["Data analysts", "Power users"]
    assert len(feature.metadata_["brief"]["core_functionality"]) == 3
    assert len(feature.metadata_["brief"]["success_metrics"]) == 2
    assert feature.metadata_["source"] == "brainstorm"
