# Product Analysis Platform - Backend

FastAPI backend for the Product Analysis Platform.

## Setup

1. Install dependencies:
   ```bash
   cd backend
   poetry install
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. Run development server:
   ```bash
   poetry run uvicorn app.main:app --reload --port 8000
   ```

## Testing

```bash
poetry run pytest -v
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
