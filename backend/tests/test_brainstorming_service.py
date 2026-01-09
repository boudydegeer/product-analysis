"""Tests for brainstorming service JSON responses."""
import pytest
from app.services.brainstorming_service import BrainstormingService


@pytest.mark.asyncio
async def test_system_prompt_instructs_json_format():
    """System prompt should instruct Claude to return JSON."""
    service = BrainstormingService(api_key="test-key")

    assert "JSON" in service.SYSTEM_PROMPT
    assert "blocks" in service.SYSTEM_PROMPT
    assert "button_group" in service.SYSTEM_PROMPT
    assert "multi_select" in service.SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_system_prompt_includes_examples():
    """System prompt should include examples of good/bad patterns."""
    service = BrainstormingService(api_key="test-key")

    # Should have examples section
    assert "Examples" in service.SYSTEM_PROMPT or "examples" in service.SYSTEM_PROMPT

    # Should show structure
    assert '"type":' in service.SYSTEM_PROMPT
