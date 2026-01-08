# Brainstorming Module (Module 4)

## Overview

The Brainstorming Module provides real-time collaborative ideation sessions with AI co-facilitation powered by Claude Agent SDK.

## Features

- **Real-time Chat**: Stream responses from Claude using Server-Sent Events (SSE)
- **Session Management**: Create, update, pause, complete, and archive sessions
- **Conversation History**: Full message persistence in PostgreSQL
- **Multi-user Ready**: Architecture supports future multi-user sessions
- **Status Tracking**: Active, paused, completed, archived states
- **Responsive UI**: Vue 3 with shadcn-vue components

## Architecture

### Backend

- **API**: FastAPI with async endpoints
- **Streaming**: Server-Sent Events (SSE) for Claude responses
- **Database**: PostgreSQL with SQLAlchemy 2.0 async
- **AI Service**: BrainstormingService wraps Anthropic API

### Frontend

- **Framework**: Vue 3 + TypeScript + Composition API
- **State**: Pinia store for session/message management
- **Components**: BrainstormList, BrainstormChat
- **Streaming**: EventSource for SSE consumption

## API Endpoints

### Session Management

- `POST /api/v1/brainstorms` - Create session
- `GET /api/v1/brainstorms` - List sessions
- `GET /api/v1/brainstorms/{id}` - Get session
- `PUT /api/v1/brainstorms/{id}` - Update session
- `DELETE /api/v1/brainstorms/{id}` - Delete session

### Streaming

- `GET /api/v1/brainstorms/{id}/stream?message=...` - Stream Claude response (SSE)

## Database Schema

### brainstorm_sessions

- `id` (string, PK)
- `title` (string)
- `description` (text)
- `status` (enum: active, paused, completed, archived)
- `created_at`, `updated_at` (timestamptz)

### brainstorm_messages

- `id` (string, PK)
- `session_id` (FK → brainstorm_sessions.id, CASCADE)
- `role` (enum: user, assistant)
- `content` (text)
- `created_at`, `updated_at` (timestamptz)

## Configuration

Add to `backend/.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

## Usage Example

### Creating a Session

```bash
curl -X POST http://localhost:8891/api/v1/brainstorms \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mobile App Redesign",
    "description": "Explore ideas for new mobile features"
  }'
```

### Streaming a Message

```bash
curl -N http://localhost:8891/api/v1/brainstorms/{session_id}/stream?message=What%20features%20should%20we%20add
```

## Testing

### Backend

```bash
cd backend
poetry run pytest tests/test_api_brainstorms.py -v
poetry run pytest tests/test_integration_brainstorm.py -v
```

### Frontend

```bash
cd frontend
npm run test -- src/components/__tests__/BrainstormChat.spec.ts
npm run test -- src/tests/integration/brainstorm.spec.ts
```

## Future Enhancements

- Multi-user real-time collaboration (WebSocket)
- Question detection with interactive UI
- Link to Ideas module (create ideas from insights)
- Session sharing and export
- Voice input/output
- Canvas/whiteboard integration
