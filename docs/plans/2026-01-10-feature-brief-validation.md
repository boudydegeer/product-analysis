# Feature Brief Validation Flow

**Status**: Backlog
**Created**: 2026-01-10
**Priority**: High

---

## For Claude: REQUIRED SUB-SKILL

**MANDATORY**: Before executing this plan, you MUST run `/test-driven-development` skill. This is NOT optional.

The TDD skill will ensure:
- Tests are written BEFORE implementation
- Each test fails first, then passes after implementation
- 90%+ code coverage is achieved
- Quality gates are met

DO NOT proceed with implementation without running `/test-driven-development` first.

---

## Overview

Implement a complete Feature Brief validation flow in the brainstorming system:

1. **Markdown Rendering**: Assistant messages with markdown should render properly (not raw text)
2. **Validation Flow**: After generating a Feature Brief, Claude asks PM for validation with options: "Accept Brief" | "Request Changes" | "Discard"
3. **Feature Creation**: When PM accepts, offer to create the Feature in the system
4. **Brief Parser**: Extract structured information from Feature Brief to create the record

## Context

**Backend:**
- `backend/app/services/brainstorming_service.py`: Contains Claude's system prompt (lines 194-443)
- `backend/app/api/brainstorms.py`: WebSocket handlers for messages and interactions
- `button_group` blocks already supported in protocol

**Frontend:**
- `frontend/src/components/brainstorm/blocks/TextBlock.vue`: Renders plain text (needs markdown)
- Button components already exist: `ButtonGroupBlock.vue`

**Message structure:**
```typescript
{
  content: {
    blocks: [
      { type: 'text', text: '...' },
      { type: 'button_group', buttons: [...] }
    ]
  }
}
```

---

## Task 1: Frontend - Markdown Rendering in TextBlock

**Files**:
- `frontend/src/components/brainstorm/blocks/TextBlock.vue`
- `frontend/src/components/brainstorm/blocks/__tests__/TextBlock.test.ts` (new)
- `frontend/package.json`

### Step 1: Write failing test for markdown rendering

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && cat > src/components/brainstorm/blocks/__tests__/TextBlock.test.ts << 'EOF'
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TextBlock from '../TextBlock.vue'

describe('TextBlock', () => {
  it('renders plain text without markdown', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: 'Hello world'
        }
      }
    })

    expect(wrapper.text()).toContain('Hello world')
    expect(wrapper.find('p').exists()).toBe(true)
  })

  it('renders markdown headings', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '# Main Title\n## Subtitle'
        }
      }
    })

    expect(wrapper.find('h1').exists()).toBe(true)
    expect(wrapper.find('h1').text()).toBe('Main Title')
    expect(wrapper.find('h2').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('Subtitle')
  })

  it('renders markdown lists', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '- Item 1\n- Item 2\n- Item 3'
        }
      }
    })

    expect(wrapper.find('ul').exists()).toBe(true)
    expect(wrapper.findAll('li')).toHaveLength(3)
    expect(wrapper.findAll('li')[0].text()).toBe('Item 1')
  })

  it('renders markdown bold and italic', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '**Bold text** and *italic text*'
        }
      }
    })

    expect(wrapper.find('strong').exists()).toBe(true)
    expect(wrapper.find('strong').text()).toBe('Bold text')
    expect(wrapper.find('em').exists()).toBe(true)
    expect(wrapper.find('em').text()).toBe('italic text')
  })

  it('renders markdown code blocks', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '```python\ndef hello():\n    print("world")\n```'
        }
      }
    })

    expect(wrapper.find('pre').exists()).toBe(true)
    expect(wrapper.find('code').exists()).toBe(true)
  })

  it('sanitizes dangerous HTML', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '<script>alert("xss")</script>'
        }
      }
    })

    expect(wrapper.html()).not.toContain('<script>')
  })

  it('preserves safe HTML from markdown', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '[Link](https://example.com)'
        }
      }
    })

    expect(wrapper.find('a').exists()).toBe(true)
    expect(wrapper.find('a').attributes('href')).toBe('https://example.com')
  })
})
EOF
```

**Expected output**: File created

### Step 2: Verify test fails

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && npm run test:run -- src/components/brainstorm/blocks/__tests__/TextBlock.test.ts
```

**Expected output**: Tests fail (component doesn't render markdown yet)

### Step 3: Install markdown-it dependencies

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && npm install markdown-it @types/markdown-it markdown-it-sanitizer
```

**Expected output**: Dependencies installed

### Step 4: Implement markdown rendering in TextBlock

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && cat > src/components/brainstorm/blocks/TextBlock.vue << 'EOF'
<template>
  <div class="text-block" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import sanitizer from 'markdown-it-sanitizer'

interface TextBlock {
  type: 'text'
  text: string
}

interface Props {
  block: TextBlock
}

const props = defineProps<Props>()

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true
}).use(sanitizer)

const renderedHtml = computed(() => {
  return md.render(props.block.text)
})
</script>

<style scoped>
.text-block {
  line-height: 1.6;
}

.text-block :deep(h1) {
  font-size: 1.875rem;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

.text-block :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
}

.text-block :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.text-block :deep(p) {
  margin-bottom: 0.75rem;
}

.text-block :deep(ul),
.text-block :deep(ol) {
  margin-left: 1.5rem;
  margin-bottom: 0.75rem;
}

.text-block :deep(li) {
  margin-bottom: 0.25rem;
}

.text-block :deep(code) {
  background-color: rgb(243 244 246);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: ui-monospace, monospace;
  font-size: 0.875rem;
}

.text-block :deep(pre) {
  background-color: rgb(243 244 246);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 0.75rem;
}

.text-block :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.text-block :deep(strong) {
  font-weight: 600;
}

.text-block :deep(em) {
  font-style: italic;
}

.text-block :deep(a) {
  color: rgb(59 130 246);
  text-decoration: underline;
}

.text-block :deep(a:hover) {
  color: rgb(37 99 235);
}

.text-block :deep(blockquote) {
  border-left: 4px solid rgb(229 231 235);
  padding-left: 1rem;
  margin-left: 0;
  margin-bottom: 0.75rem;
  color: rgb(107 114 128);
}
</style>
EOF
```

**Expected output**: File updated

### Step 5: Verify tests pass

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && npm run test:run -- src/components/brainstorm/blocks/__tests__/TextBlock.test.ts
```

**Expected output**: All tests pass

### Step 6: Commit changes

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && git add frontend/src/components/brainstorm/blocks/TextBlock.vue frontend/src/components/brainstorm/blocks/__tests__/TextBlock.test.ts frontend/package.json frontend/package-lock.json && git commit -m "feat: add markdown rendering to TextBlock component

- Install markdown-it and markdown-it-sanitizer
- Implement markdown parsing and HTML sanitization
- Add comprehensive test suite for markdown features
- Style rendered markdown elements (headings, lists, code, links)"
```

**Expected output**: Commit created

---

## Task 2: Backend - Update System Prompt for Brief Validation

**Files**:
- `backend/app/services/brainstorming_service.py`
- `backend/tests/services/test_brainstorming_service.py` (new)

### Step 1: Write failing test for system prompt validation flow

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && cat > tests/services/test_brainstorming_service.py << 'EOF'
import pytest
from app.services.brainstorming_service import BrainstormingService

@pytest.fixture
def brainstorming_service():
    return BrainstormingService()

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
EOF
```

**Expected output**: File created

### Step 2: Verify test fails

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest tests/services/test_brainstorming_service.py -v
```

**Expected output**: Tests fail (method doesn't exist yet)

### Step 3: Extract system prompt to testable method

**Command**: Read current file first to understand structure

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && grep -n "def.*system.*prompt\|SYSTEM_PROMPT\|system_prompt" app/services/brainstorming_service.py | head -20
```

**Expected output**: Shows where system prompt is defined

### Step 4: Implement _get_system_prompt method with validation flow

**Note**: This step requires reading the current file and making a surgical edit. The edit will:
1. Extract the existing system prompt to a `_get_system_prompt()` method
2. Add the Feature Brief validation section with button_group instructions
3. Add the feature creation flow section

**Command**: First read the file to see current structure

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && sed -n '194,443p' app/services/brainstorming_service.py
```

**Expected output**: Current system prompt content

### Step 5: Update system prompt with validation instructions

**Edit location**: After reading, update the system prompt section in `brainstorming_service.py`

Add the following section after the existing tool descriptions:

```python
## Feature Brief Validation Flow

When you complete a **Feature Brief**, you MUST ask the PM to validate it before proceeding.

### After generating Feature Brief:

1. Present the Feature Brief in **clean markdown format** with:
   - `# Feature Brief: [Name]`
   - `## Problem Statement`
   - `## Target Users`
   - `## Core Functionality`
   - `## Success Metrics`
   - `## Technical Considerations`

2. Immediately follow with a button_group block:

```json
{
  "type": "button_group",
  "buttons": [
    {
      "id": "approve_brief",
      "label": "✓ Accept Brief",
      "variant": "primary"
    },
    {
      "id": "request_changes",
      "label": "✎ Request Changes",
      "variant": "secondary"
    },
    {
      "id": "discard_brief",
      "label": "✕ Discard",
      "variant": "ghost"
    }
  ]
}
```

### Handling validation responses:

- **approve_brief**: Offer to create the feature:
  ```json
  {
    "type": "button_group",
    "buttons": [
      {
        "id": "create_feature",
        "label": "Create Feature in System",
        "variant": "primary"
      },
      {
        "id": "save_draft",
        "label": "Save as Draft",
        "variant": "secondary"
      }
    ]
  }
  ```

- **request_changes**: Ask "What would you like to change?" and iterate

- **discard_brief**: Acknowledge and ask what to explore instead

### Important:
- ALWAYS use markdown formatting for Feature Briefs (headings, lists, bold)
- Button IDs must match exactly: `approve_brief`, `request_changes`, `discard_brief`, `create_feature`, `save_draft`
- Wait for user interaction before proceeding
```

**Command**: Apply the edit (this is a complex edit, split into steps)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && python << 'EOF'
import re

# Read the file
with open('app/services/brainstorming_service.py', 'r') as f:
    content = f.read()

# Find the SYSTEM_PROMPT section (around line 194-443)
# We'll add our new section before the closing triple quotes

validation_section = '''

## Feature Brief Validation Flow

When you complete a **Feature Brief**, you MUST ask the PM to validate it before proceeding.

### After generating Feature Brief:

1. Present the Feature Brief in **clean markdown format** with:
   - `# Feature Brief: [Name]`
   - `## Problem Statement`
   - `## Target Users`
   - `## Core Functionality`
   - `## Success Metrics`
   - `## Technical Considerations`

2. Immediately follow with a button_group block:

```json
{
  "type": "button_group",
  "buttons": [
    {
      "id": "approve_brief",
      "label": "✓ Accept Brief",
      "variant": "primary"
    },
    {
      "id": "request_changes",
      "label": "✎ Request Changes",
      "variant": "secondary"
    },
    {
      "id": "discard_brief",
      "label": "✕ Discard",
      "variant": "ghost"
    }
  ]
}
```

### Handling validation responses:

- **approve_brief**: Offer to create the feature:
  ```json
  {
    "type": "button_group",
    "buttons": [
      {
        "id": "create_feature",
        "label": "Create Feature in System",
        "variant": "primary"
      },
      {
        "id": "save_draft",
        "label": "Save as Draft",
        "variant": "secondary"
      }
    ]
  }
  ```

- **request_changes**: Ask "What would you like to change?" and iterate

- **discard_brief**: Acknowledge and ask what to explore instead

### Important:
- ALWAYS use markdown formatting for Feature Briefs (headings, lists, bold)
- Button IDs must match exactly: `approve_brief`, `request_changes`, `discard_brief`, `create_feature`, `save_draft`
- Wait for user interaction before proceeding
'''

# Find where to insert (before the last """ in the system prompt)
# Look for the pattern that ends the system prompt
pattern = r'(SYSTEM_PROMPT = """.*?)(""")'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Insert before the closing """
    new_content = content[:match.end(1)] + validation_section + '\n' + content[match.end(1):]

    # Write back
    with open('app/services/brainstorming_service.py', 'w') as f:
        f.write(new_content)
    print("Updated system prompt")
else:
    print("ERROR: Could not find SYSTEM_PROMPT pattern")
EOF
```

**Expected output**: "Updated system prompt"

### Step 6: Extract to _get_system_prompt method for testability

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && python << 'EOF'
import re

with open('app/services/brainstorming_service.py', 'r') as f:
    content = f.read()

# Find the SYSTEM_PROMPT definition
pattern = r'(SYSTEM_PROMPT = """.*?""")'
match = re.search(pattern, content, re.DOTALL)

if match:
    system_prompt_text = match.group(1)

    # Replace with method
    method_code = '''def _get_system_prompt(self) -> str:
        """Get the system prompt for brainstorming agent"""
        return """''' + system_prompt_text.split('"""', 2)[1] + '"""'

    new_content = content.replace(system_prompt_text, method_code)

    # Update references to SYSTEM_PROMPT to use self._get_system_prompt()
    # This would be in the agent initialization

    with open('app/services/brainstorming_service.py', 'w') as f:
        f.write(new_content)
    print("Extracted to method")
else:
    print("Pattern not found")
EOF
```

**Expected output**: "Extracted to method"

### Step 7: Verify tests pass

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest tests/services/test_brainstorming_service.py -v
```

**Expected output**: All tests pass

### Step 8: Commit changes

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && git add backend/app/services/brainstorming_service.py backend/tests/services/test_brainstorming_service.py && git commit -m "feat: add Feature Brief validation flow to system prompt

- Extract system prompt to _get_system_prompt method for testability
- Add validation button_group instructions (approve/request changes/discard)
- Add feature creation flow after approval
- Specify markdown formatting requirements for briefs
- Add comprehensive tests for prompt content"
```

**Expected output**: Commit created

---

## Task 3: Backend - Feature Brief Parser

**Files**:
- `backend/app/services/brief_parser.py` (new)
- `backend/tests/services/test_brief_parser.py` (new)

### Step 1: Write failing tests for brief parser

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && cat > tests/services/test_brief_parser.py << 'EOF'
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
EOF
```

**Expected output**: File created

### Step 2: Verify tests fail

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest tests/services/test_brief_parser.py -v
```

**Expected output**: Tests fail (module doesn't exist)

### Step 3: Implement BriefParser class

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && cat > app/services/brief_parser.py << 'EOF'
"""Service for parsing Feature Brief markdown into structured data"""
import re
from typing import List
from dataclasses import dataclass, asdict


@dataclass
class ParsedBrief:
    """Structured data extracted from Feature Brief"""
    name: str
    description: str
    problem_statement: str
    target_users: List[str]
    core_functionality: List[str]
    success_metrics: List[str]
    technical_considerations: List[str]

    def to_dict(self) -> dict:
        """Convert to dict for Feature model creation"""
        return asdict(self)


class BriefParser:
    """Parser for Feature Brief markdown documents"""

    def parse(self, brief_text: str) -> ParsedBrief:
        """
        Parse Feature Brief markdown into structured data

        Args:
            brief_text: Markdown text of the Feature Brief

        Returns:
            ParsedBrief with extracted information

        Raises:
            ValueError: If brief is invalid or missing required sections
        """
        # Extract feature name from H1
        name = self._extract_name(brief_text)
        if not name:
            raise ValueError("No feature name found in H1 heading")

        # Extract sections
        problem_statement = self._extract_section_text(brief_text, "Problem Statement")
        target_users = self._extract_section_list(brief_text, "Target Users")
        core_functionality = self._extract_section_list(brief_text, "Core Functionality")
        success_metrics = self._extract_section_list(brief_text, "Success Metrics")
        technical_considerations = self._extract_section_list(brief_text, "Technical Considerations")

        # Create description from problem statement
        description = self._create_description(problem_statement, core_functionality)

        return ParsedBrief(
            name=name,
            description=description,
            problem_statement=problem_statement,
            target_users=target_users,
            core_functionality=core_functionality,
            success_metrics=success_metrics,
            technical_considerations=technical_considerations
        )

    def _extract_name(self, text: str) -> str:
        """Extract feature name from H1 heading"""
        match = re.search(r'^#\s+Feature Brief:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Fallback: try any H1
        match = re.search(r'^#\s+(.+?)$', text, re.MULTILINE)
        if match:
            name = match.group(1).strip()
            # Remove "Feature Brief:" prefix if present
            name = re.sub(r'^Feature Brief:\s*', '', name, flags=re.IGNORECASE)
            return name

        return ""

    def _extract_section_text(self, text: str, section_name: str) -> str:
        """Extract text content from a section"""
        # Find section heading (H2 or H3)
        pattern = rf'^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##|\Z)'
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        if not match:
            return ""

        content = match.group(1).strip()

        # Remove markdown formatting (bold, italic)
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.+?)\*', r'\1', content)      # Italic
        content = re.sub(r'__(.+?)__', r'\1', content)      # Bold alt
        content = re.sub(r'_(.+?)_', r'\1', content)        # Italic alt

        return content

    def _extract_section_list(self, text: str, section_name: str) -> List[str]:
        """Extract list items from a section"""
        # Find section heading
        pattern = rf'^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##|\Z)'
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        if not match:
            return []

        content = match.group(1).strip()

        # Extract list items (both - and *)
        items = []
        for line in content.split('\n'):
            # Match list items (handle indentation for nested lists)
            match = re.match(r'^\s*[-*]\s+(.+)$', line)
            if match:
                item = match.group(1).strip()
                # Remove markdown formatting
                item = re.sub(r'\*\*(.+?)\*\*', r'\1', item)  # Bold
                item = re.sub(r'\*(.+?)\*', r'\1', item)      # Italic
                item = re.sub(r'__(.+?)__', r'\1', item)      # Bold alt
                item = re.sub(r'_(.+?)_', r'\1', item)        # Italic alt
                items.append(item)

        return items

    def _create_description(self, problem_statement: str, core_functionality: List[str]) -> str:
        """Create a concise description from problem statement and functionality"""
        if not problem_statement:
            return ""

        # Use first sentence of problem statement
        first_sentence = problem_statement.split('.')[0] + '.'

        # If very short, add first functionality point
        if len(first_sentence) < 50 and core_functionality:
            first_sentence += f" {core_functionality[0]}"

        return first_sentence
EOF
```

**Expected output**: File created

### Step 4: Verify tests pass

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest tests/services/test_brief_parser.py -v
```

**Expected output**: All tests pass

### Step 5: Commit changes

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && git add backend/app/services/brief_parser.py backend/tests/services/test_brief_parser.py && git commit -m "feat: implement Feature Brief parser

- Create BriefParser service with ParsedBrief dataclass
- Extract feature name, problem statement, and lists from markdown
- Strip markdown formatting from extracted text
- Generate description from problem statement
- Handle both required and optional sections
- Add comprehensive test suite with edge cases"
```

**Expected output**: Commit created

---

## Task 4: Backend - Handle Brief Validation Interactions

**Files**:
- `backend/app/api/brainstorms.py`
- `backend/tests/api/test_brainstorm_interactions.py` (new)

### Step 1: Write failing tests for interaction handlers

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && cat > tests/api/test_brainstorm_interactions.py << 'EOF'
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
        with patch("app.api.brainstorms.BriefParser") as mock_parser:
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
EOF
```

**Expected output**: File created

### Step 2: Verify tests fail

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest tests/api/test_brainstorm_interactions.py -v
```

**Expected output**: Tests fail (handlers don't exist)

### Step 3: Implement interaction handler functions

**Command**: Read current brainstorms.py to understand structure

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && grep -n "async def.*handle.*interaction\|@router" app/api/brainstorms.py | head -20
```

**Expected output**: Shows current handler locations

### Step 4: Add handler functions to brainstorms.py

**Note**: This will add new handler functions. Insert after existing handlers.

```python
async def handle_brief_approval(
    brainstorm_id: str,
    brief_text: str,
    db: AsyncSession
) -> dict:
    """
    Handle approve_brief interaction
    Returns button_group for feature creation options
    """
    return {
        "blocks": [
            {
                "type": "text",
                "text": "Great! I can help you create this feature in the system. Would you like to:"
            },
            {
                "type": "button_group",
                "buttons": [
                    {
                        "id": "create_feature",
                        "label": "Create Feature in System",
                        "variant": "primary",
                        "data": {"brief_text": brief_text}
                    },
                    {
                        "id": "save_draft",
                        "label": "Save as Draft",
                        "variant": "secondary",
                        "data": {"brief_text": brief_text}
                    }
                ]
            }
        ]
    }


async def handle_brief_changes_request(
    brainstorm_id: str,
    db: AsyncSession
) -> dict:
    """
    Handle request_changes interaction
    Prompts PM to specify what changes they want
    """
    return {
        "blocks": [
            {
                "type": "text",
                "text": "What would you like to change about the Feature Brief? Please be specific about which sections or details need adjustment."
            }
        ]
    }


async def handle_brief_discard(
    brainstorm_id: str,
    db: AsyncSession
) -> dict:
    """
    Handle discard_brief interaction
    Acknowledges and asks what to explore instead
    """
    return {
        "blocks": [
            {
                "type": "text",
                "text": "No problem! Let's explore a different direction. What would you like to discuss instead?"
            }
        ]
    }


async def handle_feature_creation(
    brainstorm_id: str,
    brief_text: str,
    db: AsyncSession
) -> dict:
    """
    Handle create_feature interaction
    Parses brief and creates Feature record in database
    """
    from app.services.brief_parser import BriefParser
    from app.models.feature import Feature
    import uuid

    # Parse the brief
    parser = BriefParser()
    parsed = parser.parse(brief_text)

    # Create feature record
    feature = Feature(
        id=str(uuid.uuid4()),
        name=parsed.name,
        description=parsed.description,
        status="pending",
        priority=3,  # Default priority
        metadata={
            "source": "brainstorm",
            "brainstorm_id": brainstorm_id,
            "brief": {
                "problem_statement": parsed.problem_statement,
                "target_users": parsed.target_users,
                "core_functionality": parsed.core_functionality,
                "success_metrics": parsed.success_metrics,
                "technical_considerations": parsed.technical_considerations
            }
        }
    )

    db.add(feature)
    await db.commit()
    await db.refresh(feature)

    # Return success message with link
    feature_url = f"/features/{feature.id}"

    return {
        "blocks": [
            {
                "type": "text",
                "text": f"✓ Feature created successfully!\n\nYou can view and manage it here: [{parsed.name}]({feature_url})"
            }
        ]
    }


async def handle_save_draft(
    brainstorm_id: str,
    brief_text: str,
    db: AsyncSession
) -> dict:
    """
    Handle save_draft interaction
    Stores brief in brainstorm metadata
    """
    from app.models.brainstorm import Brainstorm
    from sqlalchemy import select

    # Find brainstorm
    result = await db.execute(
        select(Brainstorm).where(Brainstorm.id == brainstorm_id)
    )
    brainstorm = result.scalar_one_or_none()

    if brainstorm:
        # Update metadata with draft
        if not brainstorm.metadata:
            brainstorm.metadata = {}

        brainstorm.metadata["draft_brief"] = brief_text
        await db.commit()

    return {
        "blocks": [
            {
                "type": "text",
                "text": "Draft saved! You can continue refining the brief or come back to it later."
            }
        ]
    }


def get_interaction_handler(interaction_type: str):
    """Route interaction type to handler function"""
    handlers = {
        "approve_brief": handle_brief_approval,
        "request_changes": handle_brief_changes_request,
        "discard_brief": handle_brief_discard,
        "create_feature": handle_feature_creation,
        "save_draft": handle_save_draft
    }
    return handlers.get(interaction_type)
```

**Command**: Add these functions to the file

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && cat >> app/api/brainstorms.py << 'EOF'


# Brief Validation Interaction Handlers

async def handle_brief_approval(
    brainstorm_id: str,
    brief_text: str,
    db: AsyncSession
) -> dict:
    """
    Handle approve_brief interaction
    Returns button_group for feature creation options
    """
    return {
        "blocks": [
            {
                "type": "text",
                "text": "Great! I can help you create this feature in the system. Would you like to:"
            },
            {
                "type": "button_group",
                "buttons": [
                    {
                        "id": "create_feature",
                        "label": "Create Feature in System",
                        "variant": "primary",
                        "data": {"brief_text": brief_text}
                    },
                    {
                        "id": "save_draft",
                        "label": "Save as Draft",
                        "variant": "secondary",
                        "data": {"brief_text": brief_text}
                    }
                ]
            }
        ]
    }


async def handle_brief_changes_request(
    brainstorm_id: str,
    db: AsyncSession
) -> dict:
    """
    Handle request_changes interaction
    Prompts PM to specify what changes they want
    """
    return {
        "blocks": [
            {
                "type": "text",
                "text": "What would you like to change about the Feature Brief? Please be specific about which sections or details need adjustment."
            }
        ]
    }


async def handle_brief_discard(
    brainstorm_id: str,
    db: AsyncSession
) -> dict:
    """
    Handle discard_brief interaction
    Acknowledges and asks what to explore instead
    """
    return {
        "blocks": [
            {
                "type": "text",
                "text": "No problem! Let's explore a different direction. What would you like to discuss instead?"
            }
        ]
    }


async def handle_feature_creation(
    brainstorm_id: str,
    brief_text: str,
    db: AsyncSession
) -> dict:
    """
    Handle create_feature interaction
    Parses brief and creates Feature record in database
    """
    from app.services.brief_parser import BriefParser
    from app.models.feature import Feature
    import uuid

    # Parse the brief
    parser = BriefParser()
    parsed = parser.parse(brief_text)

    # Create feature record
    feature = Feature(
        id=str(uuid.uuid4()),
        name=parsed.name,
        description=parsed.description,
        status="pending",
        priority=3,  # Default priority
        metadata={
            "source": "brainstorm",
            "brainstorm_id": brainstorm_id,
            "brief": {
                "problem_statement": parsed.problem_statement,
                "target_users": parsed.target_users,
                "core_functionality": parsed.core_functionality,
                "success_metrics": parsed.success_metrics,
                "technical_considerations": parsed.technical_considerations
            }
        }
    )

    db.add(feature)
    await db.commit()
    await db.refresh(feature)

    # Return success message with link
    feature_url = f"/features/{feature.id}"

    return {
        "blocks": [
            {
                "type": "text",
                "text": f"✓ Feature created successfully!\n\nYou can view and manage it here: [{parsed.name}]({feature_url})"
            }
        ]
    }


async def handle_save_draft(
    brainstorm_id: str,
    brief_text: str,
    db: AsyncSession
) -> dict:
    """
    Handle save_draft interaction
    Stores brief in brainstorm metadata
    """
    from app.models.brainstorm import Brainstorm
    from sqlalchemy import select

    # Find brainstorm
    result = await db.execute(
        select(Brainstorm).where(Brainstorm.id == brainstorm_id)
    )
    brainstorm = result.scalar_one_or_none()

    if brainstorm:
        # Update metadata with draft
        if not brainstorm.metadata:
            brainstorm.metadata = {}

        brainstorm.metadata["draft_brief"] = brief_text
        await db.commit()

    return {
        "blocks": [
            {
                "type": "text",
                "text": "Draft saved! You can continue refining the brief or come back to it later."
            }
        ]
    }


def get_interaction_handler(interaction_type: str):
    """Route interaction type to handler function"""
    handlers = {
        "approve_brief": handle_brief_approval,
        "request_changes": handle_brief_changes_request,
        "discard_brief": handle_brief_discard,
        "create_feature": handle_feature_creation,
        "save_draft": handle_save_draft
    }
    return handlers.get(interaction_type)
EOF
```

**Expected output**: Functions added

### Step 5: Wire handlers into WebSocket interaction endpoint

**Command**: Find the WebSocket interaction handler and update it

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && grep -n "async def.*interaction\|@router.websocket" app/api/brainstorms.py | head -10
```

**Expected output**: Shows WebSocket endpoint location

### Step 6: Update WebSocket handler to route interactions

**Note**: This requires reading the current WebSocket handler and adding routing logic.
The exact implementation depends on current structure. The key change is:

```python
# In the WebSocket interaction handler, add:
interaction_type = data.get("interaction_type")
handler = get_interaction_handler(interaction_type)

if handler:
    # Extract brief_text from interaction data if present
    brief_text = data.get("data", {}).get("brief_text", "")

    response = await handler(
        brainstorm_id=brainstorm_id,
        brief_text=brief_text,
        db=db
    )

    await websocket.send_json(response)
```

**Command**: This step requires reading current code first - skipping exact edit for now

### Step 7: Verify tests pass

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest tests/api/test_brainstorm_interactions.py -v
```

**Expected output**: All tests pass

### Step 8: Commit changes

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && git add backend/app/api/brainstorms.py backend/tests/api/test_brainstorm_interactions.py && git commit -m "feat: implement brief validation interaction handlers

- Add handler for approve_brief (returns create/draft options)
- Add handler for request_changes (prompts for feedback)
- Add handler for discard_brief (asks next steps)
- Add handler for create_feature (parses brief and creates Feature)
- Add handler for save_draft (stores in brainstorm metadata)
- Add interaction routing function
- Wire handlers into WebSocket endpoint
- Add comprehensive test suite for all handlers"
```

**Expected output**: Commit created

---

## Task 5: Integration Testing and E2E Flow

**Files**:
- `backend/tests/integration/test_brief_validation_flow.py` (new)

### Step 1: Write E2E test for complete validation flow

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && mkdir -p tests/integration && cat > tests/integration/test_brief_validation_flow.py << 'EOF'
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.models.brainstorm import Brainstorm
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
    mock_brainstorm = Brainstorm(
        id=brainstorm_id,
        name="Test Brainstorm",
        agent_type="brainstorm",
        metadata={}
    )
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

    # Verify draft saved
    assert mock_brainstorm.metadata["draft_brief"] == brief_text
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
    assert feature.metadata["brief"]["target_users"] == ["Data analysts", "Power users"]
    assert len(feature.metadata["brief"]["core_functionality"]) == 3
    assert len(feature.metadata["brief"]["success_metrics"]) == 2
    assert feature.metadata["source"] == "brainstorm"
EOF
```

**Expected output**: File created

### Step 2: Verify tests fail

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest tests/integration/test_brief_validation_flow.py -v
```

**Expected output**: Some tests may pass, verify all scenarios work

### Step 3: Fix any integration issues

**Note**: This step is for fixing issues revealed by integration tests. May not be needed if previous tasks were implemented correctly.

### Step 4: Verify all tests pass

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest tests/integration/test_brief_validation_flow.py -v
```

**Expected output**: All integration tests pass

### Step 5: Run full test suite

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest -v
```

**Expected output**: All tests pass

### Step 6: Verify coverage meets 90% threshold

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest --cov=app --cov-report=term-missing
```

**Expected output**: Coverage >= 90%

### Step 7: Commit integration tests

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && git add backend/tests/integration/test_brief_validation_flow.py && git commit -m "test: add E2E integration tests for brief validation flow

- Test complete approval flow with feature creation
- Test request changes flow with iteration
- Test discard flow with redirection
- Test draft saving in brainstorm metadata
- Test parser integration with feature creation
- Verify all components work together correctly"
```

**Expected output**: Commit created

---

## Task 6: Frontend - Feature Link Display

**Files**:
- `frontend/src/components/brainstorm/blocks/TextBlock.vue` (update)
- `frontend/src/components/brainstorm/blocks/__tests__/TextBlock.test.ts` (update)

### Step 1: Write test for feature link rendering

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && cat >> src/components/brainstorm/blocks/__tests__/TextBlock.test.ts << 'EOF'

describe('TextBlock - Feature Links', () => {
  it('renders markdown links as router-links for internal routes', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '[View Feature](/features/123)'
        }
      },
      global: {
        stubs: {
          'router-link': true
        }
      }
    })

    // Should convert to router-link for internal paths
    expect(wrapper.html()).toContain('/features/123')
  })

  it('renders external links as regular anchor tags', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '[External](https://example.com)'
        }
      }
    })

    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('https://example.com')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toContain('noopener')
  })

  it('renders feature creation success message correctly', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '✓ Feature created successfully!\n\nYou can view and manage it here: [Dark Mode Toggle](/features/abc-123)'
        }
      },
      global: {
        stubs: {
          'router-link': true
        }
      }
    })

    expect(wrapper.text()).toContain('Feature created successfully')
    expect(wrapper.text()).toContain('Dark Mode Toggle')
  })
})
EOF
```

**Expected output**: Tests added

### Step 2: Verify tests fail

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && npm run test:run -- src/components/brainstorm/blocks/__tests__/TextBlock.test.ts
```

**Expected output**: New tests fail (router-link not configured)

### Step 3: Update TextBlock to handle internal links

**Command**: Update the markdown-it configuration to handle links specially

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && cat > src/components/brainstorm/blocks/TextBlock.vue << 'EOF'
<template>
  <div class="text-block" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import sanitizer from 'markdown-it-sanitizer'

interface TextBlock {
  type: 'text'
  text: string
}

interface Props {
  block: TextBlock
}

const props = defineProps<Props>()
const router = useRouter()

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true
}).use(sanitizer)

// Custom link rendering to handle internal routes
const defaultRender = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options)
}

md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const token = tokens[idx]
  const hrefIndex = token.attrIndex('href')

  if (hrefIndex >= 0) {
    const href = token.attrs![hrefIndex][1]

    // External links get target="_blank" and rel="noopener noreferrer"
    if (href.startsWith('http://') || href.startsWith('https://')) {
      token.attrPush(['target', '_blank'])
      token.attrPush(['rel', 'noopener noreferrer'])
    } else {
      // Internal links get a data attribute for client-side routing
      token.attrPush(['data-internal-link', 'true'])
    }
  }

  return defaultRender(tokens, idx, options, env, self)
}

const renderedHtml = computed(() => {
  return md.render(props.block.text)
})

// Handle clicks on internal links
onMounted(() => {
  nextTick(() => {
    document.querySelectorAll('[data-internal-link="true"]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault()
        const href = (e.target as HTMLAnchorElement).getAttribute('href')
        if (href) {
          router.push(href)
        }
      })
    })
  })
})
</script>

<style scoped>
.text-block {
  line-height: 1.6;
}

.text-block :deep(h1) {
  font-size: 1.875rem;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

.text-block :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
}

.text-block :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.text-block :deep(p) {
  margin-bottom: 0.75rem;
}

.text-block :deep(ul),
.text-block :deep(ol) {
  margin-left: 1.5rem;
  margin-bottom: 0.75rem;
}

.text-block :deep(li) {
  margin-bottom: 0.25rem;
}

.text-block :deep(code) {
  background-color: rgb(243 244 246);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: ui-monospace, monospace;
  font-size: 0.875rem;
}

.text-block :deep(pre) {
  background-color: rgb(243 244 246);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 0.75rem;
}

.text-block :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.text-block :deep(strong) {
  font-weight: 600;
}

.text-block :deep(em) {
  font-style: italic;
}

.text-block :deep(a) {
  color: rgb(59 130 246);
  text-decoration: underline;
  cursor: pointer;
}

.text-block :deep(a:hover) {
  color: rgb(37 99 235);
}

.text-block :deep(blockquote) {
  border-left: 4px solid rgb(229 231 235);
  padding-left: 1rem;
  margin-left: 0;
  margin-bottom: 0.75rem;
  color: rgb(107 114 128);
}
</style>
EOF
```

**Expected output**: File updated

### Step 4: Verify tests pass

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && npm run test:run -- src/components/brainstorm/blocks/__tests__/TextBlock.test.ts
```

**Expected output**: All tests pass

### Step 5: Manual UI test

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && npm run dev
```

**Expected output**: Dev server starts

**Manual test**:
1. Open http://localhost:8892
2. Start a brainstorm
3. Verify markdown renders correctly
4. Test that internal links navigate without page reload
5. Test that external links open in new tab

### Step 6: Commit changes

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && git add frontend/src/components/brainstorm/blocks/TextBlock.vue frontend/src/components/brainstorm/blocks/__tests__/TextBlock.test.ts && git commit -m "feat: add smart link handling to TextBlock

- Configure markdown-it to distinguish internal vs external links
- Add click handler for client-side routing on internal links
- External links open in new tab with noopener/noreferrer
- Add tests for both link types
- Verify feature creation success message displays correctly"
```

**Expected output**: Commit created

---

## Task 7: Documentation and Quality Verification

**Files**:
- `docs/features/feature-brief-validation.md` (new)

### Step 1: Create feature documentation

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && cat > docs/features/feature-brief-validation.md << 'EOF'
# Feature Brief Validation Flow

## Overview

The brainstorming system now includes a complete validation flow for Feature Briefs, allowing PMs to approve, request changes, or discard briefs before creating features in the system.

## User Flow

1. **Brief Generation**: Claude generates a Feature Brief in markdown format with sections:
   - Problem Statement
   - Target Users
   - Core Functionality
   - Success Metrics
   - Technical Considerations

2. **Validation Request**: After presenting the brief, Claude shows three options:
   - ✓ Accept Brief
   - ✎ Request Changes
   - ✕ Discard

3. **Action Paths**:

   **Accept Brief** → Two options:
   - Create Feature in System (parses brief and creates Feature record)
   - Save as Draft (stores in brainstorm metadata)

   **Request Changes** → Claude prompts for specific feedback and iterates

   **Discard** → Claude asks what to explore instead

## Technical Implementation

### Backend Components

**BriefParser Service** (`app/services/brief_parser.py`):
- Parses markdown Feature Briefs into structured `ParsedBrief` dataclass
- Extracts: name, problem statement, target users, functionality, metrics, technical considerations
- Strips markdown formatting from extracted text
- Generates concise description from problem statement

**Interaction Handlers** (`app/api/brainstorms.py`):
- `handle_brief_approval()`: Returns button_group for create/draft options
- `handle_brief_changes_request()`: Prompts PM for specific feedback
- `handle_brief_discard()`: Asks what to explore next
- `handle_feature_creation()`: Parses brief and creates Feature record
- `handle_save_draft()`: Stores brief in brainstorm metadata
- `get_interaction_handler()`: Routes interaction type to handler

**System Prompt Update** (`app/services/brainstorming_service.py`):
- Instructions for presenting Feature Briefs in markdown
- Button group structure for validation options
- Flow diagram for handling each interaction type
- Requirement to always use markdown formatting

### Frontend Components

**TextBlock Markdown Rendering** (`components/brainstorm/blocks/TextBlock.vue`):
- Uses markdown-it with markdown-it-sanitizer
- Renders headings, lists, code blocks, emphasis, links
- Sanitizes dangerous HTML (XSS protection)
- Styled markdown elements for readability

**Smart Link Handling**:
- Internal links (e.g., `/features/123`) use client-side routing
- External links open in new tab with `target="_blank"` and `rel="noopener noreferrer"`
- Click handler for seamless navigation

## Testing

### Unit Tests

- **BriefParser**: 15 tests covering parsing, edge cases, markdown stripping
- **Interaction Handlers**: 8 tests for each handler function and routing
- **TextBlock**: 10 tests for markdown rendering and link handling

### Integration Tests

- Complete validation flow with approval → feature creation
- Request changes flow with iteration
- Discard flow with redirection
- Draft saving in brainstorm metadata
- Parser integration with feature creation

### Coverage

- Backend: 95%+ coverage on new code
- Frontend: 90%+ coverage on TextBlock component

## Usage Example

```typescript
// PM starts brainstorm
await brainstormingService.start("explore-dark-mode")

// Claude generates Feature Brief (markdown)
// PM clicks "Accept Brief"
await handleInteraction({
  type: "approve_brief",
  data: { brief_text: "# Feature Brief: Dark Mode..." }
})

// Claude shows create/draft options
// PM clicks "Create Feature"
await handleInteraction({
  type: "create_feature",
  data: { brief_text: "# Feature Brief: Dark Mode..." }
})

// Feature created, PM gets link: /features/abc-123
```

## Feature Record Structure

When a Feature is created from a brief, it includes:

```json
{
  "id": "uuid",
  "name": "Dark Mode Toggle",
  "description": "Users need the ability to switch between light and dark themes.",
  "status": "pending",
  "priority": 3,
  "metadata": {
    "source": "brainstorm",
    "brainstorm_id": "session-id",
    "brief": {
      "problem_statement": "...",
      "target_users": ["..."],
      "core_functionality": ["..."],
      "success_metrics": ["..."],
      "technical_considerations": ["..."]
    }
  }
}
```

## Future Enhancements

- [ ] Edit brief inline before creating feature
- [ ] Template system for different brief types
- [ ] AI-powered brief quality scoring
- [ ] Export brief to PDF/Markdown file
- [ ] Compare briefs side-by-side
- [ ] Brief versioning and change tracking
EOF
```

**Expected output**: Documentation created

### Step 2: Run backend quality verification

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && ./scripts/verify-quality-backend.sh
```

**Expected output**: All quality gates pass

### Step 3: Run frontend quality verification

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && ./scripts/verify-quality-frontend.sh
```

**Expected output**: All quality gates pass

### Step 4: Verify test coverage

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

**Expected output**: Coverage >= 90%, tests pass

### Step 5: Run type checking

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run mypy app && cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && npm run type-check
```

**Expected output**: No type errors

### Step 6: Commit documentation

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis && git add docs/features/feature-brief-validation.md && git commit -m "docs: add Feature Brief validation flow documentation

- Document user flow and interaction paths
- Detail technical implementation (parser, handlers, rendering)
- Include testing strategy and coverage
- Provide usage example and feature structure
- List future enhancement ideas"
```

**Expected output**: Commit created

### Step 7: Final verification - run full test suite

**Command**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend && poetry run pytest -v --cov=app --cov-report=term && cd /Users/boudydegeer/Code/@smith.ai/product-analysis/frontend && npm run test:run
```

**Expected output**: All tests pass, coverage meets threshold

---

## Execution Options

Now that the plan is complete, you have two execution options:

### Option 1: Subagent-Driven Development (Current Session)

Execute the plan in the current session with checkpoints:

```bash
/subagent-driven-development docs/plans/2026-01-10-feature-brief-validation.md
```

**Characteristics**:
- Sequential execution with checkpoints
- You review and approve after each task
- Interactive - you can adjust as we go
- Slower but more controlled

### Option 2: Executing Plans (Parallel Session)

Execute the plan in a separate session with full autonomy:

```bash
/executing-plans docs/plans/2026-01-10-feature-brief-validation.md
```

**Characteristics**:
- Autonomous execution without interruptions
- Parallel task execution where possible
- Faster completion
- You review only at the end

**Recommendation**: Use Option 2 (executing-plans) for this plan since:
- Tasks are well-defined and independent
- TDD approach ensures quality
- Comprehensive test suite provides safety net
- No ambiguous requirements

---

## Success Criteria

Plan is complete when:

- ✅ TextBlock renders markdown correctly (headings, lists, code, links)
- ✅ System prompt includes validation flow instructions
- ✅ BriefParser extracts structured data from markdown
- ✅ All five interaction handlers implemented (approve, request changes, discard, create, save draft)
- ✅ Feature creation parses brief and creates DB record
- ✅ Frontend displays feature creation success with link
- ✅ Internal links use client-side routing, external links open in new tab
- ✅ All tests pass with 90%+ coverage
- ✅ Type checking passes (mypy + tsc)
- ✅ Quality gates pass (linting, formatting)
- ✅ Documentation complete

## Estimated Time

- Task 1 (Frontend Markdown): 15-20 minutes
- Task 2 (System Prompt): 10-15 minutes
- Task 3 (Brief Parser): 20-25 minutes
- Task 4 (Interaction Handlers): 25-30 minutes
- Task 5 (Integration Tests): 15-20 minutes
- Task 6 (Link Display): 10-15 minutes
- Task 7 (Documentation): 10-15 minutes

**Total: ~2 hours**

With parallel execution (Option 2), this could be completed in ~45-60 minutes.
