# Brainstorm Chat Debugging Guide

## Issues Investigated

1. **Assistant messages NOT being saved to database**
2. **Chatbox NOT re-enabling after Claude finishes responding**

## Investigation Results

### Backend Analysis

#### Code Review (brainstorms.py)

The streaming endpoint at `/api/v1/brainstorms/{session_id}/stream` implements:

1. ✅ User message saving (line 239-246)
2. ✅ Assistant message saving using `async_session_maker` (line 254-305)
3. ✅ Proper error handling with logging
4. ✅ `done` event sent to frontend with `saved` status

**Key Features:**
- Import of `async_session_maker` at function level (line 255)
- Separate database session for saving assistant messages (line 280)
- Enhanced logging with ✓/✗ symbols for success/failure
- Error logging includes full stack traces (`exc_info=True`)
- `done` event includes `saved: boolean` field

#### Database Verification

Manual testing confirmed:
- ✅ Assistant messages CAN be saved successfully
- ✅ Database schema is correct
- ✅ Foreign key constraints are working
- ✅ `async_session_maker` creates valid sessions

#### Test Coverage

All 24 tests pass, including:
- ✅ Stream saves both user and assistant messages
- ✅ `done` event includes `saved` status field
- ✅ Error handling works correctly

### Frontend Analysis

#### Code Review (BrainstormChat.vue)

The component implements:

1. ✅ `cleanupEventSource` function (line 144-150)
   - Closes EventSource connection
   - Calls `store.setStreaming(false)` ← **This should re-enable input**

2. ✅ Event handling (line 183-223)
   - Processes `chunk` events
   - Processes `done` events → calls `cleanupEventSource()`
   - Processes `error` events → calls `cleanupEventSource()`

3. ✅ Input disabled state (line 82)
   - `:disabled="streaming || loading || !isActive"`
   - Reactive to `streaming` computed property

4. ✅ `onBeforeUnmount` cleanup (line 245-249)
   - Ensures EventSource is closed on component unmount

#### Store Analysis (brainstorm.ts)

The Pinia store implements:

1. ✅ `streaming` ref (line 16)
2. ✅ `setStreaming(value: boolean)` action (line 122-124)
3. ✅ `addMessage` action adds messages to UI (line 138-142)

## Why Issues Might Still Occur

### Issue #1: Assistant Messages Not Saved

Even though the code is correct, messages might not be saved if:

1. **Stream is interrupted before completion**
   - EventSource connection drops
   - User navigates away
   - Network timeout

2. **Backend errors are silently caught**
   - Check backend logs for errors marked with ✗
   - Foreign key constraint violations (invalid session_id)
   - Database connection issues

3. **Frontend doesn't consume full stream**
   - EventSource closes early
   - JavaScript errors prevent event processing

**How to diagnose:**
```bash
# Check backend logs for save attempts
cd backend
poetry run uvicorn app.main:app --reload --log-level=INFO

# Look for these log lines:
# ✓ Saved assistant message {id} for session {session_id}  ← SUCCESS
# ✗ Failed to save assistant message for session {session_id}  ← FAILURE
```

### Issue #2: Chatbox Not Re-enabling

Even though the code calls `setStreaming(false)`, input might stay disabled if:

1. **`done` event is never received**
   - Backend crashes before sending `done`
   - Network interruption
   - EventSource closes without `done` event

2. **`cleanupEventSource` is never called**
   - JavaScript error in event handler
   - Event listener not properly attached

3. **Reactivity is broken**
   - Store's `streaming` ref not updating
   - Computed property not re-evaluating

**How to diagnose:**
```javascript
// Open browser console and check:
console.log('Streaming state:', store.streaming)
console.log('Loading state:', store.loading)
console.log('Is active:', store.isActive)

// Add breakpoint in BrainstormChat.vue line 207:
cleanupEventSource()  // ← Does this get called?
```

## How to Debug in Production

### 1. Enable Enhanced Logging

Backend logs now include:
- Starting stream
- Stream completion with content length
- Assistant message save success (✓) or failure (✗)
- Done event sent confirmation

Watch logs in real-time:
```bash
cd backend
poetry run uvicorn app.main:app --reload --log-level=INFO | grep -E "(Starting stream|Stream completed|Saved assistant|Failed to save)"
```

### 2. Check Browser Console

Frontend logs include:
- "Stream completed, adding assistant message"
- "Assistant message added, input should be re-enabled"
- Any EventSource errors

Open Chrome DevTools → Console tab and send a message.

### 3. Verify Database State

Check if assistant messages are actually missing:
```bash
cd backend
poetry run python -c "
import asyncio
from app.database import async_session_maker
from app.models.brainstorm import BrainstormMessage, MessageRole
from sqlalchemy import select, func

async def check():
    async with async_session_maker() as db:
        # Count messages by role
        result = await db.execute(
            select(BrainstormMessage.role, func.count(BrainstormMessage.id))
            .group_by(BrainstormMessage.role)
        )
        counts = result.all()
        for role, count in counts:
            print(f'{role}: {count}')

asyncio.run(check())
"
```

Expected output:
```
MessageRole.USER: X
MessageRole.ASSISTANT: Y  ← Should be non-zero
```

If `ASSISTANT: 0`, messages are definitely not being saved.

### 4. Test EventSource Completion

Add this to browser console while chatting:
```javascript
// Monitor EventSource events
const originalSend = store.sendMessage
store.sendMessage = async function(...args) {
  console.log('[DEBUG] Sending message...')
  const result = await originalSend.apply(this, args)
  console.log('[DEBUG] Message sent, streaming:', store.streaming)
  return result
}

// Monitor store changes
watch(() => store.streaming, (newVal) => {
  console.log('[DEBUG] Streaming changed to:', newVal)
})
```

### 5. Reproduce Issue Systematically

1. Create new brainstorm session
2. Send a short message: "Hello"
3. Wait for full response
4. Check backend logs for "✓ Saved assistant message"
5. Check browser console for "Assistant message added"
6. Check if input is enabled
7. Query database for assistant messages

If step 4 shows ✗ → Backend issue
If step 5 doesn't appear → Frontend event handling issue
If step 6 fails → Frontend state management issue

## Fixes Applied

### Backend Changes (`backend/app/api/brainstorms.py`)

1. ✅ Moved `async_session_maker` import to function level (line 255)
2. ✅ Added enhanced logging with ✓/✗ symbols
3. ✅ Added `exc_info=True` for full error stack traces
4. ✅ Added `saved` boolean to `done` event
5. ✅ Added content length logging
6. ✅ Added check for empty `assistant_content` before saving

### Frontend Changes (`frontend/src/components/BrainstormChat.vue`)

1. ✅ Added console.log for debugging event flow
2. ✅ Added explicit comment about input re-enabling
3. ✅ Ensured `cleanupEventSource` is called in all error paths

### Test Coverage (`backend/tests/test_api_brainstorm_streaming.py`)

1. ✅ Added test for `done` event with `saved` status
2. ✅ Fixed SSE event parsing to handle multiple events in one chunk
3. ✅ All 24 tests passing

## Expected Behavior

### Normal Flow:

1. User sends message
2. Backend logs: "Starting stream for session {id}"
3. Frontend receives chunks, displays with cursor
4. Backend logs: "Stream completed for session {id}, content length: X"
5. Backend logs: "✓ Saved assistant message {msg_id} for session {id}"
6. Backend logs: "Stream completed and done event sent for session {id}"
7. Frontend logs: "Stream completed, adding assistant message"
8. Frontend logs: "Assistant message added, input should be re-enabled"
9. Input is re-enabled (cursor blinking in textarea)

### Error Flow:

If backend fails to save:
- Backend logs: "✗ Failed to save assistant message for session {id}: {error}"
- Frontend still receives `done` event with `saved: false`
- Frontend still re-enables input
- User message and AI response are visible in UI
- But assistant message is NOT in database (will disappear on refresh)

## Next Steps if Issue Persists

1. **Capture full logs during issue reproduction**
   - Backend logs from start to "done event sent"
   - Frontend console logs
   - Network tab showing SSE stream

2. **Check for race conditions**
   - Is user navigating away before stream completes?
   - Is session_id changing?

3. **Verify Anthropic API response**
   - Is the BrainstormingService actually returning chunks?
   - Check if `assistant_content` is empty

4. **Database connection pool issues**
   - Check if database is accepting connections
   - Verify connection pool size in `database.py`

## Contact Information

If issues persist after following this guide, provide:
1. Full backend logs (from "Starting stream" to error)
2. Browser console output
3. Network tab screenshot showing SSE stream
4. Database query results (count of messages by role)
