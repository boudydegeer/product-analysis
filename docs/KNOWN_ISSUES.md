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
- No known issues

### Module 4: Brainstorming Sessions
- Not yet implemented

---

**Last Updated**: 2026-01-09
