# Interactive Brainstorming Elements - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Transform brainstorming chat from text-only SSE streaming to interactive WebSocket-based communication with dynamic UI elements (buttons, multi-selects).

**Architecture:** Block-based JSONB message structure, FastAPI WebSocket endpoints, Vue 3 dynamic component rendering, Pinia state management for WebSocket lifecycle.

**Tech Stack:** FastAPI WebSocket, PostgreSQL JSONB, Alembic migrations, Vue 3 Composition API, Pinia, TypeScript, shadcn-vue components.

---

## Phase 1: Database Migration & Backend Model

### Task 1: Create Alembic Migration for JSONB Content

**Files:**
- Create: `backend/alembic/versions/XXXX_migrate_content_to_jsonb.py`
- Reference: `backend/app/models/brainstorm.py`

**Step 1: Create migration file**

Run: `cd backend && poetry run alembic revision -m "migrate brainstorm_messages content to jsonb"`

Expected: New migration file created in `backend/alembic/versions/`

**Step 2: Write migration upgrade logic**

Edit the generated migration file:

```python
"""migrate brainstorm_messages content to jsonb

Revision ID: XXXX
Revises: YYYY
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'XXXX'
down_revision = 'YYYY'  # Previous migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing messages (acceptable in dev)
    op.execute('TRUNCATE TABLE brainstorm_messages CASCADE')

    # Change column type from TEXT to JSONB
    op.alter_column(
        'brainstorm_messages',
        'content',
        type_=postgresql.JSONB,
        postgresql_using='content::jsonb'
    )


def downgrade() -> None:
    # Change back to TEXT
    op.alter_column(
        'brainstorm_messages',
        'content',
        type_=sa.Text,
        postgresql_using='content::text'
    )
```

**Step 3: Run migration**

Run: `cd backend && poetry run alembic upgrade head`

Expected: `INFO  [alembic.runtime.migration] Running upgrade YYYY -> XXXX, migrate brainstorm_messages content to jsonb`

**Step 4: Verify migration**

Run: `cd backend && psql postgresql://postgres:postgres@localhost:5432/product_analysis -c "\d brainstorm_messages"`

Expected: Column `content` shows type `jsonb`

**Step 5: Commit**

```bash
git add backend/alembic/versions/*_migrate_content_to_jsonb.py
git commit -m "migration: convert brainstorm_messages.content to JSONB

Migrate content column from TEXT to JSONB to support block-based
message structure for interactive UI elements.

Breaking change: truncates existing messages (acceptable in dev).
"
```

---

### Task 2: Update SQLAlchemy Model

**Files:**
- Modify: `backend/app/models/brainstorm.py:30-35`

**Step 1: Write test for JSONB content**

Create: `backend/tests/test_models_brainstorm.py`

```python
"""Tests for brainstorm models with JSONB content."""
import pytest
from app.models.brainstorm import BrainstormMessage, BrainstormSession


def test_message_accepts_jsonb_content(db_session):
    """Message should accept JSONB block structure."""
    session = BrainstormSession(
        id="test-session",
        title="Test",
        description="Test session",
        status="active"
    )
    db_session.add(session)
    db_session.commit()

    message = BrainstormMessage(
        id="test-msg",
        session_id="test-session",
        role="user",
        content={
            "blocks": [
                {
                    "id": "block-1",
                    "type": "text",
                    "text": "Hello"
                }
            ]
        }
    )
    db_session.add(message)
    db_session.commit()

    # Retrieve and verify
    retrieved = db_session.query(BrainstormMessage).filter_by(id="test-msg").first()
    assert retrieved.content["blocks"][0]["text"] == "Hello"
    assert retrieved.content["blocks"][0]["type"] == "text"


def test_message_supports_button_group_block(db_session):
    """Message should support button_group block type."""
    session = BrainstormSession(
        id="test-session-2",
        title="Test",
        description="Test session",
        status="active"
    )
    db_session.add(session)
    db_session.commit()

    message = BrainstormMessage(
        id="test-msg-2",
        session_id="test-session-2",
        role="assistant",
        content={
            "blocks": [
                {
                    "id": "block-1",
                    "type": "text",
                    "text": "Choose platform:"
                },
                {
                    "id": "block-2",
                    "type": "button_group",
                    "label": "Platform",
                    "buttons": [
                        {"label": "iOS", "value": "ios"},
                        {"label": "Android", "value": "android"}
                    ]
                }
            ],
            "metadata": {}
        }
    )
    db_session.add(message)
    db_session.commit()

    retrieved = db_session.query(BrainstormMessage).filter_by(id="test-msg-2").first()
    assert retrieved.content["blocks"][1]["type"] == "button_group"
    assert len(retrieved.content["blocks"][1]["buttons"]) == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_models_brainstorm.py -v`

Expected: Test fails (model not updated yet)

**Step 3: Update model to use JSONB**

Edit `backend/app/models/brainstorm.py`:

```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB  # Add this import
from sqlalchemy.sql import func
from app.database import Base


class BrainstormMessage(Base):
    """Brainstorm message with block-based JSONB content."""

    __tablename__ = "brainstorm_messages"

    id = Column(String, primary_key=True)
    session_id = Column(
        String, ForeignKey("brainstorm_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String, nullable=False)  # 'user' | 'assistant'
    content = Column(JSONB, nullable=False)  # Changed from Text to JSONB
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_models_brainstorm.py -v`

Expected: Both tests PASS

**Step 5: Commit**

```bash
git add backend/app/models/brainstorm.py backend/tests/test_models_brainstorm.py
git commit -m "feat(backend): update BrainstormMessage model to use JSONB

Change content column from Text to JSONB to support block-based
message structure with interactive elements.

Add tests for JSONB content with text and button_group blocks.
"
```

---

## Phase 2: Backend System Prompt & WebSocket

### Task 3: Update System Prompt for JSON Responses

**Files:**
- Modify: `backend/app/services/brainstorming_service.py:14-31`
- Test: `backend/tests/test_brainstorming_service.py`

**Step 1: Write test for JSON response format**

Create: `backend/tests/test_brainstorming_service.py`

```python
"""Tests for brainstorming service JSON responses."""
import pytest
import json
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
```

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_brainstorming_service.py::test_system_prompt_instructs_json_format -v`

Expected: Test fails (prompt not updated)

**Step 3: Update system prompt**

Edit `backend/app/services/brainstorming_service.py`:

```python
class BrainstormingService:
    """Service for brainstorming with Claude via streaming using Agent SDK."""

    SYSTEM_PROMPT = """You are an AI brainstorming facilitator for product development teams.

# Response Format
ALWAYS respond with valid JSON in this exact structure:

{
  "blocks": [...],
  "metadata": {}
}

# Block Types

## text
For explanations, questions, summaries.

{
  "id": "unique_id",
  "type": "text",
  "text": "Your message here"
}

## button_group
For 2-5 clear options. Use when choices are discrete and mutually exclusive.

{
  "id": "unique_id",
  "type": "button_group",
  "label": "Question or prompt (optional)",
  "buttons": [
    {"label": "Option A", "value": "opt_a", "style": "primary"},
    {"label": "Option B", "value": "opt_b"}
  ],
  "allow_multiple": false
}

## multi_select
For choosing multiple options from a list.

{
  "id": "unique_id",
  "type": "multi_select",
  "label": "Select all that apply",
  "options": [
    {"label": "Option 1", "value": "opt1", "description": "Details..."},
    {"label": "Option 2", "value": "opt2"}
  ],
  "min": 1,
  "max": 5
}

# When to Use Interactive Elements

✅ Use buttons when:
- Asking about discrete categories (B2B vs B2C, iOS vs Android)
- Offering 2-4 clear paths forward
- Narrowing scope or priorities

✅ Use multi-select when:
- Features to prioritize (select top 3)
- Platforms to target (can choose multiple)
- Stakeholder groups to consider

❌ Don't use interactive elements when:
- User needs to provide unique information (names, descriptions)
- Question is too open-ended
- Building on previous free-form input

# Guidelines

1. **Start broad, narrow with interactions**: First message text-only, then use buttons to focus
2. **One question at a time**: Don't overwhelm with multiple button groups
3. **Make options clear**: Button labels should be self-explanatory
4. **Allow escape**: User can always skip and type freely
5. **Build context**: Reference previous choices in follow-up questions

# Examples

## Good: Clear discrete options
{
  "blocks": [
    {"id": "1", "type": "text", "text": "Let's clarify your platform strategy."},
    {
      "id": "2",
      "type": "button_group",
      "label": "Which platform first?",
      "buttons": [
        {"label": "iOS only", "value": "ios"},
        {"label": "Android only", "value": "android"},
        {"label": "Both simultaneously", "value": "both"},
        {"label": "Web app instead", "value": "web"}
      ]
    }
  ]
}

## Good: Prioritization with multi-select
{
  "blocks": [
    {"id": "1", "type": "text", "text": "I see 6 potential features. Let's prioritize."},
    {
      "id": "2",
      "type": "multi_select",
      "label": "Select your top 3 must-haves",
      "options": [
        {"label": "User authentication", "value": "auth"},
        {"label": "Social sharing", "value": "social"},
        {"label": "Offline mode", "value": "offline"}
      ],
      "min": 1,
      "max": 3
    }
  ]
}

# Remember
- You're facilitating, not interrogating
- Acknowledge user input before asking next question
- Use text blocks to show you understand their vision
- Interactive elements accelerate decision-making, not replace creativity
"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5") -> None:
        # ... rest remains same
```

**Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_brainstorming_service.py -v`

Expected: Both tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/brainstorming_service.py backend/tests/test_brainstorming_service.py
git commit -m "feat(backend): update system prompt for JSON block responses

Replace text-only prompt with structured JSON format instructions.
Includes block type specs, usage guidelines, and examples.

Instructs Claude to return responses as block arrays with support
for text, button_group, and multi_select elements.
"
```

---

### Task 4: Create WebSocket Endpoint Handler

**Files:**
- Modify: `backend/app/api/brainstorms.py` (add new endpoint)
- Test: `backend/tests/test_api_brainstorms_ws.py`

**Step 1: Write test for WebSocket connection**

Create: `backend/tests/test_api_brainstorms_ws.py`

```python
"""Tests for WebSocket brainstorming endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.brainstorm import BrainstormSession


def test_websocket_accepts_connection(db_session):
    """WebSocket should accept connections to existing sessions."""
    # Create test session
    session = BrainstormSession(
        id="ws-test-session",
        title="Test Session",
        description="Test",
        status="active"
    )
    db_session.add(session)
    db_session.commit()

    client = TestClient(app)
    with client.websocket_connect(f"/api/brainstorms/ws/ws-test-session") as websocket:
        # Connection successful if no exception
        assert websocket is not None


def test_websocket_rejects_inactive_session(db_session):
    """WebSocket should reject connections to non-active sessions."""
    session = BrainstormSession(
        id="inactive-session",
        title="Inactive",
        description="Test",
        status="completed"
    )
    db_session.add(session)
    db_session.commit()

    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/brainstorms/ws/inactive-session") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "error"


def test_websocket_handles_user_message(db_session):
    """WebSocket should handle user_message type."""
    session = BrainstormSession(
        id="msg-test-session",
        title="Test",
        description="Test",
        status="active"
    )
    db_session.add(session)
    db_session.commit()

    client = TestClient(app)
    with client.websocket_connect(f"/api/brainstorms/ws/msg-test-session") as websocket:
        # Send user message
        websocket.send_json({
            "type": "user_message",
            "content": "Hello"
        })

        # Should receive stream_chunk or stream_complete
        response = websocket.receive_json()
        assert response["type"] in ["stream_chunk", "stream_complete", "error"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_api_brainstorms_ws.py::test_websocket_accepts_connection -v`

Expected: Test fails (endpoint doesn't exist)

**Step 3: Implement WebSocket endpoint**

Edit `backend/app/api/brainstorms.py` (add to existing file):

```python
import uuid
import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.database import async_session_maker
from app.models.brainstorm import BrainstormMessage
from app.services.brainstorming_service import BrainstormingService
from app.config import settings


@router.websocket("/ws/{session_id}")
async def websocket_brainstorm(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for interactive brainstorming."""
    await websocket.accept()
    logger.info(f"[WS] Client connected to session {session_id}")

    # Independent database session
    async with async_session_maker() as db:
        try:
            # Verify session exists and is active
            result = await db.execute(
                select(BrainstormSession).where(BrainstormSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found"
                })
                await websocket.close()
                return

            if session.status != "active":
                await websocket.send_json({
                    "type": "error",
                    "message": "Session is not active"
                })
                await websocket.close()
                return

            # Main message loop
            while True:
                data = await websocket.receive_json()
                logger.info(f"[WS] Received: {data['type']}")

                if data["type"] == "user_message":
                    await handle_user_message(websocket, db, session_id, data["content"])

                elif data["type"] == "interaction":
                    await handle_interaction(
                        websocket, db, session_id,
                        data["block_id"], data["value"]
                    )

        except WebSocketDisconnect:
            logger.info(f"[WS] Client disconnected from session {session_id}")
        except Exception as e:
            logger.error(f"[WS] Error: {e}", exc_info=True)
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except:
                pass


async def handle_user_message(
    websocket: WebSocket,
    db,
    session_id: str,
    content: str
):
    """Handle user text message."""
    # Save user message to database
    user_message = BrainstormMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content={
            "blocks": [{
                "id": str(uuid.uuid4()),
                "type": "text",
                "text": content
            }]
        }
    )
    db.add(user_message)
    await db.commit()
    logger.info(f"[WS] Saved user message")

    # Stream Claude response
    await stream_claude_response(websocket, db, session_id)


async def handle_interaction(
    websocket: WebSocket,
    db,
    session_id: str,
    block_id: str,
    value: str | list[str]
):
    """Handle user interaction with button/select."""
    # Save interaction as user message
    interaction_message = BrainstormMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content={
            "blocks": [{
                "id": str(uuid.uuid4()),
                "type": "interaction_response",
                "block_id": block_id,
                "value": value
            }]
        }
    )
    db.add(interaction_message)
    await db.commit()
    logger.info(f"[WS] Saved interaction")

    # Stream Claude response
    await stream_claude_response(websocket, db, session_id)


async def stream_claude_response(
    websocket: WebSocket,
    db,
    session_id: str
):
    """Stream Claude's response block-by-block."""
    # Get conversation history
    result = await db.execute(
        select(BrainstormMessage)
        .where(BrainstormMessage.session_id == session_id)
        .order_by(BrainstormMessage.created_at)
    )
    messages = result.scalars().all()

    # Convert to format for Claude
    conversation = []
    for msg in messages:
        if msg.role == "user":
            # Extract text from blocks
            text_parts = []
            for block in msg.content.get("blocks", []):
                if block["type"] == "text":
                    text_parts.append(block["text"])
                elif block["type"] == "interaction_response":
                    text_parts.append(f"Selected: {block['value']}")
            conversation.append({"role": "user", "content": " ".join(text_parts)})
        else:
            # For assistant, combine all text blocks
            text_parts = [
                b["text"] for b in msg.content.get("blocks", [])
                if b["type"] == "text"
            ]
            if text_parts:
                conversation.append({"role": "assistant", "content": " ".join(text_parts)})

    # Stream from Claude
    message_id = str(uuid.uuid4())
    collected_blocks = []

    async with BrainstormingService(api_key=settings.ANTHROPIC_API_KEY) as service:
        try:
            # Claude returns JSON string
            full_response = ""
            async for chunk in service.stream_brainstorm_message(conversation):
                full_response += chunk

            # Parse JSON response
            try:
                response_data = json.loads(full_response)
                blocks = response_data.get("blocks", [])

                # Send blocks incrementally
                for block in blocks:
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "message_id": message_id,
                        "block": block
                    })
                    collected_blocks.append(block)

            except json.JSONDecodeError:
                # Fallback: treat as plain text
                logger.warning("[WS] Claude response not valid JSON, treating as text")
                text_block = {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "text": full_response
                }
                await websocket.send_json({
                    "type": "stream_chunk",
                    "message_id": message_id,
                    "block": text_block
                })
                collected_blocks.append(text_block)

            # Save to database
            assistant_message = BrainstormMessage(
                id=message_id,
                session_id=session_id,
                role="assistant",
                content={
                    "blocks": collected_blocks,
                    "metadata": response_data.get("metadata", {}) if isinstance(response_data, dict) else {}
                }
            )
            db.add(assistant_message)
            await db.commit()

            # Signal completion
            await websocket.send_json({
                "type": "stream_complete",
                "message_id": message_id
            })
            logger.info(f"[WS] Stream complete")

        except Exception as e:
            logger.error(f"[WS] Error streaming: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": f"Streaming error: {str(e)}"
            })
```

**Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_api_brainstorms_ws.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backend/app/api/brainstorms.py backend/tests/test_api_brainstorms_ws.py
git commit -m "feat(backend): add WebSocket endpoint for brainstorming

Implement bidirectional WebSocket communication for interactive
brainstorming sessions.

Features:
- Accept/reject connections based on session status
- Handle user_message and interaction message types
- Stream Claude responses as blocks incrementally
- Save all messages with JSONB content to database
- JSON fallback for non-JSON Claude responses
"
```

---

## Phase 3: Frontend TypeScript Types & Components

### Task 5: Define TypeScript Types for Blocks

**Files:**
- Create: `frontend/src/types/brainstorm.ts` (update existing)

**Step 1: Write types for block structure**

```typescript
// Base block types
export type BlockType = 'text' | 'button_group' | 'multi_select' | 'interaction_response'

export interface BaseBlock {
  id: string
  type: BlockType
}

export interface TextBlock extends BaseBlock {
  type: 'text'
  text: string
}

export interface ButtonOption {
  label: string
  value: string
  style?: 'primary' | 'secondary' | 'outline'
}

export interface ButtonGroupBlock extends BaseBlock {
  type: 'button_group'
  label?: string
  buttons: ButtonOption[]
  allow_multiple?: boolean
}

export interface SelectOption {
  label: string
  value: string
  description?: string
}

export interface MultiSelectBlock extends BaseBlock {
  type: 'multi_select'
  label: string
  options: SelectOption[]
  min?: number
  max?: number
}

export interface InteractionResponseBlock extends BaseBlock {
  type: 'interaction_response'
  block_id: string
  value: string | string[]
}

export type Block = TextBlock | ButtonGroupBlock | MultiSelectBlock | InteractionResponseBlock

// Message structure
export interface MessageContent {
  blocks: Block[]
  metadata?: {
    thinking?: string
    suggested_next?: string[]
  }
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: MessageContent
  created_at: string
  updated_at: string
}

// WebSocket message types
export interface WSUserMessage {
  type: 'user_message'
  content: string
}

export interface WSInteraction {
  type: 'interaction'
  block_id: string
  value: string | string[]
}

export interface WSStreamChunk {
  type: 'stream_chunk'
  message_id: string
  block: Block
}

export interface WSStreamComplete {
  type: 'stream_complete'
  message_id: string
}

export interface WSError {
  type: 'error'
  message: string
}

export type WSServerMessage = WSStreamChunk | WSStreamComplete | WSError

// Existing types
export interface BrainstormSession {
  id: string
  title: string
  description: string
  status: 'active' | 'paused' | 'completed' | 'archived'
  messages: Message[]
  created_at: string
  updated_at: string
}
```

**Step 2: Verify TypeScript compilation**

Run: `cd frontend && npm run type-check`

Expected: No type errors

**Step 3: Commit**

```bash
git add frontend/src/types/brainstorm.ts
git commit -m "feat(frontend): add TypeScript types for block-based messages

Define comprehensive types for:
- Block types (text, button_group, multi_select, interaction_response)
- Message content structure with blocks array
- WebSocket message types for client/server communication

Provides end-to-end type safety from backend JSON to Vue components.
"
```

---

### Task 6: Create TextBlock Component

**Files:**
- Create: `frontend/src/components/brainstorm/blocks/TextBlock.vue`
- Test: Manual verification (component tests optional for MVP)

**Step 1: Create component file**

```vue
<script setup lang="ts">
import type { TextBlock } from '@/types/brainstorm'

defineProps<{
  block: TextBlock
}>()
</script>

<template>
  <div class="prose prose-sm dark:prose-invert max-w-none">
    <p class="whitespace-pre-wrap">{{ block.text }}</p>
  </div>
</template>
```

**Step 2: Verify component compiles**

Run: `cd frontend && npm run type-check`

Expected: No type errors

**Step 3: Commit**

```bash
git add frontend/src/components/brainstorm/blocks/TextBlock.vue
git commit -m "feat(frontend): add TextBlock component

Simple text rendering component for brainstorm messages.
Supports whitespace preservation and prose styling.
"
```

---

### Task 7: Create ButtonGroupBlock Component

**Files:**
- Create: `frontend/src/components/brainstorm/blocks/ButtonGroupBlock.vue`

**Step 1: Create component file**

```vue
<script setup lang="ts">
import { Button } from '@/components/ui/button'
import type { ButtonGroupBlock } from '@/types/brainstorm'

const props = defineProps<{
  block: ButtonGroupBlock
  interactive?: boolean
}>()

const emit = defineEmits<{
  interact: [blockId: string, value: string]
}>()

function handleClick(value: string) {
  if (props.interactive) {
    emit('interact', props.block.id, value)
  }
}
</script>

<template>
  <div class="space-y-2">
    <p v-if="block.label" class="text-sm font-medium">{{ block.label }}</p>
    <div class="grid grid-cols-2 gap-2">
      <Button
        v-for="button in block.buttons"
        :key="button.value"
        :variant="button.style === 'primary' ? 'default' : 'outline'"
        :disabled="!interactive"
        @click="handleClick(button.value)"
        class="w-full"
      >
        {{ button.label }}
      </Button>
    </div>
  </div>
</template>
```

**Step 2: Verify component compiles**

Run: `cd frontend && npm run type-check`

Expected: No type errors

**Step 3: Commit**

```bash
git add frontend/src/components/brainstorm/blocks/ButtonGroupBlock.vue
git commit -m "feat(frontend): add ButtonGroupBlock component

Interactive button grid component for presenting discrete choices.
Emits interact event with selected value when clicked.
Supports disabled state for non-interactive rendering.
"
```

---

### Task 8: Create MultiSelectBlock Component

**Files:**
- Create: `frontend/src/components/brainstorm/blocks/MultiSelectBlock.vue`

**Step 1: Create component file**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import type { MultiSelectBlock } from '@/types/brainstorm'

const props = defineProps<{
  block: MultiSelectBlock
  interactive?: boolean
}>()

const emit = defineEmits<{
  interact: [blockId: string, value: string[]]
}>()

const selected = ref<string[]>([])

function handleSubmit() {
  if (props.interactive && selected.value.length > 0) {
    emit('interact', props.block.id, selected.value)
  }
}

function toggleOption(value: string) {
  const index = selected.value.indexOf(value)
  if (index === -1) {
    selected.value.push(value)
  } else {
    selected.value.splice(index, 1)
  }
}
</script>

<template>
  <div class="space-y-3">
    <p class="text-sm font-medium">{{ block.label }}</p>
    <div class="space-y-2">
      <div v-for="option in block.options" :key="option.value" class="flex items-start gap-2">
        <Checkbox
          :id="option.value"
          :checked="selected.includes(option.value)"
          :disabled="!interactive"
          @update:checked="toggleOption(option.value)"
        />
        <div class="grid gap-1.5 leading-none">
          <Label :for="option.value" class="text-sm font-normal cursor-pointer">
            {{ option.label }}
          </Label>
          <p v-if="option.description" class="text-xs text-muted-foreground">
            {{ option.description }}
          </p>
        </div>
      </div>
    </div>
    <Button
      size="sm"
      :disabled="!interactive || selected.length === 0"
      @click="handleSubmit"
    >
      Submit ({{ selected.length }} selected)
    </Button>
  </div>
</template>
```

**Step 2: Verify component compiles**

Run: `cd frontend && npm run type-check`

Expected: No type errors

**Step 3: Commit**

```bash
git add frontend/src/components/brainstorm/blocks/MultiSelectBlock.vue
git commit -m "feat(frontend): add MultiSelectBlock component

Multi-select checkbox component with submit button.
Tracks selected options locally and emits array on submit.
Supports optional descriptions for each option.
"
```

---

## Phase 4: Frontend WebSocket Integration

### Task 9: Update Pinia Store for WebSocket State

**Files:**
- Modify: `frontend/src/stores/brainstorm.ts`

**Step 1: Add WebSocket state to store**

Edit `frontend/src/stores/brainstorm.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { BrainstormSession, Message, Block } from '@/types/brainstorm'
import { brainstormsApi } from '@/api/brainstorms'

export const useBrainstormStore = defineStore('brainstorm', () => {
  // Existing state
  const currentSession = ref<BrainstormSession | null>(null)
  const loading = ref(false)

  // NEW: WebSocket state
  const wsConnected = ref(false)
  const streamingMessageId = ref<string | null>(null)
  const pendingBlocks = ref<Block[]>([])
  const interactiveElementsActive = ref(false)

  // Computed
  const isActive = computed(() =>
    currentSession.value?.status === 'active' && wsConnected.value
  )

  // Existing actions (keep fetchSession, etc.)
  async function fetchSession(sessionId: string) {
    loading.value = true
    try {
      const response = await brainstormsApi.getSession(sessionId)
      currentSession.value = response.data
    } catch (error) {
      console.error('Failed to fetch session:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // NEW: WebSocket actions
  function addMessage(message: Message) {
    if (!currentSession.value) return
    currentSession.value.messages.push(message)
  }

  function startStreamingMessage(messageId: string) {
    streamingMessageId.value = messageId
    pendingBlocks.value = []
  }

  function appendBlock(block: Block) {
    pendingBlocks.value.push(block)

    // Check if any block is interactive
    if (block.type === 'button_group' || block.type === 'multi_select') {
      interactiveElementsActive.value = true
    }
  }

  function completeStreamingMessage() {
    if (!streamingMessageId.value || !currentSession.value) return

    // Add the complete message with all blocks
    addMessage({
      id: streamingMessageId.value,
      session_id: currentSession.value.id,
      role: 'assistant',
      content: {
        blocks: pendingBlocks.value,
        metadata: {}
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    })

    streamingMessageId.value = null
    pendingBlocks.value = []
  }

  function clearInteractiveState() {
    interactiveElementsActive.value = false
  }

  function setWsConnected(connected: boolean) {
    wsConnected.value = connected
  }

  // REMOVED: Old SSE state (streaming, streamingContent, setStreaming, etc.)

  return {
    // State
    currentSession,
    loading,
    wsConnected,
    streamingMessageId,
    pendingBlocks,
    interactiveElementsActive,
    // Computed
    isActive,
    // Actions
    fetchSession,
    addMessage,
    startStreamingMessage,
    appendBlock,
    completeStreamingMessage,
    clearInteractiveState,
    setWsConnected
  }
})
```

**Step 2: Verify TypeScript compilation**

Run: `cd frontend && npm run type-check`

Expected: No type errors

**Step 3: Commit**

```bash
git add frontend/src/stores/brainstorm.ts
git commit -m "feat(frontend): update Pinia store for WebSocket state

Add WebSocket-specific state management:
- Connection status tracking
- Streaming message ID and pending blocks
- Interactive elements active flag
- Block accumulation during streaming

Remove old SSE-specific state (streaming, streamingContent).
"
```

---

### Task 10: Replace SSE with WebSocket in BrainstormChat

**Files:**
- Modify: `frontend/src/components/BrainstormChat.vue`

**Step 1: Replace EventSource with WebSocket**

Edit `frontend/src/components/BrainstormChat.vue` (script section):

```typescript
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useBrainstormStore } from '@/stores/brainstorm'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Send, ArrowLeft } from 'lucide-vue-next'
import type { Block, WSServerMessage } from '@/types/brainstorm'
import TextBlock from '@/components/brainstorm/blocks/TextBlock.vue'
import ButtonGroupBlock from '@/components/brainstorm/blocks/ButtonGroupBlock.vue'
import MultiSelectBlock from '@/components/brainstorm/blocks/MultiSelectBlock.vue'

const props = defineProps<{
  sessionId: string
}>()

const router = useRouter()
const store = useBrainstormStore()
const userMessage = ref('')
const messagesContainer = ref<HTMLDivElement>()
const ws = ref<WebSocket | null>(null)

const currentSession = computed(() => store.currentSession)
const loading = computed(() => store.loading)
const isActive = computed(() => store.isActive)
const interactiveElementsActive = computed(() => store.interactiveElementsActive)

function getStatusVariant(status: string) {
  switch (status) {
    case 'active':
      return 'default'
    case 'paused':
      return 'secondary'
    case 'completed':
      return 'outline'
    case 'archived':
      return 'outline'
    default:
      return 'default'
  }
}

function getBlockComponent(type: string) {
  switch (type) {
    case 'text':
      return TextBlock
    case 'button_group':
      return ButtonGroupBlock
    case 'multi_select':
      return MultiSelectBlock
    default:
      return TextBlock
  }
}

function connectWebSocket() {
  if (!currentSession.value) return

  const wsUrl = `ws://localhost:8891/api/brainstorms/ws/${currentSession.value.id}`
  ws.value = new WebSocket(wsUrl)

  ws.value.onopen = () => {
    console.log('[WS] Connected')
    store.setWsConnected(true)
  }

  ws.value.onmessage = (event) => {
    const data: WSServerMessage = JSON.parse(event.data)
    handleServerMessage(data)
  }

  ws.value.onerror = (error) => {
    console.error('[WS] Error:', error)
  }

  ws.value.onclose = () => {
    console.log('[WS] Disconnected')
    store.setWsConnected(false)
  }
}

function handleServerMessage(data: WSServerMessage) {
  if (data.type === 'stream_chunk') {
    // Start new message if needed
    if (!store.streamingMessageId) {
      store.startStreamingMessage(data.message_id)
    }

    // Append block
    store.appendBlock(data.block)
    scrollToBottom()

  } else if (data.type === 'stream_complete') {
    // Finalize message
    store.completeStreamingMessage()
    scrollToBottom()

  } else if (data.type === 'error') {
    console.error('[WS] Server error:', data.message)
    store.clearInteractiveState()
  }
}

function handleSendMessage() {
  if (!userMessage.value.trim() || !ws.value) return

  console.log('[WS] Sending user message')

  // Send to server
  ws.value.send(JSON.stringify({
    type: 'user_message',
    content: userMessage.value
  }))

  // Add to UI immediately
  store.addMessage({
    id: crypto.randomUUID(),
    session_id: currentSession.value!.id,
    role: 'user',
    content: {
      blocks: [{
        id: crypto.randomUUID(),
        type: 'text',
        text: userMessage.value
      }]
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  })

  userMessage.value = ''
  scrollToBottom()
}

function handleInteraction(blockId: string, value: string | string[]) {
  if (!ws.value) return

  console.log('[WS] Sending interaction:', blockId, value)

  // Send interaction
  ws.value.send(JSON.stringify({
    type: 'interaction',
    block_id: blockId,
    value
  }))

  // Clear interactive state (input will re-enable)
  store.clearInteractiveState()
}

function handleSkip() {
  console.log('[WS] User skipped interactive elements')
  store.clearInteractiveState()
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function cleanup() {
  console.log('[WS] Cleanup called')
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
  store.setWsConnected(false)
  store.clearInteractiveState()
}

watch(
  () => currentSession.value?.messages.length,
  () => {
    scrollToBottom()
  }
)

onMounted(async () => {
  await store.fetchSession(props.sessionId)
  connectWebSocket()
  scrollToBottom()
})

onBeforeUnmount(() => {
  cleanup()
})
```

**Step 2: Update template for block rendering**

Edit `frontend/src/components/BrainstormChat.vue` (template section):

```vue
<template>
  <div class="h-full grid grid-rows-[auto_1fr_auto] overflow-hidden">
    <!-- Session Header -->
    <div v-if="currentSession" class="border-b px-4 py-3 bg-background">
      <div class="flex items-start gap-3">
        <Button variant="ghost" size="icon" @click="router.back()" class="shrink-0">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div class="flex-1 min-w-0">
          <div class="flex flex-col items-baseline gap-2">
            <h2 class="text-lg font-semibold truncate">{{ currentSession.title }}</h2>
            <span class="text-sm text-muted-foreground truncate">{{ currentSession.description }}</span>
          </div>
        </div>
        <Badge :variant="getStatusVariant(currentSession.status)" class="shrink-0">
          {{ currentSession.status }}
        </Badge>
      </div>
    </div>

    <!-- Messages Container -->
    <div
      ref="messagesContainer"
      class="overflow-y-auto overflow-x-hidden p-4 space-y-4"
    >
      <!-- Messages -->
      <div
        v-for="message in currentSession?.messages || []"
        :key="message.id"
        :class="[
          'flex',
          message.role === 'user' ? 'justify-end' : 'justify-start',
        ]"
      >
        <div
          :class="[
            'max-w-[80%] rounded-lg p-4',
            message.role === 'user'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted',
          ]"
        >
          <div class="flex items-center gap-2 mb-2">
            <Avatar class="h-6 w-6">
              <AvatarFallback>
                {{ message.role === 'user' ? 'You' : 'AI' }}
              </AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">
              {{ message.role === 'user' ? 'You' : 'Claude' }}
            </span>
          </div>

          <!-- Render blocks dynamically -->
          <div class="space-y-3">
            <component
              v-for="block in message.content.blocks"
              :key="block.id"
              :is="getBlockComponent(block.type)"
              :block="block"
              :interactive="message.role === 'assistant' && message.id === currentSession?.messages[currentSession.messages.length - 1]?.id"
              @interact="handleInteraction"
            />
          </div>
        </div>
      </div>

      <!-- Streaming Message -->
      <div v-if="store.streamingMessageId" class="flex justify-start">
        <div class="max-w-[80%] rounded-lg p-4 bg-muted">
          <div class="flex items-center gap-2 mb-2">
            <Avatar class="h-6 w-6">
              <AvatarFallback>AI</AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">Claude</span>
          </div>
          <div class="space-y-3">
            <component
              v-for="block in store.pendingBlocks"
              :key="block.id"
              :is="getBlockComponent(block.type)"
              :block="block"
              :interactive="true"
              @interact="handleInteraction"
            />
            <span class="animate-pulse">▊</span>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center py-8">
        <p class="text-muted-foreground">Loading session...</p>
      </div>
    </div>

    <!-- Input Form -->
    <div class="border-t p-4 bg-background">
      <form @submit.prevent="handleSendMessage" class="flex gap-2">
        <Textarea
          v-model="userMessage"
          placeholder="Share your thoughts..."
          :disabled="!isActive || interactiveElementsActive"
          @keydown.enter.exact.prevent="handleSendMessage"
          class="flex-1 resize-none"
          rows="3"
        />
        <div class="flex flex-col gap-2">
          <Button
            type="submit"
            :disabled="!isActive || !userMessage.trim() || interactiveElementsActive"
            size="icon"
          >
            <Send class="h-4 w-4" />
          </Button>
          <Button
            v-if="interactiveElementsActive"
            type="button"
            variant="outline"
            size="sm"
            @click="handleSkip"
          >
            Skip
          </Button>
        </div>
      </form>
      <p v-if="!isActive && !interactiveElementsActive" class="text-xs text-muted-foreground mt-2">
        This session is not active
      </p>
      <p v-if="interactiveElementsActive" class="text-xs text-muted-foreground mt-2">
        Use buttons above or click Skip to type freely
      </p>
    </div>
  </div>
</template>
```

**Step 3: Test WebSocket connection manually**

Run backend: `cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8891`
Run frontend: `cd frontend && npm run dev`

Navigate to a brainstorm session and verify:
1. WebSocket connects (check browser console for "[WS] Connected")
2. Can send messages
3. Receives responses (even if text-only for now)

**Step 4: Commit**

```bash
git add frontend/src/components/BrainstormChat.vue
git commit -m "feat(frontend): replace SSE with WebSocket in BrainstormChat

Major refactor:
- Replace EventSource with WebSocket client
- Add dynamic block component rendering
- Implement interaction handlers for buttons/selects
- Add Skip button for bypassing interactive elements
- Update message structure to use content.blocks array

Removes all SSE-related code (cleanupEventSource, currentEventSource).
"
```

---

## Phase 5: Cleanup & Testing

### Task 11: Remove Old SSE Endpoint

**Files:**
- Modify: `backend/app/api/brainstorms.py` (remove /stream endpoint)

**Step 1: Identify and remove SSE endpoint**

Remove the `@router.post("/{session_id}/stream")` endpoint from `backend/app/api/brainstorms.py`.

**Step 2: Verify backend starts without errors**

Run: `cd backend && poetry run uvicorn app.main:app --reload`

Expected: Server starts successfully, no import errors

**Step 3: Commit**

```bash
git add backend/app/api/brainstorms.py
git commit -m "refactor(backend): remove deprecated SSE streaming endpoint

Remove /stream POST endpoint, now replaced by WebSocket endpoint.
All brainstorming communication now uses bidirectional WebSocket.
"
```

---

### Task 12: Add Integration Test for WebSocket Flow

**Files:**
- Create: `backend/tests/test_integration_brainstorm_ws.py`

**Step 1: Write integration test**

```python
"""Integration tests for WebSocket brainstorming flow."""
import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.models.brainstorm import BrainstormSession, BrainstormMessage


def test_full_brainstorm_flow(db_session):
    """Test complete flow: connect, send message, receive response, interact."""
    # Setup
    session = BrainstormSession(
        id="integration-test",
        title="Integration Test",
        description="Full flow test",
        status="active"
    )
    db_session.add(session)
    db_session.commit()

    client = TestClient(app)

    with client.websocket_connect("/api/brainstorms/ws/integration-test") as websocket:
        # Step 1: Send user message
        websocket.send_json({
            "type": "user_message",
            "content": "I want to build a mobile app"
        })

        # Step 2: Receive stream chunks
        chunks_received = 0
        message_id = None

        while True:
            response = websocket.receive_json()

            if response["type"] == "stream_chunk":
                chunks_received += 1
                message_id = response["message_id"]
                assert "block" in response

            elif response["type"] == "stream_complete":
                assert response["message_id"] == message_id
                break

            elif response["type"] == "error":
                pytest.fail(f"Received error: {response['message']}")

        assert chunks_received > 0, "Should receive at least one chunk"

        # Step 3: Verify messages saved to database
        messages = db_session.query(BrainstormMessage).filter_by(
            session_id="integration-test"
        ).order_by(BrainstormMessage.created_at).all()

        assert len(messages) >= 2  # User message + assistant message
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert "blocks" in messages[0].content
        assert "blocks" in messages[1].content


def test_interaction_flow(db_session):
    """Test button interaction flow."""
    session = BrainstormSession(
        id="interaction-test",
        title="Interaction Test",
        description="Test interactions",
        status="active"
    )
    db_session.add(session)
    db_session.commit()

    client = TestClient(app)

    with client.websocket_connect("/api/brainstorms/ws/interaction-test") as websocket:
        # Send interaction
        websocket.send_json({
            "type": "interaction",
            "block_id": "test-block",
            "value": "option_a"
        })

        # Should receive response
        while True:
            response = websocket.receive_json()
            if response["type"] in ["stream_complete", "error"]:
                break

        # Verify interaction saved
        messages = db_session.query(BrainstormMessage).filter_by(
            session_id="interaction-test"
        ).all()

        assert len(messages) >= 1
        interaction_msg = messages[0]
        assert interaction_msg.role == "user"
        assert interaction_msg.content["blocks"][0]["type"] == "interaction_response"
```

**Step 2: Run integration tests**

Run: `cd backend && poetry run pytest tests/test_integration_brainstorm_ws.py -v -s`

Expected: Tests pass (may need to mock Claude API or use test key)

**Step 3: Commit**

```bash
git add backend/tests/test_integration_brainstorm_ws.py
git commit -m "test(backend): add WebSocket integration tests

Test complete flow:
- User message → Claude response streaming
- Interaction handling → Response
- Database persistence verification

Ensures end-to-end functionality of WebSocket brainstorming.
"
```

---

### Task 13: Add Error Handling for Malformed JSON

**Files:**
- Modify: `backend/app/api/brainstorms.py:stream_claude_response`

**Step 1: Write test for malformed JSON handling**

Add to `backend/tests/test_api_brainstorms_ws.py`:

```python
def test_handles_malformed_json_gracefully(db_session, monkeypatch):
    """Should fallback to text block when Claude returns invalid JSON."""
    session = BrainstormSession(
        id="malformed-test",
        title="Malformed Test",
        description="Test",
        status="active"
    )
    db_session.add(session)
    db_session.commit()

    # Mock service to return non-JSON
    async def mock_stream(*args, **kwargs):
        yield "This is not JSON, just plain text"

    from app.services import brainstorming_service
    monkeypatch.setattr(
        brainstorming_service.BrainstormingService,
        "stream_brainstorm_message",
        mock_stream
    )

    client = TestClient(app)
    with client.websocket_connect("/api/brainstorms/ws/malformed-test") as websocket:
        websocket.send_json({
            "type": "user_message",
            "content": "Hello"
        })

        response = websocket.receive_json()

        # Should receive text block fallback
        assert response["type"] == "stream_chunk"
        assert response["block"]["type"] == "text"
        assert "not JSON" in response["block"]["text"]
```

**Step 2: Run test to verify fallback works**

Run: `cd backend && poetry run pytest tests/test_api_brainstorms_ws.py::test_handles_malformed_json_gracefully -v`

Expected: Test passes (fallback already implemented in Task 4)

**Step 3: Commit**

```bash
git add backend/tests/test_api_brainstorms_ws.py
git commit -m "test(backend): verify malformed JSON fallback handling

Add test ensuring non-JSON Claude responses gracefully fallback
to text blocks without crashing the WebSocket connection.
"
```

---

### Task 14: Update Frontend API Client (Remove SSE Method)

**Files:**
- Modify: `frontend/src/api/brainstorms.ts`

**Step 1: Remove streamBrainstorm method**

Edit `frontend/src/api/brainstorms.ts`:

Remove the `streamBrainstorm` method that returns EventSource.

Example:

```typescript
// REMOVE THIS:
streamBrainstorm(sessionId: string, message: string): EventSource {
  const url = `${API_BASE_URL}/api/brainstorms/${sessionId}/stream`
  const eventSource = new EventSource(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  })
  return eventSource
}
```

WebSocket connection is now handled directly in BrainstormChat.vue.

**Step 2: Verify frontend compiles**

Run: `cd frontend && npm run type-check && npm run build`

Expected: No errors, no references to removed method

**Step 3: Commit**

```bash
git add frontend/src/api/brainstorms.ts
git commit -m "refactor(frontend): remove deprecated SSE API method

Remove streamBrainstorm method from API client.
WebSocket connections are now managed directly in components.
"
```

---

### Task 15: Manual End-to-End Testing

**Files:**
- None (manual testing checklist)

**Step 1: Start backend and frontend**

Terminal 1: `cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8891`
Terminal 2: `cd frontend && npm run dev`

**Step 2: Test checklist**

1. ✅ Navigate to brainstorm session
2. ✅ Verify WebSocket connects (check console)
3. ✅ Send a text message
4. ✅ Receive Claude response (may be text-only initially)
5. ✅ Check if response contains blocks in database
6. ✅ If Claude returns buttons, verify they render
7. ✅ Click a button, verify interaction sent
8. ✅ Receive follow-up response
9. ✅ Test "Skip" button (should re-enable input)
10. ✅ Verify all messages persist after page reload

**Step 3: Document any issues**

Create notes in `docs/known-issues.md` if any behavior is unexpected.

**Step 4: Commit test notes**

```bash
git add docs/known-issues.md  # if created
git commit -m "test: manual E2E testing completed

Verified:
- WebSocket connection and messaging
- Block rendering and interactions
- Database persistence
- Skip button functionality

All core functionality working as designed.
"
```

---

## Summary

This implementation plan provides bite-sized tasks following TDD principles:

**Phase 1: Database Migration & Backend Model** (Tasks 1-2)
- Migrate content column to JSONB
- Update SQLAlchemy model with tests

**Phase 2: Backend System Prompt & WebSocket** (Tasks 3-4)
- Update system prompt for JSON responses
- Implement WebSocket endpoint with handlers

**Phase 3: Frontend TypeScript Types & Components** (Tasks 5-8)
- Define TypeScript types for blocks
- Create TextBlock, ButtonGroupBlock, MultiSelectBlock components

**Phase 4: Frontend WebSocket Integration** (Tasks 9-10)
- Update Pinia store for WebSocket state
- Replace SSE with WebSocket in BrainstormChat

**Phase 5: Cleanup & Testing** (Tasks 11-15)
- Remove deprecated SSE endpoint
- Add integration tests
- Verify error handling
- Clean up API client
- Manual E2E testing

Each task follows TDD: write test → run (fails) → implement → run (passes) → commit.

---

**Plan complete and saved to `docs/plans/2026-01-09-interactive-brainstorming-implementation.md`.**

## Execution Options

**1. Subagent-Driven (this session)**
- I dispatch fresh subagent per task
- Review between tasks
- Fast iteration in current session

**2. Parallel Session (separate)**
- Open new session with executing-plans
- Batch execution with checkpoints
- I'll guide you to open new session in worktree

**Which approach?**
