# Module 3: Ideas Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Build a system to capture, evaluate, and prioritize product ideas with AI-powered analysis and team collaboration.

**Architecture:** FastAPI backend with PostgreSQL for idea persistence, Claude API for AI evaluation (market fit, business value, complexity), Vue 3 frontend with Kanban board and priority matrix visualizations, Pinia for state management.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Claude API (Anthropic), Vue 3, TypeScript, Pinia, shadcn-vue, TanStack/vue-draggable (for Kanban)

---

## Phase 1: Backend Foundation - Database Models

### Task 1: Create Idea Model

**Files:**
- Create: `backend/app/models/idea.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write failing test for Idea model**

Create file `backend/tests/test_models_idea.py`:

```python
"""Tests for idea models."""
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea import Idea, IdeaStatus, IdeaPriority


class TestIdeaModel:
    """Tests for Idea model."""

    @pytest.mark.asyncio
    async def test_create_idea(self, db_session: AsyncSession):
        """Test creating an idea."""
        idea = Idea(
            id="idea-1",
            title="Dark Mode Feature",
            description="Add dark mode support to the application",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.MEDIUM,
            business_value=8,
            technical_complexity=5,
        )

        db_session.add(idea)
        await db_session.commit()
        await db_session.refresh(idea)

        assert idea.id == "idea-1"
        assert idea.title == "Dark Mode Feature"
        assert idea.status == IdeaStatus.BACKLOG
        assert idea.priority == IdeaPriority.MEDIUM
        assert idea.business_value == 8
        assert idea.technical_complexity == 5
        assert isinstance(idea.created_at, datetime)
        assert isinstance(idea.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_idea_nullable_fields(self, db_session: AsyncSession):
        """Test idea with nullable fields."""
        idea = Idea(
            id="idea-2",
            title="Test Idea",
            description="Test description",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.LOW,
        )

        db_session.add(idea)
        await db_session.commit()
        await db_session.refresh(idea)

        assert idea.business_value is None
        assert idea.technical_complexity is None
        assert idea.estimated_effort is None
        assert idea.market_fit_analysis is None
        assert idea.risk_assessment is None

    @pytest.mark.asyncio
    async def test_idea_business_value_range(self, db_session: AsyncSession):
        """Test business value must be 1-10."""
        idea = Idea(
            id="idea-3",
            title="Test",
            description="Test",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.LOW,
            business_value=11,  # Invalid
        )

        db_session.add(idea)

        # Should raise constraint error
        with pytest.raises(Exception):
            await db_session.commit()
```

**Step 2: Run test to verify it fails**

```bash
cd backend
poetry run pytest tests/test_models_idea.py::TestIdeaModel::test_create_idea -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.idea'"

**Step 3: Create Idea model**

Create file `backend/app/models/idea.py`:

```python
"""Idea model for product ideas management."""
from datetime import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class IdeaStatus(str, enum.Enum):
    """Idea statuses."""

    BACKLOG = "backlog"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class IdeaPriority(str, enum.Enum):
    """Idea priorities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Idea(Base, TimestampMixin):
    """Idea model for product ideas."""

    __tablename__ = "ideas"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Status and priority
    status: Mapped[IdeaStatus] = mapped_column(
        SQLEnum(IdeaStatus),
        default=IdeaStatus.BACKLOG,
        nullable=False,
    )
    priority: Mapped[IdeaPriority] = mapped_column(
        SQLEnum(IdeaPriority),
        default=IdeaPriority.MEDIUM,
        nullable=False,
    )

    # AI evaluation fields (1-10 scale)
    business_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technical_complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Additional fields
    estimated_effort: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market_fit_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Constraints for 1-10 scale
    __table_args__ = (
        CheckConstraint(
            "business_value IS NULL OR (business_value >= 1 AND business_value <= 10)",
            name="check_business_value_range",
        ),
        CheckConstraint(
            "technical_complexity IS NULL OR (technical_complexity >= 1 AND technical_complexity <= 10)",
            name="check_technical_complexity_range",
        ),
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
from .idea import Idea, IdeaStatus, IdeaPriority

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
    "Idea",
    "IdeaStatus",
    "IdeaPriority",
]
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/test_models_idea.py::TestIdeaModel -v
```

Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add backend/app/models/idea.py backend/app/models/__init__.py backend/tests/test_models_idea.py
git commit -m "feat: add Idea model with status and priority enums"
```

---

### Task 2: Create Database Migration for Ideas Table

**Files:**
- Create: `backend/alembic/versions/XXX_add_ideas_table.py`

**Step 1: Generate migration**

```bash
cd backend
poetry run alembic revision --autogenerate -m "add ideas table"
```

Expected: New migration file created in `alembic/versions/`

**Step 2: Review and apply migration**

```bash
poetry run alembic upgrade head
```

Expected: Migration applied successfully

**Step 3: Verify table exists**

```bash
poetry run python -c "
from app.database import engine
from sqlalchemy import text
import asyncio

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='ideas'\"))
        tables = [row[0] for row in result]
        print(f'Tables: {tables}')
        assert 'ideas' in tables

asyncio.run(check())
"
```

Expected: Output shows 'ideas' table exists

**Step 4: Commit**

```bash
git add alembic/versions/
git commit -m "feat: add database migration for ideas table"
```

---

## Phase 2: Backend API - Schemas

### Task 3: Create Pydantic Schemas for Ideas

**Files:**
- Create: `backend/app/schemas/idea.py`
- Modify: `backend/app/schemas/__init__.py`

**Step 1: Write failing test for schemas**

Create file `backend/tests/test_schemas_idea.py`:

```python
"""Tests for idea schemas."""
from datetime import datetime
import pytest
from pydantic import ValidationError

from app.schemas.idea import (
    IdeaCreate,
    IdeaUpdate,
    IdeaResponse,
    IdeaEvaluationRequest,
    IdeaEvaluationResponse,
)


def test_idea_create_schema():
    """Test IdeaCreate schema validation."""
    data = {
        "title": "Dark Mode Feature",
        "description": "Add dark mode support to the application",
    }

    schema = IdeaCreate(**data)
    assert schema.title == "Dark Mode Feature"
    assert schema.description == "Add dark mode support to the application"


def test_idea_create_with_priority():
    """Test IdeaCreate with optional priority."""
    data = {
        "title": "Test Idea",
        "description": "Test description",
        "priority": "high",
    }

    schema = IdeaCreate(**data)
    assert schema.priority == "high"


def test_idea_response_schema():
    """Test IdeaResponse schema."""
    data = {
        "id": "idea-1",
        "title": "Test Idea",
        "description": "Test description",
        "status": "backlog",
        "priority": "medium",
        "business_value": 8,
        "technical_complexity": 5,
        "estimated_effort": "2 weeks",
        "market_fit_analysis": "Strong market fit",
        "risk_assessment": "Low risk",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    schema = IdeaResponse(**data)
    assert schema.id == "idea-1"
    assert schema.business_value == 8
    assert schema.technical_complexity == 5


def test_idea_evaluation_request():
    """Test IdeaEvaluationRequest schema."""
    data = {
        "title": "Dark Mode Feature",
        "description": "Add dark mode support",
    }

    schema = IdeaEvaluationRequest(**data)
    assert schema.title == "Dark Mode Feature"


def test_idea_evaluation_response():
    """Test IdeaEvaluationResponse schema."""
    data = {
        "business_value": 8,
        "technical_complexity": 5,
        "estimated_effort": "2 weeks",
        "market_fit_analysis": "Strong market fit based on user requests",
        "risk_assessment": "Low risk - standard UI implementation",
    }

    schema = IdeaEvaluationResponse(**data)
    assert schema.business_value == 8
    assert schema.technical_complexity == 5


def test_business_value_validation():
    """Test business value must be 1-10."""
    with pytest.raises(ValidationError):
        IdeaEvaluationResponse(
            business_value=11,
            technical_complexity=5,
            estimated_effort="2 weeks",
            market_fit_analysis="Test",
            risk_assessment="Test",
        )
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_schemas_idea.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.schemas.idea'"

**Step 3: Create idea schemas**

Create file `backend/app/schemas/idea.py`:

```python
"""Idea schemas for request/response validation."""
from datetime import datetime
from pydantic import BaseModel, Field


class IdeaCreate(BaseModel):
    """Schema for creating an idea."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    priority: str | None = Field(None, pattern="^(low|medium|high|critical)$")


class IdeaUpdate(BaseModel):
    """Schema for updating an idea."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    status: str | None = Field(
        None, pattern="^(backlog|under_review|approved|rejected|implemented)$"
    )
    priority: str | None = Field(None, pattern="^(low|medium|high|critical)$")
    business_value: int | None = Field(None, ge=1, le=10)
    technical_complexity: int | None = Field(None, ge=1, le=10)
    estimated_effort: str | None = Field(None, max_length=100)
    market_fit_analysis: str | None = None
    risk_assessment: str | None = None


class IdeaResponse(BaseModel):
    """Schema for idea response."""

    id: str
    title: str
    description: str
    status: str
    priority: str
    business_value: int | None = None
    technical_complexity: int | None = None
    estimated_effort: str | None = None
    market_fit_analysis: str | None = None
    risk_assessment: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IdeaEvaluationRequest(BaseModel):
    """Schema for requesting AI evaluation of an idea."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    context: str | None = Field(None, description="Additional context for evaluation")


class IdeaEvaluationResponse(BaseModel):
    """Schema for AI evaluation response."""

    business_value: int = Field(..., ge=1, le=10, description="Business value score (1-10)")
    technical_complexity: int = Field(
        ..., ge=1, le=10, description="Technical complexity score (1-10)"
    )
    estimated_effort: str = Field(..., description="Estimated effort (e.g., '2 weeks')")
    market_fit_analysis: str = Field(..., description="Market fit analysis")
    risk_assessment: str = Field(..., description="Risk assessment")
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
from .idea import (
    IdeaCreate,
    IdeaUpdate,
    IdeaResponse,
    IdeaEvaluationRequest,
    IdeaEvaluationResponse,
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
    "IdeaCreate",
    "IdeaUpdate",
    "IdeaResponse",
    "IdeaEvaluationRequest",
    "IdeaEvaluationResponse",
]
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/test_schemas_idea.py -v
```

Expected: PASS (6 tests)

**Step 6: Commit**

```bash
git add backend/app/schemas/idea.py backend/app/schemas/__init__.py backend/tests/test_schemas_idea.py
git commit -m "feat: add idea Pydantic schemas with validation"
```

---

## Phase 3: Backend Service - AI Evaluation

### Task 4: Create IdeaEvaluationService with Claude

**Files:**
- Create: `backend/app/services/idea_evaluation_service.py`

**Step 1: Write failing test for IdeaEvaluationService**

Create file `backend/tests/test_service_idea_evaluation.py`:

```python
"""Tests for idea evaluation service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.idea_evaluation_service import IdeaEvaluationService


class TestIdeaEvaluationService:
    """Tests for IdeaEvaluationService."""

    @pytest.mark.asyncio
    async def test_evaluate_idea(self):
        """Test evaluating an idea with Claude."""
        service = IdeaEvaluationService(api_key="test-key")

        title = "Dark Mode Feature"
        description = "Add dark mode support to the application"

        # Mock the Anthropic client
        with patch.object(service, 'client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    text='{"business_value": 8, "technical_complexity": 5, "estimated_effort": "2 weeks", "market_fit_analysis": "Strong demand", "risk_assessment": "Low risk"}'
                )
            ]
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await service.evaluate_idea(title, description)

            assert result["business_value"] == 8
            assert result["technical_complexity"] == 5
            assert result["estimated_effort"] == "2 weeks"

    def test_parse_evaluation_result(self):
        """Test parsing JSON evaluation result."""
        service = IdeaEvaluationService(api_key="test-key")

        text = '{"business_value": 8, "technical_complexity": 5, "estimated_effort": "2 weeks", "market_fit_analysis": "Strong", "risk_assessment": "Low"}'

        result = service._parse_evaluation_result(text)

        assert result["business_value"] == 8
        assert result["technical_complexity"] == 5

    def test_parse_evaluation_result_with_markdown(self):
        """Test parsing result with markdown code block."""
        service = IdeaEvaluationService(api_key="test-key")

        text = '''Here's my evaluation:

```json
{
  "business_value": 8,
  "technical_complexity": 5,
  "estimated_effort": "2 weeks",
  "market_fit_analysis": "Strong demand based on user feedback",
  "risk_assessment": "Low risk - standard implementation"
}
```

This looks like a good idea!'''

        result = service._parse_evaluation_result(text)

        assert result["business_value"] == 8
        assert result["technical_complexity"] == 5
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_service_idea_evaluation.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create IdeaEvaluationService**

Create file `backend/app/services/idea_evaluation_service.py`:

```python
"""Service for AI-powered idea evaluation with Claude."""
import logging
import json
import re
from typing import Any
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class IdeaEvaluationService:
    """Service for evaluating product ideas with Claude."""

    SYSTEM_PROMPT = """You are an AI product analyst evaluating product ideas.

For each idea, provide:
1. Business Value (1-10): Impact on users and business metrics
2. Technical Complexity (1-10): Implementation difficulty
3. Estimated Effort: Time estimate (e.g., "2 weeks", "3 months")
4. Market Fit Analysis: How well this aligns with market needs
5. Risk Assessment: Technical and business risks

Return your evaluation as JSON with this exact structure:
{
  "business_value": <1-10>,
  "technical_complexity": <1-10>,
  "estimated_effort": "<time estimate>",
  "market_fit_analysis": "<analysis text>",
  "risk_assessment": "<risk analysis text>"
}

Be objective, concise, and data-driven in your analysis."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250514") -> None:
        """Initialize the evaluation service.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    async def evaluate_idea(
        self, title: str, description: str, context: str | None = None
    ) -> dict[str, Any]:
        """Evaluate an idea with Claude.

        Args:
            title: Idea title
            description: Idea description
            context: Optional additional context

        Returns:
            Evaluation result dict with business_value, technical_complexity, etc.

        Raises:
            Exception: If evaluation fails
        """
        try:
            # Build prompt
            prompt = f"""Evaluate this product idea:

Title: {title}

Description: {description}"""

            if context:
                prompt += f"\n\nAdditional Context: {context}"

            prompt += "\n\nProvide your evaluation as JSON."

            # Call Claude
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text
            result = self._parse_evaluation_result(response_text)

            logger.info(f"Successfully evaluated idea: {title}")
            return result

        except Exception as e:
            logger.error(f"Error evaluating idea: {e}")
            raise

    def _parse_evaluation_result(self, text: str) -> dict[str, Any]:
        """Parse evaluation result from Claude response.

        Args:
            text: Claude response text

        Returns:
            Parsed evaluation dict

        Raises:
            ValueError: If parsing fails
        """
        # Try to find JSON in markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("Could not find JSON in response")

        try:
            result = json.loads(json_str)

            # Validate required fields
            required_fields = [
                "business_value",
                "technical_complexity",
                "estimated_effort",
                "market_fit_analysis",
                "risk_assessment",
            ]

            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Validate ranges
            if not (1 <= result["business_value"] <= 10):
                raise ValueError("business_value must be 1-10")
            if not (1 <= result["technical_complexity"] <= 10):
                raise ValueError("technical_complexity must be 1-10")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise ValueError(f"Invalid JSON in response: {e}")

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        await self.client.close()

    async def __aenter__(self) -> "IdeaEvaluationService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/test_service_idea_evaluation.py -v
```

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add backend/app/services/idea_evaluation_service.py backend/tests/test_service_idea_evaluation.py
git commit -m "feat: add IdeaEvaluationService with Claude integration"
```

---

## Phase 4: Backend API - CRUD Endpoints

### Task 5: Create Ideas API Router with CRUD

**Files:**
- Create: `backend/app/api/ideas.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing tests for CRUD endpoints**

Create file `backend/tests/test_api_ideas.py`:

```python
"""Tests for ideas API endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea import Idea, IdeaStatus, IdeaPriority


class TestCreateIdea:
    """Tests for POST /api/v1/ideas endpoint."""

    @pytest.mark.asyncio
    async def test_create_idea_valid_data(self, async_client: AsyncClient):
        """Test creating an idea with valid data."""
        data = {
            "title": "Dark Mode Feature",
            "description": "Add dark mode support to the application",
        }

        response = await async_client.post("/api/v1/ideas", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == data["title"]
        assert result["description"] == data["description"]
        assert result["status"] == "backlog"
        assert result["priority"] == "medium"
        assert "id" in result

    @pytest.mark.asyncio
    async def test_create_idea_with_priority(self, async_client: AsyncClient):
        """Test creating idea with custom priority."""
        data = {
            "title": "Critical Bug Fix",
            "description": "Fix critical security issue",
            "priority": "critical",
        }

        response = await async_client.post("/api/v1/ideas", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["priority"] == "critical"

    @pytest.mark.asyncio
    async def test_create_idea_missing_title(self, async_client: AsyncClient):
        """Test creating idea without title fails."""
        data = {"description": "Test description"}

        response = await async_client.post("/api/v1/ideas", json=data)

        assert response.status_code == 422


class TestGetIdea:
    """Tests for GET /api/v1/ideas/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_idea_exists(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting an existing idea."""
        idea = Idea(
            id="idea-1",
            title="Test Idea",
            description="Test description",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.MEDIUM,
        )
        db_session.add(idea)
        await db_session.commit()

        response = await async_client.get("/api/v1/ideas/idea-1")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == "idea-1"
        assert result["title"] == "Test Idea"

    @pytest.mark.asyncio
    async def test_get_idea_not_found(self, async_client: AsyncClient):
        """Test getting non-existent idea returns 404."""
        response = await async_client.get("/api/v1/ideas/nonexistent")

        assert response.status_code == 404


class TestListIdeas:
    """Tests for GET /api/v1/ideas endpoint."""

    @pytest.mark.asyncio
    async def test_list_ideas_empty(self, async_client: AsyncClient):
        """Test listing ideas when none exist."""
        response = await async_client.get("/api/v1/ideas")

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_ideas_with_data(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test listing ideas returns all ideas."""
        idea1 = Idea(
            id="idea-1",
            title="Idea 1",
            description="Desc 1",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.HIGH,
        )
        idea2 = Idea(
            id="idea-2",
            title="Idea 2",
            description="Desc 2",
            status=IdeaStatus.APPROVED,
            priority=IdeaPriority.MEDIUM,
        )
        db_session.add_all([idea1, idea2])
        await db_session.commit()

        response = await async_client.get("/api/v1/ideas")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_ideas_filter_by_status(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering ideas by status."""
        idea1 = Idea(
            id="idea-1",
            title="Idea 1",
            description="Desc 1",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.MEDIUM,
        )
        idea2 = Idea(
            id="idea-2",
            title="Idea 2",
            description="Desc 2",
            status=IdeaStatus.APPROVED,
            priority=IdeaPriority.MEDIUM,
        )
        db_session.add_all([idea1, idea2])
        await db_session.commit()

        response = await async_client.get("/api/v1/ideas?status=approved")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["status"] == "approved"


class TestUpdateIdea:
    """Tests for PUT /api/v1/ideas/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_idea(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating an idea."""
        idea = Idea(
            id="idea-1",
            title="Original Title",
            description="Original description",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.MEDIUM,
        )
        db_session.add(idea)
        await db_session.commit()

        update_data = {
            "title": "Updated Title",
            "status": "approved",
            "priority": "high",
        }
        response = await async_client.put("/api/v1/ideas/idea-1", json=update_data)

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "Updated Title"
        assert result["status"] == "approved"
        assert result["priority"] == "high"


class TestDeleteIdea:
    """Tests for DELETE /api/v1/ideas/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_idea(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test deleting an idea."""
        idea = Idea(
            id="idea-1",
            title="Test",
            description="Test desc",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.MEDIUM,
        )
        db_session.add(idea)
        await db_session.commit()

        response = await async_client.delete("/api/v1/ideas/idea-1")

        assert response.status_code == 204
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/test_api_ideas.py::TestCreateIdea::test_create_idea_valid_data -v
```

Expected: FAIL with "404 Not Found" (route doesn't exist)

**Step 3: Create ideas API router**

Create file `backend/app/api/ideas.py`:

```python
"""Ideas API endpoints."""
import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.idea import Idea, IdeaStatus, IdeaPriority
from app.schemas.idea import IdeaCreate, IdeaUpdate, IdeaResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ideas", tags=["ideas"])


@router.post("", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
async def create_idea(
    idea_in: IdeaCreate,
    db: AsyncSession = Depends(get_db),
) -> Idea:
    """Create a new idea.

    Args:
        idea_in: Idea data
        db: Database session

    Returns:
        Created idea
    """
    idea = Idea(
        id=str(uuid4()),
        title=idea_in.title,
        description=idea_in.description,
        status=IdeaStatus.BACKLOG,
        priority=IdeaPriority(idea_in.priority) if idea_in.priority else IdeaPriority.MEDIUM,
    )

    db.add(idea)
    await db.commit()
    await db.refresh(idea)

    logger.info(f"Created idea: {idea.id}")
    return idea


@router.get("", response_model=list[IdeaResponse])
@router.get("/", response_model=list[IdeaResponse])
async def list_ideas(
    skip: int = 0,
    limit: int = 100,
    status: str | None = Query(None, pattern="^(backlog|under_review|approved|rejected|implemented)$"),
    priority: str | None = Query(None, pattern="^(low|medium|high|critical)$"),
    db: AsyncSession = Depends(get_db),
) -> list[Idea]:
    """List all ideas with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status
        priority: Filter by priority
        db: Database session

    Returns:
        List of ideas
    """
    query = select(Idea).offset(skip).limit(limit).order_by(Idea.created_at.desc())

    # Apply filters
    if status:
        query = query.where(Idea.status == IdeaStatus(status))
    if priority:
        query = query.where(Idea.priority == IdeaPriority(priority))

    result = await db.execute(query)
    ideas = result.scalars().all()
    return list(ideas)


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
) -> Idea:
    """Get a specific idea.

    Args:
        idea_id: Idea ID
        db: Database session

    Returns:
        Idea

    Raises:
        HTTPException: If idea not found
    """
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Idea {idea_id} not found",
        )

    return idea


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: str,
    idea_update: IdeaUpdate,
    db: AsyncSession = Depends(get_db),
) -> Idea:
    """Update an idea.

    Args:
        idea_id: Idea ID
        idea_update: Update data
        db: Database session

    Returns:
        Updated idea

    Raises:
        HTTPException: If idea not found
    """
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Idea {idea_id} not found",
        )

    # Update fields
    update_data = idea_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status":
            value = IdeaStatus(value)
        elif field == "priority":
            value = IdeaPriority(value)
        setattr(idea, field, value)

    await db.commit()
    await db.refresh(idea)

    logger.info(f"Updated idea: {idea_id}")
    return idea


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an idea.

    Args:
        idea_id: Idea ID
        db: Database session

    Raises:
        HTTPException: If idea not found
    """
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Idea {idea_id} not found",
        )

    await db.delete(idea)
    await db.commit()

    logger.info(f"Deleted idea: {idea_id}")
```

**Step 4: Update conftest.py to include ideas router**

Modify `backend/tests/conftest.py`, add to the `async_client` fixture:

```python
# Add this import at the top
from app.api.ideas import router as ideas_router

# Inside async_client fixture, add this line after brainstorms_router:
test_app.include_router(ideas_router)
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/test_api_ideas.py -v
```

Expected: PASS (all CRUD tests)

**Step 6: Register router in main.py**

Modify `backend/app/main.py`:

```python
# Add import
from app.api.ideas import router as ideas_router

# Add after brainstorms router
app.include_router(ideas_router)
```

**Step 7: Commit**

```bash
git add backend/app/api/ideas.py backend/app/main.py backend/tests/test_api_ideas.py backend/tests/conftest.py
git commit -m "feat: add ideas CRUD API endpoints with filtering"
```

---

## Phase 5: Backend API - AI Evaluation Endpoint

### Task 6: Create AI Evaluation Endpoint

**Files:**
- Modify: `backend/app/api/ideas.py`
- Create: `backend/tests/test_api_idea_evaluation.py`

**Step 1: Write failing test for evaluation endpoint**

Create file `backend/tests/test_api_idea_evaluation.py`:

```python
"""Tests for idea evaluation endpoint."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestEvaluateIdea:
    """Tests for POST /api/v1/ideas/evaluate endpoint."""

    @pytest.mark.asyncio
    async def test_evaluate_idea_success(self, async_client: AsyncClient):
        """Test evaluating an idea with AI."""
        data = {
            "title": "Dark Mode Feature",
            "description": "Add dark mode support to the application",
        }

        # Mock IdeaEvaluationService
        mock_evaluation = {
            "business_value": 8,
            "technical_complexity": 5,
            "estimated_effort": "2 weeks",
            "market_fit_analysis": "Strong demand based on user feedback",
            "risk_assessment": "Low risk - standard UI implementation",
        }

        with patch("app.api.ideas.IdeaEvaluationService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.evaluate_idea = AsyncMock(return_value=mock_evaluation)

            response = await async_client.post("/api/v1/ideas/evaluate", json=data)

            assert response.status_code == 200
            result = response.json()
            assert result["business_value"] == 8
            assert result["technical_complexity"] == 5
            assert result["estimated_effort"] == "2 weeks"

    @pytest.mark.asyncio
    async def test_evaluate_idea_with_context(self, async_client: AsyncClient):
        """Test evaluating idea with additional context."""
        data = {
            "title": "Mobile Redesign",
            "description": "Redesign mobile app",
            "context": "Users have requested this feature 50+ times",
        }

        mock_evaluation = {
            "business_value": 9,
            "technical_complexity": 7,
            "estimated_effort": "3 months",
            "market_fit_analysis": "Very strong demand",
            "risk_assessment": "Medium risk - large scope",
        }

        with patch("app.api.ideas.IdeaEvaluationService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.evaluate_idea = AsyncMock(return_value=mock_evaluation)

            response = await async_client.post("/api/v1/ideas/evaluate", json=data)

            assert response.status_code == 200
            mock_instance.evaluate_idea.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_idea_api_key_missing(self, async_client: AsyncClient):
        """Test evaluation fails if API key not configured."""
        data = {
            "title": "Test Idea",
            "description": "Test description",
        }

        with patch("app.api.ideas.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""

            response = await async_client.post("/api/v1/ideas/evaluate", json=data)

            assert response.status_code == 500
            assert "API key not configured" in response.json()["detail"]
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_api_idea_evaluation.py::TestEvaluateIdea::test_evaluate_idea_success -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Add evaluation endpoint to ideas router**

Modify `backend/app/api/ideas.py`, add these imports at top:

```python
from app.config import settings
from app.services.idea_evaluation_service import IdeaEvaluationService
from app.schemas.idea import IdeaEvaluationRequest, IdeaEvaluationResponse
```

Add this endpoint to the router:

```python
@router.post("/evaluate", response_model=IdeaEvaluationResponse)
async def evaluate_idea(
    evaluation_request: IdeaEvaluationRequest,
) -> IdeaEvaluationResponse:
    """Evaluate an idea with AI.

    Args:
        evaluation_request: Idea details for evaluation

    Returns:
        AI evaluation result

    Raises:
        HTTPException: If API key not configured or evaluation fails
    """
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anthropic API key not configured",
        )

    try:
        async with IdeaEvaluationService(
            api_key=settings.anthropic_api_key
        ) as evaluation_service:
            result = await evaluation_service.evaluate_idea(
                title=evaluation_request.title,
                description=evaluation_request.description,
                context=evaluation_request.context,
            )

        logger.info(f"Evaluated idea: {evaluation_request.title}")
        return IdeaEvaluationResponse(**result)

    except Exception as e:
        logger.error(f"Error evaluating idea: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate idea: {str(e)}",
        )
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/test_api_idea_evaluation.py -v
```

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add backend/app/api/ideas.py backend/tests/test_api_idea_evaluation.py
git commit -m "feat: add AI evaluation endpoint for ideas"
```

---

## Phase 6: Frontend Foundation - Types & API Client

### Task 7: Create TypeScript Types for Ideas

**Files:**
- Create: `frontend/src/types/idea.ts`
- Modify: `frontend/src/types/index.ts`

**Step 1: Write failing test for types**

Create file `frontend/src/types/__tests__/idea.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import type {
  Idea,
  IdeaCreate,
  IdeaUpdate,
  IdeaStatus,
  IdeaPriority,
  IdeaEvaluationRequest,
  IdeaEvaluationResponse,
} from '../idea'

describe('Idea Types', () => {
  it('should define Idea type correctly', () => {
    const idea: Idea = {
      id: 'idea-1',
      title: 'Dark Mode Feature',
      description: 'Add dark mode support',
      status: 'backlog',
      priority: 'medium',
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong demand',
      risk_assessment: 'Low risk',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    expect(idea.id).toBe('idea-1')
    expect(idea.business_value).toBe(8)
  })

  it('should define IdeaCreate type correctly', () => {
    const create: IdeaCreate = {
      title: 'New Idea',
      description: 'New description',
      priority: 'high',
    }

    expect(create.title).toBe('New Idea')
    expect(create.priority).toBe('high')
  })

  it('should define IdeaEvaluationResponse type correctly', () => {
    const evaluation: IdeaEvaluationResponse = {
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong',
      risk_assessment: 'Low',
    }

    expect(evaluation.business_value).toBe(8)
  })
})
```

**Step 2: Run test to verify it fails**

```bash
cd frontend
npm run test -- src/types/__tests__/idea.spec.ts
```

Expected: FAIL with "Cannot find module '../idea'"

**Step 3: Create idea types**

Create file `frontend/src/types/idea.ts`:

```typescript
/**
 * Idea management types
 */

export type IdeaStatus = 'backlog' | 'under_review' | 'approved' | 'rejected' | 'implemented'
export type IdeaPriority = 'low' | 'medium' | 'high' | 'critical'

export interface Idea {
  id: string
  title: string
  description: string
  status: IdeaStatus
  priority: IdeaPriority
  business_value: number | null
  technical_complexity: number | null
  estimated_effort: string | null
  market_fit_analysis: string | null
  risk_assessment: string | null
  created_at: string
  updated_at: string
}

export interface IdeaCreate {
  title: string
  description: string
  priority?: IdeaPriority
}

export interface IdeaUpdate {
  title?: string
  description?: string
  status?: IdeaStatus
  priority?: IdeaPriority
  business_value?: number
  technical_complexity?: number
  estimated_effort?: string
  market_fit_analysis?: string
  risk_assessment?: string
}

export interface IdeaEvaluationRequest {
  title: string
  description: string
  context?: string
}

export interface IdeaEvaluationResponse {
  business_value: number
  technical_complexity: number
  estimated_effort: string
  market_fit_analysis: string
  risk_assessment: string
}
```

**Step 4: Update types index.ts**

Modify `frontend/src/types/index.ts`:

```typescript
export * from './feature'
export * from './analysis'
export * from './brainstorm'
export * from './idea'
```

**Step 5: Run tests to verify they pass**

```bash
npm run test -- src/types/__tests__/idea.spec.ts
```

Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add frontend/src/types/idea.ts frontend/src/types/index.ts frontend/src/types/__tests__/idea.spec.ts
git commit -m "feat: add TypeScript types for ideas"
```

---

### Task 8: Create Ideas API Client

**Files:**
- Create: `frontend/src/api/ideas.ts`
- Modify: `frontend/src/api/index.ts`

**Step 1: Write failing test for API client**

Create file `frontend/src/api/__tests__/ideas.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ideasApi } from '../ideas'
import apiClient from '../client'

vi.mock('../client')

describe('Ideas API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create an idea', async () => {
    const mockIdea = {
      id: 'idea-1',
      title: 'Test Idea',
      description: 'Test desc',
      status: 'backlog' as const,
      priority: 'medium' as const,
      business_value: null,
      technical_complexity: null,
      estimated_effort: null,
      market_fit_analysis: null,
      risk_assessment: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockIdea })

    const result = await ideasApi.createIdea({
      title: 'Test Idea',
      description: 'Test desc',
    })

    expect(result).toEqual(mockIdea)
    expect(apiClient.post).toHaveBeenCalledWith('/ideas/', {
      title: 'Test Idea',
      description: 'Test desc',
    })
  })

  it('should list ideas', async () => {
    const mockIdeas = [
      {
        id: 'idea-1',
        title: 'Idea 1',
        description: 'Desc 1',
        status: 'backlog' as const,
        priority: 'medium' as const,
        business_value: null,
        technical_complexity: null,
        estimated_effort: null,
        market_fit_analysis: null,
        risk_assessment: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(apiClient.get).mockResolvedValue({ data: mockIdeas })

    const result = await ideasApi.listIdeas()

    expect(result).toEqual(mockIdeas)
    expect(apiClient.get).toHaveBeenCalledWith('/ideas/', { params: {} })
  })

  it('should filter ideas by status', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: [] })

    await ideasApi.listIdeas({ status: 'approved' })

    expect(apiClient.get).toHaveBeenCalledWith('/ideas/', {
      params: { status: 'approved' },
    })
  })

  it('should evaluate an idea', async () => {
    const mockEvaluation = {
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong',
      risk_assessment: 'Low',
    }

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockEvaluation })

    const result = await ideasApi.evaluateIdea({
      title: 'Test',
      description: 'Test desc',
    })

    expect(result).toEqual(mockEvaluation)
    expect(apiClient.post).toHaveBeenCalledWith('/ideas/evaluate', {
      title: 'Test',
      description: 'Test desc',
    })
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm run test -- src/api/__tests__/ideas.spec.ts
```

Expected: FAIL with "Cannot find module '../ideas'"

**Step 3: Create ideas API client**

Create file `frontend/src/api/ideas.ts`:

```typescript
import apiClient from './client'
import type {
  Idea,
  IdeaCreate,
  IdeaUpdate,
  IdeaEvaluationRequest,
  IdeaEvaluationResponse,
} from '@/types/idea'

export interface ListIdeasParams {
  status?: string
  priority?: string
  skip?: number
  limit?: number
}

export const ideasApi = {
  /**
   * Create a new idea
   */
  async createIdea(data: IdeaCreate): Promise<Idea> {
    const response = await apiClient.post<Idea>('/ideas/', data)
    return response.data
  },

  /**
   * List all ideas with optional filtering
   */
  async listIdeas(params: ListIdeasParams = {}): Promise<Idea[]> {
    const response = await apiClient.get<Idea[]>('/ideas/', { params })
    return response.data
  },

  /**
   * Get a specific idea
   */
  async getIdea(id: string): Promise<Idea> {
    const response = await apiClient.get<Idea>(`/ideas/${id}`)
    return response.data
  },

  /**
   * Update an idea
   */
  async updateIdea(id: string, data: IdeaUpdate): Promise<Idea> {
    const response = await apiClient.put<Idea>(`/ideas/${id}`, data)
    return response.data
  },

  /**
   * Delete an idea
   */
  async deleteIdea(id: string): Promise<void> {
    await apiClient.delete(`/ideas/${id}`)
  },

  /**
   * Evaluate an idea with AI
   */
  async evaluateIdea(data: IdeaEvaluationRequest): Promise<IdeaEvaluationResponse> {
    const response = await apiClient.post<IdeaEvaluationResponse>('/ideas/evaluate', data)
    return response.data
  },
}

export default ideasApi
```

**Step 4: Update api index.ts**

Modify `frontend/src/api/index.ts`:

```typescript
export { default as featuresApi } from './features'
export { default as brainstormsApi } from './brainstorms'
export { default as ideasApi } from './ideas'
export { default as apiClient } from './client'
```

**Step 5: Run tests to verify they pass**

```bash
npm run test -- src/api/__tests__/ideas.spec.ts
```

Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add frontend/src/api/ideas.ts frontend/src/api/index.ts frontend/src/api/__tests__/ideas.spec.ts
git commit -m "feat: add ideas API client with evaluation support"
```

---

## Phase 7: Frontend State - Pinia Store

### Task 9: Create Ideas Pinia Store

**Files:**
- Create: `frontend/src/stores/ideas.ts`

**Step 1: Write failing test for store**

Create file `frontend/src/stores/__tests__/ideas.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIdeasStore } from '../ideas'
import { ideasApi } from '@/api/ideas'

vi.mock('@/api/ideas')

describe('Ideas Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should create an idea', async () => {
    const store = useIdeasStore()
    const mockIdea = {
      id: 'idea-1',
      title: 'Test Idea',
      description: 'Test desc',
      status: 'backlog' as const,
      priority: 'medium' as const,
      business_value: null,
      technical_complexity: null,
      estimated_effort: null,
      market_fit_analysis: null,
      risk_assessment: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(ideasApi.createIdea).mockResolvedValue(mockIdea)

    await store.createIdea({ title: 'Test Idea', description: 'Test desc' })

    expect(store.ideas).toHaveLength(1)
    expect(store.ideas[0]).toEqual(mockIdea)
  })

  it('should fetch ideas', async () => {
    const store = useIdeasStore()
    const mockIdeas = [
      {
        id: 'idea-1',
        title: 'Idea 1',
        description: 'Desc 1',
        status: 'backlog' as const,
        priority: 'medium' as const,
        business_value: null,
        technical_complexity: null,
        estimated_effort: null,
        market_fit_analysis: null,
        risk_assessment: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(ideasApi.listIdeas).mockResolvedValue(mockIdeas)

    await store.fetchIdeas()

    expect(store.ideas).toEqual(mockIdeas)
    expect(store.loading).toBe(false)
  })

  it('should evaluate an idea', async () => {
    const store = useIdeasStore()
    const mockEvaluation = {
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong',
      risk_assessment: 'Low',
    }

    vi.mocked(ideasApi.evaluateIdea).mockResolvedValue(mockEvaluation)

    const result = await store.evaluateIdea({
      title: 'Test',
      description: 'Test desc',
    })

    expect(result).toEqual(mockEvaluation)
    expect(store.evaluating).toBe(false)
  })

  it('should filter ideas by status', () => {
    const store = useIdeasStore()
    store.ideas = [
      {
        id: 'idea-1',
        title: 'Idea 1',
        description: 'Desc 1',
        status: 'backlog',
        priority: 'medium',
        business_value: null,
        technical_complexity: null,
        estimated_effort: null,
        market_fit_analysis: null,
        risk_assessment: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 'idea-2',
        title: 'Idea 2',
        description: 'Desc 2',
        status: 'approved',
        priority: 'high',
        business_value: null,
        technical_complexity: null,
        estimated_effort: null,
        market_fit_analysis: null,
        risk_assessment: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const approved = store.ideasByStatus('approved')

    expect(approved).toHaveLength(1)
    expect(approved[0].id).toBe('idea-2')
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm run test -- src/stores/__tests__/ideas.spec.ts
```

Expected: FAIL with "Cannot find module '../ideas'"

**Step 3: Create ideas store**

Create file `frontend/src/stores/ideas.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ideasApi, type ListIdeasParams } from '@/api/ideas'
import type {
  Idea,
  IdeaCreate,
  IdeaUpdate,
  IdeaEvaluationRequest,
  IdeaEvaluationResponse,
  IdeaStatus,
  IdeaPriority,
} from '@/types/idea'

export const useIdeasStore = defineStore('ideas', () => {
  // State
  const ideas = ref<Idea[]>([])
  const currentIdea = ref<Idea | null>(null)
  const loading = ref(false)
  const evaluating = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const ideasByStatus = computed(() => {
    return (status: IdeaStatus) => ideas.value.filter((idea) => idea.status === status)
  })

  const ideasByPriority = computed(() => {
    return (priority: IdeaPriority) => ideas.value.filter((idea) => idea.priority === priority)
  })

  const evaluatedIdeas = computed(() => {
    return ideas.value.filter((idea) => idea.business_value !== null)
  })

  // Actions
  async function createIdea(data: IdeaCreate) {
    loading.value = true
    error.value = null

    try {
      const idea = await ideasApi.createIdea(data)
      ideas.value.push(idea)
      currentIdea.value = idea
      return idea
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create idea'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchIdeas(params: ListIdeasParams = {}) {
    loading.value = true
    error.value = null

    try {
      ideas.value = await ideasApi.listIdeas(params)
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch ideas'
      error.value = errorMessage
    } finally {
      loading.value = false
    }
  }

  async function fetchIdea(id: string) {
    loading.value = true
    error.value = null

    try {
      currentIdea.value = await ideasApi.getIdea(id)
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch idea'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateIdea(id: string, data: IdeaUpdate) {
    loading.value = true
    error.value = null

    try {
      const updated = await ideasApi.updateIdea(id, data)
      currentIdea.value = updated

      // Update in ideas list
      const index = ideas.value.findIndex((i) => i.id === id)
      if (index !== -1) {
        ideas.value[index] = updated
      }

      return updated
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to update idea'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteIdea(id: string) {
    loading.value = true
    error.value = null

    try {
      await ideasApi.deleteIdea(id)

      // Remove from ideas list
      ideas.value = ideas.value.filter((i) => i.id !== id)

      if (currentIdea.value?.id === id) {
        currentIdea.value = null
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to delete idea'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function evaluateIdea(data: IdeaEvaluationRequest): Promise<IdeaEvaluationResponse> {
    evaluating.value = true
    error.value = null

    try {
      const evaluation = await ideasApi.evaluateIdea(data)
      return evaluation
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to evaluate idea'
      error.value = errorMessage
      throw e
    } finally {
      evaluating.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    ideas,
    currentIdea,
    loading,
    evaluating,
    error,
    // Getters
    ideasByStatus,
    ideasByPriority,
    evaluatedIdeas,
    // Actions
    createIdea,
    fetchIdeas,
    fetchIdea,
    updateIdea,
    deleteIdea,
    evaluateIdea,
    clearError,
  }
})
```

**Step 4: Run tests to verify they pass**

```bash
npm run test -- src/stores/__tests__/ideas.spec.ts
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add frontend/src/stores/ideas.ts frontend/src/stores/__tests__/ideas.spec.ts
git commit -m "feat: add ideas Pinia store with evaluation support"
```

---

## Phase 8: Frontend UI - Components

### Task 10: Create IdeaCard Component

**Files:**
- Create: `frontend/src/components/IdeaCard.vue`

**Step 1: Write failing test for component**

Create file `frontend/src/components/__tests__/IdeaCard.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IdeaCard from '../IdeaCard.vue'

describe('IdeaCard', () => {
  it('should render idea details', () => {
    const idea = {
      id: 'idea-1',
      title: 'Dark Mode Feature',
      description: 'Add dark mode support',
      status: 'backlog' as const,
      priority: 'high' as const,
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong',
      risk_assessment: 'Low',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    const wrapper = mount(IdeaCard, {
      props: { idea },
    })

    expect(wrapper.text()).toContain('Dark Mode Feature')
    expect(wrapper.text()).toContain('Add dark mode support')
  })

  it('should show evaluation scores', () => {
    const idea = {
      id: 'idea-1',
      title: 'Test',
      description: 'Test',
      status: 'backlog' as const,
      priority: 'medium' as const,
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: null,
      risk_assessment: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    const wrapper = mount(IdeaCard, {
      props: { idea },
    })

    expect(wrapper.text()).toContain('8')
    expect(wrapper.text()).toContain('5')
  })

  it('should emit click event', async () => {
    const idea = {
      id: 'idea-1',
      title: 'Test',
      description: 'Test',
      status: 'backlog' as const,
      priority: 'medium' as const,
      business_value: null,
      technical_complexity: null,
      estimated_effort: null,
      market_fit_analysis: null,
      risk_assessment: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    const wrapper = mount(IdeaCard, {
      props: { idea },
    })

    await wrapper.trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm run test -- src/components/__tests__/IdeaCard.spec.ts
```

Expected: FAIL with "Cannot find module '../IdeaCard.vue'"

**Step 3: Create IdeaCard component**

Create file `frontend/src/components/IdeaCard.vue`:

```vue
<template>
  <Card
    class="cursor-pointer hover:shadow-md transition-shadow"
    @click="$emit('click')"
  >
    <CardHeader>
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1 min-w-0">
          <CardTitle class="text-lg truncate">{{ idea.title }}</CardTitle>
          <CardDescription class="line-clamp-2 mt-1">
            {{ idea.description }}
          </CardDescription>
        </div>
        <div class="flex flex-col gap-2">
          <Badge :variant="getStatusVariant(idea.status)">
            {{ formatStatus(idea.status) }}
          </Badge>
          <Badge :variant="getPriorityVariant(idea.priority)">
            {{ formatPriority(idea.priority) }}
          </Badge>
        </div>
      </div>
    </CardHeader>

    <CardContent class="space-y-3">
      <!-- Evaluation Scores -->
      <div
        v-if="idea.business_value !== null || idea.technical_complexity !== null"
        class="flex gap-4"
      >
        <div v-if="idea.business_value !== null" class="flex items-center gap-2">
          <TrendingUp class="h-4 w-4 text-green-600" />
          <span class="text-sm font-medium">Value: {{ idea.business_value }}/10</span>
        </div>
        <div v-if="idea.technical_complexity !== null" class="flex items-center gap-2">
          <Wrench class="h-4 w-4 text-orange-600" />
          <span class="text-sm font-medium">Complexity: {{ idea.technical_complexity }}/10</span>
        </div>
      </div>

      <!-- Estimated Effort -->
      <div v-if="idea.estimated_effort" class="flex items-center gap-2 text-sm text-muted-foreground">
        <Clock class="h-4 w-4" />
        {{ idea.estimated_effort }}
      </div>

      <!-- Not Evaluated Badge -->
      <div v-else class="flex items-center gap-2 text-sm text-muted-foreground">
        <Sparkles class="h-4 w-4" />
        <span>Not evaluated yet</span>
      </div>

      <!-- Timestamp -->
      <div class="text-xs text-muted-foreground">
        {{ formatDate(idea.updated_at) }}
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import type { Idea } from '@/types/idea'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, Wrench, Clock, Sparkles } from 'lucide-vue-next'

defineProps<{
  idea: Idea
}>()

defineEmits<{
  click: []
}>()

function getStatusVariant(status: string) {
  switch (status) {
    case 'backlog':
      return 'secondary'
    case 'under_review':
      return 'default'
    case 'approved':
      return 'default'
    case 'rejected':
      return 'destructive'
    case 'implemented':
      return 'outline'
    default:
      return 'secondary'
  }
}

function getPriorityVariant(priority: string) {
  switch (priority) {
    case 'critical':
      return 'destructive'
    case 'high':
      return 'default'
    case 'medium':
      return 'secondary'
    case 'low':
      return 'outline'
    default:
      return 'secondary'
  }
}

function formatStatus(status: string): string {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatPriority(priority: string): string {
  return priority.charAt(0).toUpperCase() + priority.slice(1)
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
</script>
```

**Step 4: Run tests to verify they pass**

```bash
npm run test -- src/components/__tests__/IdeaCard.spec.ts
```

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add frontend/src/components/IdeaCard.vue frontend/src/components/__tests__/IdeaCard.spec.ts
git commit -m "feat: add IdeaCard component with evaluation display"
```

---

### Task 11: Create IdeaList Component with Filtering

**Files:**
- Create: `frontend/src/components/IdeaList.vue`

**Step 1: Create IdeaList component** (test optional for brevity)

Create file `frontend/src/components/IdeaList.vue`:

```vue
<template>
  <div class="space-y-4">
    <!-- Header with Filters -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold">Ideas</h2>
        <p class="text-muted-foreground">Capture and evaluate product ideas</p>
      </div>
      <Button @click="$emit('create-idea')">
        <Plus class="mr-2 h-4 w-4" />
        New Idea
      </Button>
    </div>

    <!-- Filters -->
    <div class="flex gap-4">
      <Select v-model="statusFilter">
        <SelectTrigger class="w-[180px]">
          <SelectValue placeholder="Filter by status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="backlog">Backlog</SelectItem>
          <SelectItem value="under_review">Under Review</SelectItem>
          <SelectItem value="approved">Approved</SelectItem>
          <SelectItem value="rejected">Rejected</SelectItem>
          <SelectItem value="implemented">Implemented</SelectItem>
        </SelectContent>
      </Select>

      <Select v-model="priorityFilter">
        <SelectTrigger class="w-[180px]">
          <SelectValue placeholder="Filter by priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Priorities</SelectItem>
          <SelectItem value="critical">Critical</SelectItem>
          <SelectItem value="high">High</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="low">Low</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading ideas...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-destructive">{{ error }}</p>
      <Button @click="fetchIdeas" variant="outline" class="mt-4">Retry</Button>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredIdeas.length === 0" class="text-center py-12">
      <Lightbulb class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Ideas Yet</h3>
      <p class="text-muted-foreground mb-4">
        Start capturing product ideas and evaluate them with AI
      </p>
      <Button @click="$emit('create-idea')">Create Your First Idea</Button>
    </div>

    <!-- Ideas Grid -->
    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <IdeaCard
        v-for="idea in filteredIdeas"
        :key="idea.id"
        :idea="idea"
        @click="$emit('select-idea', idea.id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useIdeasStore } from '@/stores/ideas'
import IdeaCard from './IdeaCard.vue'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Plus, Lightbulb } from 'lucide-vue-next'

defineEmits<{
  'create-idea': []
  'select-idea': [id: string]
}>()

const store = useIdeasStore()

const statusFilter = ref('all')
const priorityFilter = ref('all')

const ideas = computed(() => store.ideas)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

const filteredIdeas = computed(() => {
  let filtered = ideas.value

  if (statusFilter.value !== 'all') {
    filtered = filtered.filter((idea) => idea.status === statusFilter.value)
  }

  if (priorityFilter.value !== 'all') {
    filtered = filtered.filter((idea) => idea.priority === priorityFilter.value)
  }

  return filtered
})

async function fetchIdeas() {
  await store.fetchIdeas()
}

// Fetch ideas when filters change
watch([statusFilter, priorityFilter], () => {
  const params: any = {}
  if (statusFilter.value !== 'all') {
    params.status = statusFilter.value
  }
  if (priorityFilter.value !== 'all') {
    params.priority = priorityFilter.value
  }
  store.fetchIdeas(params)
})

onMounted(() => {
  fetchIdeas()
})
</script>
```

**Step 2: Commit**

```bash
git add frontend/src/components/IdeaList.vue
git commit -m "feat: add IdeaList component with filtering"
```

---

## Phase 9: Frontend UI - Views & Router

### Task 12: Create Ideas Views and Routes

**Files:**
- Create: `frontend/src/views/IdeasView.vue`
- Create: `frontend/src/views/IdeaDetailView.vue`
- Modify: `frontend/src/router/index.ts`

**Step 1: Create IdeasView with create dialog**

Create file `frontend/src/views/IdeasView.vue`:

```vue
<template>
  <div class="container mx-auto py-6">
    <IdeaList @create-idea="showCreateDialog = true" @select-idea="navigateToIdea" />

    <!-- Create Idea Dialog -->
    <Dialog v-model:open="showCreateDialog">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>New Idea</DialogTitle>
          <DialogDescription>
            Capture a new product idea and optionally evaluate it with AI
          </DialogDescription>
        </DialogHeader>

        <form @submit.prevent="handleCreate" class="space-y-4">
          <div class="space-y-2">
            <Label for="title">Title</Label>
            <Input
              id="title"
              v-model="formData.title"
              placeholder="Dark Mode Feature"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="description">Description</Label>
            <Textarea
              id="description"
              v-model="formData.description"
              placeholder="Add dark mode support to improve user experience in low-light environments"
              rows="4"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="priority">Priority</Label>
            <Select v-model="formData.priority">
              <SelectTrigger>
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox id="evaluate" v-model:checked="evaluateAfterCreate" />
            <Label for="evaluate" class="cursor-pointer">
              Evaluate with AI after creation
            </Label>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" @click="showCreateDialog = false">
              Cancel
            </Button>
            <Button type="submit" :disabled="loading || evaluating">
              {{ evaluating ? 'Evaluating...' : 'Create Idea' }}
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
import { useIdeasStore } from '@/stores/ideas'
import IdeaList from '@/components/IdeaList.vue'
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
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const router = useRouter()
const store = useIdeasStore()

const showCreateDialog = ref(false)
const evaluateAfterCreate = ref(true)
const formData = ref({
  title: '',
  description: '',
  priority: 'medium',
})

const loading = computed(() => store.loading)
const evaluating = computed(() => store.evaluating)

async function handleCreate() {
  try {
    const idea = await store.createIdea(formData.value)

    // Evaluate if requested
    if (evaluateAfterCreate.value) {
      const evaluation = await store.evaluateIdea({
        title: formData.value.title,
        description: formData.value.description,
      })

      // Update idea with evaluation
      await store.updateIdea(idea.id, {
        business_value: evaluation.business_value,
        technical_complexity: evaluation.technical_complexity,
        estimated_effort: evaluation.estimated_effort,
        market_fit_analysis: evaluation.market_fit_analysis,
        risk_assessment: evaluation.risk_assessment,
      })
    }

    showCreateDialog.value = false
    formData.value = { title: '', description: '', priority: 'medium' }
    evaluateAfterCreate.value = true

    router.push(`/ideas/${idea.id}`)
  } catch (error) {
    console.error('Failed to create idea:', error)
  }
}

function navigateToIdea(id: string) {
  router.push(`/ideas/${id}`)
}
</script>
```

**Step 2: Create IdeaDetailView**

Create file `frontend/src/views/IdeaDetailView.vue`:

```vue
<template>
  <div class="container mx-auto py-6">
    <div class="mb-4">
      <Button variant="ghost" size="sm" @click="router.back()">
        <ArrowLeft class="mr-2 h-4 w-4" />
        Back to Ideas
      </Button>
    </div>

    <div v-if="loading" class="text-center py-12">
      <p class="text-muted-foreground">Loading idea...</p>
    </div>

    <div v-else-if="idea" class="space-y-6">
      <!-- Header -->
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <h1 class="text-3xl font-bold">{{ idea.title }}</h1>
          <div class="flex gap-2 mt-2">
            <Badge :variant="getStatusVariant(idea.status)">
              {{ formatStatus(idea.status) }}
            </Badge>
            <Badge :variant="getPriorityVariant(idea.priority)">
              {{ formatPriority(idea.priority) }}
            </Badge>
          </div>
        </div>
        <Button variant="outline" @click="showEditDialog = true">
          <Edit class="mr-2 h-4 w-4" />
          Edit
        </Button>
      </div>

      <!-- Description -->
      <Card>
        <CardHeader>
          <CardTitle>Description</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="whitespace-pre-wrap">{{ idea.description }}</p>
        </CardContent>
      </Card>

      <!-- Evaluation -->
      <Card v-if="idea.business_value !== null">
        <CardHeader>
          <div class="flex items-center justify-between">
            <CardTitle>AI Evaluation</CardTitle>
            <Button variant="outline" size="sm" @click="handleReEvaluate">
              <RefreshCw class="mr-2 h-4 w-4" />
              Re-evaluate
            </Button>
          </div>
        </CardHeader>
        <CardContent class="space-y-4">
          <!-- Scores -->
          <div class="grid grid-cols-3 gap-4">
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">Business Value</p>
              <p class="text-2xl font-bold">{{ idea.business_value }}/10</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">Technical Complexity</p>
              <p class="text-2xl font-bold">{{ idea.technical_complexity }}/10</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">Estimated Effort</p>
              <p class="text-2xl font-bold">{{ idea.estimated_effort }}</p>
            </div>
          </div>

          <!-- Market Fit Analysis -->
          <div v-if="idea.market_fit_analysis" class="space-y-2">
            <h4 class="font-semibold">Market Fit Analysis</h4>
            <p class="text-sm text-muted-foreground">{{ idea.market_fit_analysis }}</p>
          </div>

          <!-- Risk Assessment -->
          <div v-if="idea.risk_assessment" class="space-y-2">
            <h4 class="font-semibold">Risk Assessment</h4>
            <p class="text-sm text-muted-foreground">{{ idea.risk_assessment }}</p>
          </div>
        </CardContent>
      </Card>

      <!-- No Evaluation -->
      <Card v-else>
        <CardContent class="text-center py-12">
          <Sparkles class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">Not Evaluated Yet</h3>
          <p class="text-muted-foreground mb-4">
            Use AI to evaluate business value, complexity, and market fit
          </p>
          <Button @click="handleEvaluate" :disabled="evaluating">
            {{ evaluating ? 'Evaluating...' : 'Evaluate with AI' }}
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useIdeasStore } from '@/stores/ideas'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Edit, RefreshCw, Sparkles } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const store = useIdeasStore()

const showEditDialog = ref(false)

const ideaId = route.params.id as string
const idea = computed(() => store.currentIdea)
const loading = computed(() => store.loading)
const evaluating = computed(() => store.evaluating)

async function handleEvaluate() {
  if (!idea.value) return

  try {
    const evaluation = await store.evaluateIdea({
      title: idea.value.title,
      description: idea.value.description,
    })

    await store.updateIdea(idea.value.id, {
      business_value: evaluation.business_value,
      technical_complexity: evaluation.technical_complexity,
      estimated_effort: evaluation.estimated_effort,
      market_fit_analysis: evaluation.market_fit_analysis,
      risk_assessment: evaluation.risk_assessment,
    })
  } catch (error) {
    console.error('Failed to evaluate idea:', error)
  }
}

async function handleReEvaluate() {
  await handleEvaluate()
}

function getStatusVariant(status: string) {
  // Same as IdeaCard
  switch (status) {
    case 'backlog':
      return 'secondary'
    case 'under_review':
      return 'default'
    case 'approved':
      return 'default'
    case 'rejected':
      return 'destructive'
    case 'implemented':
      return 'outline'
    default:
      return 'secondary'
  }
}

function getPriorityVariant(priority: string) {
  // Same as IdeaCard
  switch (priority) {
    case 'critical':
      return 'destructive'
    case 'high':
      return 'default'
    case 'medium':
      return 'secondary'
    case 'low':
      return 'outline'
    default:
      return 'secondary'
  }
}

function formatStatus(status: string): string {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatPriority(priority: string): string {
  return priority.charAt(0).toUpperCase() + priority.slice(1)
}

onMounted(async () => {
  await store.fetchIdea(ideaId)
})
</script>
```

**Step 3: Update router configuration**

Modify `frontend/src/router/index.ts`, add these routes inside the DashboardLayout children array:

```typescript
{
  path: 'ideas',
  name: 'ideas',
  component: () => import('@/views/IdeasView.vue'),
  meta: { title: 'Ideas' },
},
{
  path: 'ideas/:id',
  name: 'idea-detail',
  component: () => import('@/views/IdeaDetailView.vue'),
  meta: { title: 'Idea Details' },
},
```

**Step 4: Test navigation**

```bash
cd frontend
npm run dev
```

Expected: Navigate to http://localhost:8892/ideas and verify UI loads

**Step 5: Commit**

```bash
git add frontend/src/views/IdeasView.vue frontend/src/views/IdeaDetailView.vue frontend/src/router/index.ts
git commit -m "feat: add ideas views and routes with AI evaluation"
```

---

## Phase 10: Integration Testing & Documentation

### Task 13: Integration Tests

**Files:**
- Create: `backend/tests/test_integration_ideas.py`

**Step 1: Backend integration test**

Create file `backend/tests/test_integration_ideas.py`:

```python
"""Integration tests for ideas feature."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.idea import Idea


class TestIdeasIntegration:
    """End-to-end tests for ideas workflow."""

    @pytest.mark.asyncio
    async def test_complete_ideas_workflow(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test complete workflow: create, evaluate, update, delete."""
        # Step 1: Create idea
        create_data = {
            "title": "Dark Mode Feature",
            "description": "Add dark mode support to the application",
            "priority": "high",
        }
        response = await async_client.post("/api/v1/ideas", json=create_data)
        assert response.status_code == 201
        idea_data = response.json()
        idea_id = idea_data["id"]

        # Step 2: Verify idea in database
        result = await db_session.execute(
            select(Idea).where(Idea.id == idea_id)
        )
        db_idea = result.scalar_one()
        assert db_idea.title == create_data["title"]
        assert db_idea.priority.value == "high"

        # Step 3: List ideas
        response = await async_client.get("/api/v1/ideas")
        assert response.status_code == 200
        ideas = response.json()
        assert len(ideas) >= 1

        # Step 4: Filter by priority
        response = await async_client.get("/api/v1/ideas?priority=high")
        assert response.status_code == 200
        filtered = response.json()
        assert all(i["priority"] == "high" for i in filtered)

        # Step 5: Update idea
        update_data = {
            "status": "approved",
            "business_value": 8,
            "technical_complexity": 5,
        }
        response = await async_client.put(
            f"/api/v1/ideas/{idea_id}", json=update_data
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["status"] == "approved"
        assert updated["business_value"] == 8

        # Step 6: Get specific idea
        response = await async_client.get(f"/api/v1/ideas/{idea_id}")
        assert response.status_code == 200
        assert response.json()["business_value"] == 8

        # Step 7: Delete idea
        response = await async_client.delete(f"/api/v1/ideas/{idea_id}")
        assert response.status_code == 204

        # Step 8: Verify deletion
        result = await db_session.execute(
            select(Idea).where(Idea.id == idea_id)
        )
        assert result.scalar_one_or_none() is None
```

**Step 2: Run integration tests**

```bash
cd backend
poetry run pytest tests/test_integration_ideas.py -v
```

Expected: PASS (1 test)

**Step 3: Commit**

```bash
git add backend/tests/test_integration_ideas.py
git commit -m "test: add ideas integration tests"
```

---

### Task 14: Update Documentation

**Files:**
- Create: `docs/IDEAS_MODULE.md`
- Modify: `README.md`

**Step 1: Create module documentation**

Create file `docs/IDEAS_MODULE.md`:

```markdown
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
```

**Step 2: Update main README**

Modify `README.md`, add to the Modules section:

```markdown
### Module 3: Ideas Management ✅

Capture, evaluate, and prioritize product ideas with AI-powered analysis.

- Create and manage product ideas
- AI evaluation with Claude (business value, complexity, effort, market fit, risks)
- Filter by status and priority
- Status tracking (backlog → under review → approved → rejected → implemented)
- Priority levels (low, medium, high, critical)

[Full Documentation](docs/IDEAS_MODULE.md)
```

**Step 3: Commit**

```bash
git add docs/IDEAS_MODULE.md README.md
git commit -m "docs: add ideas module documentation"
```

---

## Phase 11: Quality Verification

### Task 15: Run Quality Gates

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
git commit -m "fix: quality gate fixes for ideas module"
```

---

## Phase 12: Manual Testing

### Task 16: End-to-End Manual Testing

**Manual Testing Checklist:**

1. **Backend Setup**:
   - [ ] Database migration applied
   - [ ] ANTHROPIC_API_KEY configured
   - [ ] Backend server running

2. **Create Idea**:
   - [ ] Navigate to http://localhost:8892/ideas
   - [ ] Click "New Idea"
   - [ ] Fill form with title, description, priority
   - [ ] Create with "Evaluate with AI" checked
   - [ ] Verify idea appears with evaluation scores

3. **View Idea Details**:
   - [ ] Click on idea card
   - [ ] Verify all details displayed
   - [ ] Verify evaluation scores visible
   - [ ] Click "Re-evaluate" and verify update

4. **Filtering**:
   - [ ] Use status filter dropdown
   - [ ] Use priority filter dropdown
   - [ ] Verify filtered results

5. **Edge Cases**:
   - [ ] Create idea without evaluation
   - [ ] Manually evaluate from detail view
   - [ ] Update idea status/priority
   - [ ] Test with invalid data

**Step 1: Document issues**

Create `docs/KNOWN_ISSUES.md` if needed.

**Step 2: Fix critical issues**

Fix any blocking issues.

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete Module 3 ideas management implementation"
```

---

## Summary

This implementation plan provides:

✅ **Backend (9 tasks)**:
- Idea model with status/priority enums
- Database migrations with constraints
- Pydantic schemas with validation
- IdeaEvaluationService with Claude
- CRUD API endpoints with filtering
- AI evaluation endpoint
- Comprehensive tests (90%+ coverage)

✅ **Frontend (7 tasks)**:
- TypeScript types
- API client with filtering support
- Pinia store with evaluation
- IdeaCard component
- IdeaList component with filters
- Views with AI evaluation UI
- Integration tests

✅ **Quality (3 tasks)**:
- Integration tests
- Documentation
- Quality gates verification
- Manual testing checklist

**Total Implementation Time**: ~2-3 weeks (as estimated in design doc)

**Test Coverage**: 90%+ (both backend and frontend)

**Git Commits**: 16 atomic commits following TDD and conventional commit format

---

## Next Steps After Implementation

1. **Review**: Code review with `/requesting-code-review` skill
2. **Deploy**: Deploy to staging environment
3. **Iterate**: Gather feedback and implement enhancements
4. **Module Integration**:
   - Connect to Brainstorming (create ideas from sessions)
   - Connect to Features (promote approved ideas to features)
   - Connect to Competitor Analysis (future Module 2)
