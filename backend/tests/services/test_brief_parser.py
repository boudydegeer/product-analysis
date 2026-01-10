import pytest
from app.services.brief_parser import BriefParser, ParsedBrief

@pytest.fixture
def sample_brief():
    return """# Feature Brief: Dark Mode Toggle

## Problem Statement
Users need the ability to switch between light and dark themes to reduce eye strain and match their system preferences.

## Target Users
- Power users who work long hours
- Users with visual sensitivity
- Users who prefer dark interfaces

## Core Functionality
- Toggle button in settings
- Persists preference across sessions
- Respects system preference on first load
- Smooth theme transitions

## Success Metrics
- 40% of users enable dark mode within first week
- 90% retention of dark mode users after one month
- Zero increase in bounce rate after implementation

## Technical Considerations
- Use CSS variables for theming
- Store preference in localStorage
- Test accessibility contrast ratios
- Ensure all components support both themes
"""

@pytest.fixture
def minimal_brief():
    return """# Feature Brief: Simple Feature

## Problem Statement
A problem to solve.

## Core Functionality
- Feature 1
- Feature 2
"""

@pytest.fixture
def parser():
    return BriefParser()

def test_parse_extracts_name(parser, sample_brief):
    """Test that parser extracts feature name from H1"""
    result = parser.parse(sample_brief)

    assert result.name == "Dark Mode Toggle"
    assert "Feature Brief:" not in result.name

def test_parse_extracts_problem_statement(parser, sample_brief):
    """Test that parser extracts problem statement section"""
    result = parser.parse(sample_brief)

    assert "eye strain" in result.problem_statement
    assert "system preferences" in result.problem_statement

def test_parse_extracts_target_users(parser, sample_brief):
    """Test that parser extracts target users list"""
    result = parser.parse(sample_brief)

    assert len(result.target_users) == 3
    assert "Power users who work long hours" in result.target_users
    assert "Users with visual sensitivity" in result.target_users

def test_parse_extracts_core_functionality(parser, sample_brief):
    """Test that parser extracts functionality list"""
    result = parser.parse(sample_brief)

    assert len(result.core_functionality) >= 4
    assert any("Toggle button" in item for item in result.core_functionality)
    assert any("Persists preference" in item for item in result.core_functionality)

def test_parse_extracts_success_metrics(parser, sample_brief):
    """Test that parser extracts success metrics"""
    result = parser.parse(sample_brief)

    assert len(result.success_metrics) == 3
    assert any("40%" in item for item in result.success_metrics)
    assert any("retention" in item for item in result.success_metrics)

def test_parse_extracts_technical_considerations(parser, sample_brief):
    """Test that parser extracts technical considerations"""
    result = parser.parse(sample_brief)

    assert len(result.technical_considerations) >= 4
    assert any("CSS variables" in item for item in result.technical_considerations)
    assert any("localStorage" in item for item in result.technical_considerations)

def test_parse_minimal_brief(parser, minimal_brief):
    """Test that parser handles brief with only required sections"""
    result = parser.parse(minimal_brief)

    assert result.name == "Simple Feature"
    assert result.problem_statement == "A problem to solve."
    assert len(result.core_functionality) == 2
    assert result.target_users == []
    assert result.success_metrics == []
    assert result.technical_considerations == []

def test_parse_creates_description(parser, sample_brief):
    """Test that parser creates a description for the feature"""
    result = parser.parse(sample_brief)

    assert result.description != ""
    assert "eye strain" in result.description or "dark mode" in result.description.lower()

def test_parsed_brief_to_dict(parser, sample_brief):
    """Test that ParsedBrief can convert to dict for Feature creation"""
    result = parser.parse(sample_brief)
    data = result.to_dict()

    assert data["name"] == "Dark Mode Toggle"
    assert data["description"] != ""
    assert "problem_statement" in data
    assert "target_users" in data
    assert "core_functionality" in data

def test_parse_invalid_brief():
    """Test that parser raises error for invalid brief"""
    parser = BriefParser()

    with pytest.raises(ValueError, match="No feature name found"):
        parser.parse("Just some text without heading")

def test_parse_extracts_list_items_correctly(parser):
    """Test that parser correctly extracts both - and * list items"""
    brief = """# Feature Brief: Test

## Problem Statement
Test problem

## Core Functionality
- Item with dash
* Item with asterisk
- Another dash item
"""

    result = parser.parse(brief)
    assert len(result.core_functionality) == 3

def test_parse_handles_nested_lists(parser):
    """Test that parser handles nested list items"""
    brief = """# Feature Brief: Test

## Problem Statement
Test problem

## Core Functionality
- Parent item
  - Nested item
- Another parent
"""

    result = parser.parse(brief)
    assert len(result.core_functionality) >= 2

def test_parse_strips_markdown_formatting(parser):
    """Test that parser strips bold, italic from extracted text"""
    brief = """# Feature Brief: Test

## Problem Statement
This is **bold** and *italic* text.

## Core Functionality
- Feature with **emphasis**
"""

    result = parser.parse(brief)
    assert "**" not in result.problem_statement
    assert "*" not in result.core_functionality[0] or "emphasis" in result.core_functionality[0]
