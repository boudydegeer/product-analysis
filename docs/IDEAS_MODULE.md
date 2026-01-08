# Ideas Management Module (Module 3)

## Overview

The Ideas Management Module provides a system to capture, evaluate, and prioritize product ideas using AI-powered analysis with Claude.

## Features

- **Quick Idea Capture**: Create ideas with title, description, and priority
- **AI Evaluation**: Automatic evaluation of business value, technical complexity, estimated effort, market fit, and risks
- **Filtering**: Filter ideas by status and priority
- **Status Tracking**: Backlog → Under Review → Approved → Rejected → Implemented
- **Priority Levels**: Low, Medium, High, Critical

## Architecture

### Backend

- **API**: FastAPI with async endpoints
- **AI Service**: IdeaEvaluationService with Claude API
- **Database**: PostgreSQL with SQLAlchemy 2.0 async
- **Evaluation**: JSON-structured responses from Claude with validation

### Frontend

- **Framework**: Vue 3 + TypeScript + Composition API
- **State**: Pinia store for idea management
- **Components**: IdeaCard, IdeaList with filtering
- **Views**: IdeasView (list), IdeaDetailView (detail with evaluation)

## API Endpoints

### Idea Management

- `POST /api/v1/ideas` - Create idea
- `GET /api/v1/ideas` - List ideas (with optional status/priority filters)
- `GET /api/v1/ideas/{id}` - Get idea
- `PUT /api/v1/ideas/{id}` - Update idea
- `DELETE /api/v1/ideas/{id}` - Delete idea

### AI Evaluation

- `POST /api/v1/ideas/evaluate` - Evaluate idea with AI

## Database Schema

### ideas

- `id` (string, PK)
- `title` (string, max 200)
- `description` (text)
- `status` (enum: backlog, under_review, approved, rejected, implemented)
- `priority` (enum: low, medium, high, critical)
- `business_value` (integer 1-10, nullable)
- `technical_complexity` (integer 1-10, nullable)
- `estimated_effort` (string, nullable)
- `market_fit_analysis` (text, nullable)
- `risk_assessment` (text, nullable)
- `created_at`, `updated_at` (timestamptz)

## Configuration

Add to `backend/.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

## Usage Example

### Creating an Idea

```bash
curl -X POST http://localhost:8891/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Dark Mode Feature",
    "description": "Add dark mode support to improve user experience",
    "priority": "high"
  }'
```

### Evaluating an Idea

```bash
curl -X POST http://localhost:8891/api/v1/ideas/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Dark Mode Feature",
    "description": "Add dark mode support to improve user experience"
  }'
```

Response:
```json
{
  "business_value": 8,
  "technical_complexity": 5,
  "estimated_effort": "2 weeks",
  "market_fit_analysis": "Strong demand based on user feedback and industry trends",
  "risk_assessment": "Low risk - standard UI implementation with well-established patterns"
}
```

## Testing

### Backend

```bash
cd backend
poetry run pytest tests/test_api_ideas.py -v
poetry run pytest tests/test_integration_ideas.py -v
```

### Frontend

```bash
cd frontend
npm run test -- src/stores/__tests__/ideas.spec.ts
npm run test -- src/components/__tests__/IdeaCard.spec.ts
```

## Future Enhancements

- Kanban board view with drag-and-drop
- Priority matrix visualization (business value vs complexity)
- Team voting system
- Link to Features module (promote approved ideas)
- Link to Brainstorming sessions (refine ideas)
- Link to Competitor Analysis (ideas from insights)
- Bulk operations (approve/reject multiple ideas)
- Comments and discussion threads
