# Dynamic Tools System Design

## Executive Summary

This document outlines a flexible, database-driven system for managing Claude Agent SDK tools dynamically. Instead of hardcoding tools in the SDK client, tools are stored in the database and loaded at runtime based on agent type and configuration. This enables:

- Multiple agent types (Brainstorm, Analysis, Evaluation) with different tool sets
- Runtime tool configuration without code redeploy
- Tool permission management and security controls
- Audit trail of tool usage
- Easy addition/removal of tools

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  API Routes         Services            Database          │
│  ┌──────────┐      ┌──────────┐        ┌──────────┐      │
│  │ /tools   │─────→│ Tools    │───────→│ tools    │      │
│  │ /config  │      │ Service  │        │ configs  │      │
│  └──────────┘      └──────────┘        └──────────┘      │
│       ↓                  ↓                    ↓           │
│       └──────────────┬───────────────────────┘           │
│                      ↓                                     │
│            ┌──────────────────────┐                       │
│            │ Agent Initialization │                       │
│            │    (SDK Client)      │                       │
│            └──────────────────────┘                       │
│                      ↓                                     │
│            ┌──────────────────────┐                       │
│            │  Claude SDK Client   │                       │
│            │  w/ Dynamic Tools    │                       │
│            └──────────────────────┘                       │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Database Schema

### 1. Tools Table
Stores available tools and their definitions.

```sql
CREATE TABLE tools (
    id SERIAL PRIMARY KEY,

    -- Basic Information
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,  -- e.g., "file", "search", "code", "web"

    -- Tool Definition
    tool_type VARCHAR(50) NOT NULL,  -- "builtin" | "custom" | "mcp"
    definition JSONB NOT NULL,        -- Full tool definition (parameters, description, etc.)

    -- Configuration
    enabled BOOLEAN DEFAULT TRUE,
    is_dangerous BOOLEAN DEFAULT FALSE,  -- Tools requiring extra verification
    requires_approval BOOLEAN DEFAULT FALSE,  -- User must approve each use

    -- Metadata
    version VARCHAR(20) DEFAULT '1.0.0',
    tags JSONB DEFAULT '[]'::jsonb,   -- ["filesystem", "security-critical"]
    example_usage TEXT,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),

    CONSTRAINT tool_name_format CHECK (name ~ '^[a-z0-9_-]+$'),
    INDEX idx_category (category),
    INDEX idx_enabled (enabled),
    INDEX idx_tags (tags)
);
```

### 2. Agent Types Table
Defines different agent configurations.

```sql
CREATE TABLE agent_types (
    id SERIAL PRIMARY KEY,

    -- Identity
    name VARCHAR(100) NOT NULL UNIQUE,  -- "brainstorm" | "analysis" | "evaluation"
    display_name VARCHAR(200) NOT NULL,  -- "Claude the Brainstormer" | "Ana the Analyst"
    description TEXT,

    -- Personalization
    avatar_url VARCHAR(500),  -- URL to avatar image or emoji/icon identifier
    avatar_color VARCHAR(7) DEFAULT '#6366f1',  -- Hex color for avatar background
    personality_traits JSONB DEFAULT '[]'::jsonb,  -- ["creative", "focused", "detail-oriented"]

    -- Configuration
    model VARCHAR(100) NOT NULL,         -- "claude-sonnet-4-5"
    system_prompt TEXT NOT NULL,

    -- Behavior
    streaming_enabled BOOLEAN DEFAULT TRUE,
    max_context_tokens INTEGER DEFAULT 200000,
    temperature FLOAT DEFAULT 0.7,

    -- Status
    enabled BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,

    -- Metadata
    version VARCHAR(20) DEFAULT '1.0.0',

    -- Audit
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_enabled (enabled)
);
```

### 3. Agent Configuration Table
Maps tools to agent types (junction table with additional configuration).

```sql
CREATE TABLE agent_tool_configs (
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    agent_type_id INTEGER NOT NULL REFERENCES agent_types(id) ON DELETE CASCADE,
    tool_id INTEGER NOT NULL REFERENCES tools(id) ON DELETE CASCADE,

    -- Tool-Specific Configuration
    enabled_for_agent BOOLEAN DEFAULT TRUE,
    order_index INTEGER,  -- Order in which tools appear (affects selection)

    -- Security Configuration
    allow_use BOOLEAN DEFAULT TRUE,  -- Agent can use this tool
    requires_approval BOOLEAN DEFAULT FALSE,  -- Override: force approval for this agent
    usage_limit INTEGER,  -- Max times per session (-1 = unlimited)

    -- Constraints
    allowed_parameters JSONB,  -- Restrict tool parameters
    denied_parameters JSONB,   -- Specifically deny parameters
    parameter_defaults JSONB,  -- Default values if not specified

    -- Audit
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (agent_type_id, tool_id),
    INDEX idx_agent_type (agent_type_id),
    INDEX idx_enabled (enabled_for_agent)
);
```

### 4. Tool Usage Audit Table
Tracks tool usage for security and debugging.

```sql
CREATE TABLE tool_usage_audit (
    id BIGSERIAL PRIMARY KEY,

    -- Session Context
    session_id VARCHAR(50),
    agent_type_id INTEGER REFERENCES agent_types(id),
    tool_id INTEGER REFERENCES tools(id),

    -- Usage Details
    parameters JSONB,
    result JSONB,

    -- Outcome
    status VARCHAR(50),  -- "success" | "failed" | "denied" | "blocked"
    error_message TEXT,

    -- Performance
    execution_time_ms INTEGER,
    tokens_used INTEGER,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_id VARCHAR(255),

    INDEX idx_session (session_id),
    INDEX idx_tool (tool_id),
    INDEX idx_created (created_at),
    INDEX idx_agent_type (agent_type_id)
);
```

## Tool Definition Format

Tools in the database are stored as JSONB with a standard format:

```python
{
    # Required
    "name": "read_file",
    "description": "Read file contents",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to read"
            }
        },
        "required": ["path"]
    },

    # Optional
    "category": "filesystem",
    "requires_approval": False,
    "is_dangerous": False,
    "examples": [
        {
            "input": {"path": "/path/to/file.txt"},
            "output": "File contents here"
        }
    ]
}
```

## Service Implementation

### ToolsService
Manages tool loading and configuration.

```python
class ToolsService:
    """Service for dynamic tool management."""

    async def get_tools_for_agent(
        self,
        agent_type_id: int,
        enabled_only: bool = True
    ) -> list[dict[str, Any]]:
        """Load all tools configured for an agent type.

        Returns tool definitions ready for SDK client initialization.
        """

    async def get_tool_by_name(self, name: str) -> Tool | None:
        """Get single tool definition by name."""

    async def register_tool(self, tool_def: dict) -> Tool:
        """Register new tool in database."""

    async def update_tool(self, tool_id: int, updates: dict) -> Tool:
        """Update tool definition."""

    async def assign_tool_to_agent(
        self,
        agent_type_id: int,
        tool_id: int,
        config: AgentToolConfig
    ) -> None:
        """Assign tool to agent type with optional config."""

    async def check_tool_allowed(
        self,
        agent_type_id: int,
        tool_name: str,
        parameters: dict | None = None
    ) -> bool:
        """Check if tool is allowed for agent."""

    async def audit_tool_usage(
        self,
        session_id: str,
        agent_type_id: int,
        tool_name: str,
        parameters: dict,
        result: dict,
        status: str,
        execution_time_ms: int
    ) -> None:
        """Log tool usage for audit trail."""
```

### AgentFactory
Creates SDK clients with dynamically loaded tools.

```python
class AgentFactory:
    """Factory for creating Agent SDK clients with dynamic tools."""

    def __init__(self, db: AsyncSession, tools_service: ToolsService):
        self.db = db
        self.tools_service = tools_service

    async def create_agent_client(
        self,
        agent_type: str
    ) -> ClaudeSDKClient:
        """Create an SDK client for the given agent type.

        Flow:
        1. Load agent type configuration from database
        2. Load tools assigned to this agent via ToolsService
        3. Apply security restrictions
        4. Initialize ClaudeSDKClient with tools
        5. Return ready-to-use client
        """

        # Get agent configuration
        agent = await self.db.execute(
            select(AgentType).where(AgentType.name == agent_type)
        )
        agent_config = agent.scalar_one_or_none()

        # Load tools
        tools = await self.tools_service.get_tools_for_agent(
            agent_config.id,
            enabled_only=True
        )

        # Build SDK options
        options = ClaudeAgentOptions(
            model=agent_config.model,
            system_prompt=agent_config.system_prompt,
            # Pass tools to SDK
            tools=tools,
            temperature=agent_config.temperature,
            max_tokens=agent_config.max_context_tokens,
        )

        # Create and return client
        return ClaudeSDKClient(options=options)
```

## Security Considerations

### 1. Tool Whitelist Approach
- Only tools explicitly enabled for an agent type are available
- Dangerous tools (filesystem, code execution) require explicit approval per use
- Audit all tool usage

**Implementation:**
```python
async def check_tool_allowed(
    agent_type_id: int,
    tool_name: str,
    parameters: dict | None = None
) -> bool:
    # Query agent_tool_configs junction table
    config = await db.execute(
        select(AgentToolConfig).where(
            (AgentToolConfig.agent_type_id == agent_type_id) &
            (AgentToolConfig.tool.name == tool_name) &
            (AgentToolConfig.enabled_for_agent == True)
        )
    )

    if not config:
        return False

    # Check parameter restrictions
    if config.denied_parameters:
        if any(key in config.denied_parameters for key in parameters.keys()):
            return False

    return True
```

### 2. Parameter Validation
Tools can restrict which parameters are allowed or deny specific ones:

```jsonb
// In agent_tool_configs
{
    "allowed_parameters": ["path", "read_length"],  // Whitelist
    "denied_parameters": {"path": ["/etc", "/root"]},  // Block specific values
    "parameter_defaults": {"read_length": 1000}
}
```

### 3. Approval System
Dangerous tools can require per-use approval:

```python
if tool_config.requires_approval:
    # Queue for user approval
    await send_approval_request(
        session_id=session_id,
        tool_name=tool_name,
        parameters=parameters,
        description=tool_definition.description
    )
```

### 4. Audit Trail
All tool usage is logged:

```sql
SELECT
    tool_usage_audit.created_at,
    tools.name,
    agent_types.name as agent_type,
    tool_usage_audit.status,
    tool_usage_audit.parameters
FROM tool_usage_audit
JOIN tools ON tools.id = tool_usage_audit.tool_id
JOIN agent_types ON agent_types.id = tool_usage_audit.agent_type_id
WHERE tool_usage_audit.session_id = 'sess-123'
ORDER BY created_at DESC;
```

### 5. Dangerous Tool Classification
Mark tools as dangerous to trigger extra checks:

```python
DANGEROUS_TOOLS = {
    "bash": {"requires_approval": True, "is_dangerous": True},
    "edit": {"requires_approval": True, "is_dangerous": True},
    "read": {"requires_approval": False, "is_dangerous": False},  # Info gathering
}
```

## Database Initialization

### Alembic Migration
```python
def upgrade():
    op.create_table(
        'tools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('tool_type', sa.String(50), nullable=False),
        sa.Column('definition', postgresql.JSONB(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('is_dangerous', sa.Boolean(), server_default='false'),
        sa.Column('requires_approval', sa.Boolean(), server_default='false'),
        sa.Column('version', sa.String(20), server_default='1.0.0'),
        sa.Column('tags', postgresql.JSONB(), server_default='[]'),
        sa.Column('example_usage', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    # ... create other tables
```

### Seed Data
Bootstrap default agent types and tools:

```python
async def seed_default_tools(db: AsyncSession):
    """Seed database with default tools."""

    default_tools = [
        {
            "name": "web_search",
            "description": "Search the web for information",
            "category": "web",
            "tool_type": "builtin",
            "definition": {...},
            "is_dangerous": False,
        },
        {
            "name": "read_file",
            "description": "Read file contents",
            "category": "filesystem",
            "tool_type": "builtin",
            "definition": {...},
            "is_dangerous": True,  # Requires approval
            "requires_approval": True,
        },
    ]

    for tool_def in default_tools:
        tool = Tool(**tool_def)
        db.add(tool)

    await db.commit()

async def seed_default_agent_types(db: AsyncSession):
    """Seed default agent type configurations."""

    brainstorm_agent = AgentType(
        name="brainstorm",
        display_name="Claude the Brainstormer",
        description="Creative facilitator for product discovery sessions",
        avatar_url="🎨",  # Emoji or URL to image
        avatar_color="#f59e0b",  # Warm orange
        personality_traits=["creative", "strategic", "goal-oriented"],
        model="claude-sonnet-4-5",
        system_prompt="You are a brainstorming facilitator...",
        temperature=0.8,  # More creative
    )
    db.add(brainstorm_agent)

    analysis_agent = AgentType(
        name="analysis",
        display_name="Ana the Analyst",
        description="Detail-oriented code analysis expert",
        avatar_url="🔍",  # Emoji or URL to image
        avatar_color="#3b82f6",  # Cool blue
        personality_traits=["analytical", "precise", "thorough"],
        model="claude-sonnet-4-5",
        system_prompt="You are a code analysis expert...",
        temperature=0.3,  # More focused
    )
    db.add(analysis_agent)

    await db.commit()
```

## Integration with BrainstormingService

Update existing BrainstormingService to use dynamic tools:

```python
class BrainstormingService:
    def __init__(
        self,
        api_key: str,
        agent_factory: AgentFactory,
        model: str = "claude-sonnet-4-5"
    ):
        self.api_key = api_key
        self.agent_factory = agent_factory
        self.model = model
        self.client = None
        self.connected = False

    async def initialize(self):
        """Initialize client with dynamic tools for brainstorm agent."""
        # Create agent-specific client with tools
        self.client = await self.agent_factory.create_agent_client("brainstorm")

    async def stream_brainstorm_message(
        self,
        messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream response with dynamically-loaded tools."""
        if not self.client:
            await self.initialize()

        # Rest of implementation uses self.client
        # Tools are automatically available based on agent config
```

## API Endpoints

### Tool Management
```
GET    /api/tools                  # List all tools
POST   /api/tools                  # Create new tool
GET    /api/tools/{tool_id}        # Get tool details
PUT    /api/tools/{tool_id}        # Update tool
DELETE /api/tools/{tool_id}        # Delete tool

# Agent configuration
GET    /api/agents                 # List agent types
POST   /api/agents                 # Create agent type
GET    /api/agents/{agent_id}      # Get agent details
GET    /api/agents/{agent_id}/tools # Get tools for agent
POST   /api/agents/{agent_id}/tools/{tool_id} # Assign tool

# Audit
GET    /api/audit/tool-usage       # Get tool usage logs
```

## Frontend Integration

### Agent Personalization in UI

When displaying agent messages, use the agent's personalization fields:

```vue
<!-- BrainstormChat.vue -->
<template>
  <div class="flex items-center gap-2 mb-2">
    <Avatar class="h-6 w-6">
      <AvatarFallback :style="{ backgroundColor: agentConfig.avatar_color }">
        <span v-if="isEmoji(agentConfig.avatar_url)">
          {{ agentConfig.avatar_url }}
        </span>
        <img v-else :src="agentConfig.avatar_url" alt="avatar" />
      </AvatarFallback>
    </Avatar>
    <span class="text-xs font-semibold">
      {{ agentConfig.display_name }}
    </span>
    <Badge v-for="trait in agentConfig.personality_traits" :key="trait" variant="outline" class="text-xs">
      {{ trait }}
    </Badge>
  </div>
</template>

<script setup lang="ts">
// Fetch agent config when session loads
const agentConfig = ref({
  display_name: "Claude the Brainstormer",
  avatar_url: "🎨",
  avatar_color: "#f59e0b",
  personality_traits: ["creative", "strategic"]
})

const isEmoji = (str: string) => /\p{Emoji}/u.test(str)
</script>
```

### Agent Selection UI

Allow users to choose which agent to use for a session:

```vue
<!-- AgentSelector.vue -->
<template>
  <div class="grid grid-cols-3 gap-4">
    <Card
      v-for="agent in agents"
      :key="agent.id"
      @click="selectAgent(agent)"
      class="cursor-pointer hover:border-primary"
    >
      <CardHeader>
        <div class="flex items-center gap-3">
          <Avatar class="h-12 w-12">
            <AvatarFallback :style="{ backgroundColor: agent.avatar_color }">
              {{ agent.avatar_url }}
            </AvatarFallback>
          </Avatar>
          <div>
            <h3 class="font-semibold">{{ agent.display_name }}</h3>
            <p class="text-xs text-muted-foreground">{{ agent.description }}</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div class="flex flex-wrap gap-1">
          <Badge v-for="trait in agent.personality_traits" :key="trait" variant="secondary" class="text-xs">
            {{ trait }}
          </Badge>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
```

## Example Implementation

### Creating a new agent type with specific tools

```python
# 1. Create agent type
agent = AgentType(
    name="code_reviewer",
    model="claude-opus-4-5",
    system_prompt="You are a code review expert...",
)
db.add(agent)
await db.commit()

# 2. Load tools from database
web_search = await tools_service.get_tool_by_name("web_search")
read_file = await tools_service.get_tool_by_name("read_file")
bash = await tools_service.get_tool_by_name("bash")

# 3. Assign tools with custom config
await tools_service.assign_tool_to_agent(
    agent_type_id=agent.id,
    tool_id=web_search.id,
    config=AgentToolConfig(
        enabled_for_agent=True,
        requires_approval=False,
        usage_limit=-1,
    )
)

await tools_service.assign_tool_to_agent(
    agent_type_id=agent.id,
    tool_id=bash.id,
    config=AgentToolConfig(
        enabled_for_agent=True,
        requires_approval=True,  # Require approval for bash
        denied_parameters={"command": ["rm -rf", "sudo"]},
    )
)

# 4. Create client - tools loaded automatically
client = await agent_factory.create_agent_client("code_reviewer")
```

## Migration Path

### Phase 1: Foundation (Week 1)
1. Create database schema and models
2. Implement ToolsService
3. Create AlembicSeed for default tools and agents
4. Unit tests for service

### Phase 2: Integration (Week 2)
1. Implement AgentFactory
2. Update BrainstormingService to use dynamic tools
3. Add API endpoints for tool management
4. Integration tests

### Phase 3: Security & Audit (Week 3)
1. Implement approval system
2. Add tool usage audit logging
3. Create audit endpoints
4. Security testing

### Phase 4: UI & Admin (Week 4)
1. Create admin UI for tool management
2. Add approval workflow UI
3. Audit log viewer
4. E2E tests

## Benefits

1. **Flexibility**: Add/remove/modify tools without code changes
2. **Security**: Explicit whitelist, per-tool approval, audit trail
3. **Scalability**: Support multiple agent types with different capabilities
4. **Auditability**: Full history of tool usage
5. **Maintainability**: Tools managed as data, not code
6. **Extensibility**: Easy to add MCP server integration, custom tool executors

## References

- [Claude Agent SDK - Custom Tools](https://docs.claude.com/en/api/agent-sdk/custom-tools)
- [Anthropic Tool Search - Dynamic Tool Loading](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)
- [Claude Code Security Best Practices](https://code.claude.com/docs/en/security)
- [Implementing Tool Use - Claude Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use)

