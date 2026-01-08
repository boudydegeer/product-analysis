# Quality Workflow - Product Analysis Platform

## Overview

Mandatory quality system to ensure minimum quality standards for all code changes in the Product Analysis Platform. This workflow applies to **ALL** code changes including new features, bug fixes, and refactoring tasks.

**Core Principle**: Quality is not negotiable. No task is complete until all quality gates pass.

---

## Core Principles

### 1. TDD Obligatorio (MUST)

Test-Driven Development is mandatory for all implementation work.

**Requirements**:
- Use `/test-driven-development` skill at the START of every implementation
- Follow the Red → Green → Refactor cycle
- Tests must be written BEFORE implementation code
- Coverage requirement: **90%+ mandatory**

**Why TDD?**
- Catches bugs early in development
- Ensures code is testable by design
- Provides living documentation
- Reduces debugging time
- Improves code quality and maintainability

### 2. Visual Verification (UI Changes)

All UI changes must be visually verified before completion.

**Process**:
1. Start frontend in dev or preview mode
2. Navigate to the modified component/page
3. Capture screenshot using Playwright
4. Review screenshot visually before completing task

**Required for**: All tasks that modify UI components, pages, or styling

**Command**:
```bash
npm run screenshot -- --url=http://localhost:5173/path
```

### 3. Mandatory Skills by Task Type

Different task types require different skill workflows.

#### New Feature
1. `/brainstorming` - Explore requirements and design
2. `/writing-plans` - Create implementation plan
3. `/test-driven-development` - Implement with TDD
4. `/requesting-code-review` - Review before completion

#### Multi-step Task
1. `/writing-plans` - Create implementation plan
2. `/test-driven-development` - Implement with TDD
3. `/requesting-code-review` - Review before completion

#### Simple Bug Fix
1. `/test-driven-development` - Implement with TDD
2. `/requesting-code-review` - Review before completion

#### Refactoring
1. `/test-driven-development` - Ensure tests cover existing behavior
2. Refactor implementation
3. `/requesting-code-review` - Review before completion

### 4. Quality Gates (Checklist Before Completion)

Every task MUST pass ALL these gates before being marked as completed:

- ✅ **Tests written first** (TDD methodology followed)
- ✅ **Tests passing** with 90%+ coverage
- ✅ **Linting without errors**
  - Backend: `poetry run ruff check .`
  - Frontend: `npm run lint` (if configured)
- ✅ **Type checking without errors**
  - Backend: `poetry run mypy app`
  - Frontend: `npm run type-check` (if configured)
- ✅ **Code review executed and approved** (`/requesting-code-review`)
- ✅ **(UI tasks only) Screenshot verified visually**

---

## Plan Status Management

ALL implementation work should be tracked in `/docs/plans/index.md`. Plan status must be updated automatically at key workflow stages.

### Plan Status Lifecycle

```
🔴 Backlog → 🟣 Ready → 🟡 In Progress → 🟢 For Review → ✅ Done
                               ↓
                          ⚫ Blocked (any stage)
```

### Automatic Status Updates

Claude automatically updates plan status at these points:

1. **After `/brainstorming`** → Register new plan as **Backlog** (🔴)
   - Design document created
   - Not yet planned for implementation

2. **After `/writing-plans`** → Update to **Ready** (🟣)
   - Implementation plan completed
   - Ready to start coding

3. **When first todo marked `in_progress`** → Update to **In Progress** (🟡)
   - Active implementation started
   - Developers working on it

4. **When ALL todos completed** → Update to **Done** (✅)
   - Implementation finished
   - All quality gates passed
   - Code reviewed and merged

5. **When blocked** → Update to **Blocked** (⚫)
   - Implementation cannot proceed
   - Waiting on dependencies, decisions, or fixes

### Manual Status Management

Use the `/update-plan-status` skill or helper script for manual updates:

```bash
# Register new plan
node scripts/update-plan-status.js --register \
  --file=2026-01-08-feature-name.md \
  --title="Feature Name" \
  --description="Brief description" \
  --status=backlog

# Update plan status
node scripts/update-plan-status.js --update \
  --file=2026-01-08-feature-name.md \
  --status=in-progress \
  --note="Started implementing API endpoints"

# List all plans
node scripts/update-plan-status.js --list
```

**Note**: Skills are located in `.claude/skills/` in the project root and are versioned in git for team-wide availability.

### Archiving Completed Plans

Plans are NOT automatically archived. Archive manually when needed:

```bash
# Archive a completed plan
./scripts/archive-plan.sh 2026-01-08-feature-name.md
```

Archived plans:
- Move to `/docs/plans/archived/`
- Remain in index.md with updated path
- Keep "Done" status with "(Archived)" note

### Integration with Quality Gates

Before marking any task as **completed**, if it's part of a plan:

- ✅ All quality gates passed (tests, linting, type checking, review)
- ✅ Plan status updated to appropriate state
- ✅ If last task of plan: Update plan to "Done"

### Best Practices

1. **One plan per feature/module** - Don't mix unrelated work
2. **Descriptive notes** - When updating status, explain why
3. **Keep index.md current** - Update status promptly, don't batch
4. **Archive old plans** - Keep active plans visible, archive completed work periodically
5. **Reference plan in commits** - Link commits to plan docs when relevant

### Tools Reference

| Tool | Purpose | Usage |
|------|---------|-------|
| `update-plan-status.js` | Update plan status | `node scripts/update-plan-status.js --help` |
| `archive-plan.sh` | Archive completed plans | `./scripts/archive-plan.sh <filename>` |
| `/update-plan-status` | Skill for automatic updates | Called automatically by Claude |

---

## Helper Scripts

Use the provided scripts to verify quality gates efficiently.

### Backend Quality Verification

```bash
./scripts/verify-quality-backend.sh
```

This script runs:
- All tests with coverage report
- Ruff linting
- MyPy type checking

Exit code 0 = all checks passed, non-zero = failures detected.

### Frontend Quality Verification

```bash
./scripts/verify-quality-frontend.sh
```

This script runs:
- All tests
- Linting (if configured)
- Type checking (if configured)
- Build verification

Exit code 0 = all checks passed, non-zero = failures detected.

### UI Screenshot Capture

```bash
npm run screenshot -- --url=http://localhost:5173/path
```

Captures a screenshot of the specified URL for visual verification.

---

## Workflow Examples

### Example 1: Adding a New Feature

**User Request**: "Add user profile page with avatar upload"

**Claude Workflow**:

1. **Planning Phase**
   - Uses `/brainstorming` to explore requirements
   - Uses `/writing-plans` to design implementation

2. **Implementation Phase**
   - Uses `/test-driven-development`
   - Delegates to claudia:
     - Write tests for profile API endpoint
     - Implement profile endpoint
     - Write tests for ProfilePage component
     - Implement ProfilePage component
     - Write tests for avatar upload
     - Implement avatar upload

3. **Quality Verification Phase**
   - Runs `./scripts/verify-quality-backend.sh`
   - Runs `./scripts/verify-quality-frontend.sh`
   - Takes screenshot of profile page
   - Verifies screenshot visually

4. **Review Phase**
   - Uses `/requesting-code-review`
   - Addresses any review feedback

5. **Completion**
   - Marks task as completed only after all gates pass

### Example 2: Fixing a Bug

**User Request**: "Fix validation error in login form"

**Claude Workflow**:

1. **Implementation Phase**
   - Uses `/test-driven-development`
   - Delegates to claudia:
     - Write test that reproduces the bug (fails - RED)
     - Fix the validation logic (test passes - GREEN)
     - Add additional edge case tests
     - Refactor if needed (REFACTOR)

2. **Quality Verification Phase**
   - Runs `./scripts/verify-quality-frontend.sh`
   - Takes screenshot of login form
   - Verifies screenshot visually

3. **Review Phase**
   - Uses `/requesting-code-review`
   - Addresses any review feedback

4. **Completion**
   - Marks task as completed only after all gates pass

### Example 3: Refactoring Existing Code

**User Request**: "Refactor feature service to use dependency injection"

**Claude Workflow**:

1. **Planning Phase**
   - Uses `/writing-plans` to outline refactoring approach
   - Identifies affected components and tests

2. **Implementation Phase**
   - Uses `/test-driven-development`
   - Delegates to claudia:
     - Ensure existing tests cover current behavior
     - Add any missing tests for edge cases
     - Refactor implementation
     - Verify all tests still pass

3. **Quality Verification Phase**
   - Runs `./scripts/verify-quality-backend.sh`
   - Verifies coverage remains at 90%+

4. **Review Phase**
   - Uses `/requesting-code-review`
   - Addresses any review feedback

5. **Completion**
   - Marks task as completed only after all gates pass

---

## Non-Compliance Protocol

Tasks that don't meet quality gates should **NOT** be marked as completed.

**Process for Blocked Tasks**:

1. **Keep task as `in_progress`** - Do not mark as completed
2. **Create new task(s)** to resolve blockers
   - Example: "Fix failing test in user service"
   - Example: "Resolve type errors in ProfilePage component"
3. **Fix issues** - Work on blocker tasks
4. **Re-run quality gates** - Verify all checks pass
5. **Only then mark as completed** - When all gates are green

**Common Blocker Examples**:
- Tests failing
- Coverage below 90%
- Linting errors
- Type checking errors
- Code review feedback not addressed
- Screenshot reveals UI issues

---

## Quality Metrics

### Test Coverage Requirements

- **Minimum**: 90% line coverage (strict standard)
- **Target**: 95%+ line coverage
- **Measure with**:
  - Backend: `poetry run pytest --cov=app --cov-report=term-missing`
  - Frontend: `npm run test:coverage`

### Code Quality Standards

**Backend**:
- Ruff linting: Zero errors, zero warnings
- MyPy type checking: Zero errors
- All tests passing

**Frontend**:
- ESLint (if configured): Zero errors
- TypeScript: Zero type errors
- All tests passing

### Visual Quality Standards

**UI Changes**:
- Screenshot captures expected behavior
- No visual regressions
- Responsive design verified (if applicable)
- Accessibility considerations met

---

## Tools Reference

### Testing Tools

**Backend**:
- pytest: Test framework
- pytest-asyncio: Async test support
- pytest-cov: Coverage reporting
- aiosqlite: In-memory test database

**Frontend**:
- Vitest: Test framework
- Vue Test Utils: Component testing
- jsdom: DOM environment for tests
- Playwright: E2E and screenshot testing

### Quality Tools

**Backend**:
- Ruff: Fast Python linter
- MyPy: Static type checker
- Black: Code formatter

**Frontend**:
- ESLint: JavaScript/TypeScript linter
- Prettier: Code formatter
- TypeScript: Static type checker

---

## Best Practices

### Writing Tests

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Test edge cases** and error conditions
4. **Mock external dependencies** (APIs, databases)
5. **Keep tests independent** - no shared state between tests

### TDD Red-Green-Refactor

1. **RED**: Write a failing test that defines desired behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve code quality while keeping tests green

### Code Review

1. **Review for correctness** - Does it solve the problem?
2. **Review for quality** - Is it maintainable?
3. **Review for performance** - Are there bottlenecks?
4. **Review for security** - Are there vulnerabilities?
5. **Review for tests** - Is coverage adequate?

---

## Plan Status Verification

Use verification tools to keep `/docs/plans/index.md` synchronized with reality.

### Automatic Verification

Run the verification script to auto-fix obvious issues and report problems:

```bash
./scripts/verify-plan-status.sh
```

**Auto-fixes:**
- ✅ Statistics (counts and percentages)
- ✅ Last Updated date
- ✅ Markdown formatting

**Reports for review:**
- ⚠️ Stale plans (no commits in 7+ days)
- ⚠️ Long-running plans (30+ days)
- ⚠️ Missing files
- ⚠️ Status inconsistencies

### Intelligent Synchronization

Use the `/sync-plan-status` skill for Claude to analyze code and update statuses:

```bash
# In Claude Code CLI
/sync-plan-status
```

**Note**: The `update-plan-status` and `sync-plan-status` skills are located in `.claude/skills/` and are part of this project's repository.

**What Claude does:**
1. Runs verification script first
2. For each warning/discrepancy:
   - Reads plan document
   - Checks codebase for implementation
   - Reviews git commits and activity
   - Analyzes tests and TODOs
3. Suggests status updates with evidence
4. Asks for confirmation before updating
5. Updates index.md with detailed notes

**When to sync:**
- After major development milestones
- Weekly/monthly project audits
- When index.md seems out of date
- Before project status meetings

### Best Practices

1. **Run verification regularly** - Weekly or after major changes
2. **Investigate warnings** - Stale plans may need status updates
3. **Use sync for deep analysis** - Let Claude verify implementation state
4. **Keep plans current** - Update as work progresses, not in batches
5. **Archive old plans** - Keep active plans visible and relevant

---

## Notes

- This workflow applies to **ALL** code changes (features, bugs, refactoring)
- **No exceptions** - quality is not negotiable
- If quality gates fail, the task is not complete
- Screenshots should be reviewed by Claude before completing UI tasks
- Coverage threshold: **90%+ (strict standard)**
- Quality gates must pass before merge/PR creation
- All skills (`/test-driven-development`, `/requesting-code-review`, etc.) are mandatory for their respective task types

---

## Quick Reference

### Task Type Decision Tree

```
Is it a new feature?
├─ Yes → /brainstorming → /writing-plans → /test-driven-development → /requesting-code-review
└─ No
   └─ Is it multi-step?
      ├─ Yes → /writing-plans → /test-driven-development → /requesting-code-review
      └─ No → /test-driven-development → /requesting-code-review
```

### Quality Gate Checklist

Before marking ANY task as completed:

```
□ TDD methodology followed (tests first)
□ All tests passing
□ Coverage ≥ 90%
□ Linting passing (ruff/eslint)
□ Type checking passing (mypy/tsc)
□ Code review completed and approved
□ (UI only) Screenshot verified
```

### Command Quick Reference

```bash
# Backend
cd backend
poetry run pytest --cov=app                     # Tests + coverage
poetry run ruff check .                         # Linting
poetry run mypy app                             # Type checking
./scripts/verify-quality-backend.sh             # All checks

# Frontend
cd frontend
npm run test                                    # Tests
npm run lint                                    # Linting (if configured)
npm run type-check                              # Type checking (if configured)
npm run screenshot -- --url=URL                 # Screenshot
./scripts/verify-quality-frontend.sh            # All checks
```

---

**Remember**: Quality first, speed second. A task done right is better than a task done fast.
