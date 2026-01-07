# Product Analysis Platform MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build minimal viable web platform for AI-powered feature analysis, integrating existing GitHub Actions workflow with user-friendly interface.

**Architecture:** Full-stack web application with FastAPI backend serving REST API and static frontend, PostgreSQL for data persistence, integration with existing Claude Agent SDK workflow via GitHub API. MVP focuses on feature analysis module only - defer competitor analysis and brainstorming to Phase 2.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, Vue.js 3, Vite, TypeScript, Shadcn-vue, Tailwind CSS, GitHub Actions (existing)

---

## Phase 1: Backend Foundation

### Task 1: Project Structure Setup

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/.env.example`
- Create: `backend/README.md`

**Step 1: Create backend directory structure**

```bash
mkdir -p backend/app/core backend/app/api backend/app/models backend/app/schemas backend/app/services
mkdir -p backend/tests
touch backend/app/__init__.py backend/app/core/__init__.py backend/app/api/__init__.py
touch backend/app/models/__init__.py backend/app/schemas/__init__.py backend/app/services/__init__.py
```

**Step 2: Create pyproject.toml with dependencies**

```toml
[tool.poetry]
name = "product-analysis-backend"
version = "0.1.0"
description = "Backend API for Product Analysis Platform"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"
psycopg2-binary = "^2.9.9"
pydantic = "^2.5.3"
pydantic-settings = "^2.1.0"
python-dotenv = "^1.0.0"
PyGithub = "^2.1.1"
httpx = "^0.26.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
black = "^23.12.1"
ruff = "^0.1.11"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Step 3: Create configuration module**

Create `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Application
    app_name: str = "Product Analysis Platform"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/product_analysis"

    # GitHub
    github_token: str
    github_repo: str = "boudydegeer/product-analysis"

    # Security
    secret_key: str = "change-this-in-production"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
```

**Step 4: Create main FastAPI application**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}
```

**Step 5: Create .env.example**

Create `backend/.env.example`:

```bash
# Application
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/product_analysis

# GitHub
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=boudydegeer/product-analysis

# Security
SECRET_KEY=change-this-in-production-use-openssl-rand-hex-32
```

**Step 6: Create README**

Create `backend/README.md`:

```markdown
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
poetry run pytest
```
```

**Step 7: Initialize Poetry and verify setup**

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

Expected: Server starts on http://localhost:8000, visit http://localhost:8000/health returns `{"status": "healthy"}`

**Step 8: Commit**

```bash
git add backend/
git commit -m "feat: initialize FastAPI backend with basic structure

- Add pyproject.toml with dependencies
- Create app structure with core config
- Add health check endpoint
- Configure CORS for frontend
- Add .env.example and README"
```

---

### Task 2: Database Models

**Files:**
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/feature.py`
- Create: `backend/app/models/analysis.py`

**Step 1: Create base model**

Create `backend/app/models/base.py`:

```python
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

**Step 2: Create Feature model**

Create `backend/app/models/feature.py`:

```python
from sqlalchemy import String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum

from app.models.base import Base, TimestampMixin


class FeatureStatus(str, enum.Enum):
    """Feature request status."""
    DRAFT = "draft"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Feature(Base, TimestampMixin):
    """Feature request model."""

    __tablename__ = "features"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FeatureStatus] = mapped_column(
        SQLEnum(FeatureStatus),
        default=FeatureStatus.DRAFT,
        nullable=False
    )

    # GitHub integration
    github_workflow_run_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relations
    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis",
        back_populates="feature",
        cascade="all, delete-orphan"
    )
```

**Step 3: Create Analysis model**

Create `backend/app/models/analysis.py`:

```python
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.models.base import Base, TimestampMixin


class Analysis(Base, TimestampMixin):
    """Feature analysis result model."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("features.id", ondelete="CASCADE"),
        nullable=False
    )

    # Analysis metadata
    workflow_run_id: Mapped[str] = mapped_column(String(50), nullable=False)
    workflow_run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    analyzed_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Complexity metrics
    story_points: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    prerequisite_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    total_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    complexity_level: Mapped[str] = mapped_column(String(20), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    # Repository state
    repository_maturity: Mapped[str] = mapped_column(String(20), nullable=False)

    # Full analysis data (JSON)
    warnings: Mapped[dict] = mapped_column(JSON, nullable=False)
    repository_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    affected_modules: Mapped[list] = mapped_column(JSON, nullable=False)
    implementation_tasks: Mapped[list] = mapped_column(JSON, nullable=False)
    technical_risks: Mapped[list] = mapped_column(JSON, nullable=False)
    recommendations: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Relations
    feature: Mapped["Feature"] = relationship("Feature", back_populates="analyses")
```

**Step 4: Update models __init__.py**

Create `backend/app/models/__init__.py`:

```python
from app.models.base import Base
from app.models.feature import Feature, FeatureStatus
from app.models.analysis import Analysis

__all__ = [
    "Base",
    "Feature",
    "FeatureStatus",
    "Analysis",
]
```

**Step 5: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add database models for features and analyses

- Create Base model with timestamp mixin
- Add Feature model with status enum
- Add Analysis model for storing workflow results
- Support full JSON storage of analysis data"
```

---

### Task 3: Database Setup with Alembic

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/app/core/database.py`

**Step 1: Create database module**

Create `backend/app/core/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings
from app.models.base import Base

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database - create all tables."""
    Base.metadata.create_all(bind=engine)
```

**Step 2: Initialize Alembic**

```bash
cd backend
poetry run alembic init alembic
```

**Step 3: Configure Alembic env.py**

Edit `backend/alembic/env.py` - replace the entire file:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import models
from app.core.config import settings
from app.models import Base

# Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 4: Create initial migration**

```bash
cd backend
poetry run alembic revision --autogenerate -m "initial schema"
```

**Step 5: Apply migration to create tables**

First, ensure PostgreSQL is running:

```bash
docker run -d \
  --name product-analysis-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=product_analysis \
  -p 5432:5432 \
  postgres:16
```

Then apply migration:

```bash
cd backend
poetry run alembic upgrade head
```

Expected: Tables `features` and `analyses` created in database

**Step 6: Commit**

```bash
git add backend/app/core/database.py backend/alembic/
git commit -m "feat: setup database with Alembic migrations

- Add database module with session management
- Configure Alembic for migrations
- Create initial migration with features and analyses tables
- Add Docker command for local PostgreSQL"
```

---

### Task 4: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/feature.py`
- Create: `backend/app/schemas/analysis.py`

**Step 1: Create feature schemas**

Create `backend/app/schemas/feature.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from app.models.feature import FeatureStatus


class FeatureBase(BaseModel):
    """Base feature schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)


class FeatureCreate(FeatureBase):
    """Schema for creating a feature."""
    id: str = Field(..., min_length=1, max_length=50, pattern="^[A-Z]+-[0-9]+$")


class FeatureUpdate(BaseModel):
    """Schema for updating a feature."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[FeatureStatus] = None


class FeatureResponse(FeatureBase):
    """Schema for feature response."""
    id: str
    status: FeatureStatus
    github_workflow_run_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FeatureTriggerAnalysis(BaseModel):
    """Schema for triggering analysis."""
    callback_url: Optional[str] = None
```

**Step 2: Create analysis schemas**

Create `backend/app/schemas/analysis.py`:

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Any


class AnalysisWarning(BaseModel):
    """Warning from analysis."""
    type: str
    severity: str
    message: str
    impact: str


class AnalysisComplexity(BaseModel):
    """Complexity metrics."""
    story_points: int
    estimated_hours: int
    prerequisite_hours: int
    total_hours: int
    level: str
    rationale: str


class AnalysisResponse(BaseModel):
    """Schema for analysis response."""
    id: int
    feature_id: str
    workflow_run_id: str
    workflow_run_number: int
    analyzed_at: str

    # Complexity
    story_points: int
    estimated_hours: int
    prerequisite_hours: int
    total_hours: int
    complexity_level: str
    rationale: str
    repository_maturity: str

    # Full data
    warnings: list[dict[str, Any]]
    repository_state: dict[str, Any]
    affected_modules: list[dict[str, Any]]
    implementation_tasks: list[dict[str, Any]]
    technical_risks: list[dict[str, Any]]
    recommendations: dict[str, Any]

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisSummary(BaseModel):
    """Simplified analysis for lists."""
    id: int
    feature_id: str
    analyzed_at: str
    story_points: int
    total_hours: int
    complexity_level: str
    repository_maturity: str
    warnings_count: int

    @classmethod
    def from_analysis(cls, analysis: Any) -> "AnalysisSummary":
        return cls(
            id=analysis.id,
            feature_id=analysis.feature_id,
            analyzed_at=analysis.analyzed_at,
            story_points=analysis.story_points,
            total_hours=analysis.total_hours,
            complexity_level=analysis.complexity_level,
            repository_maturity=analysis.repository_maturity,
            warnings_count=len(analysis.warnings)
        )
```

**Step 3: Update schemas __init__.py**

Create `backend/app/schemas/__init__.py`:

```python
from app.schemas.feature import (
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
    FeatureTriggerAnalysis,
)
from app.schemas.analysis import (
    AnalysisResponse,
    AnalysisSummary,
    AnalysisComplexity,
    AnalysisWarning,
)

__all__ = [
    "FeatureCreate",
    "FeatureUpdate",
    "FeatureResponse",
    "FeatureTriggerAnalysis",
    "AnalysisResponse",
    "AnalysisSummary",
    "AnalysisComplexity",
    "AnalysisWarning",
]
```

**Step 4: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for API validation

- Create feature schemas for CRUD operations
- Add analysis schemas for responses
- Include validation rules and field constraints
- Add summary schemas for list views"
```

---

### Task 5: GitHub Service

**Files:**
- Create: `backend/app/services/github_service.py`
- Create: `backend/tests/test_github_service.py`

**Step 1: Write failing test**

Create `backend/tests/test_github_service.py`:

```python
import pytest
from unittest.mock import Mock, patch
from app.services.github_service import GitHubService


@pytest.fixture
def github_service():
    return GitHubService(token="test_token", repo="owner/repo")


def test_trigger_workflow_success(github_service):
    """Test triggering GitHub Actions workflow."""
    with patch("app.services.github_service.Github") as mock_github:
        # Setup mock
        mock_repo = Mock()
        mock_workflow = Mock()
        mock_github.return_value.get_repo.return_value = mock_repo
        mock_repo.get_workflow.return_value = mock_workflow
        mock_workflow.create_dispatch.return_value = True

        # Test
        result = github_service.trigger_analysis(
            feature_id="TEST-001",
            description="Test feature"
        )

        # Verify
        assert result is True
        mock_workflow.create_dispatch.assert_called_once()


def test_get_workflow_run_not_found(github_service):
    """Test getting non-existent workflow run."""
    with patch("app.services.github_service.Github") as mock_github:
        mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = mock_repo
        mock_repo.get_workflow_run.side_effect = Exception("Not found")

        result = github_service.get_workflow_run("invalid_id")
        assert result is None
```

**Step 2: Run test to verify it fails**

```bash
cd backend
poetry run pytest tests/test_github_service.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.github_service'"

**Step 3: Write minimal implementation**

Create `backend/app/services/github_service.py`:

```python
from github import Github, GithubException
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""

    def __init__(self, token: str, repo: str):
        """Initialize GitHub service.

        Args:
            token: GitHub personal access token
            repo: Repository in format "owner/repo"
        """
        self.client = Github(token)
        self.repo_name = repo
        self.repo = self.client.get_repo(repo)

    def trigger_analysis(
        self,
        feature_id: str,
        description: str,
        callback_url: Optional[str] = None
    ) -> bool:
        """Trigger feature analysis workflow.

        Args:
            feature_id: Unique feature identifier
            description: Feature description or path to markdown file
            callback_url: Optional URL to POST results to

        Returns:
            True if workflow triggered successfully
        """
        try:
            workflow = self.repo.get_workflow("analyze-feature.yml")

            inputs = {
                "feature_id": feature_id,
                "feature_description": description,
            }

            if callback_url:
                inputs["callback_url"] = callback_url

            success = workflow.create_dispatch(
                ref="main",
                inputs=inputs
            )

            logger.info(f"Triggered analysis workflow for {feature_id}")
            return success

        except GithubException as e:
            logger.error(f"Failed to trigger workflow: {e}")
            return False

    def get_workflow_run(self, run_id: str) -> Optional[dict[str, Any]]:
        """Get workflow run details.

        Args:
            run_id: GitHub Actions workflow run ID

        Returns:
            Workflow run data or None if not found
        """
        try:
            run = self.repo.get_workflow_run(int(run_id))

            return {
                "id": str(run.id),
                "number": run.run_number,
                "status": run.status,
                "conclusion": run.conclusion,
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat(),
                "html_url": run.html_url,
            }

        except Exception as e:
            logger.error(f"Failed to get workflow run {run_id}: {e}")
            return None

    def get_workflow_artifact(self, run_id: str, artifact_name: str) -> Optional[bytes]:
        """Download workflow artifact.

        Args:
            run_id: GitHub Actions workflow run ID
            artifact_name: Name of artifact to download

        Returns:
            Artifact content as bytes or None if not found
        """
        try:
            run = self.repo.get_workflow_run(int(run_id))

            for artifact in run.get_artifacts():
                if artifact.name == artifact_name:
                    # Download artifact
                    url = artifact.archive_download_url
                    response = self.client._Github__requester.requestBlob(
                        "GET", url, None, None
                    )
                    return response[1]

            logger.warning(f"Artifact {artifact_name} not found in run {run_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to download artifact: {e}")
            return None
```

**Step 4: Run test to verify it passes**

```bash
cd backend
poetry run pytest tests/test_github_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/github_service.py backend/tests/test_github_service.py
git commit -m "feat: add GitHub service for workflow integration

- Implement workflow trigger via GitHub API
- Add methods to get workflow run status
- Support downloading workflow artifacts
- Include unit tests with mocks"
```

---

### Task 6: Feature API Endpoints

**Files:**
- Create: `backend/app/api/v1/features.py`
- Create: `backend/app/api/v1/__init__.py`
- Modify: `backend/app/main.py`

**Step 1: Create features API router**

Create `backend/app/api/v1/features.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.models import Feature, FeatureStatus
from app.schemas import (
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
    FeatureTriggerAnalysis,
)
from app.services.github_service import GitHubService

router = APIRouter(prefix="/features", tags=["features"])


def get_github_service() -> GitHubService:
    """Dependency for GitHub service."""
    return GitHubService(
        token=settings.github_token,
        repo=settings.github_repo
    )


@router.post("/", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
def create_feature(
    feature_in: FeatureCreate,
    db: Session = Depends(get_db)
):
    """Create a new feature request."""
    # Check if feature ID already exists
    existing = db.query(Feature).filter(Feature.id == feature_in.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feature with ID {feature_in.id} already exists"
        )

    # Create feature
    feature = Feature(
        id=feature_in.id,
        title=feature_in.title,
        description=feature_in.description,
        status=FeatureStatus.DRAFT,
    )

    db.add(feature)
    db.commit()
    db.refresh(feature)

    return feature


@router.get("/", response_model=List[FeatureResponse])
def list_features(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all features."""
    features = db.query(Feature).offset(skip).limit(limit).all()
    return features


@router.get("/{feature_id}", response_model=FeatureResponse)
def get_feature(
    feature_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific feature."""
    feature = db.query(Feature).filter(Feature.id == feature_id).first()
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )
    return feature


@router.patch("/{feature_id}", response_model=FeatureResponse)
def update_feature(
    feature_id: str,
    feature_in: FeatureUpdate,
    db: Session = Depends(get_db)
):
    """Update a feature."""
    feature = db.query(Feature).filter(Feature.id == feature_id).first()
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )

    # Update fields
    update_data = feature_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feature, field, value)

    db.commit()
    db.refresh(feature)

    return feature


@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feature(
    feature_id: str,
    db: Session = Depends(get_db)
):
    """Delete a feature."""
    feature = db.query(Feature).filter(Feature.id == feature_id).first()
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )

    db.delete(feature)
    db.commit()


@router.post("/{feature_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
def trigger_analysis(
    feature_id: str,
    trigger_in: FeatureTriggerAnalysis,
    db: Session = Depends(get_db),
    github: GitHubService = Depends(get_github_service)
):
    """Trigger GitHub Actions workflow to analyze feature."""
    feature = db.query(Feature).filter(Feature.id == feature_id).first()
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )

    # Trigger workflow
    success = github.trigger_analysis(
        feature_id=feature.id,
        description=feature.description,
        callback_url=trigger_in.callback_url
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger analysis workflow"
        )

    # Update feature status
    feature.status = FeatureStatus.ANALYZING
    db.commit()

    return {
        "message": "Analysis workflow triggered",
        "feature_id": feature_id,
        "status": "analyzing"
    }
```

**Step 2: Create API v1 router**

Create `backend/app/api/v1/__init__.py`:

```python
from fastapi import APIRouter
from app.api.v1 import features

router = APIRouter(prefix="/api/v1")

router.include_router(features.router)
```

**Step 3: Mount API router in main app**

Edit `backend/app/main.py` - add after CORS middleware:

```python
from app.api.v1 import router as api_router

# ... existing code ...

app.include_router(api_router)
```

**Step 4: Test API endpoints**

```bash
# Start server
cd backend
poetry run uvicorn app.main:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/api/v1/features/

# Create a feature
curl -X POST http://localhost:8000/api/v1/features/ \
  -H "Content-Type: application/json" \
  -d '{"id": "TEST-001", "title": "Test Feature", "description": "Test description"}'

# Get the feature
curl http://localhost:8000/api/v1/features/TEST-001
```

Expected: All endpoints work correctly

**Step 5: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add feature management API endpoints

- Implement CRUD endpoints for features
- Add endpoint to trigger GitHub Actions analysis
- Include GitHub service integration
- Mount API router in main app"
```

---

## Phase 2: Frontend Foundation

### Task 7: Frontend Project Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`

**Step 1: Create frontend directory and initialize project**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
npm create vite@latest frontend -- --template vue-ts
cd frontend
```

**Step 2: Install dependencies**

```bash
npm install
npm install -D tailwindcss postcss autoprefixer
npm install vue-router@4 pinia axios
npx tailwindcss init -p
```

**Step 3: Configure Tailwind CSS**

Edit `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Step 4: Create Tailwind CSS entry point**

Create `frontend/src/style.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Step 5: Update main.ts**

Edit `frontend/src/main.ts`:

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
```

**Step 6: Create basic App.vue**

Edit `frontend/src/App.vue`:

```vue
<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-900">
          Product Analysis Platform
        </h1>
      </div>
    </header>
    <main>
      <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
          <div class="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
            <p class="text-gray-500">Frontend setup complete! Ready for components.</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
// Component logic will go here
</script>
```

**Step 7: Test frontend**

```bash
cd frontend
npm run dev
```

Expected: Frontend runs on http://localhost:5173 with styled page

**Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: initialize Vue.js frontend with Vite

- Create Vue 3 + TypeScript project with Vite
- Install Tailwind CSS for styling
- Add Pinia for state management
- Add axios for API calls
- Create basic app layout"
```

---

### Task 8: API Client

**Files:**
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/types/feature.ts`

**Step 1: Create type definitions**

Create `frontend/src/types/feature.ts`:

```typescript
export enum FeatureStatus {
  DRAFT = 'draft',
  ANALYZING = 'analyzing',
  ANALYZED = 'analyzed',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
}

export interface Feature {
  id: string
  title: string
  description: string
  status: FeatureStatus
  github_workflow_run_id?: string
  created_at: string
  updated_at: string
}

export interface FeatureCreate {
  id: string
  title: string
  description: string
}

export interface FeatureUpdate {
  title?: string
  description?: string
  status?: FeatureStatus
}

export interface Analysis {
  id: number
  feature_id: string
  workflow_run_id: string
  workflow_run_number: number
  analyzed_at: string
  story_points: number
  estimated_hours: number
  prerequisite_hours: number
  total_hours: number
  complexity_level: string
  rationale: string
  repository_maturity: string
  warnings: any[]
  repository_state: any
  affected_modules: any[]
  implementation_tasks: any[]
  technical_risks: any[]
  recommendations: any
  created_at: string
  updated_at: string
}
```

**Step 2: Create API client**

Create `frontend/src/services/api.ts`:

```typescript
import axios from 'axios'
import type { Feature, FeatureCreate, FeatureUpdate, Analysis } from '@/types/feature'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const featureApi = {
  // List all features
  list: async (): Promise<Feature[]> => {
    const response = await api.get('/features/')
    return response.data
  },

  // Get single feature
  get: async (id: string): Promise<Feature> => {
    const response = await api.get(`/features/${id}`)
    return response.data
  },

  // Create new feature
  create: async (data: FeatureCreate): Promise<Feature> => {
    const response = await api.post('/features/', data)
    return response.data
  },

  // Update feature
  update: async (id: string, data: FeatureUpdate): Promise<Feature> => {
    const response = await api.patch(`/features/${id}`, data)
    return response.data
  },

  // Delete feature
  delete: async (id: string): Promise<void> => {
    await api.delete(`/features/${id}`)
  },

  // Trigger analysis
  triggerAnalysis: async (id: string): Promise<void> => {
    await api.post(`/features/${id}/analyze`, {})
  },
}

export default api
```

**Step 3: Create .env file for configuration**

Create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Step 4: Commit**

```bash
git add frontend/src/services/ frontend/src/types/ frontend/.env
git commit -m "feat: add API client and type definitions

- Create TypeScript types for Feature and Analysis
- Implement API client with axios
- Add all feature endpoints
- Configure base URL via environment variable"
```

---

### Task 9: Feature List Component

**Files:**
- Create: `frontend/src/components/FeatureList.vue`
- Create: `frontend/src/stores/features.ts`
- Modify: `frontend/src/App.vue`

**Step 1: Create Pinia store for features**

Create `frontend/src/stores/features.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { featureApi } from '@/services/api'
import type { Feature, FeatureCreate } from '@/types/feature'

export const useFeaturesStore = defineStore('features', () => {
  const features = ref<Feature[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFeatures() {
    loading.value = true
    error.value = null
    try {
      features.value = await featureApi.list()
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch features'
      console.error('Error fetching features:', e)
    } finally {
      loading.value = false
    }
  }

  async function createFeature(data: FeatureCreate) {
    loading.value = true
    error.value = null
    try {
      const newFeature = await featureApi.create(data)
      features.value.push(newFeature)
      return newFeature
    } catch (e: any) {
      error.value = e.message || 'Failed to create feature'
      console.error('Error creating feature:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function triggerAnalysis(id: string) {
    loading.value = true
    error.value = null
    try {
      await featureApi.triggerAnalysis(id)
      // Refresh feature to get updated status
      const updated = await featureApi.get(id)
      const index = features.value.findIndex(f => f.id === id)
      if (index !== -1) {
        features.value[index] = updated
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to trigger analysis'
      console.error('Error triggering analysis:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    features,
    loading,
    error,
    fetchFeatures,
    createFeature,
    triggerAnalysis,
  }
})
```

**Step 2: Create FeatureList component**

Create `frontend/src/components/FeatureList.vue`:

```vue
<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h2 class="text-2xl font-semibold text-gray-900">Features</h2>
      <button
        @click="showCreateForm = true"
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        New Feature
      </button>
    </div>

    <!-- Create Form Modal -->
    <div v-if="showCreateForm" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-semibold mb-4">Create New Feature</h3>
        <form @submit.prevent="handleCreate" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Feature ID</label>
            <input
              v-model="newFeature.id"
              type="text"
              placeholder="FEAT-001"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Title</label>
            <input
              v-model="newFeature.title"
              type="text"
              placeholder="Feature title"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              v-model="newFeature.description"
              rows="4"
              placeholder="Detailed feature description"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
              required
            ></textarea>
          </div>
          <div class="flex justify-end space-x-2">
            <button
              type="button"
              @click="showCreateForm = false"
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.loading" class="text-center py-8">
      <p class="text-gray-500">Loading features...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-800">{{ store.error }}</p>
    </div>

    <!-- Feature List -->
    <div v-else-if="store.features.length > 0" class="bg-white shadow overflow-hidden rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="feature in store.features" :key="feature.id" class="p-4 hover:bg-gray-50">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-2">
                <h3 class="text-lg font-medium text-gray-900">{{ feature.title }}</h3>
                <span
                  class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="getStatusClass(feature.status)"
                >
                  {{ feature.status }}
                </span>
              </div>
              <p class="text-sm text-gray-500 mt-1">{{ feature.id }}</p>
              <p class="text-sm text-gray-700 mt-2">{{ feature.description }}</p>
            </div>
            <button
              @click="handleAnalyze(feature.id)"
              :disabled="feature.status === 'analyzing'"
              class="ml-4 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {{ feature.status === 'analyzing' ? 'Analyzing...' : 'Analyze' }}
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12 bg-white rounded-lg shadow">
      <p class="text-gray-500">No features yet. Create your first feature to get started!</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFeaturesStore } from '@/stores/features'
import type { FeatureStatus } from '@/types/feature'

const store = useFeaturesStore()
const showCreateForm = ref(false)
const newFeature = ref({
  id: '',
  title: '',
  description: '',
})

onMounted(() => {
  store.fetchFeatures()
})

async function handleCreate() {
  try {
    await store.createFeature(newFeature.value)
    showCreateForm.value = false
    newFeature.value = { id: '', title: '', description: '' }
  } catch (e) {
    console.error('Failed to create feature:', e)
  }
}

async function handleAnalyze(id: string) {
  try {
    await store.triggerAnalysis(id)
    alert('Analysis started! Check back in a few minutes.')
  } catch (e) {
    console.error('Failed to trigger analysis:', e)
    alert('Failed to start analysis. Please try again.')
  }
}

function getStatusClass(status: FeatureStatus): string {
  const classes: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    analyzing: 'bg-yellow-100 text-yellow-800',
    analyzed: 'bg-blue-100 text-blue-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    in_progress: 'bg-purple-100 text-purple-800',
    completed: 'bg-green-100 text-green-800',
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}
</script>
```

**Step 3: Update App.vue to use FeatureList**

Edit `frontend/src/App.vue`:

```vue
<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-900">
          Product Analysis Platform
        </h1>
      </div>
    </header>
    <main>
      <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <FeatureList />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import FeatureList from './components/FeatureList.vue'
</script>
```

**Step 4: Test the full stack**

```bash
# Terminal 1: Start backend
cd backend
poetry run uvicorn app.main:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev
```

Visit http://localhost:5173, create a feature, and trigger analysis.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: add feature list component with full CRUD

- Create Pinia store for features state
- Build FeatureList component with create form
- Add trigger analysis button
- Integrate with backend API
- Complete MVP frontend"
```

---

## Summary

This plan creates a working MVP of the Product Analysis Platform with:

1. ✅ **Backend (FastAPI)**
   - Database models for features and analyses
   - REST API for feature management
   - GitHub Actions integration for triggering analysis
   - PostgreSQL with Alembic migrations

2. ✅ **Frontend (Vue.js 3)**
   - Feature list with CRUD operations
   - Trigger analysis workflow
   - Tailwind CSS styling
   - TypeScript type safety

3. ✅ **Integration**
   - Existing GitHub Actions workflow for Claude Agent SDK analysis
   - API to trigger workflows
   - Store and display results

**Next Steps (Phase 2):**
- Add analysis results API endpoint
- Create analysis detail view component
- Add webhook endpoint for GitHub to POST results
- Export to ClickUp integration
- Competitor analysis module
- Brainstorming chat interface

**Total Estimated Time:** 8-12 hours for Phase 1 MVP
