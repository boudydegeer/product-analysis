# Interactive Brainstorming Elements - Design Document

**Date**: 2026-01-09
**Status**: Design Approved
**Author**: Design collaboration session

## Overview

Transform the brainstorming chat from simple text streaming to an interactive experience where Claude can dynamically present buttons, multi-selects, and other UI elements to guide productive conversations.

## Problem Statement

Current brainstorming implementation:
- Simple text-only streaming chat using Server-Sent Events (SSE)
- No way for Claude to present structured choices
- Users must always type free-form responses
- Limited ability to guide conversations effectively

Desired state:
- Claude can dynamically decide when to show interactive elements
- Support for buttons, multi-selects, and future element types
- Users retain ability to skip interactions and type freely
- Extensible architecture for new UI element types

## Key Design Decisions

### 1. Interactive Element Types
**Decision**: Dynamic combination of all element types based on Claude's assessment

Supported elements:
- **Buttons**: Quick-choice options (2-5 buttons)
- **Multi-select**: Choose multiple options with submit
- **Text blocks**: Regular explanatory text
- Future: Sliders, date pickers, file uploads, etc.

### 2. Decision Authority
**Decision**: Hybrid approach (A + C + D)
- **Claude decides**: AI determines which elements to show based on context
- **Backend validates**: Server validates responses and can override
- **User can force**: "Skip" button allows user to bypass and type freely

### 3. Data Structure
**Decision**: Block-based architecture (Option B)

```json
{
  "blocks": [
    {
      "id": "block_xyz",
      "type": "text",
      "text": "What's your target market?"
    },
    {
      "id": "block_abc",
      "type": "button_group",
      "label": "Select market segment",
      "buttons": [
        {"label": "B2B", "value": "b2b"},
        {"label": "B2C", "value": "b2c"}
      ]
    }
  ],
  "metadata": {
    "thinking": "User needs clarity on scope",
    "suggested_next": ["market_size", "competitors"]
  }
}
```

**Rationale**: Extensible, composable, supports arbitrary element types without schema changes.

### 4. Communication Protocol
**Decision**: WebSocket with automatic response and element-defined behavior

- Replace SSE with bidirectional WebSocket
- Server streams blocks incrementally as Claude generates them
- Interactive elements automatically trigger responses when user interacts
- Element configuration defines behavior (immediate submit, wait for multiple selections, etc.)

### 5. Text Input Behavior
**Decision**: Elements temporarily disable input with skip option (Option B)

When interactive elements appear:
- Textarea becomes disabled
- "Skip to type freely" button appears
- Clicking skip removes interactive elements and re-enables textarea
- User retains full control

### 6. Database Schema
**Decision**: Pure JSONB unified structure (Option C)

Migrate `brainstorm_messages.content` from `TEXT` to `JSONB`:
- No backwards compatibility needed (dev data is disposable)
- User messages: `{"blocks": [{"type": "text", "text": "user input"}]}`
- Assistant messages: Full block structure as shown above
- Unified schema simplifies querying and rendering

### 7. System Prompt Strategy
**Decision**: Hybrid approach (instructions + few-shot examples)

Approximately 700 words combining:
- Clear structural rules for JSON response format
- Block type specifications with constraints
- 2-3 realistic examples showing good/bad patterns
- Guidelines for when to use interactive vs text-only

### 8. WebSocket Implementation
**Decision**: FastAPI native (Option A - simple MVP)

Use FastAPI's built-in WebSocket support:
- Simple for MVP
- Can migrate to Socket.IO later if needed
- Sufficient for single-server deployment

---

## Architecture

### System Flow

```
┌─────────┐                    ┌─────────┐                    ┌──────────────┐
│         │   WebSocket        │         │   Claude Agent SDK │              │
│ Browser │◄──────────────────►│ FastAPI │◄──────────────────►│ Claude API   │
│         │   bidirectional    │         │   streaming        │              │
└─────────┘                    └─────────┘                    └──────────────┘
     │                              │
     │                              │
     ▼                              ▼
┌─────────┐                    ┌─────────┐
│  Pinia  │                    │PostgreSQL│
│  Store  │                    │  JSONB   │
└─────────┘                    └─────────┘
```

### Migration Path (SSE → WebSocket)

**Current (SSE)**:
1. User sends POST request with message
2. Server opens SSE stream
3. Claude generates text chunks
4. Server sends `data: {"type": "chunk", "content": "..."}` events
5. Client accumulates chunks
6. Server sends `data: {"type": "done"}` and closes stream

**New (WebSocket)**:
1. Client connects via `ws://server/api/brainstorms/ws/{session_id}`
2. User sends `{"type": "user_message", "content": "..."}`
3. Server queries Claude Agent SDK
4. Server streams `{"type": "stream_chunk", "block": {...}}` incrementally
5. Client renders blocks as they arrive
6. User interacts → sends `{"type": "interaction", "block_id": "...", "value": "..."}`
7. Server repeats process with interaction context

---

## Database Schema

### Current Schema
```sql
CREATE TABLE brainstorm_messages (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES brainstorm_sessions(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,  -- Plain text
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
```

### New Schema
```sql
CREATE TABLE brainstorm_messages (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES brainstorm_sessions(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,
    content JSONB NOT NULL,  -- Block-based structure
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
```

### Example Data

**User message**:
```json
{
  "blocks": [
    {
      "id": "user_abc",
      "type": "text",
      "text": "I want to build a mobile app for fitness tracking"
    }
  ]
}
```

**Assistant message**:
```json
{
  "blocks": [
    {
      "id": "text_1",
      "type": "text",
      "text": "Great! Let's start by understanding your target users."
    },
    {
      "id": "btn_1",
      "type": "button_group",
      "label": "Who is your primary audience?",
      "buttons": [
        {"label": "Casual fitness enthusiasts", "value": "casual"},
        {"label": "Serious athletes", "value": "athletes"},
        {"label": "Rehabilitation patients", "value": "rehab"},
        {"label": "All of the above", "value": "all"}
      ]
    }
  ],
  "metadata": {
    "thinking": "Need to narrow scope before discussing features",
    "suggested_next": ["feature_priorities", "platform_choice"]
  }
}
```

---

## System Prompt Design

### Structure (~700 words)

```markdown
# Role
You are an AI brainstorming facilitator for product development teams.

# Response Format
ALWAYS respond with valid JSON in this exact structure:

{
  "blocks": [...],
  "metadata": {...}
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
        {"label": "Offline mode", "value": "offline"},
        {"label": "Push notifications", "value": "push"},
        {"label": "Analytics dashboard", "value": "analytics"},
        {"label": "Payment integration", "value": "payments"}
      ],
      "min": 1,
      "max": 3
    }
  ]
}

## Bad: Too open-ended for buttons
{
  "blocks": [
    {"id": "1", "type": "text", "text": "What features do you want?"},
    {
      "id": "2",
      "type": "button_group",
      "buttons": [
        {"label": "Type them out", "value": "manual"}  // ❌ This defeats the purpose
      ]
    }
  ]
}

# Remember
- You're facilitating, not interrogating
- Acknowledge user input before asking next question
- Use text blocks to show you understand their vision
- Interactive elements accelerate decision-making, not replace creativity
```

---

## Backend Implementation

### WebSocket Endpoint

**File**: `backend/app/api/brainstorms.py`

```python
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.services.brainstorming_service import BrainstormingService
import json
import logging

logger = logging.getLogger(__name__)

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
            # Verify session exists
            session = await get_session_or_404(db, session_id)
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

                if data["type"] == "user_message":
                    await handle_user_message(websocket, db, session_id, data["content"])

                elif data["type"] == "interaction":
                    await handle_interaction(websocket, db, session_id, data["block_id"], data["value"])

        except WebSocketDisconnect:
            logger.info(f"[WS] Client disconnected from session {session_id}")
        except Exception as e:
            logger.error(f"[WS] Error: {e}", exc_info=True)
            await websocket.send_json({"type": "error", "message": str(e)})


async def handle_user_message(
    websocket: WebSocket,
    db: AsyncSession,
    session_id: str,
    content: str
):
    """Handle user text message."""
    # Save user message to database
    user_message = BrainstormMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content={"blocks": [{"id": str(uuid.uuid4()), "type": "text", "text": content}]}
    )
    db.add(user_message)
    await db.commit()

    # Stream Claude response
    await stream_claude_response(websocket, db, session_id)


async def handle_interaction(
    websocket: WebSocket,
    db: AsyncSession,
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

    # Stream Claude response
    await stream_claude_response(websocket, db, session_id)


async def stream_claude_response(
    websocket: WebSocket,
    db: AsyncSession,
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
            text_parts = [b["text"] for b in msg.content.get("blocks", []) if b["type"] == "text"]
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
                content={"blocks": collected_blocks, "metadata": response_data.get("metadata", {})}
            )
            db.add(assistant_message)
            await db.commit()

            # Signal completion
            await websocket.send_json({
                "type": "stream_complete",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"[WS] Error streaming: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": f"Streaming error: {str(e)}"
            })
```

---

## Frontend Implementation

### WebSocket Client

**File**: `frontend/src/components/BrainstormChat.vue`

```typescript
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useBrainstormStore } from '@/stores/brainstorm'
import type { Block, WSServerMessage } from '@/types/brainstorm'

const store = useBrainstormStore()
const ws = ref<WebSocket | null>(null)
const userMessage = ref('')
const messagesContainer = ref<HTMLDivElement>()

const currentSession = computed(() => store.currentSession)
const isActive = computed(() => store.isActive)
const interactiveElementsActive = computed(() => store.interactiveElementsActive)

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
}

function handleInteraction(blockId: string, value: string | string[]) {
  if (!ws.value) return

  // Send interaction
  ws.value.send(JSON.stringify({
    type: 'interaction',
    block_id: blockId,
    value
  }))

  // Clear interactive state
  store.clearInteractiveState()
}

function handleSkip() {
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
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
  store.setWsConnected(false)
}

onMounted(async () => {
  await store.fetchSession(props.sessionId)
  connectWebSocket()
  scrollToBottom()
})

onBeforeUnmount(() => {
  cleanup()
})
```

**Template** (updated):

```vue
<template>
  <div class="h-full grid grid-rows-[auto_1fr_auto] overflow-hidden">
    <!-- Header (unchanged) -->
    <div v-if="currentSession" class="border-b px-4 py-3 bg-background">
      <!-- ... existing header ... -->
    </div>

    <!-- Messages -->
    <div ref="messagesContainer" class="overflow-y-auto overflow-x-hidden p-4 space-y-4">
      <div
        v-for="message in currentSession?.messages || []"
        :key="message.id"
        :class="['flex', message.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <div :class="['max-w-[80%] rounded-lg p-4', message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted']">
          <!-- Render blocks -->
          <div class="flex items-center gap-2 mb-2">
            <Avatar class="h-6 w-6">
              <AvatarFallback>{{ message.role === 'user' ? 'You' : 'AI' }}</AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">{{ message.role === 'user' ? 'You' : 'Claude' }}</span>
          </div>

          <div class="space-y-3">
            <component
              v-for="block in message.content.blocks"
              :key="block.id"
              :is="getBlockComponent(block.type)"
              :block="block"
              :interactive="message.role === 'assistant'"
              @interact="handleInteraction"
            />
          </div>
        </div>
      </div>

      <!-- Streaming message -->
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
    </div>

    <!-- Input -->
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
      <p v-if="interactiveElementsActive" class="text-xs text-muted-foreground mt-2">
        Use buttons above or click Skip to type freely
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
// ... (implementation above)

function getBlockComponent(type: string) {
  switch (type) {
    case 'text':
      return 'TextBlock'
    case 'button_group':
      return 'ButtonGroupBlock'
    case 'multi_select':
      return 'MultiSelectBlock'
    default:
      return 'TextBlock'
  }
}
</script>
```

### Block Components

**File**: `frontend/src/components/brainstorm/blocks/TextBlock.vue`

```vue
<script setup lang="ts">
import type { TextBlock } from '@/types/brainstorm'

defineProps<{ block: TextBlock }>()
</script>

<template>
  <div class="prose prose-sm dark:prose-invert max-w-none">
    <p class="whitespace-pre-wrap">{{ block.text }}</p>
  </div>
</template>
```

**File**: `frontend/src/components/brainstorm/blocks/ButtonGroupBlock.vue`

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

**File**: `frontend/src/components/brainstorm/blocks/MultiSelectBlock.vue`

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

---

## State Management

**File**: `frontend/src/stores/brainstorm.ts`

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { BrainstormSession, Message, Block } from '@/types/brainstorm'

export const useBrainstormStore = defineStore('brainstorm', () => {
  // State
  const currentSession = ref<BrainstormSession | null>(null)
  const loading = ref(false)
  const wsConnected = ref(false)
  const streamingMessageId = ref<string | null>(null)
  const pendingBlocks = ref<Block[]>([])
  const interactiveElementsActive = ref(false)

  // Computed
  const isActive = computed(() =>
    currentSession.value?.status === 'active' && wsConnected.value
  )

  // Actions
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

  async function fetchSession(sessionId: string) {
    // ... existing implementation
  }

  return {
    currentSession,
    loading,
    wsConnected,
    streamingMessageId,
    pendingBlocks,
    interactiveElementsActive,
    isActive,
    addMessage,
    startStreamingMessage,
    appendBlock,
    completeStreamingMessage,
    clearInteractiveState,
    setWsConnected,
    fetchSession
  }
})
```

---

## TypeScript Types

**File**: `frontend/src/types/brainstorm.ts`

```typescript
// Base block types
export type BlockType = 'text' | 'button_group' | 'multi_select'

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

export type Block = TextBlock | ButtonGroupBlock | MultiSelectBlock

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

---

## Implementation Tasks

### Phase 1: Database Migration
1. Create Alembic migration to change `content` column from TEXT to JSONB
2. Run migration (data loss acceptable in dev environment)
3. Update SQLAlchemy model in `backend/app/models/brainstorm.py`

### Phase 2: Backend WebSocket
1. Update system prompt in `backend/app/services/brainstorming_service.py`
2. Add WebSocket endpoint in `backend/app/api/brainstorms.py`
3. Implement helper functions (`handle_user_message`, `handle_interaction`, `stream_claude_response`)
4. Add JSON validation/sanitization layer
5. Test WebSocket connection with manual client

### Phase 3: Frontend Components
1. Create block component files (`TextBlock.vue`, `ButtonGroupBlock.vue`, `MultiSelectBlock.vue`)
2. Add TypeScript types in `frontend/src/types/brainstorm.ts`
3. Update Pinia store with WebSocket state management
4. Test components in isolation (Storybook/manual testing)

### Phase 4: Frontend WebSocket Integration
1. Replace SSE logic with WebSocket in `BrainstormChat.vue`
2. Implement dynamic component rendering for blocks
3. Add "Skip" button and input state management
4. Test full flow end-to-end

### Phase 5: Cleanup & Testing
1. Remove old SSE endpoint (`/stream`)
2. Add comprehensive error handling
3. Write integration tests for WebSocket flow
4. Test with various Claude response formats
5. Add fallback handling for malformed JSON

---

## Success Criteria

### Functional
- ✅ User can send text messages
- ✅ Claude can respond with interactive elements (buttons, multi-select)
- ✅ User can click buttons to respond
- ✅ User can select multiple options and submit
- ✅ User can skip interactive elements and type freely
- ✅ Messages persist correctly in database with block structure
- ✅ WebSocket handles disconnections gracefully

### Technical
- ✅ Database stores unified JSONB structure for all messages
- ✅ Backend validates Claude's JSON responses
- ✅ Frontend renders blocks dynamically based on type
- ✅ System prompt generates well-structured responses 80%+ of the time
- ✅ Fallback to text-only works when JSON parsing fails
- ✅ Type-safe end-to-end (Python → JSON → TypeScript)

### UX
- ✅ Interactive elements appear smoothly during streaming
- ✅ Input is clearly disabled with helpful message when elements are active
- ✅ "Skip" button is discoverable and works immediately
- ✅ Button/select interactions feel responsive
- ✅ Conversation history displays correctly with mixed content types

---

## Future Enhancements

### Additional Element Types
- Slider (for numeric ranges)
- Date/time picker
- File upload with drag-and-drop
- Inline forms (multiple inputs)
- Code editor block
- Diagram/whiteboard integration

### Advanced Features
- Message editing/regeneration
- Branching conversations (explore multiple paths)
- Export conversation as structured data
- Collaborative sessions (multiple users)
- Voice input/output integration

### System Prompt Evolution
- A/B testing different prompt strategies
- Dynamic prompt adjustment based on session context
- Learning from user feedback (skip rate, interaction patterns)
- Domain-specific prompt variants (technical, creative, strategic)

---

## Risks & Mitigations

### Risk: Claude doesn't consistently generate valid JSON
**Mitigation**:
- Comprehensive system prompt with clear examples
- Backend fallback to text-only rendering
- Validation layer that can salvage partial JSON
- Monitor and log parsing failures for prompt iteration

### Risk: WebSocket connection instability
**Mitigation**:
- Automatic reconnection logic with exponential backoff
- Message queue for unsent interactions
- Graceful degradation to polling if WebSocket unavailable
- Clear UI indicators of connection status

### Risk: Interactive elements confuse users
**Mitigation**:
- Always show "Skip to type freely" option prominently
- First-time user tutorial/tooltip
- Analytics on skip rate to measure friction
- Fallback to text-only mode if user skips repeatedly

### Risk: Complex state management bugs
**Mitigation**:
- Comprehensive integration tests
- State machine for message/block lifecycle
- Detailed logging at each state transition
- Dev tools for inspecting WebSocket messages

---

## Conclusion

This design transforms brainstorming from passive text streaming to an active, guided experience. The block-based architecture provides extensibility for future element types, while the hybrid decision authority (AI + validation + user override) balances guidance with user freedom.

Key innovations:
- **Dynamic structure**: Claude decides what elements to show based on context
- **Extensible architecture**: Adding new block types requires no schema changes
- **User control**: "Skip" button ensures users never feel trapped
- **Type-safe**: End-to-end type checking from Python to Vue

Implementation can proceed incrementally:
1. Database migration (breaking change in dev)
2. Backend WebSocket (parallel to existing SSE)
3. Frontend components (isolated development)
4. Integration (replace SSE with WebSocket)
5. Cleanup (remove old code)

This allows testing at each phase while maintaining a working system.
