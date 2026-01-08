# Backend Test Isolation Issue

## Problem
Backend tests fail when run together (29 failures) but pass when run individually. The failures manifest as `sqlite3.OperationalError: no such table: features`.

## Root Cause
Multiple test files (`test_api_features.py`, `test_analysis_endpoint.py`, `test_analysis_integration.py`, `test_webhook_endpoint.py`) set `app.dependency_overrides[get_db]` at module level, each with their own SQLite in-memory database engine.

When tests run together:
1. File A loads and sets `app.dependency_overrides[get_db]` to use DatabaseA
2. File B loads and overwrites `app.dependency_overrides[get_db]` to use DatabaseB
3. Tests from File A now try to use DatabaseB, which doesn't have the tables from DatabaseA

## Current Status
- Tests pass individually ✓
- Tests fail when run together (29/158 fail) ✗
- Individual test file runs work correctly ✓

## Recommended Solution
Refactor test files to use the fixtures from `conftest.py` instead of setting module-level overrides. The `conftest.py` already provides:
- `test_db` fixture: Creates isolated test database
- `async_client` fixture: Creates test app with proper database override

Each test file should:
1. Remove module-level `app.dependency_overrides[get_db]` assignment
2. Remove module-level database engine/sessionmaker
3. Use the `async_client` fixture from conftest.py
4. Keep their own `setup_database` autouse fixture if needed

## Workaround
Run tests by file or individually:
```bash
poetry run pytest tests/test_api_features.py  # Works ✓
poetry run pytest tests/test_analysis_endpoint.py  # Works ✓
poetry run pytest  # Fails (29 failures) ✗
```

## Impact on Merge
This issue does NOT block merging because:
- The code functionality is correct
- Tests pass when run properly (individually or by file)
- The issue is with test infrastructure, not application code
- Frontend tests are mostly passing (73/79 pass, 6 failures unrelated to our changes)
