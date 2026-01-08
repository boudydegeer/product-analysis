# CLAUDE.md - Product Analysis Platform

## Project Overview

Full-stack application for AI-powered feature analysis using GitHub Actions and Claude Agent SDK. Users submit feature requests, which are analyzed by Claude running in GitHub Actions, with results returned via webhook or polling.

## Tech Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0 (async), PostgreSQL, APScheduler
- **Frontend**: Vue 3 (Composition API + TypeScript), Vite, shadcn-vue, Pinia, Vue Router
- **Infrastructure**: GitHub Actions + Claude Agent SDK, Docker (PostgreSQL)
- **Testing**: pytest (backend), Vitest (frontend)

## Commands

### Backend (from `/backend` directory)

```bash
# Development
poetry install                          # Install dependencies
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8891
                                       # Start dev server on http://localhost:8891

# Database
docker run --name postgres-dev -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=product_analysis -p 5432:5432 -d postgres:16
                                       # Start PostgreSQL container
poetry run alembic upgrade head        # Run migrations
poetry run alembic revision --autogenerate -m "description"
                                       # Create new migration
poetry run alembic downgrade -1        # Rollback one migration

# Code Quality
poetry run pytest                      # Run tests
poetry run pytest --cov=app            # Run tests with coverage
poetry run black .                     # Format code
poetry run ruff check .                # Lint code
poetry run mypy app                    # Type checking

# API Documentation
# Available at http://localhost:8891/docs (Swagger UI)
# Available at http://localhost:8891/redoc (ReDoc)
```

### Frontend (from `/frontend` directory)

```bash
# Development
npm install                            # Install dependencies
npm run dev                            # Start dev server on http://localhost:8892

# Build & Test
npm run build                          # Build for production
npm run preview                        # Preview production build
npm run test                           # Run tests in watch mode
npm run test:run                       # Run tests once
```

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
- `services/github_service.py`: GitHub Actions API integration (trigger workflow, check status, download artifacts)
- `services/polling_service.py`: Fallback polling for localhost (checks ANALYZING features every 30s)
- `api/`: FastAPI routers with async endpoints
- `config.py`: Settings via pydantic-settings (env vars)
- `scheduler.py`: APScheduler background task for polling

**Frontend (`/frontend/src/`):**
- `stores/features.ts`: Pinia store for feature state management
- `api/`: Axios-based API client with TypeScript
- `components/`: shadcn-vue UI components (Sidebar-07 pattern)
- `router/`: Vue Router with lazy-loaded routes

**GitHub Actions (`.github/workflows/`):**
- `analyze-feature.yml`: Claude Agent SDK workflow with custom system prompt
  - Explores codebase to assess maturity (empty|early|partial|mature)
  - Estimates story points, hours, and identifies prerequisites
  - Returns structured JSON with tasks, risks, recommendations

### Database Schema

```
features
  - id (string, primary key)
  - name, description (text)
  - status (enum: pending|analyzing|completed|failed)
  - priority (integer)
  - analysis_workflow_run_id (string, nullable)
  - webhook_received_at (timestamptz, nullable)
  - last_polled_at (timestamptz, nullable)
  - created_at, updated_at (timestamptz)

analyses
  - id (integer, autoincrement)
  - feature_id (foreign key to features.id, cascade delete)
  - result (json)
  - tokens_used, model_used (string)
  - completed_at (timestamptz)
  - created_at, updated_at (timestamptz)
```

## Configuration

### Backend Environment Variables (`/backend/.env`)

Required:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/product_analysis
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx        # Token needs repo + workflow permissions
GITHUB_REPO=owner/repo                # Format: owner/repo
SECRET_KEY=xxxxxxxxxxxxx              # For session security
```

Optional:
```bash
DEBUG=true                             # Enable debug mode
WEBHOOK_BASE_URL=                      # Leave empty for localhost (uses polling)
                                       # Set to https://api.yourapp.com for production
                                       # Set to https://abc123.ngrok.io for localhost webhook testing
WEBHOOK_SECRET=xxxxxxxxxxxxx          # Secret for webhook verification
ANALYSIS_POLLING_INTERVAL_SECONDS=30  # How often to poll (default: 30)
ANALYSIS_POLLING_TIMEOUT_SECONDS=900  # Give up after this time (default: 900)
```

### Frontend Environment Variables

Frontend uses Vite env vars. Backend API URL is configured in `/frontend/src/api/client.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8891'
```

### GitHub Actions Secrets

Required in repository secrets:
- `ANTHROPIC_API_KEY`: Claude API key for Agent SDK

## Important Patterns

### SQLAlchemy 2.0 Async Pattern
```python
# Use select() for queries
from sqlalchemy import select
result = await db.execute(select(Feature).where(Feature.id == feature_id))
feature = result.scalar_one_or_none()

# Use explicit commit
db.add(feature)
await db.commit()
await db.refresh(feature)
```

### Webhook vs Polling Strategy
- **Localhost**: WEBHOOK_BASE_URL empty = polling only (scheduler checks every 30s)
- **Production**: WEBHOOK_BASE_URL set = webhook preferred, polling as backup
- Backend uses APScheduler background task that starts with app
- Polling queries features in ANALYZING status without recent webhook

### CORS Configuration
Backend CORS pre-configured for:
- `http://localhost:8892` (Frontend dev server - default)
- `http://localhost:5173` (Vite dev server - fallback)
- `http://localhost:5174`
- `http://localhost:8080`
- `http://localhost:3000`

## Testing

### Backend Tests
- Use aiosqlite for test database (in-memory)
- pytest-asyncio for async test support
- Fixtures for db session, test client
- Tests isolated with transaction rollback

### Frontend Tests
- Vitest with jsdom environment
- Vue Test Utils for component testing
- Mock axios for API calls

## Development Workflow

1. **Start PostgreSQL**: `docker run --name postgres-dev -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=product_analysis -p 5432:5432 -d postgres:16`
2. **Setup backend**: `cd backend && poetry install && poetry run alembic upgrade head`
3. **Start backend**: `poetry run uvicorn app.main:app --reload`
4. **Setup frontend**: `cd frontend && npm install`
5. **Start frontend**: `npm run dev`
6. **Configure GitHub**: Set ANTHROPIC_API_KEY secret in repo settings

## Quality Workflow (MANDATORY)

ALL code changes must follow this quality workflow. No exceptions.

### TDD Obligatorio (MUST)
- Use `/test-driven-development` skill for EVERY implementation
- Write tests BEFORE implementation code
- Coverage requirement: 90%+ mandatory
- Verify: `./scripts/verify-quality-backend.sh` or `./scripts/verify-quality-frontend.sh`

### Mandatory Skills by Task Type

**New Feature:**
1. `/brainstorming` → explore requirements
2. `/writing-plans` → design implementation
3. `/test-driven-development` → implement with TDD
4. `/requesting-code-review` → review before completion

**Multi-step Task:**
1. `/writing-plans` → design implementation
2. `/test-driven-development` → implement with TDD
3. `/requesting-code-review` → review before completion

**Bug Fix:**
1. `/test-driven-development` → implement with TDD
2. `/requesting-code-review` → review before completion

### Quality Gates Checklist

Before completing ANY task, verify ALL gates pass:

- ✅ Tests written first (TDD)
- ✅ Tests passing with 90%+ coverage
- ✅ Linting without errors (`ruff`/`eslint`)
- ✅ Type checking without errors (`mypy`/`tsc`)
- ✅ Code review executed (`/requesting-code-review`)
- ✅ (UI only) Screenshot verified visually

### UI Screenshot Verification

For UI changes:
```bash
cd frontend
npm run screenshot -- --url=http://localhost:8892/path --name=feature-name
```

Claude reviews screenshot before completing task.

### Verification Scripts

```bash
# Backend quality gates
./scripts/verify-quality-backend.sh

# Frontend quality gates
./scripts/verify-quality-frontend.sh
```

See `/docs/QUALITY_WORKFLOW.md` for complete documentation.

### Plan Status Management (Automatic)

ALL implementation work must be tracked in `/docs/plans/index.md`. Claude automatically updates plan status at these workflow stages.

**Note**: The `update-plan-status` and `sync-plan-status` skills are located in `.claude/skills/` and are part of this project's repository.

**Automatic Updates:**

1. **After `/brainstorming`** → Register plan as **Backlog** (🔴)
   ```bash
   node scripts/update-plan-status.js --register --file=YYYY-MM-DD-name.md --title="Title" --description="Desc" --status=backlog
   ```

2. **After `/writing-plans`** → Update to **Ready** (🟣)
   ```bash
   node scripts/update-plan-status.js --update --file=YYYY-MM-DD-name.md --status=ready --note="Plan completed"
   ```

3. **When first todo marked `in_progress`** → Update to **In Progress** (🟡)
   ```bash
   node scripts/update-plan-status.js --update --file=YYYY-MM-DD-name.md --status=in-progress --note="Started implementation"
   ```

4. **When ALL todos completed** → Update to **Done** (✅)
   ```bash
   node scripts/update-plan-status.js --update --file=YYYY-MM-DD-name.md --status=done --note="Implementation completed"
   ```

5. **When blocked** → Update to **Blocked** (⚫)
   ```bash
   node scripts/update-plan-status.js --update --file=YYYY-MM-DD-name.md --status=blocked --note="Reason"
   ```

**Manual Archiving:**
```bash
./scripts/archive-plan.sh <filename>  # Archive completed plans to docs/plans/archived/
```

**Verification Tools:**

```bash
# Auto-fix obvious issues, report problems
./scripts/verify-plan-status.sh

# Claude analyzes code and syncs statuses (requires confirmation)
/sync-plan-status
```

Use verification weekly or when index.md seems out of sync with reality.

**Status Lifecycle:** Backlog → Ready → In Progress → For Review → Done (or Blocked at any stage)

## Notes

- Feature IDs are user-provided strings (not auto-generated)
- Analysis results are stored as JSON (flexible schema)
- Polling service only checks features without recent webhooks (5min grace period)
- GitHub Action artifacts retained for 30 days
- Database uses timestamptz for all timestamps (UTC aware)
- Backend uses structured logging with Python logging module
