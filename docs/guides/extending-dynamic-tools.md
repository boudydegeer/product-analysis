# Extending the Dynamic Tools System

**Quick Start Guide for Adding New Agents and Tools**

This guide provides step-by-step instructions for extending the Dynamic Tools System with new agents and tools. Perfect for product managers, developers, and AI engineers who want to customize the platform.

---

## Table of Contents

1. [Adding a New Agent](#adding-a-new-agent)
2. [Adding a New Tool](#adding-a-new-tool)
3. [Assigning Tools to Agents](#assigning-tools-to-agents)
4. [Testing Your Changes](#testing-your-changes)
5. [Common Patterns](#common-patterns)
6. [Troubleshooting](#troubleshooting)

---

## Adding a New Agent

### Option 1: Using Python Script (Recommended)

Create a new file `backend/scripts/add_code_reviewer_agent.py`:

```python
"""Add Code Reviewer agent to the system."""
import asyncio
from app.database import async_session_maker
from app.models.agent import AgentType

async def add_code_reviewer():
    """Add Code Reviewer agent."""
    async with async_session_maker() as db:
        # Check if agent already exists
        from sqlalchemy import select
        result = await db.execute(
            select(AgentType).where(AgentType.name == "code_reviewer")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("✅ Code Reviewer agent already exists")
            return existing

        # Create new agent
        agent = AgentType(
            name="code_reviewer",
            display_name="Rita the Reviewer 👩‍💻",
            description="Expert code reviewer focused on best practices, security, and maintainability",
            avatar_url="👩‍💻",  # Emoji avatar
            avatar_color="#3b82f6",  # Blue
            personality_traits=[
                "analytical",
                "thorough",
                "constructive",
                "security-focused",
                "detail-oriented"
            ],
            model="claude-opus-4-5",  # Use Opus for deeper analysis
            system_prompt="""You are Rita, an expert code reviewer with 15+ years of experience.

Your role is to:
- Review code for bugs, security issues, and performance problems
- Suggest improvements following best practices
- Explain your reasoning clearly and constructively
- Provide actionable feedback with examples
- Balance perfectionism with pragmatism

Review style:
- Start with what's good about the code
- Group feedback by category (bugs, security, performance, style)
- Prioritize issues (critical, important, nice-to-have)
- Provide specific code examples for suggestions
- Be encouraging while maintaining high standards""",
            temperature=0.3,  # Lower temperature for analytical tasks
            streaming_enabled=True,
            max_context_tokens=200000,
            enabled=True,
            is_default=False,
        )

        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        print(f"✅ Created Code Reviewer agent (ID: {agent.id})")
        return agent

if __name__ == "__main__":
    asyncio.run(add_code_reviewer())
```

**Run the script:**
```bash
cd backend
poetry run python scripts/add_code_reviewer_agent.py
```

### Option 2: Using SQL (Quick)

```sql
INSERT INTO agent_types (
    name, display_name, description, avatar_url, avatar_color,
    personality_traits, model, system_prompt, temperature,
    streaming_enabled, max_context_tokens, enabled, is_default
) VALUES (
    'code_reviewer',
    'Rita the Reviewer 👩‍💻',
    'Expert code reviewer focused on best practices',
    '👩‍💻',
    '#3b82f6',
    '["analytical", "thorough", "constructive"]',
    'claude-opus-4-5',
    'You are Rita, an expert code reviewer...',
    0.3,
    true,
    200000,
    true,
    false
);
```

### Agent Configuration Best Practices

**Choosing a Model:**
- **claude-sonnet-4-5**: Balanced (creative + analytical) - Good for: brainstorming, general chat
- **claude-opus-4-5**: Deep reasoning - Good for: code review, complex analysis, research
- **claude-haiku-4-5**: Fast responses - Good for: simple queries, quick suggestions

**Setting Temperature:**
- **0.2-0.4**: Analytical tasks (code review, data analysis, technical writing)
- **0.5-0.7**: Balanced tasks (product planning, general chat, Q&A)
- **0.7-0.9**: Creative tasks (brainstorming, ideation, marketing copy)

**Personality Traits:**
Choose 3-5 traits that define the agent's approach:
- Analytical: detail-oriented, thorough, methodical
- Creative: innovative, open-minded, strategic
- Practical: pragmatic, action-oriented, efficient
- Supportive: encouraging, constructive, empathetic

---

## Adding a New Tool

### Step 1: Define the Tool

Create `backend/scripts/add_code_analysis_tool.py`:

```python
"""Add code analysis tool."""
import asyncio
from app.database import async_session_maker
from app.services.tools_service import ToolsService

async def add_code_analysis_tool():
    """Add code analysis tool."""
    async with async_session_maker() as db:
        tools_service = ToolsService(db)

        # Check if tool exists
        existing = await tools_service.get_tool_by_name("analyze_code")
        if existing:
            print("✅ analyze_code tool already exists")
            return existing

        # Define tool
        tool_def = {
            "name": "analyze_code",
            "description": "Analyzes code for bugs, security issues, and improvements",
            "category": "code_quality",
            "tool_type": "custom",
            "definition": {
                "type": "function",
                "function": {
                    "name": "analyze_code",
                    "description": "Performs static analysis on code to identify issues",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The code to analyze"
                            },
                            "language": {
                                "type": "string",
                                "description": "Programming language (e.g., python, javascript, typescript)",
                                "enum": ["python", "javascript", "typescript", "java", "go", "rust"]
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["security", "performance", "bugs", "style", "best_practices"]
                                },
                                "description": "Areas to focus on during analysis"
                            }
                        },
                        "required": ["code", "language"]
                    }
                }
            },
            "is_dangerous": False,
            "requires_approval": False,
            "tags": ["code", "analysis", "quality"],
            "example_usage": "analyze_code(code='def foo(): pass', language='python', focus_areas=['bugs', 'style'])"
        }

        tool = await tools_service.register_tool(tool_def)
        print(f"✅ Created analyze_code tool (ID: {tool.id})")
        return tool

if __name__ == "__main__":
    asyncio.run(add_code_analysis_tool())
```

**Run the script:**
```bash
poetry run python scripts/add_code_analysis_tool.py
```

### Step 2: Implement the Tool Handler (Optional)

If you want the tool to actually execute:

Create `backend/app/tools/code_analysis.py`:

```python
"""Code analysis tool implementation."""
import ast
from typing import Any

def analyze_code(code: str, language: str, focus_areas: list[str] | None = None) -> dict[str, Any]:
    """
    Analyze code for issues.

    This is a simplified example. In production, you'd use tools like:
    - Python: pylint, flake8, bandit
    - JavaScript: eslint, prettier
    - Security: semgrep, snyk
    """
    focus_areas = focus_areas or ["bugs", "style", "best_practices"]
    issues = []

    if language == "python":
        # Simple Python AST analysis
        try:
            tree = ast.parse(code)

            # Check for common issues
            for node in ast.walk(tree):
                # Example: Check for bare except
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append({
                        "severity": "warning",
                        "category": "bugs",
                        "message": "Bare except clause catches all exceptions",
                        "line": node.lineno,
                        "suggestion": "Catch specific exceptions or use 'except Exception:'"
                    })

                # Example: Check for unused variables
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if node.id.startswith('_') and node.id != '_':
                        issues.append({
                            "severity": "info",
                            "category": "style",
                            "message": f"Variable '{node.id}' appears unused (starts with _)",
                            "line": node.lineno,
                            "suggestion": "Remove if truly unused, or use just '_'"
                        })

        except SyntaxError as e:
            issues.append({
                "severity": "error",
                "category": "syntax",
                "message": f"Syntax error: {e.msg}",
                "line": e.lineno,
                "suggestion": "Fix the syntax error before analysis"
            })

    return {
        "language": language,
        "total_issues": len(issues),
        "issues": issues,
        "focus_areas_analyzed": focus_areas,
        "summary": f"Found {len(issues)} issues in {language} code"
    }
```

### Tool Definition Best Practices

**Required Fields:**
- `name`: Lowercase, snake_case, descriptive
- `description`: Clear one-liner explaining what the tool does
- `category`: Group related tools (code, research, planning, data)
- `tool_type`: "builtin" | "custom" | "mcp"
- `definition`: Claude SDK function schema

**Parameter Design:**
- Use descriptive parameter names
- Provide clear descriptions for each parameter
- Mark truly required fields in `required` array
- Use `enum` for fixed choices
- Use `default` for optional parameters with sensible defaults

**Safety:**
- Set `is_dangerous: true` for tools that:
  - Execute code
  - Make external API calls
  - Modify data
  - Access sensitive information
- Set `requires_approval: true` for tools needing human review

---

## Assigning Tools to Agents

### Python Script

Create `backend/scripts/assign_tools.py`:

```python
"""Assign tools to agents."""
import asyncio
from sqlalchemy import select
from app.database import async_session_maker
from app.models.agent import AgentType
from app.models.tool import Tool
from app.services.tools_service import ToolsService

async def assign_tools_to_code_reviewer():
    """Assign relevant tools to code reviewer agent."""
    async with async_session_maker() as db:
        tools_service = ToolsService(db)

        # Get agent
        result = await db.execute(
            select(AgentType).where(AgentType.name == "code_reviewer")
        )
        agent = result.scalar_one()

        # Get tools
        analyze_code = await tools_service.get_tool_by_name("analyze_code")
        web_search = await tools_service.get_tool_by_name("web_search")

        # Assign with priority ordering
        assignments = [
            {
                "tool": analyze_code,
                "config": {
                    "enabled_for_agent": True,
                    "order_index": 1,  # Highest priority
                    "allow_use": True,
                    "usage_limit": 50,  # Max 50 analyses per session
                }
            },
            {
                "tool": web_search,
                "config": {
                    "enabled_for_agent": True,
                    "order_index": 2,
                    "allow_use": True,
                    "usage_limit": 20,  # Limit web searches
                }
            }
        ]

        for assignment in assignments:
            await tools_service.assign_tool_to_agent(
                agent_type_id=agent.id,
                tool_id=assignment["tool"].id,
                config=assignment["config"]
            )
            print(f"✅ Assigned {assignment['tool'].name} to {agent.display_name}")

if __name__ == "__main__":
    asyncio.run(assign_tools_to_code_reviewer())
```

**Run:**
```bash
poetry run python scripts/assign_tools.py
```

---

## Testing Your Changes

### 1. Verify Agent Created

```bash
curl http://localhost:8891/api/v1/agents | jq .
```

Expected: See your new agent in the list.

### 2. Verify Tools Assigned

```bash
curl http://localhost:8891/api/v1/agents/<agent_id>/tools | jq .
```

Expected: See assigned tools in SDK format.

### 3. Test in Frontend

1. Navigate to http://localhost:8892/brainstorm
2. Click "New Session"
3. Verify your new agent appears in the selector
4. Verify avatar, color, and personality traits display correctly
5. Create a session with the agent
6. Test that the agent responds with its configured personality

### 4. Test Tool Usage

In chat, test that tools are available:
```
User: "Can you analyze this code: def foo(): pass"
```

The agent should recognize and attempt to use the analyze_code tool.

---

## Common Patterns

### Pattern 1: Technical Expert Agent

**Use Case:** Code review, debugging, technical Q&A

```python
AgentType(
    name="tech_expert",
    model="claude-opus-4-5",  # Deep reasoning
    temperature=0.3,  # Analytical
    personality_traits=["precise", "thorough", "technical"],
    system_prompt="You are a senior technical expert..."
)
```

**Recommended Tools:**
- analyze_code
- search_documentation
- debug_error
- explain_concept

### Pattern 2: Creative Strategist Agent

**Use Case:** Brainstorming, product strategy, innovation

```python
AgentType(
    name="strategist",
    model="claude-sonnet-4-5",  # Balanced
    temperature=0.8,  # Creative
    personality_traits=["innovative", "strategic", "visionary"],
    system_prompt="You are a creative product strategist..."
)
```

**Recommended Tools:**
- create_plan
- web_search
- analyze_market
- generate_ideas

### Pattern 3: Customer Support Agent

**Use Case:** Answering user questions, providing guidance

```python
AgentType(
    name="support",
    model="claude-haiku-4-5",  # Fast responses
    temperature=0.6,  # Friendly but accurate
    personality_traits=["helpful", "patient", "empathetic"],
    system_prompt="You are a friendly customer support agent..."
)
```

**Recommended Tools:**
- search_knowledge_base
- create_ticket
- check_status
- send_email

---

## Troubleshooting

### Agent Not Appearing in UI

**Check:**
1. Agent is enabled: `enabled = true`
2. Frontend fetched agents (check browser console)
3. Clear browser cache
4. Restart backend server

**SQL Query:**
```sql
SELECT id, name, display_name, enabled FROM agent_types;
```

### Tools Not Working

**Check:**
1. Tools assigned: Query `agent_tool_configs` table
2. Tools enabled: `enabled_for_agent = true`
3. Tool definition valid: Must match Claude SDK format
4. Check backend logs for errors

**SQL Query:**
```sql
SELECT
    at.name as agent,
    t.name as tool,
    atc.enabled_for_agent,
    atc.allow_use
FROM agent_tool_configs atc
JOIN agent_types at ON atc.agent_type_id = at.id
JOIN tools t ON atc.tool_id = t.id;
```

### Agent Using Wrong Personality

**Check:**
1. `system_prompt` is specific and clear
2. `temperature` matches use case (creative vs analytical)
3. `personality_traits` align with system prompt
4. Model choice appropriate (Opus for deep thinking, Haiku for quick)

**Fix:**
Update the agent record and restart backend:
```sql
UPDATE agent_types
SET system_prompt = 'New prompt...', temperature = 0.5
WHERE name = 'agent_name';
```

---

## Quick Reference

### Agent Fields

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| name | string | Unique identifier | "code_reviewer" |
| display_name | string | UI display | "Rita the Reviewer" |
| avatar_url | string | Emoji or URL | "👩‍💻" |
| avatar_color | string | Hex color | "#3b82f6" |
| personality_traits | array | Character traits | ["analytical", "thorough"] |
| model | string | Claude model | "claude-opus-4-5" |
| temperature | float | Creativity (0-1) | 0.3 |
| system_prompt | text | Instructions | "You are..." |

### Tool Fields

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| name | string | Function name | "analyze_code" |
| description | string | What it does | "Analyzes code..." |
| category | string | Grouping | "code_quality" |
| tool_type | string | Source | "custom" |
| definition | json | SDK schema | {"type": "function"...} |
| is_dangerous | boolean | Safety flag | false |

---

## Next Steps

1. **Create your first agent** following Pattern 1, 2, or 3
2. **Add specialized tools** for your use case
3. **Test thoroughly** using the testing section
4. **Share with team** and gather feedback
5. **Iterate** based on real usage

For more details, see:
- [Dynamic Tools Usage Guide](./dynamic-tools-usage.md)
- [API Documentation](http://localhost:8891/docs)
- [CLAUDE.md](../../CLAUDE.md)

---

**Happy Building! 🚀**
