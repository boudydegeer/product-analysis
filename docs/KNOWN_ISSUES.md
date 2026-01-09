# Known Issues

This document tracks known issues and limitations in the Product Analysis Platform.

## Module 3: Ideas Management

### AI Evaluation Endpoint Timeout (CRITICAL)

**Issue**: The `/api/v1/ideas/evaluate` endpoint times out when making requests.

**Status**: Under Investigation

**Details**:
- Endpoint: `POST /api/v1/ideas/evaluate`
- Symptom: Request hangs indefinitely without returning response
- Impact: AI-powered idea evaluation feature is non-functional
- First Observed: 2026-01-09

**Environment**:
- Backend: Running on port 8891
- Claude Agent SDK: claude-agent-sdk package
- Model: claude-sonnet-4-5
- ANTHROPIC_API_KEY: Configured

**Investigation**:
- Backend server starts successfully without errors
- Health endpoint works: `GET /health` returns `200 OK`
- All other CRUD endpoints work correctly:
  - `GET /api/v1/ideas` - ✅ Working
  - `POST /api/v1/ideas` - ✅ Working
  - `GET /api/v1/ideas/{id}` - ✅ Working
- No error logs in backend output
- Request appears to hang at the `IdeaEvaluationService.evaluate_idea()` call

**Possible Causes**:
1. Claude Agent SDK `receive_messages()` async generator may be waiting indefinitely
2. Network/connection issue with Anthropic API
3. SDK client connection lifecycle issue
4. Async context manager cleanup not being triggered

**Workaround**:
- Use `evaluate=false` when creating ideas via `POST /api/v1/ideas`
- Manual evaluation from detail view should be avoided until fixed

**Next Steps**:
1. Add detailed logging to `IdeaEvaluationService.evaluate_idea()`
2. Add timeout to Claude SDK client calls
3. Test with different Claude models
4. Consider switching to direct Anthropic API calls instead of Agent SDK
5. Add request timeout at FastAPI route level

## Other Modules

### Module 1: Feature Analysis
- No known issues

### Module 2: Brainstorming Sessions

#### Interactive Elements Not Consistently Rendered

**Issue**: Claude sometimes returns interactive button_group elements as JSON code blocks in text instead of proper structured blocks.

**Status**: Behavioral Limitation

**Details**:
- Manual E2E testing completed on 2026-01-09
- WebSocket connection: ✅ Working correctly
- Message persistence: ✅ Blocks structure saved to database correctly
- Claude responses: ✅ Streaming responses received
- Interactive blocks: ⚠️ Inconsistent format

**Observed Behavior**:
When asked "Can you suggest some features for a mobile app?", Claude responded with:
- Text content with JSON code block containing button_group structure
- Instead of returning proper structured blocks like:
  ```json
  [
    {"type": "text", "text": "..."},
    {"type": "button_group", "buttons": [...]}
  ]
  ```
- Claude returned:
  ```
  "I'd love to help! ```json\n[...button_group...]```"
  ```

**Root Cause**:
- System prompt instructs Claude to return JSON array of blocks
- Claude understood the intent but chose to embed the JSON in a markdown code block
- This is a model behavior issue, not a code bug
- The current system prompt may need reinforcement about strict JSON structure

**Impact**:
- Interactive elements may not render in the UI
- Users see JSON code instead of clickable buttons
- Workaround: Users can read the options and type their choice manually

**Possible Solutions**:
1. Enhance system prompt with more explicit JSON formatting requirements
2. Add post-processing to extract JSON from code blocks
3. Use few-shot examples in the system prompt showing exact expected format
4. Add validation layer that rejects non-conforming responses

**Test Results** (2026-01-09):
- ✅ Backend startup successful (port 8891)
- ✅ Frontend startup successful (port 8892)
- ✅ WebSocket connection established
- ✅ Text message sent successfully
- ✅ Claude response received (973 chars)
- ✅ Messages persisted to database with blocks structure
- ✅ Database query confirms proper JSONB storage
- ⚠️ Interactive blocks embedded in text instead of structured blocks
- ℹ️ Skip button not tested (no interaction elements rendered)
- ℹ️ Page refresh persistence not tested (requires UI interaction)

### Module 4: Brainstorming Sessions
- Not yet implemented

---

**Last Updated**: 2026-01-09
