# Claude Agent SDK Experiments

This directory contains proof-of-concept experiments for integrating the Claude Agent SDK into interactive applications.

## Experiments

### 1. Brainstorming PoC (`claude-sdk-brainstorming-test.py`)

A proof-of-concept script that validates the Claude Agent SDK for interactive brainstorming sessions.

#### What It Validates

- **Streaming Responses**: Demonstrates real-time streaming of Claude's responses, essential for responsive UI
- **Question Detection**: Parses responses to identify questions and multiple-choice options for interactive UI elements
- **Multi-turn Conversations**: Shows how to maintain conversation context across multiple interactions
- **Tool Restrictions**: Validates restricting tools to `WebSearch` and `WebFetch` only (no code access during brainstorming)

#### Prerequisites

```bash
# Install required package
pip install claude-agent-sdk

# Set your Anthropic API key
export ANTHROPIC_API_KEY='your-api-key-here'
```

#### Running the Test

```bash
cd experiments
python claude-sdk-brainstorming-test.py
```

#### Expected Output

The script will:

1. Start a brainstorming session about a "Smart Meeting Scheduler" feature
2. Stream Claude's response in real-time (you'll see text appearing gradually)
3. Detect any questions and multiple-choice options in the response
4. Continue the conversation with follow-up messages
5. Show statistics about detected interactive elements

#### Sample Output

```
================================================================================
STARTING BRAINSTORMING SESSION
Topic: Smart Meeting Scheduler that uses AI to find optimal meeting times across teams
================================================================================

================================================================================
CLAUDE'S RESPONSE (streaming...)
================================================================================

[Claude's response streams here in real-time...]

================================================================================
DETECTED INTERACTIVE ELEMENTS
================================================================================

Question 1: What size teams will primarily use this feature?
Options detected: 3
  1. Small teams (2-5 people)
  2. Medium teams (5-15 people)
  3. Large teams (15+ people)

In the FastAPI frontend, these would be rendered as:
- Radio buttons or clickable cards for single choice
- Checkboxes for multiple choice
- Quick reply buttons below the chat message
```

## FastAPI Integration Guide

The brainstorming PoC script includes detailed comments showing how to integrate into a FastAPI backend. Key integration points:

### 1. Server-Sent Events (SSE) Endpoint

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

@app.get("/brainstorm/stream")
async def stream_brainstorm(session_id: str, message: str):
    # Initialize session (load from Redis/database)
    session = get_or_create_session(session_id)

    async def event_generator():
        accumulated_text = ""

        async for chunk in session.agent.stream_message(messages):
            accumulated_text += chunk

            # Send text chunk to frontend
            yield {
                "event": "chunk",
                "data": json.dumps({"content": chunk})
            }

            # Check for questions as they form
            if questions := detect_questions(accumulated_text):
                yield {
                    "event": "question",
                    "data": json.dumps(questions[-1])
                }

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())
```

### 2. Session Management

```python
# Store conversation state in Redis
def save_session(session_id: str, conversation_history: List[Dict]):
    redis_client.setex(
        f"session:{session_id}",
        3600,  # 1 hour TTL
        json.dumps(conversation_history)
    )

def load_session(session_id: str) -> List[Dict]:
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else []
```

### 3. Frontend Integration (React/Vue)

```javascript
// Connect to SSE endpoint
const eventSource = new EventSource(`/brainstorm/stream?session_id=${sessionId}&message=${message}`);

eventSource.addEventListener('chunk', (event) => {
    const data = JSON.parse(event.data);
    // Append chunk to UI in real-time
    appendToMessage(data.content);
});

eventSource.addEventListener('question', (event) => {
    const question = JSON.parse(event.data);
    // Render interactive UI element (buttons, cards, etc.)
    renderInteractiveQuestion(question);
});

eventSource.addEventListener('done', () => {
    eventSource.close();
    enableInput();
});
```

## Key Findings

### Question Detection Patterns

The script identifies several patterns for interactive elements:

1. **Numbered lists**: `1. Option A`, `2. Option B`
2. **Lettered lists**: `a. Option A`, `b. Option B`
3. **Bulleted lists**: `- Option A`, `* Option B`
4. **Inline options**: "Would you prefer A, B, or C?"

These patterns can be used to automatically render:
- Radio buttons for single-choice questions
- Checkboxes for multiple-choice questions
- Quick reply buttons for common responses

### Performance Notes

- Streaming is fast and responsive (chunks arrive within milliseconds)
- Question detection adds minimal overhead (~few milliseconds per response)
- Conversation history grows linearly; consider implementing history trimming for long sessions

## Next Steps

1. **FastAPI Implementation**: Create SSE endpoints using the patterns shown
2. **Frontend Components**: Build React/Vue components for interactive questions
3. **State Management**: Implement Redis-based session storage
4. **Testing**: Add unit tests for question detection patterns
5. **Production Hardening**: Add error handling, rate limiting, and authentication

## Troubleshooting

### API Key Issues

```
ERROR: ANTHROPIC_API_KEY environment variable not set
```

**Solution**: Set your API key:
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

### Import Errors

```
ModuleNotFoundError: No module named 'claude_agent_sdk'
```

**Solution**: Install the package:
```bash
pip install claude-agent-sdk
```

### Streaming Issues

If streaming appears slow or buffered, ensure you're:
- Using `flush=True` in print statements
- Not buffering output in your terminal
- Running Python with unbuffered output: `python -u script.py`

## Additional Resources

- [Claude Agent SDK Documentation](https://github.com/anthropics/anthropic-sdk-python)
- [FastAPI Server-Sent Events](https://github.com/sysid/sse-starlette)
- [Building Chat Interfaces](https://platform.openai.com/docs/guides/chat)
