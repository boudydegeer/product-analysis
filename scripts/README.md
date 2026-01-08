# Scripts

This directory contains automation scripts for the Product Analysis Platform, including quality verification and plan management utilities.

## Scripts Overview

### 1. `archive-plan.sh`

Archives completed plan documents from `docs/plans/` to `docs/plans/archived/` and updates the index.

#### What it does:

1. **Moves plan files** - Relocates completed plans to the archived/ subdirectory
2. **Updates index.md** - Modifies links to point to archived location and adds "(Archived)" notation
3. **Creates archive directory** - Automatically creates `docs/plans/archived/` if it doesn't exist
4. **Interactive confirmation** - Prompts before archiving (unless `--yes` flag is used)
5. **Batch archiving** - Supports archiving multiple plans in one command

#### Usage:

```bash
# Archive a single plan
./scripts/archive-plan.sh 2026-01-07-product-analysis-platform-mvp.md

# Archive multiple plans at once
./scripts/archive-plan.sh plan1.md plan2.md plan3.md

# Skip confirmation prompt
./scripts/archive-plan.sh -y plan1.md

# Dry-run mode (preview changes without making them)
./scripts/archive-plan.sh --dry-run plan1.md

# Show help
./scripts/archive-plan.sh --help
```

#### Features:

- **Validation** - Ensures files exist, are .md files, and are in the correct directory
- **Colored output** - Green for success, yellow for warnings, red for errors
- **Error handling** - Gracefully handles missing files, permission errors, and invalid inputs
- **Backup creation** - Creates `index.md.bak` before modifying the index
- **Summary report** - Shows which files were successfully archived and which failed

#### Example Output:

```
=========================================
  Archive Plan Documents
=========================================

Plans to archive: 1
  - 2026-01-07-product-analysis-platform-mvp.md

Archiving: 2026-01-07-product-analysis-platform-mvp.md
  ✓ Created archive directory
  ✓ Moved file to archive
  ✓ Updated index.md
  ✓ Successfully archived '2026-01-07-product-analysis-platform-mvp.md'

=========================================
  Summary
=========================================

✓ Successfully archived (1):
  - 2026-01-07-product-analysis-platform-mvp.md

Archived files location:
  /path/to/docs/plans/archived
```

---

### 2. `verify-plan-status.sh`

Verifies consistency between docs/plans/index.md and the actual project state.

#### Purpose:
- Auto-fixes obvious issues (statistics, dates, formatting)
- Reports plans that may be stale or incorrect
- Suggests status updates based on git history
- Validates plan file existence and links

#### Usage:

```bash
# Run verification with auto-fixes
./scripts/verify-plan-status.sh

# Report only, no auto-fixes
./scripts/verify-plan-status.sh --report-only

# Verbose output
./scripts/verify-plan-status.sh --verbose

# Dry-run (preview fixes)
./scripts/verify-plan-status.sh --dry-run

# Show help
./scripts/verify-plan-status.sh --help
```

#### What it checks:
- ✅ Plan file existence (referenced in index.md)
- ✅ Statistics accuracy (counts and percentages)
- ✅ Staleness (plans without recent commits)
- ✅ Consistency (status matches section)
- ✅ Last Updated date

#### Auto-fixed issues:
- Statistics if counts/percentages are wrong
- Last Updated date if outdated
- Markdown formatting issues

#### Reported issues (require decision):
- Plans "In Progress" without commits in 7+ days
- Plans "Ready" or "In Progress" for 30+ days
- Missing plan files
- Orphaned plan files not in index
- Plans in wrong section

#### Exit codes:
- 0: All checks passed
- 1: Warnings found (plans may need attention)
- 2: Errors found (missing files, broken references)

---

### 3. `check-services.sh`

Checks if backend, frontend, and database services are running on their configured ports.

#### What it checks:

1. **Backend Service** - Port 8891, attempts to verify health via `/docs` endpoint
2. **Frontend Service** - Port 8892
3. **PostgreSQL Database** - Port 5432

#### Usage:

```bash
# From project root
./scripts/check-services.sh
```

#### Exit Codes:

- `0` - All services are running
- `1` - One or more services are not running

#### Example Output:

```
╔════════════════════════════════════════════════════════════╗
║         Service Status Check                              ║
╚════════════════════════════════════════════════════════════╝

Checking backend service (port 8891)...
✓ Backend is running on http://localhost:8891
  API Docs: http://localhost:8891/docs

Checking frontend service (port 8892)...
✓ Frontend is running on http://localhost:8892

Checking PostgreSQL database (port 5432)...
✓ PostgreSQL is running on port 5432

╔════════════════════════════════════════════════════════════╗
║  ✓ All services are running!                             ║
╚════════════════════════════════════════════════════════════╝

Quick links:
  Frontend: http://localhost:8892
  Backend:  http://localhost:8891
  API Docs: http://localhost:8891/docs
```

---

### 3. `dev.sh`

Starts backend and frontend services in FOREGROUND with real-time interleaved logs - ideal for local development.

#### What it does:

1. **Checks prerequisites** - Verifies PostgreSQL is running
2. **Validates ports** - Ensures ports 8891 and 8892 are free (exits with error if occupied)
3. **Starts both services in foreground** - Runs backend and frontend simultaneously
4. **Shows real-time logs** - Displays output from both services in the same terminal with color-coded prefixes
5. **Clean shutdown** - Ctrl+C kills both processes cleanly

#### Usage:

```bash
# From project root
./scripts/dev.sh
```

#### Prerequisites:

- PostgreSQL running on port 5432
- Backend dependencies installed: `cd backend && poetry install`
- Frontend dependencies installed: `cd frontend && npm install`
- Ports 8891 and 8892 must be free

#### Log Prefixes:

- `[BACKEND]` - Cyan colored, for backend logs
- `[FRONTEND]` - Green colored, for frontend logs

#### Stopping:

- Press `Ctrl+C` to stop both services cleanly
- The script automatically kills both processes and cleans up

#### Example Output:

```
╔════════════════════════════════════════════════════════════╗
║         Development Environment - Product Analysis        ║
╚════════════════════════════════════════════════════════════╝

Checking prerequisites...
✓ PostgreSQL is running

╔════════════════════════════════════════════════════════════╗
║  ✓ Prerequisites OK - Starting services...               ║
╚════════════════════════════════════════════════════════════╝

Quick links:
  Frontend: http://localhost:8892
  Backend:  http://localhost:8891
  API Docs: http://localhost:8891/docs

Press Ctrl+C to stop all services

════════════════════════════════════════════════════════════

[BACKEND]  INFO:     Uvicorn running on http://0.0.0.0:8891
[BACKEND]  INFO:     Application startup complete
[FRONTEND] VITE v7.3.1  ready in 234 ms
[FRONTEND] ➜  Local:   http://localhost:8892/
[BACKEND]  INFO:     127.0.0.1:54321 - "GET /docs HTTP/1.1" 200 OK
[FRONTEND] ➜  Network: use --host to expose
```

#### When to Use:

- **Local development** - Perfect for actively developing and seeing logs in real-time
- **Debugging** - Easier to see errors and logs from both services simultaneously
- **Quick testing** - Fast startup, easy to stop/restart with Ctrl+C

#### When NOT to Use:

- **Background services** - Use `start-services.sh` instead if you want services running in background
- **CI/CD** - Use individual service commands or `start-services.sh`
- **Production** - Never use for production deployments

---

### 4. `start-services.sh`

Starts backend and frontend services in the background with logging.

#### What it does:

1. **Checks prerequisites** - Verifies PostgreSQL is running
2. **Checks port availability** - Ensures ports 8891 and 8892 are free (offers to kill existing processes)
3. **Starts backend** - Launches backend on port 8891 in background
4. **Starts frontend** - Launches frontend on port 8892 in background
5. **Saves PIDs** - Stores process IDs in `.logs/*.pid` files
6. **Logs output** - Redirects stdout/stderr to `.logs/*.log` files

#### Usage:

```bash
# From project root
./scripts/start-services.sh
```

#### Prerequisites:

- PostgreSQL running on port 5432
- Backend dependencies installed: `cd backend && poetry install`
- Frontend dependencies installed: `cd frontend && npm install`

#### Logs:

- Backend: `.logs/backend.log`
- Frontend: `.logs/frontend.log`
- PIDs: `.logs/backend.pid`, `.logs/frontend.pid`

#### View logs:

```bash
# Watch backend logs
tail -f .logs/backend.log

# Watch frontend logs
tail -f .logs/frontend.log
```

#### Example Output:

```
╔════════════════════════════════════════════════════════════╗
║         Starting Product Analysis Platform                ║
╚════════════════════════════════════════════════════════════╝

Checking prerequisites...
✓ PostgreSQL is running

Starting backend (port 8891)...
✓ Backend started (PID: 12345)
  URL: http://localhost:8891
  Logs: /path/to/.logs/backend.log

Starting frontend (port 8892)...
✓ Frontend started (PID: 12346)
  URL: http://localhost:8892
  Logs: /path/to/.logs/frontend.log

╔════════════════════════════════════════════════════════════╗
║  ✓ All services started successfully!                    ║
╚════════════════════════════════════════════════════════════╝

Quick links:
  Frontend: http://localhost:8892
  Backend:  http://localhost:8891
  API Docs: http://localhost:8891/docs

Logs:
  Backend:  tail -f .logs/backend.log
  Frontend: tail -f .logs/frontend.log

Stop services with: ./scripts/stop-services.sh
```

---

### 5. `stop-services.sh`

Stops backend and frontend services started by `start-services.sh`.

#### What it does:

1. **Reads PIDs** - Loads process IDs from `.logs/*.pid` files
2. **Graceful shutdown** - Sends SIGTERM to each process
3. **Force kill** - Uses SIGKILL if process doesn't respond
4. **Port-based fallback** - If PID files missing, kills processes by port
5. **Cleanup** - Removes PID files

#### Usage:

```bash
# From project root
./scripts/stop-services.sh
```

#### Example Output:

```
╔════════════════════════════════════════════════════════════╗
║         Stopping Product Analysis Platform                ║
╚════════════════════════════════════════════════════════════╝

Stopping backend (PID: 12345)...
✓ Backend stopped

Stopping frontend (PID: 12346)...
✓ Frontend stopped

╔════════════════════════════════════════════════════════════╗
║  ✓ Services stopped (2)                                ║
╚════════════════════════════════════════════════════════════╝
```

---

### 6. `verify-quality-backend.sh`

Verifies quality gates for the **FastAPI/Python backend**.

#### What it checks:

1. **Test Coverage** - Runs pytest with coverage reporting, requires minimum 90% coverage
2. **Code Linting** - Runs ruff to check code quality and potential issues
3. **Code Formatting** - Verifies code is formatted with black
4. **Type Checking** - Runs mypy to ensure type safety

#### Usage:

```bash
# From project root
./scripts/verify-quality-backend.sh

# Or make it executable first
chmod +x scripts/verify-quality-backend.sh
./scripts/verify-quality-backend.sh
```

#### Requirements:

- Must be run from a location where backend directory is accessible
- Requires Poetry to be installed
- All backend dependencies must be installed (`poetry install`)

#### Exit Codes:

- `0` - All checks passed
- `1` - One or more checks failed

#### Example Output:

```
╔════════════════════════════════════════════════════════════╗
║         Backend Quality Verification                      ║
╚════════════════════════════════════════════════════════════╝

[1/4] Running pytest with coverage (minimum 90%)...
✓ Tests passed with sufficient coverage

[2/4] Running ruff linter...
✓ Linting passed

[3/4] Checking code formatting with black...
✓ Code formatting is correct

[4/4] Running type checker (mypy)...
✓ Type checking passed

╔════════════════════════════════════════════════════════════╗
║  ✓ All quality checks passed!                            ║
╚════════════════════════════════════════════════════════════╝
```

---

### 7. `verify-quality-frontend.sh`

Verifies quality gates for the **Vue 3/TypeScript frontend**.

#### What it checks:

1. **Unit Tests** - Runs vitest in run mode (non-watch)
2. **Type Checking** - Verifies TypeScript types via build process
3. **Linting** (optional) - Runs ESLint if configured in package.json

#### Usage:

```bash
# From project root
./scripts/verify-quality-frontend.sh

# Or make it executable first
chmod +x scripts/verify-quality-frontend.sh
./scripts/verify-quality-frontend.sh
```

#### Requirements:

- Must be run from a location where frontend directory is accessible
- Requires Node.js and npm to be installed
- All frontend dependencies must be installed (`npm install`)

#### Exit Codes:

- `0` - All checks passed
- `1` - One or more checks failed

#### Graceful Degradation:

The frontend script is designed to handle missing scripts gracefully:

- If `lint` script doesn't exist in `package.json`, it will skip linting with a warning
- If `type-check` script doesn't exist, it will use the build process for type checking

#### Example Output:

```
╔════════════════════════════════════════════════════════════╗
║         Frontend Quality Verification                     ║
╚════════════════════════════════════════════════════════════╝

[1/3] Running unit tests (vitest)...
✓ Tests passed

[2/3] Running TypeScript type checker...
✓ Type checking passed

[3/3] Checking for linter...
⚠ No lint script found in package.json - skipping
Consider adding ESLint or another linter to your project

╔════════════════════════════════════════════════════════════╗
║ Results: 2/2 checks passed                                   ║
║  ✓ All quality checks passed!                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## Port Configuration

The following ports are used by default:

| Service    | Port | URL                          | Description                    |
|------------|------|------------------------------|--------------------------------|
| Backend    | 8891 | http://localhost:8891        | FastAPI application            |
| Backend    | 8891 | http://localhost:8891/docs   | Swagger UI documentation       |
| Backend    | 8891 | http://localhost:8891/redoc  | ReDoc documentation            |
| Frontend   | 8892 | http://localhost:8892        | Vue 3 application              |
| PostgreSQL | 5432 | postgresql://localhost:5432  | Database                       |

### Overriding Ports

**Backend:**
- Set `PORT` in `backend/.env` file
- Or pass via command line: `uvicorn app.main:app --port YOUR_PORT`

**Frontend:**
- Configured in `frontend/vite.config.ts` (server.port)
- Vite will automatically use next available port if 8892 is occupied

**PostgreSQL:**
- Configured via Docker: `-p YOUR_PORT:5432`
- Update `DATABASE_URL` in `backend/.env` accordingly

---

## Quick Start Guide

### Option A: Development Mode (Foreground with Real-time Logs)

Ideal for active development - see all logs in real-time, easy to restart:

```bash
# 1. Start PostgreSQL
docker run --name postgres-dev \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=product_analysis \
  -p 5432:5432 -d postgres:16

# 2. Start both services with real-time logs
./scripts/dev.sh

# Press Ctrl+C to stop when done
```

### Option B: Background Services (Production-like)

Services run in background, logs saved to files:

```bash
# 1. Start PostgreSQL
docker run --name postgres-dev \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=product_analysis \
  -p 5432:5432 -d postgres:16

# 2. Start all services (backend + frontend)
./scripts/start-services.sh

# 3. Check services are running
./scripts/check-services.sh

# 4. View logs (optional)
tail -f .logs/backend.log   # Backend logs
tail -f .logs/frontend.log  # Frontend logs

# 5. Stop all services when done
./scripts/stop-services.sh
```

---

## Integration with CI/CD

These scripts are designed to be easily integrated into CI/CD pipelines:

### GitHub Actions Example:

```yaml
- name: Run Backend Quality Checks
  run: ./scripts/verify-quality-backend.sh

- name: Run Frontend Quality Checks
  run: ./scripts/verify-quality-frontend.sh
```

### Pre-commit Hook Example:

```bash
#!/bin/bash
./scripts/verify-quality-backend.sh && ./scripts/verify-quality-frontend.sh
```

---

## Troubleshooting

### Service Management Issues:

**Port already in use:**
```bash
# Check what's using the port
lsof -i :8891  # backend
lsof -i :8892  # frontend

# Kill process on port
lsof -ti:8891 | xargs kill -9
lsof -ti:8892 | xargs kill -9
```

**Services won't start:**
1. Check logs in `.logs/` directory
2. Verify PostgreSQL is running: `./scripts/check-services.sh`
3. Verify dependencies are installed:
   - Backend: `cd backend && poetry install`
   - Frontend: `cd frontend && npm install`
4. Check for port conflicts with `lsof -i :8891` and `lsof -i :8892`

**Can't stop services:**
```bash
# Force kill by port
lsof -ti:8891 | xargs kill -9  # backend
lsof -ti:8892 | xargs kill -9  # frontend

# Or manually remove PID files and kill processes
rm -f .logs/*.pid
pkill -f "uvicorn app.main:app"
pkill -f "vite"
```

**PostgreSQL not running:**
```bash
# Start PostgreSQL container
docker run --name postgres-dev \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=product_analysis \
  -p 5432:5432 -d postgres:16

# Or start existing container
docker start postgres-dev
```

**View detailed logs:**
```bash
# Real-time logs
tail -f .logs/backend.log
tail -f .logs/frontend.log

# Full logs
cat .logs/backend.log
cat .logs/frontend.log
```

---

### Backend Issues:

**Coverage below 90%:**
```bash
# Add more tests to increase coverage
cd backend
poetry run pytest --cov=app --cov-report=html
# Open htmlcov/index.html to see coverage report
```

**Black formatting issues:**
```bash
# Auto-fix formatting
cd backend
poetry run black .
```

**Ruff linting issues:**
```bash
# See detailed errors
cd backend
poetry run ruff check .

# Auto-fix some issues
poetry run ruff check --fix .
```

**Mypy type errors:**
```bash
# See detailed type errors
cd backend
poetry run mypy app --show-error-codes
```

### Frontend Issues:

**Test failures:**
```bash
# Run tests in watch mode to debug
cd frontend
npm run test
```

**Type checking issues:**
```bash
# See detailed type errors
cd frontend
npm run build
```

**Missing lint script:**
```bash
# Add ESLint to your project
cd frontend
npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Add lint script to package.json
# "lint": "eslint . --ext .ts,.tsx,.vue"
```

---

## Quality Gates Summary

| Check | Backend | Frontend | Required |
|-------|---------|----------|----------|
| Test Coverage (90%+) | ✓ | - | Yes |
| Unit Tests Pass | ✓ | ✓ | Yes |
| Code Linting | ✓ (ruff) | ✓ (optional) | Backend: Yes, Frontend: Optional |
| Code Formatting | ✓ (black) | - | Backend: Yes |
| Type Checking | ✓ (mypy) | ✓ (tsc) | Yes |

---

## Making Scripts Executable

After cloning the repository, you may need to make the scripts executable:

```bash
chmod +x scripts/archive-plan.sh
chmod +x scripts/check-services.sh
chmod +x scripts/dev.sh
chmod +x scripts/start-services.sh
chmod +x scripts/stop-services.sh
chmod +x scripts/verify-quality-backend.sh
chmod +x scripts/verify-quality-frontend.sh
```

Or run them directly with bash:

```bash
bash scripts/archive-plan.sh plan.md
bash scripts/check-services.sh
bash scripts/dev.sh
bash scripts/start-services.sh
bash scripts/stop-services.sh
bash scripts/verify-quality-backend.sh
bash scripts/verify-quality-frontend.sh
```

---

## Skills

This project includes custom Claude Code skills in `.claude/skills/`:
- `update-plan-status/` - Auto-updates plan status during workflow
- `sync-plan-status/` - Intelligently syncs plan status with codebase

See `.claude/skills/README.md` for details on how to use them.

---

## Notes

- Both scripts use colored output for better readability (green for success, red for errors, yellow for warnings)
- Scripts will exit immediately on the first error to provide fast feedback
- All checks must pass for the script to return exit code 0
- Scripts are designed to be idempotent and safe to run multiple times
