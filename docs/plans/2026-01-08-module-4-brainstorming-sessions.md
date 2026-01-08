# Module 4: Brainstorming Sessions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Build a real-time collaborative brainstorming system with AI co-facilitation using Claude Agent SDK.

**Architecture:** FastAPI backend with Server-Sent Events (SSE) for streaming Claude responses, PostgreSQL for session/message persistence, Vue 3 frontend with real-time UI updates, Pinia for state management.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Claude Agent SDK, Vue 3, TypeScript, Pinia, shadcn-vue, Server-Sent Events (SSE)

---

## Phase 1: Backend Foundation - Database Models

### Task 1: Create BrainstormSession Model

**Files:**
- Create: `backend/app/models/brainstorm.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write failing test for BrainstormSession model**

Create file `backend/tests/test_models_brainstorm.py`:

```python
"""Tests for brainstorm models."""
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brainstorm import (
    BrainstormSession,
    BrainstormMessage,
    BrainstormSessionStatus,
    MessageRole,
)


class TestBrainstormSessionModel:
    """Tests for BrainstormSession model."""

    @pytest.mark.asyncio
    async def test_create_session(self, db_session: AsyncSession):
        """Test creating a brainstorm session."""
        session = BrainstormSession(
            id="test-session-1",
            title="Mobile App Redesign",
            description="Reimagine the mobile experience",
            status=BrainstormSessionStatus.ACTIVE,
        )

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id == "test-session-1"
        assert session.title == "Mobile App Redesign"
        assert session.status == BrainstormSessionStatus.ACTIVE
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_session_cascade_delete_messages(self, db_session: AsyncSession):
        """Test that deleting session deletes messages."""
        session = BrainstormSession(
            id="test-session-2",
            title="Test Session",
            description="Test description",
        )
        db_session.add(session)
        await db_session.commit()

        message = BrainstormMessage(
            id="msg-1",
            session_id=session.id,
            role=MessageRole.USER,
            content="Hello",
        )
        db_session.add(message)
        await db_session.commit()

        # Delete session
        await db_session.delete(session)
        await db_session.commit()

        # Message should be deleted
        result = await db_session.execute(
            select(BrainstormMessage).where(BrainstormMessage.id == "msg-1")
        )
        assert result.scalar_one_or_none() is None
```

**Step 2: Run test to verify it fails**

```bash
cd backend
poetry run pytest tests/test_models_brainstorm.py::TestBrainstormSessionModel::test_create_session -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.brainstorm'"

**Step 3: Create BrainstormSession model**

Create file `backend/app/models/brainstorm.py`:

```python
"""Brainstorm session and message models."""
from datetime import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SQLEnum

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class BrainstormSessionStatus(str, enum.Enum):
    """Brainstorm session statuses."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, enum.Enum):
    """Message roles."""

    USER = "user"
    ASSISTANT = "assistant"


class BrainstormSession(Base, TimestampMixin):
    """Brainstorm session model."""

    __tablename__ = "brainstorm_sessions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[BrainstormSessionStatus] = mapped_column(
        SQLEnum(BrainstormSessionStatus),
        default=BrainstormSessionStatus.ACTIVE,
        nullable=False,
    )

    # Relationships
    messages: Mapped[list["BrainstormMessage"]] = relationship(
        "BrainstormMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class BrainstormMessage(Base, TimestampMixin):
    """Brainstorm message model."""

    __tablename__ = "brainstorm_messages"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("brainstorm_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    session: Mapped["BrainstormSession"] = relationship(
        "BrainstormSession", back_populates="messages"
    )
```

**Step 4: Update models __init__.py**

Modify `backend/app/models/__init__.py`:

```python
"""Models package."""
from .base import Base, TimestampMixin
from .feature import Feature, FeatureStatus
from .analysis import Analysis
from .brainstorm import (
    BrainstormSession,
    BrainstormMessage,
    BrainstormSessionStatus,
    MessageRole,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "Feature",
    "FeatureStatus",
    "Analysis",
    "BrainstormSession",
    "BrainstormMessage",
    "BrainstormSessionStatus",
    "MessageRole",
]
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/test_models_brainstorm.py::TestBrainstormSessionModel -v
```

Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add backend/app/models/brainstorm.py backend/app/models/__init__.py backend/tests/test_models_brainstorm.py
git commit -m "feat: add BrainstormSession and BrainstormMessage models"
```

---

### Task 2: Create Database Migration for Brainstorm Tables

**Files:**
- Create: `backend/alembic/versions/XXX_add_brainstorm_tables.py`

**Step 1: Generate migration**

```bash
cd backend
poetry run alembic revision --autogenerate -m "add brainstorm tables"
```

Expected: New migration file created in `alembic/versions/`

**Step 2: Review and apply migration**

```bash
poetry run alembic upgrade head
```

Expected: Migration applied successfully

**Step 3: Verify tables exist**

```bash
poetry run python -c "
from app.database import engine
from sqlalchemy import text
import asyncio

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('brainstorm_sessions', 'brainstorm_messages')\"))
        tables = [row[0] for row in result]
        print(f'Tables: {tables}')
        assert 'brainstorm_sessions' in tables
        assert 'brainstorm_messages' in tables

asyncio.run(check())
"
```

Expected: Output shows both tables exist

**Step 4: Commit**

```bash
git add alembic/versions/
git commit -m "feat: add database migration for brainstorm tables"
```

---

## Phase 2: Backend API - Schemas

### Task 3: Create Pydantic Schemas for Brainstorm

**Files:**
- Create: `backend/app/schemas/brainstorm.py`
- Modify: `backend/app/schemas/__init__.py`

**Step 1: Write failing test for schemas**

Add to `backend/tests/test_schemas_brainstorm.py`:

```python
"""Tests for brainstorm schemas."""
from datetime import datetime
from app.schemas.brainstorm import (
    BrainstormSessionCreate,
    BrainstormSessionResponse,
    BrainstormMessageResponse,
)


def test_session_create_schema():
    """Test BrainstormSessionCreate schema validation."""
    data = {
        "title": "Mobile App Redesign",
        "description": "Reimagine the mobile experience",
    }

    schema = BrainstormSessionCreate(**data)
    assert schema.title == "Mobile App Redesign"
    assert schema.description == "Reimagine the mobile experience"


def test_session_response_schema():
    """Test BrainstormSessionResponse schema."""
    data = {
        "id": "session-1",
        "title": "Test Session",
        "description": "Test description",
        "status": "active",
        "messages": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    schema = BrainstormSessionResponse(**data)
    assert schema.id == "session-1"
    assert schema.status == "active"


def test_message_response_schema():
    """Test BrainstormMessageResponse schema."""
    data = {
        "id": "msg-1",
        "session_id": "session-1",
        "role": "user",
        "content": "Hello",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    schema = BrainstormMessageResponse(**data)
    assert schema.role == "user"
    assert schema.content == "Hello"
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_schemas_brainstorm.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.schemas.brainstorm'"

**Step 3: Create brainstorm schemas**

Create file `backend/app/schemas/brainstorm.py`:

```python
"""Brainstorm session and message schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class BrainstormSessionCreate(BaseModel):
    """Schema for creating a brainstorm session."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)


class BrainstormSessionUpdate(BaseModel):
    """Schema for updating a brainstorm session."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    status: str | None = Field(None, pattern="^(active|paused|completed|archived)$")


class BrainstormMessageResponse(BaseModel):
    """Schema for brainstorm message response."""

    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BrainstormSessionResponse(BaseModel):
    """Schema for brainstorm session response."""

    id: str
    title: str
    description: str
    status: str
    messages: list[BrainstormMessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BrainstormMessageCreate(BaseModel):
    """Schema for creating a brainstorm message."""

    content: str = Field(..., min_length=1)
```

**Step 4: Update schemas __init__.py**

Modify `backend/app/schemas/__init__.py`:

```python
"""Schemas package."""
from .feature import (
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
    TriggerAnalysisResponse,
)
from .analysis import (
    AnalysisDetailResponse,
    AnalysisErrorResponse,
)
from .brainstorm import (
    BrainstormSessionCreate,
    BrainstormSessionUpdate,
    BrainstormSessionResponse,
    BrainstormMessageCreate,
    BrainstormMessageResponse,
)

__all__ = [
    "FeatureCreate",
    "FeatureUpdate",
    "FeatureResponse",
    "TriggerAnalysisResponse",
    "AnalysisDetailResponse",
    "AnalysisErrorResponse",
    "BrainstormSessionCreate",
    "BrainstormSessionUpdate",
    "BrainstormSessionResponse",
    "BrainstormMessageCreate",
    "BrainstormMessageResponse",
]
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/test_schemas_brainstorm.py -v
```

Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add backend/app/schemas/brainstorm.py backend/app/schemas/__init__.py backend/tests/test_schemas_brainstorm.py
git commit -m "feat: add brainstorm Pydantic schemas"
```

---

## Phase 3: Backend Service - Claude Agent Integration

### Task 4: Create BrainstormingService with Claude SDK

**Files:**
- Create: `backend/app/services/brainstorming_service.py`
- Modify: `backend/pyproject.toml` (add claude-agent-sdk dependency)

**Step 1: Add Claude Agent SDK dependency**

```bash
cd backend
poetry add anthropic
```

Expected: Package added successfully

**Step 2: Write failing test for BrainstormingService**

Create file `backend/tests/test_service_brainstorming.py`:

```python
"""Tests for brainstorming service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.brainstorming_service import BrainstormingService


class TestBrainstormingService:
    """Tests for BrainstormingService."""

    @pytest.mark.asyncio
    async def test_stream_message(self):
        """Test streaming a brainstorm message."""
        service = BrainstormingService(api_key="test-key")

        messages = [
            {"role": "user", "content": "What are key features of a mobile app?"}
        ]

        # Mock the Anthropic client
        with patch.object(service, 'client') as mock_client:
            mock_stream = AsyncMock()
            mock_stream.__aiter__.return_value = [
                MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="Key ")),
                MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="features ")),
                MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="include...")),
            ]
            mock_client.messages.stream.return_value.__aenter__.return_value.text_stream = mock_stream

            chunks = []
            async for chunk in service.stream_brainstorm_message(messages):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert chunks[0] == "Key "
            assert chunks[1] == "features "

    def test_format_messages(self):
        """Test message formatting."""
        service = BrainstormingService(api_key="test-key")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        formatted = service._format_messages(messages)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello"
```

**Step 3: Run test to verify it fails**

```bash
poetry run pytest tests/test_service_brainstorming.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 4: Create BrainstormingService**

Create file `backend/app/services/brainstorming_service.py`:

```python
"""Service for AI-powered brainstorming with Claude."""
import logging
from typing import AsyncGenerator, Any
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class BrainstormingService:
    """Service for brainstorming with Claude via streaming."""

    SYSTEM_PROMPT = """You are an AI co-facilitator in a product brainstorming session.

Your role:
- Help teams explore ideas and possibilities
- Ask clarifying questions to deepen thinking
- Suggest alternatives and variations
- Identify risks and opportunities
- Summarize key points when requested
- Keep discussions focused and productive

Guidelines:
- Be concise but thoughtful
- Ask one question at a time
- Acknowledge and build on user ideas
- Offer 2-3 alternatives when suggesting options
- Use web search to find relevant information when needed

You have access to WebSearch and WebFetch tools for research."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250514") -> None:
        """Initialize the brainstorming service.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    def _format_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        """Format messages for Claude API.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Formatted messages
        """
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

    async def stream_brainstorm_message(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream a brainstorm response from Claude.

        Args:
            messages: Conversation history with role and content

        Yields:
            Text chunks from Claude's response
        """
        try:
            formatted_messages = self._format_messages(messages)

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self.SYSTEM_PROMPT,
                messages=formatted_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Error streaming brainstorm message: {e}")
            raise

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        await self.client.close()

    async def __aenter__(self) -> "BrainstormingService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/test_service_brainstorming.py -v
```

Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add backend/app/services/brainstorming_service.py backend/tests/test_service_brainstorming.py backend/pyproject.toml backend/poetry.lock
git commit -m "feat: add BrainstormingService with Claude streaming"
```

---

## Phase 4: Backend API - CRUD Endpoints

### Task 5: Create Brainstorm API Router with CRUD

**Files:**
- Create: `backend/app/api/brainstorms.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing tests for CRUD endpoints**

Create file `backend/tests/test_api_brainstorms.py`:

```python
"""Tests for brainstorm API endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brainstorm import BrainstormSession, BrainstormSessionStatus


class TestCreateBrainstormSession:
    """Tests for POST /api/v1/brainstorms endpoint."""

    @pytest.mark.asyncio
    async def test_create_session_valid_data(self, async_client: AsyncClient):
        """Test creating a brainstorm session with valid data."""
        data = {
            "title": "Mobile App Redesign",
            "description": "Reimagine the mobile experience",
        }

        response = await async_client.post("/api/v1/brainstorms", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == data["title"]
        assert result["description"] == data["description"]
        assert result["status"] == "active"
        assert "id" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_create_session_missing_title(self, async_client: AsyncClient):
        """Test creating session without title fails."""
        data = {"description": "Test description"}

        response = await async_client.post("/api/v1/brainstorms", json=data)

        assert response.status_code == 422


class TestGetBrainstormSession:
    """Tests for GET /api/v1/brainstorms/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_exists(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting an existing session."""
        session = BrainstormSession(
            id="test-session-1",
            title="Test Session",
            description="Test description",
        )
        db_session.add(session)
        await db_session.commit()

        response = await async_client.get("/api/v1/brainstorms/test-session-1")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == "test-session-1"
        assert result["title"] == "Test Session"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, async_client: AsyncClient):
        """Test getting non-existent session returns 404."""
        response = await async_client.get("/api/v1/brainstorms/nonexistent")

        assert response.status_code == 404


class TestListBrainstormSessions:
    """Tests for GET /api/v1/brainstorms endpoint."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, async_client: AsyncClient):
        """Test listing sessions when none exist."""
        response = await async_client.get("/api/v1/brainstorms")

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test listing sessions returns all sessions."""
        session1 = BrainstormSession(
            id="session-1", title="Session 1", description="Desc 1"
        )
        session2 = BrainstormSession(
            id="session-2", title="Session 2", description="Desc 2"
        )
        db_session.add_all([session1, session2])
        await db_session.commit()

        response = await async_client.get("/api/v1/brainstorms")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2


class TestUpdateBrainstormSession:
    """Tests for PUT /api/v1/brainstorms/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_session(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating a session."""
        session = BrainstormSession(
            id="session-1",
            title="Original Title",
            description="Original description",
        )
        db_session.add(session)
        await db_session.commit()

        update_data = {"title": "Updated Title", "status": "completed"}
        response = await async_client.put(
            "/api/v1/brainstorms/session-1", json=update_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "Updated Title"
        assert result["status"] == "completed"


class TestDeleteBrainstormSession:
    """Tests for DELETE /api/v1/brainstorms/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_session(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test deleting a session."""
        session = BrainstormSession(
            id="session-1", title="Test", description="Test desc"
        )
        db_session.add(session)
        await db_session.commit()

        response = await async_client.delete("/api/v1/brainstorms/session-1")

        assert response.status_code == 204
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/test_api_brainstorms.py::TestCreateBrainstormSession::test_create_session_valid_data -v
```

Expected: FAIL with "404 Not Found" (route doesn't exist)

**Step 3: Create brainstorms API router**

Create file `backend/app/api/brainstorms.py`:

```python
"""Brainstorm sessions API endpoints."""
import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brainstorm import BrainstormSession, BrainstormSessionStatus
from app.schemas.brainstorm import (
    BrainstormSessionCreate,
    BrainstormSessionUpdate,
    BrainstormSessionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/brainstorms", tags=["brainstorms"])


@router.post(
    "",
    response_model=BrainstormSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/",
    response_model=BrainstormSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_brainstorm_session(
    session_in: BrainstormSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> BrainstormSession:
    """Create a new brainstorm session.

    Args:
        session_in: Session data
        db: Database session

    Returns:
        Created brainstorm session
    """
    session = BrainstormSession(
        id=str(uuid4()),
        title=session_in.title,
        description=session_in.description,
        status=BrainstormSessionStatus.ACTIVE,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"Created brainstorm session: {session.id}")
    return session


@router.get("", response_model=list[BrainstormSessionResponse])
@router.get("/", response_model=list[BrainstormSessionResponse])
async def list_brainstorm_sessions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[BrainstormSession]:
    """List all brainstorm sessions.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of brainstorm sessions
    """
    result = await db.execute(
        select(BrainstormSession)
        .offset(skip)
        .limit(limit)
        .order_by(BrainstormSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return list(sessions)


@router.get("/{session_id}", response_model=BrainstormSessionResponse)
async def get_brainstorm_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> BrainstormSession:
    """Get a specific brainstorm session.

    Args:
        session_id: Session ID
        db: Database session

    Returns:
        Brainstorm session

    Raises:
        HTTPException: If session not found
    """
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brainstorm session {session_id} not found",
        )

    return session


@router.put("/{session_id}", response_model=BrainstormSessionResponse)
async def update_brainstorm_session(
    session_id: str,
    session_update: BrainstormSessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> BrainstormSession:
    """Update a brainstorm session.

    Args:
        session_id: Session ID
        session_update: Update data
        db: Database session

    Returns:
        Updated session

    Raises:
        HTTPException: If session not found
    """
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brainstorm session {session_id} not found",
        )

    # Update fields
    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status":
            value = BrainstormSessionStatus(value)
        setattr(session, field, value)

    await db.commit()
    await db.refresh(session)

    logger.info(f"Updated brainstorm session: {session_id}")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brainstorm_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a brainstorm session.

    Args:
        session_id: Session ID
        db: Database session

    Raises:
        HTTPException: If session not found
    """
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brainstorm session {session_id} not found",
        )

    await db.delete(session)
    await db.commit()

    logger.info(f"Deleted brainstorm session: {session_id}")
```

**Step 4: Update conftest.py to include brainstorm router**

Modify `backend/tests/conftest.py`, add to the `async_client` fixture:

```python
# Add this import at the top
from app.api.brainstorms import router as brainstorms_router

# Inside async_client fixture, add this line after features_router:
test_app.include_router(brainstorms_router)
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/test_api_brainstorms.py -v
```

Expected: PASS (all CRUD tests)

**Step 6: Register router in main.py**

Modify `backend/app/main.py`:

```python
# Add import
from app.api.brainstorms import router as brainstorms_router

# Add after features router
app.include_router(brainstorms_router)
```

**Step 7: Commit**

```bash
git add backend/app/api/brainstorms.py backend/app/main.py backend/tests/test_api_brainstorms.py backend/tests/conftest.py
git commit -m "feat: add brainstorm CRUD API endpoints"
```

---

## Phase 5: Backend API - Streaming Endpoint

### Task 6: Create SSE Streaming Endpoint for Claude

**Files:**
- Modify: `backend/app/api/brainstorms.py`
- Create: `backend/tests/test_api_brainstorm_streaming.py`
- Modify: `backend/app/config.py`

**Step 1: Add ANTHROPIC_API_KEY to config**

Modify `backend/app/config.py`, add this field to Settings class:

```python
# Anthropic
anthropic_api_key: str = Field(
    default="",
    description="Anthropic API key for Claude",
)
```

**Step 2: Add to backend/.env file**

```bash
echo "ANTHROPIC_API_KEY=your-api-key-here" >> backend/.env
```

**Step 3: Write failing test for streaming**

Create file `backend/tests/test_api_brainstorm_streaming.py`:

```python
"""Tests for brainstorm streaming endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from app.models.brainstorm import BrainstormSession, BrainstormMessage, MessageRole


class TestStreamBrainstorm:
    """Tests for streaming brainstorm endpoint."""

    @pytest.mark.asyncio
    async def test_stream_endpoint_returns_sse(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that streaming endpoint returns SSE stream."""
        # Create session
        session = BrainstormSession(
            id="session-1",
            title="Test Session",
            description="Test description",
        )
        db_session.add(session)
        await db_session.commit()

        # Mock BrainstormingService
        async def mock_stream(*args, **kwargs):
            yield "Hello "
            yield "world"

        with patch(
            "app.api.brainstorms.BrainstormingService"
        ) as MockService:
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.stream_brainstorm_message = mock_stream

            response = await async_client.get(
                f"/api/v1/brainstorms/session-1/stream",
                params={"message": "Hello Claude"},
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_stream_saves_messages(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that streaming saves user and assistant messages."""
        session = BrainstormSession(
            id="session-2",
            title="Test",
            description="Test",
        )
        db_session.add(session)
        await db_session.commit()

        async def mock_stream(*args, **kwargs):
            yield "Response text"

        with patch(
            "app.api.brainstorms.BrainstormingService"
        ) as MockService:
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.stream_brainstorm_message = mock_stream

            await async_client.get(
                f"/api/v1/brainstorms/session-2/stream",
                params={"message": "User message"},
            )

            # Verify messages were saved
            await db_session.refresh(session)
            assert len(session.messages) == 2
            assert session.messages[0].role == MessageRole.USER
            assert session.messages[0].content == "User message"
            assert session.messages[1].role == MessageRole.ASSISTANT
```

**Step 4: Run test to verify it fails**

```bash
poetry run pytest tests/test_api_brainstorm_streaming.py::TestStreamBrainstorm::test_stream_endpoint_returns_sse -v
```

Expected: FAIL with "404 Not Found"

**Step 5: Implement streaming endpoint**

Modify `backend/app/api/brainstorms.py`, add these imports at top:

```python
import json
from fastapi.responses import StreamingResponse
from app.config import settings
from app.services.brainstorming_service import BrainstormingService
from app.models.brainstorm import BrainstormMessage, MessageRole
```

Add this endpoint to the router:

```python
@router.get("/{session_id}/stream")
async def stream_brainstorm(
    session_id: str,
    message: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream brainstorm conversation with Claude.

    Args:
        session_id: Session ID
        message: User message
        db: Database session

    Returns:
        SSE stream of Claude's response

    Raises:
        HTTPException: If session not found or API key not configured
    """
    # Verify session exists
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brainstorm session {session_id} not found",
        )

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anthropic API key not configured",
        )

    # Save user message
    user_message = BrainstormMessage(
        id=str(uuid4()),
        session_id=session_id,
        role=MessageRole.USER,
        content=message,
    )
    db.add(user_message)
    await db.commit()

    # Build conversation history
    messages = [
        {"role": msg.role.value, "content": msg.content}
        for msg in session.messages
    ]
    messages.append({"role": "user", "content": message})

    # Stream response
    async def event_generator():
        """Generate SSE events."""
        assistant_content = ""

        try:
            async with BrainstormingService(
                api_key=settings.anthropic_api_key
            ) as brainstorm_service:
                async for chunk in brainstorm_service.stream_brainstorm_message(
                    messages
                ):
                    assistant_content += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Save assistant message
            assistant_message = BrainstormMessage(
                id=str(uuid4()),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
            )
            db.add(assistant_message)
            await db.commit()

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Error streaming brainstorm: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

**Step 6: Run tests to verify they pass**

```bash
poetry run pytest tests/test_api_brainstorm_streaming.py -v
```

Expected: PASS (2 tests)

**Step 7: Commit**

```bash
git add backend/app/api/brainstorms.py backend/app/config.py backend/tests/test_api_brainstorm_streaming.py backend/.env
git commit -m "feat: add SSE streaming endpoint for Claude brainstorming"
```

---

## Phase 6: Frontend Foundation - Types & API Client

### Task 7: Create TypeScript Types for Brainstorm

**Files:**
- Create: `frontend/src/types/brainstorm.ts`
- Modify: `frontend/src/types/index.ts`

**Step 1: Write failing test for types**

Create file `frontend/src/types/__tests__/brainstorm.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import type {
  BrainstormSession,
  BrainstormMessage,
  BrainstormSessionCreate,
  MessageRole,
  BrainstormSessionStatus,
} from '../brainstorm'

describe('Brainstorm Types', () => {
  it('should define BrainstormSession type correctly', () => {
    const session: BrainstormSession = {
      id: 'session-1',
      title: 'Test Session',
      description: 'Test description',
      status: 'active',
      messages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    expect(session.id).toBe('session-1')
    expect(session.status).toBe('active')
  })

  it('should define BrainstormMessage type correctly', () => {
    const message: BrainstormMessage = {
      id: 'msg-1',
      session_id: 'session-1',
      role: 'user',
      content: 'Hello',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    expect(message.role).toBe('user')
    expect(message.content).toBe('Hello')
  })

  it('should define BrainstormSessionCreate type correctly', () => {
    const create: BrainstormSessionCreate = {
      title: 'New Session',
      description: 'New description',
    }

    expect(create.title).toBe('New Session')
  })
})
```

**Step 2: Run test to verify it fails**

```bash
cd frontend
npm run test -- src/types/__tests__/brainstorm.spec.ts
```

Expected: FAIL with "Cannot find module '../brainstorm'"

**Step 3: Create brainstorm types**

Create file `frontend/src/types/brainstorm.ts`:

```typescript
/**
 * Brainstorm session and message types
 */

export type BrainstormSessionStatus = 'active' | 'paused' | 'completed' | 'archived'
export type MessageRole = 'user' | 'assistant'

export interface BrainstormMessage {
  id: string
  session_id: string
  role: MessageRole
  content: string
  created_at: string
  updated_at: string
}

export interface BrainstormSession {
  id: string
  title: string
  description: string
  status: BrainstormSessionStatus
  messages: BrainstormMessage[]
  created_at: string
  updated_at: string
}

export interface BrainstormSessionCreate {
  title: string
  description: string
}

export interface BrainstormSessionUpdate {
  title?: string
  description?: string
  status?: BrainstormSessionStatus
}

export interface StreamChunk {
  type: 'chunk' | 'done' | 'error'
  content?: string
  message?: string
}
```

**Step 4: Update types index.ts**

Modify `frontend/src/types/index.ts`:

```typescript
export * from './feature'
export * from './analysis'
export * from './brainstorm'
```

**Step 5: Run tests to verify they pass**

```bash
npm run test -- src/types/__tests__/brainstorm.spec.ts
```

Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add frontend/src/types/brainstorm.ts frontend/src/types/index.ts frontend/src/types/__tests__/brainstorm.spec.ts
git commit -m "feat: add TypeScript types for brainstorm"
```

---

### Task 8: Create Brainstorm API Client

**Files:**
- Create: `frontend/src/api/brainstorms.ts`
- Modify: `frontend/src/api/index.ts`

**Step 1: Write failing test for API client**

Create file `frontend/src/api/__tests__/brainstorms.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { brainstormsApi } from '../brainstorms'
import apiClient from '../client'

vi.mock('../client')

describe('Brainstorms API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create a session', async () => {
    const mockSession = {
      id: 'session-1',
      title: 'Test',
      description: 'Test desc',
      status: 'active' as const,
      messages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockSession })

    const result = await brainstormsApi.createSession({
      title: 'Test',
      description: 'Test desc',
    })

    expect(result).toEqual(mockSession)
    expect(apiClient.post).toHaveBeenCalledWith('/brainstorms/', {
      title: 'Test',
      description: 'Test desc',
    })
  })

  it('should list sessions', async () => {
    const mockSessions = [
      {
        id: 'session-1',
        title: 'Session 1',
        description: 'Desc 1',
        status: 'active' as const,
        messages: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(apiClient.get).mockResolvedValue({ data: mockSessions })

    const result = await brainstormsApi.listSessions()

    expect(result).toEqual(mockSessions)
    expect(apiClient.get).toHaveBeenCalledWith('/brainstorms/')
  })

  it('should get a session by id', async () => {
    const mockSession = {
      id: 'session-1',
      title: 'Test',
      description: 'Test desc',
      status: 'active' as const,
      messages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(apiClient.get).mockResolvedValue({ data: mockSession })

    const result = await brainstormsApi.getSession('session-1')

    expect(result).toEqual(mockSession)
    expect(apiClient.get).toHaveBeenCalledWith('/brainstorms/session-1')
  })

  it('should create EventSource for streaming', () => {
    const mockEventSource = brainstormsApi.streamBrainstorm('session-1', 'Hello')

    expect(mockEventSource).toBeInstanceOf(EventSource)
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm run test -- src/api/__tests__/brainstorms.spec.ts
```

Expected: FAIL with "Cannot find module '../brainstorms'"

**Step 3: Create brainstorms API client**

Create file `frontend/src/api/brainstorms.ts`:

```typescript
import apiClient from './client'
import type {
  BrainstormSession,
  BrainstormSessionCreate,
  BrainstormSessionUpdate,
} from '@/types/brainstorm'

export const brainstormsApi = {
  /**
   * Create a new brainstorm session
   */
  async createSession(data: BrainstormSessionCreate): Promise<BrainstormSession> {
    const response = await apiClient.post<BrainstormSession>('/brainstorms/', data)
    return response.data
  },

  /**
   * List all brainstorm sessions
   */
  async listSessions(): Promise<BrainstormSession[]> {
    const response = await apiClient.get<BrainstormSession[]>('/brainstorms/')
    return response.data
  },

  /**
   * Get a specific brainstorm session
   */
  async getSession(id: string): Promise<BrainstormSession> {
    const response = await apiClient.get<BrainstormSession>(`/brainstorms/${id}`)
    return response.data
  },

  /**
   * Update a brainstorm session
   */
  async updateSession(
    id: string,
    data: BrainstormSessionUpdate
  ): Promise<BrainstormSession> {
    const response = await apiClient.put<BrainstormSession>(`/brainstorms/${id}`, data)
    return response.data
  },

  /**
   * Delete a brainstorm session
   */
  async deleteSession(id: string): Promise<void> {
    await apiClient.delete(`/brainstorms/${id}`)
  },

  /**
   * Create EventSource for streaming brainstorm
   */
  streamBrainstorm(sessionId: string, message: string): EventSource {
    const baseUrl = apiClient.defaults.baseURL || 'http://localhost:8891/api/v1'
    const url = `${baseUrl}/brainstorms/${sessionId}/stream?message=${encodeURIComponent(message)}`
    return new EventSource(url)
  },
}

export default brainstormsApi
```

**Step 4: Update api index.ts**

Modify `frontend/src/api/index.ts`:

```typescript
export { default as featuresApi } from './features'
export { default as brainstormsApi } from './brainstorms'
export { default as apiClient } from './client'
```

**Step 5: Run tests to verify they pass**

```bash
npm run test -- src/api/__tests__/brainstorms.spec.ts
```

Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add frontend/src/api/brainstorms.ts frontend/src/api/index.ts frontend/src/api/__tests__/brainstorms.spec.ts
git commit -m "feat: add brainstorm API client"
```

---

## Phase 7: Frontend State - Pinia Store

### Task 9: Create Brainstorm Pinia Store

**Files:**
- Create: `frontend/src/stores/brainstorm.ts`

**Step 1: Write failing test for store**

Create file `frontend/src/stores/__tests__/brainstorm.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBrainstormStore } from '../brainstorm'
import { brainstormsApi } from '@/api/brainstorms'

vi.mock('@/api/brainstorms')

describe('Brainstorm Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should create a session', async () => {
    const store = useBrainstormStore()
    const mockSession = {
      id: 'session-1',
      title: 'Test',
      description: 'Test desc',
      status: 'active' as const,
      messages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(brainstormsApi.createSession).mockResolvedValue(mockSession)

    await store.createSession({ title: 'Test', description: 'Test desc' })

    expect(store.currentSession).toEqual(mockSession)
    expect(store.sessions).toHaveLength(1)
  })

  it('should fetch sessions', async () => {
    const store = useBrainstormStore()
    const mockSessions = [
      {
        id: 'session-1',
        title: 'Session 1',
        description: 'Desc 1',
        status: 'active' as const,
        messages: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(brainstormsApi.listSessions).mockResolvedValue(mockSessions)

    await store.fetchSessions()

    expect(store.sessions).toEqual(mockSessions)
    expect(store.loading).toBe(false)
  })

  it('should handle errors', async () => {
    const store = useBrainstormStore()
    vi.mocked(brainstormsApi.listSessions).mockRejectedValue(new Error('Failed'))

    await store.fetchSessions()

    expect(store.error).toBe('Failed')
    expect(store.loading).toBe(false)
  })

  it('should set streaming state', () => {
    const store = useBrainstormStore()

    store.setStreaming(true)
    expect(store.streaming).toBe(true)

    store.setStreaming(false)
    expect(store.streaming).toBe(false)
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm run test -- src/stores/__tests__/brainstorm.spec.ts
```

Expected: FAIL with "Cannot find module '../brainstorm'"

**Step 3: Create brainstorm store**

Create file `frontend/src/stores/brainstorm.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { brainstormsApi } from '@/api/brainstorms'
import type {
  BrainstormSession,
  BrainstormSessionCreate,
  BrainstormSessionUpdate,
  BrainstormMessage,
} from '@/types/brainstorm'

export const useBrainstormStore = defineStore('brainstorm', () => {
  // State
  const currentSession = ref<BrainstormSession | null>(null)
  const sessions = ref<BrainstormSession[]>([])
  const loading = ref(false)
  const streaming = ref(false)
  const error = ref<string | null>(null)
  const streamingContent = ref('')

  // Getters
  const isActive = computed(() => currentSession.value?.status === 'active')

  // Actions
  async function createSession(data: BrainstormSessionCreate) {
    loading.value = true
    error.value = null

    try {
      const session = await brainstormsApi.createSession(data)
      sessions.value.push(session)
      currentSession.value = session
      return session
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to create session'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchSessions() {
    loading.value = true
    error.value = null

    try {
      sessions.value = await brainstormsApi.listSessions()
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to fetch sessions'
      error.value = errorMessage
    } finally {
      loading.value = false
    }
  }

  async function fetchSession(id: string) {
    loading.value = true
    error.value = null

    try {
      currentSession.value = await brainstormsApi.getSession(id)
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to fetch session'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateSession(id: string, data: BrainstormSessionUpdate) {
    loading.value = true
    error.value = null

    try {
      const updated = await brainstormsApi.updateSession(id, data)
      currentSession.value = updated

      // Update in sessions list
      const index = sessions.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        sessions.value[index] = updated
      }

      return updated
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to update session'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteSession(id: string) {
    loading.value = true
    error.value = null

    try {
      await brainstormsApi.deleteSession(id)

      // Remove from sessions list
      sessions.value = sessions.value.filter((s) => s.id !== id)

      if (currentSession.value?.id === id) {
        currentSession.value = null
      }
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to delete session'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  function setStreaming(value: boolean) {
    streaming.value = value
  }

  function setStreamingContent(content: string) {
    streamingContent.value = content
  }

  function appendStreamingContent(chunk: string) {
    streamingContent.value += chunk
  }

  function clearStreamingContent() {
    streamingContent.value = ''
  }

  function addMessage(message: BrainstormMessage) {
    if (currentSession.value) {
      currentSession.value.messages.push(message)
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    currentSession,
    sessions,
    loading,
    streaming,
    error,
    streamingContent,
    // Getters
    isActive,
    // Actions
    createSession,
    fetchSessions,
    fetchSession,
    updateSession,
    deleteSession,
    setStreaming,
    setStreamingContent,
    appendStreamingContent,
    clearStreamingContent,
    addMessage,
    clearError,
  }
})
```

**Step 4: Run tests to verify they pass**

```bash
npm run test -- src/stores/__tests__/brainstorm.spec.ts
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add frontend/src/stores/brainstorm.ts frontend/src/stores/__tests__/brainstorm.spec.ts
git commit -m "feat: add brainstorm Pinia store"
```

---

## Phase 8: Frontend UI - Components

### Task 10: Create BrainstormList Component

**Files:**
- Create: `frontend/src/components/BrainstormList.vue`

**Step 1: Write failing test for component**

Create file `frontend/src/components/__tests__/BrainstormList.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BrainstormList from '../BrainstormList.vue'
import { useBrainstormStore } from '@/stores/brainstorm'

describe('BrainstormList', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render sessions list', async () => {
    const wrapper = mount(BrainstormList)
    const store = useBrainstormStore()

    store.sessions = [
      {
        id: 'session-1',
        title: 'Mobile App Redesign',
        description: 'Reimagine the mobile experience',
        status: 'active',
        messages: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Mobile App Redesign')
  })

  it('should show loading state', async () => {
    const wrapper = mount(BrainstormList)
    const store = useBrainstormStore()

    store.loading = true
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Loading')
  })

  it('should emit create-session event', async () => {
    const wrapper = mount(BrainstormList)

    // Simulate clicking create button
    const createButton = wrapper.find('[data-testid="create-session-btn"]')
    await createButton.trigger('click')

    expect(wrapper.emitted('create-session')).toBeTruthy()
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm run test -- src/components/__tests__/BrainstormList.spec.ts
```

Expected: FAIL with "Cannot find module '../BrainstormList.vue'"

**Step 3: Create BrainstormList component**

Create file `frontend/src/components/BrainstormList.vue`:

```vue
<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold">Brainstorming Sessions</h2>
        <p class="text-muted-foreground">
          Collaborate with Claude to explore ideas
        </p>
      </div>
      <Button
        data-testid="create-session-btn"
        @click="$emit('create-session')"
      >
        <Plus class="mr-2 h-4 w-4" />
        New Session
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading sessions...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-destructive">{{ error }}</p>
      <Button @click="fetchSessions" variant="outline" class="mt-4">
        Retry
      </Button>
    </div>

    <!-- Empty State -->
    <div v-else-if="sessions.length === 0" class="text-center py-12">
      <Lightbulb class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Sessions Yet</h3>
      <p class="text-muted-foreground mb-4">
        Start a brainstorming session to collaborate with Claude
      </p>
      <Button @click="$emit('create-session')">
        Create Your First Session
      </Button>
    </div>

    <!-- Sessions Grid -->
    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="session in sessions"
        :key="session.id"
        class="cursor-pointer hover:shadow-md transition-shadow"
        @click="$emit('select-session', session.id)"
      >
        <CardHeader>
          <div class="flex items-start justify-between">
            <CardTitle class="text-lg">{{ session.title }}</CardTitle>
            <Badge :variant="getStatusVariant(session.status)">
              {{ session.status }}
            </Badge>
          </div>
          <CardDescription class="line-clamp-2">
            {{ session.description }}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="flex items-center text-sm text-muted-foreground">
            <MessageSquare class="mr-2 h-4 w-4" />
            {{ session.messages.length }} messages
          </div>
          <div class="text-xs text-muted-foreground mt-2">
            {{ formatDate(session.updated_at) }}
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useBrainstormStore } from '@/stores/brainstorm'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Plus, MessageSquare, Lightbulb } from 'lucide-vue-next'

defineEmits<{
  'create-session': []
  'select-session': [id: string]
}>()

const store = useBrainstormStore()

const sessions = computed(() => store.sessions)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

function getStatusVariant(status: string) {
  switch (status) {
    case 'active':
      return 'default'
    case 'paused':
      return 'secondary'
    case 'completed':
      return 'outline'
    case 'archived':
      return 'outline'
    default:
      return 'default'
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 60) {
    return `${diffMins}m ago`
  }

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) {
    return `${diffHours}h ago`
  }

  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) {
    return `${diffDays}d ago`
  }

  return date.toLocaleDateString()
}

async function fetchSessions() {
  await store.fetchSessions()
}

onMounted(() => {
  fetchSessions()
})
</script>
```

**Step 4: Run tests to verify they pass**

```bash
npm run test -- src/components/__tests__/BrainstormList.spec.ts
```

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add frontend/src/components/BrainstormList.vue frontend/src/components/__tests__/BrainstormList.spec.ts
git commit -m "feat: add BrainstormList component"
```

---

### Task 11: Create BrainstormChat Component

**Files:**
- Create: `frontend/src/components/BrainstormChat.vue`

**Step 1: Write failing test for chat component**

Create file `frontend/src/components/__tests__/BrainstormChat.spec.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BrainstormChat from '../BrainstormChat.vue'
import { useBrainstormStore } from '@/stores/brainstorm'

describe('BrainstormChat', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render messages', async () => {
    const store = useBrainstormStore()
    store.currentSession = {
      id: 'session-1',
      title: 'Test Session',
      description: 'Test',
      status: 'active',
      messages: [
        {
          id: 'msg-1',
          session_id: 'session-1',
          role: 'user',
          content: 'Hello',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'msg-2',
          session_id: 'session-1',
          role: 'assistant',
          content: 'Hi there!',
          created_at: '2024-01-01T00:00:01Z',
          updated_at: '2024-01-01T00:00:01Z',
        },
      ],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:01Z',
    }

    const wrapper = mount(BrainstormChat, {
      props: { sessionId: 'session-1' },
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Hello')
    expect(wrapper.text()).toContain('Hi there!')
  })

  it('should show streaming indicator', async () => {
    const store = useBrainstormStore()
    store.streaming = true
    store.streamingContent = 'Thinking...'

    const wrapper = mount(BrainstormChat, {
      props: { sessionId: 'session-1' },
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Thinking...')
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm run test -- src/components/__tests__/BrainstormChat.spec.ts
```

Expected: FAIL with "Cannot find module '../BrainstormChat.vue'"

**Step 3: Create BrainstormChat component**

Create file `frontend/src/components/BrainstormChat.vue`:

```vue
<template>
  <div class="flex flex-col h-full">
    <!-- Session Header -->
    <div v-if="currentSession" class="border-b p-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold">{{ currentSession.title }}</h2>
          <p class="text-sm text-muted-foreground">
            {{ currentSession.description }}
          </p>
        </div>
        <Badge :variant="getStatusVariant(currentSession.status)">
          {{ currentSession.status }}
        </Badge>
      </div>
    </div>

    <!-- Messages Container -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-4 space-y-4"
    >
      <!-- Messages -->
      <div
        v-for="message in currentSession?.messages || []"
        :key="message.id"
        :class="[
          'flex',
          message.role === 'user' ? 'justify-end' : 'justify-start',
        ]"
      >
        <div
          :class="[
            'max-w-[80%] rounded-lg p-4',
            message.role === 'user'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted',
          ]"
        >
          <div class="flex items-center gap-2 mb-2">
            <Avatar class="h-6 w-6">
              <AvatarFallback>
                {{ message.role === 'user' ? 'You' : 'AI' }}
              </AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">
              {{ message.role === 'user' ? 'You' : 'Claude' }}
            </span>
          </div>
          <p class="whitespace-pre-wrap">{{ message.content }}</p>
        </div>
      </div>

      <!-- Streaming Message -->
      <div v-if="streaming" class="flex justify-start">
        <div class="max-w-[80%] rounded-lg p-4 bg-muted">
          <div class="flex items-center gap-2 mb-2">
            <Avatar class="h-6 w-6">
              <AvatarFallback>AI</AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">Claude</span>
          </div>
          <p class="whitespace-pre-wrap">
            {{ streamingContent }}
            <span class="animate-pulse">▊</span>
          </p>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center py-8">
        <p class="text-muted-foreground">Loading session...</p>
      </div>
    </div>

    <!-- Input Form -->
    <div class="border-t p-4">
      <form @submit.prevent="handleSendMessage" class="flex gap-2">
        <Textarea
          v-model="userMessage"
          placeholder="Share your thoughts..."
          :disabled="streaming || loading || !isActive"
          @keydown.enter.exact.prevent="handleSendMessage"
          class="flex-1 resize-none"
          rows="3"
        />
        <Button
          type="submit"
          :disabled="streaming || loading || !userMessage.trim() || !isActive"
          size="icon"
          class="self-end"
        >
          <Send class="h-4 w-4" />
        </Button>
      </form>
      <p v-if="!isActive" class="text-xs text-muted-foreground mt-2">
        This session is not active
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useBrainstormStore } from '@/stores/brainstorm'
import { brainstormsApi } from '@/api/brainstorms'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Send } from 'lucide-vue-next'
import type { StreamChunk } from '@/types/brainstorm'

const props = defineProps<{
  sessionId: string
}>()

const store = useBrainstormStore()
const userMessage = ref('')
const messagesContainer = ref<HTMLDivElement>()

const currentSession = computed(() => store.currentSession)
const loading = computed(() => store.loading)
const streaming = computed(() => store.streaming)
const streamingContent = computed(() => store.streamingContent)
const isActive = computed(() => store.isActive)

function getStatusVariant(status: string) {
  switch (status) {
    case 'active':
      return 'default'
    case 'paused':
      return 'secondary'
    case 'completed':
      return 'outline'
    case 'archived':
      return 'outline'
    default:
      return 'default'
  }
}

async function handleSendMessage() {
  if (!userMessage.value.trim() || !currentSession.value) return

  const message = userMessage.value
  userMessage.value = ''

  // Add user message to UI immediately
  store.addMessage({
    id: crypto.randomUUID(),
    session_id: currentSession.value.id,
    role: 'user',
    content: message,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  })

  try {
    store.setStreaming(true)
    store.clearStreamingContent()

    const eventSource = brainstormsApi.streamBrainstorm(
      currentSession.value.id,
      message
    )

    eventSource.addEventListener('message', (event: MessageEvent) => {
      const data: StreamChunk = JSON.parse(event.data)

      if (data.type === 'chunk' && data.content) {
        store.appendStreamingContent(data.content)
        scrollToBottom()
      } else if (data.type === 'done') {
        eventSource.close()

        // Add assistant message
        if (streamingContent.value) {
          store.addMessage({
            id: crypto.randomUUID(),
            session_id: currentSession.value!.id,
            role: 'assistant',
            content: streamingContent.value,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        }

        store.setStreaming(false)
        store.clearStreamingContent()
      } else if (data.type === 'error') {
        eventSource.close()
        store.setStreaming(false)
        console.error('Streaming error:', data.message)
      }
    })

    eventSource.addEventListener('error', () => {
      eventSource.close()
      store.setStreaming(false)
      console.error('EventSource connection failed')
    })
  } catch (error) {
    store.setStreaming(false)
    console.error('Failed to send message:', error)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(
  () => currentSession.value?.messages.length,
  () => {
    scrollToBottom()
  }
)

onMounted(async () => {
  await store.fetchSession(props.sessionId)
  scrollToBottom()
})
</script>
```

**Step 4: Run tests to verify they pass**

```bash
npm run test -- src/components/__tests__/BrainstormChat.spec.ts
```

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add frontend/src/components/BrainstormChat.vue frontend/src/components/__tests__/BrainstormChat.spec.ts
git commit -m "feat: add BrainstormChat component with SSE streaming"
```

---

## Phase 9: Frontend UI - Views & Router

### Task 12: Create Brainstorm Views

**Files:**
- Create: `frontend/src/views/BrainstormListView.vue`
- Create: `frontend/src/views/BrainstormDetailView.vue`
- Modify: `frontend/src/router/index.ts`

**Step 1: Create BrainstormListView**

Create file `frontend/src/views/BrainstormListView.vue`:

```vue
<template>
  <div class="container mx-auto py-6">
    <BrainstormList
      @create-session="showCreateDialog = true"
      @select-session="navigateToSession"
    />

    <!-- Create Session Dialog -->
    <Dialog v-model:open="showCreateDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Brainstorming Session</DialogTitle>
          <DialogDescription>
            Create a new session to collaborate with Claude on ideas
          </DialogDescription>
        </DialogHeader>

        <form @submit.prevent="handleCreate" class="space-y-4">
          <div class="space-y-2">
            <Label for="title">Title</Label>
            <Input
              id="title"
              v-model="formData.title"
              placeholder="Mobile App Redesign"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="description">Description</Label>
            <Textarea
              id="description"
              v-model="formData.description"
              placeholder="Explore ideas for reimagining our mobile experience"
              rows="4"
              required
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              @click="showCreateDialog = false"
            >
              Cancel
            </Button>
            <Button type="submit" :disabled="loading">
              Create Session
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useBrainstormStore } from '@/stores/brainstorm'
import BrainstormList from '@/components/BrainstormList.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

const router = useRouter()
const store = useBrainstormStore()

const showCreateDialog = ref(false)
const formData = ref({
  title: '',
  description: '',
})

const loading = computed(() => store.loading)

async function handleCreate() {
  try {
    const session = await store.createSession(formData.value)
    showCreateDialog.value = false
    formData.value = { title: '', description: '' }
    router.push(`/brainstorm/${session.id}`)
  } catch (error) {
    console.error('Failed to create session:', error)
  }
}

function navigateToSession(id: string) {
  router.push(`/brainstorm/${id}`)
}
</script>
```

**Step 2: Create BrainstormDetailView**

Create file `frontend/src/views/BrainstormDetailView.vue`:

```vue
<template>
  <div class="h-full flex flex-col">
    <div class="border-b p-4">
      <Button variant="ghost" size="sm" @click="router.back()">
        <ArrowLeft class="mr-2 h-4 w-4" />
        Back to Sessions
      </Button>
    </div>

    <div class="flex-1 overflow-hidden">
      <BrainstormChat :session-id="sessionId" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import BrainstormChat from '@/components/BrainstormChat.vue'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const sessionId = route.params.id as string
</script>
```

**Step 3: Update router configuration**

Modify `frontend/src/router/index.ts`, add these routes inside the DashboardLayout children array:

```typescript
{
  path: 'brainstorm',
  name: 'brainstorm-list',
  component: () => import('@/views/BrainstormListView.vue'),
  meta: { title: 'Brainstorming' },
},
{
  path: 'brainstorm/:id',
  name: 'brainstorm-detail',
  component: () => import('@/views/BrainstormDetailView.vue'),
  meta: { title: 'Brainstorming Session' },
},
```

**Step 4: Test navigation**

```bash
npm run dev
```

Expected: Navigate to http://localhost:8892/brainstorm and verify UI loads

**Step 5: Commit**

```bash
git add frontend/src/views/BrainstormListView.vue frontend/src/views/BrainstormDetailView.vue frontend/src/router/index.ts
git commit -m "feat: add brainstorm views and routes"
```

---

## Phase 10: Integration & End-to-End Testing

### Task 13: Integration Testing

**Files:**
- Create: `backend/tests/test_integration_brainstorm.py`
- Create: `frontend/src/tests/integration/brainstorm.spec.ts`

**Step 1: Backend integration test**

Create file `backend/tests/test_integration_brainstorm.py`:

```python
"""Integration tests for brainstorm feature."""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.brainstorm import BrainstormSession, BrainstormMessage, MessageRole


class TestBrainstormIntegration:
    """End-to-end tests for brainstorm workflow."""

    @pytest.mark.asyncio
    async def test_complete_brainstorm_workflow(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test complete workflow: create session, send message, verify storage."""
        # Step 1: Create session
        create_data = {
            "title": "Mobile App Features",
            "description": "Brainstorm new features for mobile app",
        }
        response = await async_client.post("/api/v1/brainstorms", json=create_data)
        assert response.status_code == 201
        session_data = response.json()
        session_id = session_data["id"]

        # Step 2: Verify session in database
        result = await db_session.execute(
            select(BrainstormSession).where(BrainstormSession.id == session_id)
        )
        db_session_obj = result.scalar_one()
        assert db_session_obj.title == create_data["title"]

        # Step 3: Get session via API
        response = await async_client.get(f"/api/v1/brainstorms/{session_id}")
        assert response.status_code == 200
        assert response.json()["id"] == session_id

        # Step 4: List sessions
        response = await async_client.get("/api/v1/brainstorms")
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= 1
        assert any(s["id"] == session_id for s in sessions)

        # Step 5: Update session status
        update_data = {"status": "completed"}
        response = await async_client.put(
            f"/api/v1/brainstorms/{session_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        # Step 6: Delete session
        response = await async_client.delete(f"/api/v1/brainstorms/{session_id}")
        assert response.status_code == 204

        # Step 7: Verify deletion
        result = await db_session.execute(
            select(BrainstormSession).where(BrainstormSession.id == session_id)
        )
        assert result.scalar_one_or_none() is None
```

**Step 2: Run backend integration tests**

```bash
cd backend
poetry run pytest tests/test_integration_brainstorm.py -v
```

Expected: PASS (1 test)

**Step 3: Frontend integration test**

Create file `frontend/src/tests/integration/brainstorm.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import BrainstormListView from '@/views/BrainstormListView.vue'
import { brainstormsApi } from '@/api/brainstorms'

vi.mock('@/api/brainstorms')

describe('Brainstorm Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should complete create session workflow', async () => {
    const mockSessions = [
      {
        id: 'session-1',
        title: 'Test Session',
        description: 'Test',
        status: 'active' as const,
        messages: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(brainstormsApi.listSessions).mockResolvedValue(mockSessions)
    vi.mocked(brainstormsApi.createSession).mockResolvedValue(mockSessions[0])

    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: BrainstormListView },
        { path: '/brainstorm/:id', component: { template: '<div>Detail</div>' } },
      ],
    })

    const wrapper = mount(BrainstormListView, {
      global: {
        plugins: [router],
      },
    })

    await wrapper.vm.$nextTick()

    // Verify sessions loaded
    expect(brainstormsApi.listSessions).toHaveBeenCalled()
  })
})
```

**Step 4: Run frontend integration tests**

```bash
cd frontend
npm run test -- src/tests/integration/brainstorm.spec.ts
```

Expected: PASS (1 test)

**Step 5: Commit**

```bash
git add backend/tests/test_integration_brainstorm.py frontend/src/tests/integration/brainstorm.spec.ts
git commit -m "test: add brainstorm integration tests"
```

---

## Phase 11: Documentation & Final Polish

### Task 14: Update Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/BRAINSTORMING_MODULE.md`

**Step 1: Create module documentation**

Create file `docs/BRAINSTORMING_MODULE.md`:

```markdown
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
```

**Step 2: Update main README**

Modify `README.md`, add to the Modules section:

```markdown
### Module 4: Brainstorming Sessions ✅

Real-time collaborative ideation with Claude AI co-facilitation.

- Create and manage brainstorming sessions
- Stream AI responses with Server-Sent Events
- Persistent conversation history
- Session status tracking (active, paused, completed, archived)
- Chat interface with real-time updates

[Full Documentation](docs/BRAINSTORMING_MODULE.md)
```

**Step 3: Commit**

```bash
git add docs/BRAINSTORMING_MODULE.md README.md
git commit -m "docs: add brainstorming module documentation"
```

---

## Phase 12: Quality Verification

### Task 15: Run Quality Gates

**Files:**
- Run linting, type checking, tests

**Step 1: Backend quality checks**

```bash
cd backend

# Format
poetry run black .

# Lint
poetry run ruff check .

# Type check
poetry run mypy app

# Run all tests
poetry run pytest -v

# Coverage check
poetry run pytest --cov=app --cov-report=term
```

Expected: All checks pass, 90%+ coverage

**Step 2: Frontend quality checks**

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run type-check

# Run all tests
npm run test:run

# Build check
npm run build
```

Expected: All checks pass, no errors

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: quality gate fixes for brainstorming module"
```

---

## Phase 13: Manual Testing & Final Deployment

### Task 16: End-to-End Manual Testing

**Manual Testing Checklist:**

1. **Backend Setup**:
   - [ ] Database migration applied (`alembic upgrade head`)
   - [ ] ANTHROPIC_API_KEY configured in `.env`
   - [ ] Backend server running on port 8891

2. **Create Session**:
   - [ ] Navigate to http://localhost:8892/brainstorm
   - [ ] Click "New Session"
   - [ ] Fill form with title and description
   - [ ] Verify session appears in list

3. **Chat with Claude**:
   - [ ] Click on session card
   - [ ] Type message in chat input
   - [ ] Press Enter or click Send
   - [ ] Verify streaming response appears with typing indicator
   - [ ] Verify complete message saved after stream ends

4. **Session Management**:
   - [ ] Update session status to "completed"
   - [ ] Verify badge updates
   - [ ] Create multiple sessions
   - [ ] Verify list shows all sessions sorted by date

5. **Edge Cases**:
   - [ ] Try sending empty message (should be disabled)
   - [ ] Test long messages (>1000 chars)
   - [ ] Test rapid consecutive messages
   - [ ] Test with slow network (throttle in DevTools)
   - [ ] Refresh page mid-conversation (should reload)

**Step 1: Document any issues found**

Create file `docs/KNOWN_ISSUES.md` if any issues found during testing.

**Step 2: Fix critical issues**

Fix any blocking issues found during manual testing.

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete Module 4 brainstorming sessions implementation"
```

---

## Summary

This implementation plan provides:

✅ **Backend (8 tasks)**:
- Models with relationships and cascade delete
- Database migrations
- Pydantic schemas
- BrainstormingService with Claude SDK
- CRUD API endpoints
- SSE streaming endpoint
- Comprehensive tests (90%+ coverage)

✅ **Frontend (7 tasks)**:
- TypeScript types
- API client with EventSource
- Pinia store for state management
- BrainstormList component
- BrainstormChat component with streaming
- Views and router configuration
- Integration tests

✅ **Quality (3 tasks)**:
- Integration tests (backend + frontend)
- Documentation
- Quality gates verification
- Manual testing checklist

**Total Implementation Time**: ~3-4 weeks (as estimated in design doc)

**Test Coverage**: 90%+ (both backend and frontend)

**Git Commits**: 16 atomic commits following conventional commit format

---

## Next Steps After Implementation

1. **Review**: Code review with `/requesting-code-review` skill
2. **Deploy**: Deploy to staging environment
3. **Monitor**: Track usage and performance
4. **Iterate**: Gather feedback and implement enhancements
5. **Module Integration**: Connect to Ideas module (create ideas from insights)
