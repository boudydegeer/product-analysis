# Product Analysis Platform

Full-stack application for AI-powered feature analysis using GitHub Actions and Claude Agent SDK. Users submit feature requests, which are analyzed by Claude running in GitHub Actions, with results returned via webhook or polling.

## Tech Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0 (async), PostgreSQL, APScheduler
- **Frontend**: Vue 3 (Composition API + TypeScript), Vite, shadcn-vue, Pinia, Vue Router
- **Infrastructure**: GitHub Actions + Claude Agent SDK, Docker (PostgreSQL)
- **Testing**: pytest (backend), Vitest (frontend)

## Features

### Feature Analysis Flow

Submit feature requests through the UI and receive comprehensive AI-powered analysis:

1. User submits feature description via frontend form
2. Backend creates Feature record and triggers GitHub Action workflow
3. Claude Agent explores codebase and generates detailed analysis
4. Results delivered via webhook (production) or polling (localhost)
5. Analysis presented in interactive UI with multiple views

### Analysis Details UI

View comprehensive AI-generated analysis for features in a four-tab interface:
- **Overview**: Summary, key points, and metrics
- **Implementation**: Architecture, technical details, and data flow
- **Risks & Warnings**: Technical risks, security concerns, scalability issues
- **Recommendations**: Priority improvements, best practices, next steps

See [docs/features/analysis-details-ui.md](docs/features/analysis-details-ui.md) for details.

## Modules

### Module 3: Ideas Management ✅

Capture, evaluate, and prioritize product ideas with AI-powered analysis.

- Create and manage product ideas
- AI evaluation with Claude (business value, complexity, effort, market fit, risks)
- Filter by status and priority
- Status tracking (backlog → under review → approved → rejected → implemented)
- Priority levels (low, medium, high, critical)

[Full Documentation](docs/IDEAS_MODULE.md)

### Module 4: Brainstorming Sessions ✅

Real-time collaborative ideation with Claude AI co-facilitation.

- Create and manage brainstorming sessions
- Stream AI responses with Server-Sent Events
- Persistent conversation history
- Session status tracking (active, paused, completed, archived)
- Chat interface with real-time updates

[Full Documentation](docs/BRAINSTORMING_MODULE.md)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for PostgreSQL)
- Poetry (Python dependency management)
- GitHub repository with Actions enabled
- Anthropic API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd product-analysis
   ```

2. **Start PostgreSQL**
   ```bash
   docker run --name postgres-dev \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=product_analysis \
     -p 5432:5432 -d postgres:16
   ```

3. **Setup Backend**
   ```bash
   cd backend
   poetry install
   cp .env.example .env
   # Edit .env with your configuration
   poetry run alembic upgrade head
   ```

4. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   ```

5. **Configure GitHub Actions**
   - Add `ANTHROPIC_API_KEY` to repository secrets
   - Update `GITHUB_REPO` in backend/.env

### Development

**Option A: Run services in foreground with real-time logs**
```bash
./scripts/dev.sh
```

**Option B: Run services in background**
```bash
./scripts/start-services.sh  # Start services
./scripts/check-services.sh  # Verify services are running
./scripts/stop-services.sh   # Stop services when done
```

**Access the application:**
- Frontend: http://localhost:8892
- Backend API: http://localhost:8891
- API Docs: http://localhost:8891/docs

## Architecture

### Feature Analysis Flow

1. **User submits feature** via frontend form
2. **Backend creates Feature record** with PENDING status
3. **Backend triggers GitHub Action workflow** (`analyze-feature.yml`)
   - Passes feature_id, description, and optional callback_url
   - Workflow installs Claude Agent SDK and runs analysis
   - Claude explores codebase using Read/Glob/Grep/Bash tools
   - Results saved to artifact and optionally POSTed to callback_url
4. **Results return via dual mechanism**:
   - **Webhook (production)**: GitHub Action POSTs to callback_url
   - **Polling (localhost)**: Background scheduler polls workflow status every 30s
5. **Backend updates Feature status** to COMPLETED/FAILED and stores Analysis

### Key Components

**Backend (`/backend/app/`):**
- `models/`: SQLAlchemy models (Feature, Analysis) with async support
- `services/github_service.py`: GitHub Actions API integration
- `services/polling_service.py`: Fallback polling for localhost
- `api/`: FastAPI routers with async endpoints
- `config.py`: Settings via pydantic-settings (env vars)
- `scheduler.py`: APScheduler background task for polling

**Frontend (`/frontend/src/`):**
- `stores/`: Pinia stores for state management (features, analysis)
- `api/`: Axios-based API client with TypeScript
- `components/`: shadcn-vue UI components (Sidebar-07 pattern)
- `router/`: Vue Router with lazy-loaded routes

**GitHub Actions (`.github/workflows/`):**
- `analyze-feature.yml`: Claude Agent SDK workflow with custom system prompt

## Configuration

### Backend Environment Variables

Create `backend/.env`:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/product_analysis
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx        # Token needs repo + workflow permissions
GITHUB_REPO=owner/repo                # Format: owner/repo
SECRET_KEY=xxxxxxxxxxxxx              # For session security

# Optional
DEBUG=true                             # Enable debug mode
WEBHOOK_BASE_URL=                      # Leave empty for localhost (uses polling)
WEBHOOK_SECRET=xxxxxxxxxxxxx          # Secret for webhook verification
ANALYSIS_POLLING_INTERVAL_SECONDS=30  # How often to poll (default: 30)
```

### Frontend Environment Variables

Frontend uses Vite env vars. Backend API URL is configured in `/frontend/src/api/client.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8891'
```

### GitHub Actions Secrets

Required in repository secrets:
- `ANTHROPIC_API_KEY`: Claude API key for Agent SDK

## Testing

### Backend Tests

```bash
cd backend
poetry run pytest -v                  # Run all tests
poetry run pytest --cov=app           # Run with coverage
poetry run pytest --cov=app --cov-report=html  # Generate HTML coverage report
```

### Frontend Tests

```bash
cd frontend
npm test          # Run tests in watch mode
npm run test:run  # Run tests once
```

### Quality Verification

```bash
./scripts/verify-quality-backend.sh   # Backend quality gates
./scripts/verify-quality-frontend.sh  # Frontend quality gates
```

## Database

### Schema

```sql
features
  - id (string, primary key)
  - name, description (text)
  - status (enum: pending|analyzing|completed|failed)
  - priority (integer)
  - analysis_workflow_run_id (string, nullable)
  - created_at, updated_at (timestamptz)

analyses
  - id (integer, autoincrement)
  - feature_id (foreign key to features.id, cascade delete)
  - result (json)
  - tokens_used, model_used (string)
  - completed_at (timestamptz)
  - created_at, updated_at (timestamptz)
```

### Migrations

```bash
cd backend

# Apply migrations
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Rollback one migration
poetry run alembic downgrade -1
```

## Scripts

The `scripts/` directory contains automation tools for development and quality assurance.

### Service Management

- `dev.sh` - Start services in foreground with real-time logs
- `start-services.sh` - Start services in background
- `stop-services.sh` - Stop background services
- `check-services.sh` - Check if services are running

### Quality Verification

- `verify-quality-backend.sh` - Backend quality gates (tests, linting, types)
- `verify-quality-frontend.sh` - Frontend quality gates (tests, types)

### Plan Management

- `archive-plan.sh` - Archive completed plan documents
- `verify-plan-status.sh` - Verify plan status consistency

See [scripts/README.md](scripts/README.md) for detailed documentation.

## Development Workflow

See [docs/QUALITY_WORKFLOW.md](docs/QUALITY_WORKFLOW.md) for the complete quality workflow including:

- Test-Driven Development (TDD) requirements
- Code review process
- Quality gates checklist
- UI screenshot verification

## Documentation

- [CLAUDE.md](CLAUDE.md) - Project instructions for Claude Code
- [docs/QUALITY_WORKFLOW.md](docs/QUALITY_WORKFLOW.md) - Quality workflow and standards
- [docs/features/](docs/features/) - Feature documentation
- [docs/plans/](docs/plans/) - Implementation plans and design documents
- [scripts/README.md](scripts/README.md) - Scripts documentation

## API Documentation

Once the backend server is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8891/docs
- **ReDoc**: http://localhost:8891/redoc

## Troubleshooting

### Port Conflicts

```bash
# Check what's using a port
lsof -i :8891  # backend
lsof -i :8892  # frontend

# Kill process on port
lsof -ti:8891 | xargs kill -9
lsof -ti:8892 | xargs kill -9
```

### PostgreSQL Issues

```bash
# Start PostgreSQL container
docker start postgres-dev

# Or create new container if it doesn't exist
docker run --name postgres-dev \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=product_analysis \
  -p 5432:5432 -d postgres:16
```

### View Service Logs

```bash
# If using background services
tail -f .logs/backend.log
tail -f .logs/frontend.log
```

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]
