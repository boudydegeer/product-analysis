import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db():
    """Mock database session"""
    mock = AsyncMock(spec=AsyncSession)
    return mock


@pytest.mark.asyncio
async def test_approve_brief_sends_feature_creation_options(client, mock_db):
    """Test that approve_brief interaction sends feature creation button_group"""

    with patch("app.api.brainstorms.get_db", return_value=mock_db):
        # This would be a WebSocket test in reality
        # For now, test the handler function directly
        from app.api.brainstorms import handle_brief_approval

        result = await handle_brief_approval(
            brainstorm_id="test-123",
            brief_text="# Feature Brief: Test\n\n## Problem Statement\nTest problem",
            db=mock_db
        )

        assert "blocks" in result
        assert any(block["type"] == "button_group" for block in result["blocks"])

        button_group = next(b for b in result["blocks"] if b["type"] == "button_group")
        button_ids = [btn["id"] for btn in button_group["buttons"]]

        assert "create_feature" in button_ids
        assert "save_draft" in button_ids


@pytest.mark.asyncio
async def test_request_changes_prompts_for_feedback(client, mock_db):
    """Test that request_changes interaction asks what to change"""

    with patch("app.api.brainstorms.get_db", return_value=mock_db):
        from app.api.brainstorms import handle_brief_changes_request

        result = await handle_brief_changes_request(
            brainstorm_id="test-123",
            db=mock_db
        )

        assert "blocks" in result
        text_block = next(b for b in result["blocks"] if b["type"] == "text")

        assert "change" in text_block["text"].lower()


@pytest.mark.asyncio
async def test_discard_brief_acknowledges_and_asks_next(client, mock_db):
    """Test that discard_brief interaction acknowledges and prompts"""

    with patch("app.api.brainstorms.get_db", return_value=mock_db):
        from app.api.brainstorms import handle_brief_discard

        result = await handle_brief_discard(
            brainstorm_id="test-123",
            db=mock_db
        )

        assert "blocks" in result
        text_block = next(b for b in result["blocks"] if b["type"] == "text")

        assert len(text_block["text"]) > 0


@pytest.mark.asyncio
async def test_create_feature_creates_feature_record(client, mock_db):
    """Test that create_feature interaction creates Feature in database"""

    from app.services.brief_parser import ParsedBrief

    parsed_brief = ParsedBrief(
        name="Test Feature",
        description="Test description",
        problem_statement="Test problem",
        target_users=["User 1"],
        core_functionality=["Func 1"],
        success_metrics=["Metric 1"],
        technical_considerations=["Tech 1"]
    )

    with patch("app.api.brainstorms.get_db", return_value=mock_db):
        with patch("app.services.brief_parser.BriefParser") as mock_parser:
            mock_parser.return_value.parse.return_value = parsed_brief

            from app.api.brainstorms import handle_feature_creation

            result = await handle_feature_creation(
                brainstorm_id="test-123",
                brief_text="# Feature Brief: Test",
                db=mock_db
            )

            # Verify feature was added to db
            assert mock_db.add.called
            assert mock_db.commit.called

            # Verify response includes success message with link
            assert "blocks" in result
            text_block = next(b for b in result["blocks"] if b["type"] == "text")
            assert "created" in text_block["text"].lower()


@pytest.mark.asyncio
async def test_save_draft_stores_brief_in_brainstorm(client, mock_db):
    """Test that save_draft interaction stores brief in brainstorm metadata"""

    # Mock brainstorm object
    from app.models.brainstorm import BrainstormSession
    mock_brainstorm = MagicMock(spec=BrainstormSession)
    mock_brainstorm.metadata_ = {}

    # Mock execute result
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_brainstorm)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.brainstorms.get_db", return_value=mock_db):
        from app.api.brainstorms import handle_save_draft

        result = await handle_save_draft(
            brainstorm_id="test-123",
            brief_text="# Feature Brief: Test",
            db=mock_db
        )

        # Verify brainstorm metadata updated
        assert mock_db.commit.called

        # Verify response
        assert "blocks" in result
        text_block = next(b for b in result["blocks"] if b["type"] == "text")
        assert "saved" in text_block["text"].lower()


@pytest.mark.asyncio
async def test_interaction_routing_calls_correct_handler():
    """Test that interaction_type routes to correct handler function"""

    handlers = {
        "approve_brief": "handle_brief_approval",
        "request_changes": "handle_brief_changes_request",
        "discard_brief": "handle_brief_discard",
        "create_feature": "handle_feature_creation",
        "save_draft": "handle_save_draft"
    }

    from app.api.brainstorms import get_interaction_handler

    for interaction_type, expected_handler in handlers.items():
        handler = get_interaction_handler(interaction_type)
        assert handler.__name__ == expected_handler
