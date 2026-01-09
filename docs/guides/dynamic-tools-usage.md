# Dynamic Tools System - Usage Guide

## Overview

The Dynamic Tools System allows you to manage Claude Agent SDK tools and personalized agents through the database, without code changes.

## Creating a New Agent Type

### Via Python Script

```python
from app.models.agent import AgentType
from app.database import async_session_maker

async def create_custom_agent():
    async with async_session_maker() as db:
        agent = AgentType(
            name="code_reviewer",
            display_name="Rita the Reviewer",
            description="Code review expert with focus on best practices",
            avatar_url="👩‍💻",
            avatar_color="#3b82f6",
            personality_traits=["analytical", "thorough", "constructive"],
            model="claude-opus-4-5",
            system_prompt="You are an expert code reviewer...",
            temperature=0.3,
        )
        db.add(agent)
        await db.commit()
```

### Via API (Future)

```bash
curl -X POST http://localhost:8891/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code_reviewer",
    "display_name": "Rita the Reviewer",
    "avatar_url": "👩‍💻",
    "avatar_color": "#3b82f6",
    "model": "claude-opus-4-5",
    "system_prompt": "You are an expert code reviewer..."
  }'
```

## Registering a New Tool

### Via Python Script

```python
from app.services.tools_service import ToolsService

tool_def = {
    "name": "search_codebase",
    "description": "Search for code patterns in the codebase",
    "category": "code",
    "tool_type": "custom",
    "definition": {
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "File pattern to search (e.g., '*.py')"
                }
            },
            "required": ["query"]
        }
    },
    "is_dangerous": False,
}

async with async_session_maker() as db:
    tools_service = ToolsService(db)
    tool = await tools_service.register_tool(tool_def)
```

## Assigning Tools to Agents

```python
from app.services.tools_service import ToolsService

async with async_session_maker() as db:
    tools_service = ToolsService(db)

    # Get agent and tool
    agent = await db.execute(select(AgentType).where(AgentType.name == "code_reviewer"))
    tool = await tools_service.get_tool_by_name("search_codebase")

    # Assign with optional config
    await tools_service.assign_tool_to_agent(
        agent_type_id=agent.id,
        tool_id=tool.id,
        config={
            "enabled_for_agent": True,
            "order_index": 1,
            "usage_limit": 50,  # Max 50 uses per session
        }
    )
```

## Using Agents in Code

```python
from app.services.agent_factory import AgentFactory
from app.services.tools_service import ToolsService

async with async_session_maker() as db:
    tools_service = ToolsService(db)
    agent_factory = AgentFactory(db, tools_service)

    # Create SDK client with all configured tools
    client = await agent_factory.create_agent_client("code_reviewer")

    # Use client for conversation
    await client.query("Review this code...")
```

## Security Considerations

- Tools marked `is_dangerous=True` should require approval
- Use `allowed_parameters` to restrict tool inputs
- All tool usage is logged in `tool_usage_audit` table
- Review audit logs regularly for suspicious activity

## Best Practices

1. **Tool Naming**: Use snake_case, descriptive names
2. **Descriptions**: Write clear descriptions for Claude to understand when to use
3. **Input Schemas**: Provide detailed schemas with descriptions
4. **Agent Personalities**: Choose temperature based on use case:
   - Creative tasks (brainstorming): 0.7-0.9
   - Analytical tasks (code review): 0.3-0.5
   - Balanced: 0.5-0.7
5. **Testing**: Always test new tools with sample inputs before production use

## Troubleshooting

### Tool Not Available to Agent

1. Check tool is enabled: `SELECT * FROM tools WHERE name='tool_name'`
2. Check assignment exists: `SELECT * FROM agent_tool_configs WHERE agent_type_id=X AND tool_id=Y`
3. Check `enabled_for_agent=true` and `allow_use=true`

### Agent Not Showing in UI

1. Check agent is enabled: `SELECT * FROM agent_types WHERE name='agent_name'`
2. Check frontend fetched agents: Console should show API call
3. Clear browser cache and reload

### Tool Usage Not Working

1. Check audit logs: `SELECT * FROM tool_usage_audit ORDER BY created_at DESC LIMIT 10`
2. Check for errors in `error_message` field
3. Verify tool definition schema matches SDK expectations
