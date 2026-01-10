import pytest
from app.services.brainstorming_service import BrainstormingService

@pytest.fixture
def brainstorming_service():
    return BrainstormingService(api_key="test-key")

def test_system_prompt_contains_feature_brief_validation(brainstorming_service):
    """Test that system prompt includes Feature Brief validation instructions"""
    system_prompt = brainstorming_service._get_system_prompt()

    assert "Feature Brief" in system_prompt
    assert "validation" in system_prompt.lower()
    assert "button_group" in system_prompt

def test_system_prompt_includes_validation_options(brainstorming_service):
    """Test that system prompt defines the three validation options"""
    system_prompt = brainstorming_service._get_system_prompt()

    # Check for the three button options
    assert "approve_brief" in system_prompt
    assert "request_changes" in system_prompt
    assert "discard_brief" in system_prompt

def test_system_prompt_includes_button_group_structure(brainstorming_service):
    """Test that system prompt shows correct button_group format"""
    system_prompt = brainstorming_service._get_system_prompt()

    # Check for button_group structure example
    assert '"type": "button_group"' in system_prompt
    assert '"buttons"' in system_prompt
    assert '"id"' in system_prompt
    assert '"label"' in system_prompt

def test_system_prompt_includes_feature_creation_flow(brainstorming_service):
    """Test that system prompt includes feature creation after approval"""
    system_prompt = brainstorming_service._get_system_prompt()

    assert "create_feature" in system_prompt
    assert "save_draft" in system_prompt

def test_system_prompt_markdown_format_instruction(brainstorming_service):
    """Test that system prompt instructs to use markdown for Feature Brief"""
    system_prompt = brainstorming_service._get_system_prompt()

    assert "markdown" in system_prompt.lower()
    assert "#" in system_prompt  # Heading example
