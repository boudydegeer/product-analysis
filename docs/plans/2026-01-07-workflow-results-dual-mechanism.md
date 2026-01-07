# Implementation Plan: Dual Mechanism for GitHub Workflow Results

**Date:** 2026-01-07
**Author:** Product Analysis Team
**Status:** Ready for Execution

---

## Goal

Implement a robust dual mechanism system to receive GitHub workflow analysis results:
1. **Primary mechanism**: Webhook endpoint that receives results via HTTP POST callback
2. **Fallback mechanism**: Polling service that checks workflow status and downloads artifacts

This ensures reliable result delivery regardless of network conditions, localhost development limitations, or webhook failures.

---

## Architecture Overview

### Components

1. **Webhook Endpoint** (`POST /api/v1/webhooks/analysis-result`)
   - Receives analysis results from GitHub workflow
   - Validates webhook signature/secret
   - Stores results in database
   - Updates feature status to COMPLETED/FAILED

2. **Polling Service** (`AnalysisPollingService`)
   - Background task that monitors workflows in ANALYZING status
   - Falls back when webhook doesn't deliver within timeout
   - Checks workflow status via GitHub API
   - Downloads artifacts when workflow completes
   - Updates feature with results

3. **Configuration**
   - Webhook secret for signature validation
   - Webhook URL generation (with ngrok support for localhost)
   - Polling interval and timeout settings

4. **Database Changes**
   - Add `webhook_secret` to Feature model (for validating incoming webhooks)
   - Add `last_polled_at` timestamp to Feature model
   - Add `webhook_received_at` timestamp to Feature model

### Flow Diagram

```
Feature Analysis Request
         |
         v
Trigger GitHub Workflow (with callback_url if available)
         |
         +------------------+
         |                  |
         v                  v
    WEBHOOK PATH      POLLING PATH
         |                  |
    Workflow posts         |
    to callback_url        |
         |                  |
         v                  v
    Webhook endpoint    Poll workflow status
    validates & stores  every 30s for 15 min
         |                  |
         v                  v
    Update Feature      Download artifact
         |              & Update Feature
         |                  |
         +--------+---------+
                  |
                  v
         Feature COMPLETED/FAILED
```

---

## Tech Stack

- **Backend**: FastAPI (async)
- **Database**: PostgreSQL with SQLAlchemy async
- **HTTP Client**: httpx (already used in GitHubService)
- **Background Tasks**: asyncio tasks + APScheduler for polling
- **Webhook Security**: HMAC-SHA256 signature validation
- **Testing**: pytest with pytest-asyncio

---

## Tasks Breakdown

### Task 1: Add Configuration for Webhooks and Polling

**Duration**: 2 minutes

**Files to modify**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/config.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/.env.example`

**Steps**:

1. **Write tests first** (TDD RED phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_config.py`

```python
"""Tests for configuration settings."""
import pytest
from app.config import Settings


class TestWebhookConfig:
    """Tests for webhook configuration."""

    def test_webhook_secret_is_configurable(self):
        """Webhook secret should be configurable via env var."""
        settings = Settings(webhook_secret="test-secret-123")
        assert settings.webhook_secret == "test-secret-123"

    def test_webhook_base_url_is_configurable(self):
        """Webhook base URL should be configurable for different environments."""
        settings = Settings(webhook_base_url="https://api.example.com")
        assert settings.webhook_base_url == "https://api.example.com"

    def test_webhook_base_url_defaults_to_none_for_localhost(self):
        """Webhook base URL should default to None for localhost development."""
        settings = Settings()
        assert settings.webhook_base_url is None


class TestPollingConfig:
    """Tests for polling configuration."""

    def test_polling_interval_is_configurable(self):
        """Polling interval should be configurable."""
        settings = Settings(analysis_polling_interval_seconds=60)
        assert settings.analysis_polling_interval_seconds == 60

    def test_polling_interval_has_default(self):
        """Polling interval should have a sensible default."""
        settings = Settings()
        assert settings.analysis_polling_interval_seconds == 30

    def test_polling_timeout_is_configurable(self):
        """Polling timeout should be configurable."""
        settings = Settings(analysis_polling_timeout_seconds=1800)
        assert settings.analysis_polling_timeout_seconds == 1800

    def test_polling_timeout_has_default(self):
        """Polling timeout should have default of 15 minutes."""
        settings = Settings()
        assert settings.analysis_polling_timeout_seconds == 900  # 15 minutes
```

**Run tests** (should FAIL):
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_config.py -v
```

**Expected output**: Tests fail because settings don't exist yet

2. **Implement configuration** (TDD GREEN phase)

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Product Analysis Platform"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/product_analysis"

    # GitHub
    github_token: str = "placeholder"
    github_repo: str = "boudydegeer/product-analysis"

    # Security
    secret_key: str = "change-this-in-production"

    # Webhooks
    webhook_secret: str = "change-this-webhook-secret-in-production"
    webhook_base_url: str | None = None  # Set for production, leave None for localhost

    # Analysis Polling
    analysis_polling_interval_seconds: int = 30  # Check every 30 seconds
    analysis_polling_timeout_seconds: int = 900  # Give up after 15 minutes

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",  # Vite dev server (default)
        "http://localhost:5174",  # Vite fallback port
        "http://localhost:5175",  # Vite fallback port
        "http://localhost:5176",  # Vite fallback port
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
```

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/.env.example`:

```bash
# Application
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/product_analysis

# GitHub
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=boudydegeer/product-analysis

# Security
SECRET_KEY=change-this-in-production-use-openssl-rand-hex-32

# Webhooks
# For localhost: leave WEBHOOK_BASE_URL empty (webhooks won't work, polling will be used)
# For production: set to your public API URL (e.g., https://api.yourapp.com)
# For localhost with ngrok: set to your ngrok URL (e.g., https://abc123.ngrok.io)
WEBHOOK_BASE_URL=
WEBHOOK_SECRET=change-this-webhook-secret-in-production

# Analysis Polling
ANALYSIS_POLLING_INTERVAL_SECONDS=30
ANALYSIS_POLLING_TIMEOUT_SECONDS=900
```

3. **Verify tests pass** (TDD GREEN phase)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_config.py -v
```

**Expected output**: All tests pass

4. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/config.py backend/.env.example backend/tests/test_config.py
git commit -m "feat(backend): add webhook and polling configuration settings

Add configuration for:
- Webhook secret and base URL
- Analysis polling interval and timeout

This supports dual mechanism for receiving workflow results."
```

---

### Task 2: Update Database Models for Webhook Tracking

**Duration**: 3 minutes

**Files to modify**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/models/feature.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_models.py`

**Steps**:

1. **Write tests first** (TDD RED phase)

Add to `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_models.py`:

```python
"""Add these test methods to existing TestFeature class or create if it doesn't exist."""

import pytest
from datetime import datetime
from app.models.feature import Feature, FeatureStatus


class TestFeatureWebhookFields:
    """Tests for webhook-related fields in Feature model."""

    def test_feature_has_webhook_secret_field(self):
        """Feature should have webhook_secret field for validation."""
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
            webhook_secret="secret-abc-123",
        )
        assert feature.webhook_secret == "secret-abc-123"

    def test_webhook_secret_is_optional(self):
        """Webhook secret should be optional (can be None)."""
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
        )
        assert feature.webhook_secret is None

    def test_feature_has_webhook_received_at_field(self):
        """Feature should track when webhook was received."""
        now = datetime.utcnow()
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
            webhook_received_at=now,
        )
        assert feature.webhook_received_at == now

    def test_webhook_received_at_is_optional(self):
        """Webhook received timestamp should be optional."""
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
        )
        assert feature.webhook_received_at is None

    def test_feature_has_last_polled_at_field(self):
        """Feature should track when it was last polled."""
        now = datetime.utcnow()
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
            last_polled_at=now,
        )
        assert feature.last_polled_at == now

    def test_last_polled_at_is_optional(self):
        """Last polled timestamp should be optional."""
        feature = Feature(
            id="test-123",
            name="Test Feature",
            description="Test",
        )
        assert feature.last_polled_at is None
```

**Run tests** (should FAIL):
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_models.py::TestFeatureWebhookFields -v
```

**Expected output**: Tests fail because fields don't exist

2. **Implement model changes** (TDD GREEN phase)

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/models/feature.py`:

```python
"""Feature model for tracking feature requests."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
import enum

from sqlalchemy import String, Text, Integer, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis import Analysis


class FeatureStatus(str, enum.Enum):
    """Feature request status."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class Feature(Base, TimestampMixin):
    """Feature request model."""

    __tablename__ = "features"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FeatureStatus] = mapped_column(
        SQLEnum(FeatureStatus),
        default=FeatureStatus.PENDING,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    github_issue_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    analysis_workflow_run_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Webhook tracking
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    webhook_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Polling tracking
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis",
        back_populates="feature",
        cascade="all, delete-orphan",
    )
```

3. **Create database migration**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
alembic revision --autogenerate -m "add webhook and polling fields to feature model"
```

**Expected output**: New migration file created in `alembic/versions/`

4. **Verify tests pass** (TDD GREEN phase)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_models.py::TestFeatureWebhookFields -v
```

**Expected output**: All tests pass

5. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/models/feature.py backend/tests/test_models.py backend/alembic/versions/*.py
git commit -m "feat(backend): add webhook and polling tracking fields to Feature model

Add fields:
- webhook_secret: for validating incoming webhooks
- webhook_received_at: timestamp when webhook was received
- last_polled_at: timestamp of last polling attempt

Include database migration for new fields."
```

---

### Task 3: Create Webhook Schema and Validation

**Duration**: 3 minutes

**Files to create**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/schemas/webhook.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_webhook_schemas.py`

**Steps**:

1. **Write tests first** (TDD RED phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_webhook_schemas.py`

```python
"""Tests for webhook schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.webhook import AnalysisResultWebhook


class TestAnalysisResultWebhook:
    """Tests for AnalysisResultWebhook schema."""

    def test_webhook_parses_valid_payload(self):
        """Should parse valid webhook payload from GitHub workflow."""
        payload = {
            "feature_id": "test-123",
            "complexity": {
                "story_points": 5,
                "estimated_hours": 16,
                "level": "Medium",
            },
            "metadata": {
                "workflow_run_id": "12345",
                "repository": "owner/repo",
            },
        }

        webhook = AnalysisResultWebhook(**payload)

        assert webhook.feature_id == "test-123"
        assert webhook.complexity["story_points"] == 5
        assert webhook.metadata["workflow_run_id"] == "12345"

    def test_webhook_requires_feature_id(self):
        """Feature ID is required in webhook payload."""
        payload = {
            "complexity": {"story_points": 5},
        }

        with pytest.raises(ValidationError) as exc_info:
            AnalysisResultWebhook(**payload)

        assert "feature_id" in str(exc_info.value)

    def test_webhook_accepts_error_field(self):
        """Webhook should accept error field for failed analyses."""
        payload = {
            "feature_id": "test-123",
            "error": "Analysis timeout",
            "metadata": {
                "workflow_run_id": "12345",
            },
        }

        webhook = AnalysisResultWebhook(**payload)

        assert webhook.error == "Analysis timeout"
        assert webhook.feature_id == "test-123"

    def test_webhook_metadata_is_optional(self):
        """Metadata field should be optional."""
        payload = {
            "feature_id": "test-123",
            "complexity": {"story_points": 3},
        }

        webhook = AnalysisResultWebhook(**payload)

        assert webhook.feature_id == "test-123"
        assert webhook.metadata is None

    def test_webhook_preserves_full_result_structure(self):
        """Webhook should preserve the complete result structure."""
        payload = {
            "feature_id": "test-123",
            "warnings": [
                {
                    "type": "missing_infrastructure",
                    "severity": "high",
                    "message": "No backend code found",
                }
            ],
            "repository_state": {
                "has_backend_code": False,
                "maturity_level": "empty",
            },
            "complexity": {
                "story_points": 8,
                "estimated_hours": 24,
            },
            "affected_modules": [
                {"path": "src/api.py", "change_type": "new"}
            ],
            "implementation_tasks": [
                {
                    "id": "task-1",
                    "description": "Setup backend",
                    "task_type": "prerequisite",
                }
            ],
            "technical_risks": [
                {"category": "security", "severity": "medium"}
            ],
            "recommendations": {
                "approach": "Start with MVP",
                "alternatives": ["Use existing framework"],
            },
            "metadata": {
                "workflow_run_id": "12345",
                "analyzed_at": "2026-01-07T10:00:00Z",
            },
        }

        webhook = AnalysisResultWebhook(**payload)

        assert webhook.feature_id == "test-123"
        assert len(webhook.warnings) == 1
        assert webhook.repository_state["maturity_level"] == "empty"
        assert len(webhook.implementation_tasks) == 1
```

**Run tests** (should FAIL):
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_webhook_schemas.py -v
```

**Expected output**: Tests fail because schema doesn't exist

2. **Implement webhook schema** (TDD GREEN phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/schemas/webhook.py`

```python
"""Webhook schemas for receiving analysis results."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class AnalysisResultWebhook(BaseModel):
    """Schema for analysis result webhook payload from GitHub workflow.

    This matches the JSON structure sent by the analyze-feature.yml workflow.
    """

    feature_id: str = Field(..., description="Feature ID that was analyzed")

    # Analysis result fields (all optional as structure may vary)
    warnings: Optional[list[dict[str, Any]]] = Field(
        None, description="Warnings about missing infrastructure or risks"
    )
    repository_state: Optional[dict[str, Any]] = Field(
        None, description="State of the repository"
    )
    complexity: Optional[dict[str, Any]] = Field(
        None, description="Complexity estimation"
    )
    affected_modules: Optional[list[dict[str, Any]]] = Field(
        None, description="Modules affected by the feature"
    )
    implementation_tasks: Optional[list[dict[str, Any]]] = Field(
        None, description="List of implementation tasks"
    )
    technical_risks: Optional[list[dict[str, Any]]] = Field(
        None, description="Technical risks identified"
    )
    recommendations: Optional[dict[str, Any]] = Field(
        None, description="Implementation recommendations"
    )

    # Error handling
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    stack: Optional[str] = Field(None, description="Stack trace if analysis failed")
    raw_output: Optional[str] = Field(
        None, description="Raw output if structured parsing failed"
    )

    # Metadata
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Workflow metadata (run_id, timestamp, etc.)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "feature_id": "feat-12345",
                "complexity": {
                    "story_points": 5,
                    "estimated_hours": 16,
                    "level": "Medium",
                },
                "metadata": {
                    "workflow_run_id": "98765",
                    "analyzed_at": "2026-01-07T10:30:00Z",
                },
            }
        }
```

Update `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/schemas/__init__.py` to export webhook schema:

```python
"""Schemas for API request/response models."""

from app.schemas.feature import FeatureCreate, FeatureUpdate, FeatureResponse
from app.schemas.webhook import AnalysisResultWebhook

__all__ = [
    "FeatureCreate",
    "FeatureUpdate",
    "FeatureResponse",
    "AnalysisResultWebhook",
]
```

3. **Verify tests pass** (TDD GREEN phase)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_webhook_schemas.py -v
```

**Expected output**: All tests pass

4. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/schemas/webhook.py backend/app/schemas/__init__.py backend/tests/test_webhook_schemas.py
git commit -m "feat(backend): add webhook schema for analysis results

Create AnalysisResultWebhook schema to validate incoming webhook
payloads from GitHub workflow. Supports both successful results
and error cases."
```

---

### Task 4: Implement Webhook Security Utilities

**Duration**: 4 minutes

**Files to create**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/utils/webhook_security.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_webhook_security.py`

**Steps**:

1. **Write tests first** (TDD RED phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_webhook_security.py`

```python
"""Tests for webhook security utilities."""
import pytest
import secrets

from app.utils.webhook_security import (
    generate_webhook_secret,
    compute_webhook_signature,
    verify_webhook_signature,
)


class TestGenerateWebhookSecret:
    """Tests for generate_webhook_secret function."""

    def test_generates_random_secret(self):
        """Should generate a random webhook secret."""
        secret = generate_webhook_secret()

        assert isinstance(secret, str)
        assert len(secret) > 20  # Should be reasonably long

    def test_generates_different_secrets(self):
        """Should generate different secrets on each call."""
        secret1 = generate_webhook_secret()
        secret2 = generate_webhook_secret()

        assert secret1 != secret2

    def test_secret_is_url_safe(self):
        """Generated secret should be URL-safe."""
        secret = generate_webhook_secret()

        # Should not contain problematic characters
        assert " " not in secret
        assert "\n" not in secret
        assert "+" not in secret
        assert "/" not in secret


class TestComputeWebhookSignature:
    """Tests for compute_webhook_signature function."""

    def test_computes_signature_for_payload(self):
        """Should compute HMAC signature for payload."""
        payload = '{"feature_id": "test-123", "status": "completed"}'
        secret = "test-secret-key"

        signature = compute_webhook_signature(payload, secret)

        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length

    def test_same_payload_produces_same_signature(self):
        """Same payload and secret should produce same signature."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"

        sig1 = compute_webhook_signature(payload, secret)
        sig2 = compute_webhook_signature(payload, secret)

        assert sig1 == sig2

    def test_different_payload_produces_different_signature(self):
        """Different payload should produce different signature."""
        secret = "test-secret"

        sig1 = compute_webhook_signature('{"id": "1"}', secret)
        sig2 = compute_webhook_signature('{"id": "2"}', secret)

        assert sig1 != sig2

    def test_different_secret_produces_different_signature(self):
        """Different secret should produce different signature."""
        payload = '{"feature_id": "test-123"}'

        sig1 = compute_webhook_signature(payload, "secret1")
        sig2 = compute_webhook_signature(payload, "secret2")

        assert sig1 != sig2


class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature function."""

    def test_verifies_valid_signature(self):
        """Should return True for valid signature."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"
        signature = compute_webhook_signature(payload, secret)

        is_valid = verify_webhook_signature(payload, signature, secret)

        assert is_valid is True

    def test_rejects_invalid_signature(self):
        """Should return False for invalid signature."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"
        wrong_signature = "0" * 64  # Invalid signature

        is_valid = verify_webhook_signature(payload, wrong_signature, secret)

        assert is_valid is False

    def test_rejects_signature_with_wrong_secret(self):
        """Should return False when signature computed with different secret."""
        payload = '{"feature_id": "test-123"}'
        signature = compute_webhook_signature(payload, "secret1")

        is_valid = verify_webhook_signature(payload, signature, "secret2")

        assert is_valid is False

    def test_rejects_signature_for_modified_payload(self):
        """Should return False if payload was modified after signing."""
        original_payload = '{"feature_id": "test-123"}'
        secret = "test-secret"
        signature = compute_webhook_signature(original_payload, secret)

        modified_payload = '{"feature_id": "test-456"}'
        is_valid = verify_webhook_signature(modified_payload, signature, secret)

        assert is_valid is False

    def test_handles_empty_signature(self):
        """Should handle empty signature gracefully."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"

        is_valid = verify_webhook_signature(payload, "", secret)

        assert is_valid is False

    def test_timing_safe_comparison(self):
        """Should use timing-safe comparison to prevent timing attacks."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"
        signature = compute_webhook_signature(payload, secret)

        # This test verifies the function runs without errors
        # Actual timing-safe comparison is handled by hmac.compare_digest
        is_valid = verify_webhook_signature(payload, signature, secret)

        assert is_valid is True
```

**Run tests** (should FAIL):
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_webhook_security.py -v
```

**Expected output**: Tests fail because utilities don't exist

2. **Implement webhook security utilities** (TDD GREEN phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/utils/__init__.py`

```python
"""Utility modules."""
```

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/utils/webhook_security.py`

```python
"""Security utilities for webhook validation."""

import hmac
import hashlib
import secrets


def generate_webhook_secret(length: int = 32) -> str:
    """Generate a random webhook secret.

    Args:
        length: Length of the secret in bytes (default 32).

    Returns:
        A URL-safe random string to use as webhook secret.
    """
    return secrets.token_urlsafe(length)


def compute_webhook_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload.

    Args:
        payload: The webhook payload as a string (JSON).
        secret: The webhook secret key.

    Returns:
        Hexadecimal string of the HMAC signature.
    """
    payload_bytes = payload.encode("utf-8")
    secret_bytes = secret.encode("utf-8")

    signature = hmac.new(
        secret_bytes,
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    return signature


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature matches expected value.

    Uses timing-safe comparison to prevent timing attacks.

    Args:
        payload: The webhook payload as a string (JSON).
        signature: The signature to verify (hex string).
        secret: The webhook secret key.

    Returns:
        True if signature is valid, False otherwise.
    """
    if not signature:
        return False

    expected_signature = compute_webhook_signature(payload, secret)

    # Use timing-safe comparison
    return hmac.compare_digest(signature, expected_signature)
```

3. **Verify tests pass** (TDD GREEN phase)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_webhook_security.py -v
```

**Expected output**: All tests pass

4. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/utils/ backend/tests/test_webhook_security.py
git commit -m "feat(backend): add webhook security utilities

Implement:
- generate_webhook_secret: creates random URL-safe secrets
- compute_webhook_signature: HMAC-SHA256 signing
- verify_webhook_signature: timing-safe signature verification

These utilities secure webhook endpoints against tampering."
```

---

### Task 5: Create Webhook Endpoint

**Duration**: 5 minutes

**Files to create**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/api/webhooks.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_api_webhooks.py`

**Files to modify**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/main.py`

**Steps**:

1. **Write tests first** (TDD RED phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_api_webhooks.py`

```python
"""Tests for webhook API endpoints."""
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import Feature, FeatureStatus
from app.utils.webhook_security import compute_webhook_signature


@pytest.fixture
async def feature_with_webhook_secret(db: AsyncSession) -> Feature:
    """Create a test feature with webhook secret."""
    feature = Feature(
        id="test-feature-123",
        name="Test Feature",
        description="Test description",
        status=FeatureStatus.ANALYZING,
        analysis_workflow_run_id="12345",
        webhook_secret="test-webhook-secret-abc123",
    )
    db.add(feature)
    await db.commit()
    await db.refresh(feature)
    return feature


@pytest.mark.asyncio
class TestAnalysisResultWebhook:
    """Tests for POST /api/v1/webhooks/analysis-result endpoint."""

    async def test_webhook_accepts_valid_payload(
        self, db: AsyncSession, feature_with_webhook_secret: Feature
    ):
        """Webhook should accept and process valid payload with correct signature."""
        payload = {
            "feature_id": feature_with_webhook_secret.id,
            "complexity": {
                "story_points": 5,
                "estimated_hours": 16,
                "level": "Medium",
            },
            "metadata": {
                "workflow_run_id": "12345",
                "analyzed_at": "2026-01-07T10:00:00Z",
            },
        }

        payload_str = '{"feature_id":"test-feature-123","complexity":{"story_points":5,"estimated_hours":16,"level":"Medium"},"metadata":{"workflow_run_id":"12345","analyzed_at":"2026-01-07T10:00:00Z"}}'
        signature = compute_webhook_signature(
            payload_str, feature_with_webhook_secret.webhook_secret
        )

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Feature-ID": feature_with_webhook_secret.id,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["feature_id"] == feature_with_webhook_secret.id

    async def test_webhook_rejects_invalid_signature(
        self, db: AsyncSession, feature_with_webhook_secret: Feature
    ):
        """Webhook should reject payload with invalid signature."""
        payload = {
            "feature_id": feature_with_webhook_secret.id,
            "complexity": {"story_points": 5},
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={
                    "X-Webhook-Signature": "invalid-signature",
                    "X-Feature-ID": feature_with_webhook_secret.id,
                },
            )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_webhook_rejects_missing_signature(
        self, db: AsyncSession, feature_with_webhook_secret: Feature
    ):
        """Webhook should reject payload without signature header."""
        payload = {
            "feature_id": feature_with_webhook_secret.id,
            "complexity": {"story_points": 5},
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={"X-Feature-ID": feature_with_webhook_secret.id},
            )

        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()

    async def test_webhook_rejects_nonexistent_feature(self, db: AsyncSession):
        """Webhook should reject payload for non-existent feature."""
        payload = {
            "feature_id": "nonexistent-feature-999",
            "complexity": {"story_points": 5},
        }

        payload_str = '{"feature_id":"nonexistent-feature-999","complexity":{"story_points":5}}'
        signature = compute_webhook_signature(payload_str, "any-secret")

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Feature-ID": "nonexistent-feature-999",
                },
            )

        assert response.status_code == 404

    async def test_webhook_updates_feature_status_to_completed(
        self, db: AsyncSession, feature_with_webhook_secret: Feature
    ):
        """Webhook should update feature status to COMPLETED on success."""
        payload = {
            "feature_id": feature_with_webhook_secret.id,
            "complexity": {"story_points": 5},
            "metadata": {"workflow_run_id": "12345"},
        }

        payload_str = '{"feature_id":"test-feature-123","complexity":{"story_points":5},"metadata":{"workflow_run_id":"12345"}}'
        signature = compute_webhook_signature(
            payload_str, feature_with_webhook_secret.webhook_secret
        )

        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Feature-ID": feature_with_webhook_secret.id,
                },
            )

        await db.refresh(feature_with_webhook_secret)
        assert feature_with_webhook_secret.status == FeatureStatus.COMPLETED
        assert feature_with_webhook_secret.webhook_received_at is not None

    async def test_webhook_updates_feature_status_to_failed_on_error(
        self, db: AsyncSession, feature_with_webhook_secret: Feature
    ):
        """Webhook should update feature status to FAILED when error in payload."""
        payload = {
            "feature_id": feature_with_webhook_secret.id,
            "error": "Analysis timeout after 15 minutes",
            "metadata": {"workflow_run_id": "12345"},
        }

        payload_str = '{"feature_id":"test-feature-123","error":"Analysis timeout after 15 minutes","metadata":{"workflow_run_id":"12345"}}'
        signature = compute_webhook_signature(
            payload_str, feature_with_webhook_secret.webhook_secret
        )

        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Feature-ID": feature_with_webhook_secret.id,
                },
            )

        await db.refresh(feature_with_webhook_secret)
        assert feature_with_webhook_secret.status == FeatureStatus.FAILED

    async def test_webhook_creates_analysis_record(
        self, db: AsyncSession, feature_with_webhook_secret: Feature
    ):
        """Webhook should create Analysis record in database."""
        payload = {
            "feature_id": feature_with_webhook_secret.id,
            "complexity": {
                "story_points": 5,
                "estimated_hours": 16,
            },
            "metadata": {
                "workflow_run_id": "12345",
            },
        }

        payload_str = '{"feature_id":"test-feature-123","complexity":{"story_points":5,"estimated_hours":16},"metadata":{"workflow_run_id":"12345"}}'
        signature = compute_webhook_signature(
            payload_str, feature_with_webhook_secret.webhook_secret
        )

        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Feature-ID": feature_with_webhook_secret.id,
                },
            )

        await db.refresh(feature_with_webhook_secret)
        assert len(feature_with_webhook_secret.analyses) == 1

        analysis = feature_with_webhook_secret.analyses[0]
        assert analysis.feature_id == feature_with_webhook_secret.id
        assert analysis.result["complexity"]["story_points"] == 5
```

**Run tests** (should FAIL):
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_api_webhooks.py -v
```

**Expected output**: Tests fail because endpoint doesn't exist

2. **Implement webhook endpoint** (TDD GREEN phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/api/webhooks.py`

```python
"""Webhook API endpoints for receiving analysis results."""

import logging
from datetime import datetime, UTC
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Feature, FeatureStatus, Analysis
from app.schemas import AnalysisResultWebhook
from app.utils.webhook_security import verify_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/analysis-result")
async def receive_analysis_result(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
    x_feature_id: str | None = Header(None, alias="X-Feature-ID"),
) -> dict[str, Any]:
    """Receive analysis results from GitHub workflow via webhook.

    This endpoint is called by the GitHub workflow after analysis completes.
    It validates the webhook signature, stores the results, and updates the feature status.

    Args:
        request: FastAPI request object (to get raw body)
        db: Database session
        x_webhook_signature: HMAC signature from X-Webhook-Signature header
        x_feature_id: Feature ID from X-Feature-ID header

    Returns:
        Success response with feature_id

    Raises:
        HTTPException 400: If signature header is missing
        HTTPException 401: If signature is invalid
        HTTPException 404: If feature not found
        HTTPException 500: If database operation fails
    """
    logger.info(f"Received webhook for feature_id={x_feature_id}")

    # Validate required headers
    if not x_webhook_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Webhook-Signature header",
        )

    if not x_feature_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Feature-ID header",
        )

    # Get raw request body for signature verification
    raw_body = await request.body()
    payload_str = raw_body.decode("utf-8")

    # Parse and validate webhook payload
    try:
        webhook_data = AnalysisResultWebhook.model_validate_json(payload_str)
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {str(e)}",
        )

    # Verify feature_id matches header
    if webhook_data.feature_id != x_feature_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feature ID mismatch between header and payload",
        )

    # Find the feature
    result = await db.execute(select(Feature).where(Feature.id == x_feature_id))
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {x_feature_id} not found",
        )

    # Verify webhook signature
    if not feature.webhook_secret:
        logger.warning(f"Feature {x_feature_id} has no webhook_secret")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Feature has no webhook secret configured",
        )

    is_valid = verify_webhook_signature(
        payload_str, x_webhook_signature, feature.webhook_secret
    )

    if not is_valid:
        logger.warning(f"Invalid webhook signature for feature {x_feature_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Process the webhook data
    try:
        # Determine if analysis succeeded or failed
        has_error = webhook_data.error is not None

        # Update feature status
        feature.status = FeatureStatus.FAILED if has_error else FeatureStatus.COMPLETED
        feature.webhook_received_at = datetime.now(UTC)

        # Create Analysis record
        analysis = Analysis(
            feature_id=feature.id,
            result=webhook_data.model_dump(exclude_none=True),
            tokens_used=0,  # TODO: Extract from metadata if available
            model_used=webhook_data.metadata.get("model", "claude-3-5-sonnet-20241022")
            if webhook_data.metadata
            else "claude-3-5-sonnet-20241022",
            completed_at=datetime.now(UTC),
        )

        db.add(analysis)
        await db.commit()
        await db.refresh(feature)

        logger.info(
            f"Successfully processed webhook for feature {x_feature_id}, "
            f"status={feature.status}"
        )

        return {
            "status": "success",
            "feature_id": feature.id,
            "analysis_status": feature.status.value,
        }

    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )
```

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.features import router as features_router
from app.api.webhooks import router as webhooks_router

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

# Include routers
app.include_router(features_router)
app.include_router(webhooks_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}
```

3. **Verify tests pass** (TDD GREEN phase)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_api_webhooks.py -v
```

**Expected output**: All tests pass

4. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/api/webhooks.py backend/app/main.py backend/tests/test_api_webhooks.py
git commit -m "feat(backend): add webhook endpoint for analysis results

Implement POST /api/v1/webhooks/analysis-result endpoint:
- Validates webhook signature using HMAC-SHA256
- Parses and validates result payload
- Updates feature status (COMPLETED/FAILED)
- Creates Analysis record in database
- Includes comprehensive security checks"
```

---

### Task 6: Update Feature Creation to Generate Webhook Secrets

**Duration**: 3 minutes

**Files to modify**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/api/features.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_api_features.py`

**Steps**:

1. **Write tests first** (TDD RED phase)

Add to `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_api_features.py`:

```python
"""Add these test methods to test_api_features.py"""


class TestFeatureCreationWithWebhook:
    """Tests for feature creation with webhook secret generation."""

    @pytest.mark.asyncio
    async def test_create_feature_generates_webhook_secret(self, db: AsyncSession):
        """Creating a feature should automatically generate webhook secret."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/features/",
                json={
                    "name": "Test Feature",
                    "description": "Test description",
                    "priority": 1,
                },
            )

        assert response.status_code == 201
        data = response.json()

        # Webhook secret should not be exposed in API response
        assert "webhook_secret" not in data

        # But it should exist in database
        from sqlalchemy import select
        from app.models import Feature

        result = await db.execute(select(Feature).where(Feature.id == data["id"]))
        feature = result.scalar_one()

        assert feature.webhook_secret is not None
        assert len(feature.webhook_secret) > 20  # Should be reasonably long

    @pytest.mark.asyncio
    async def test_each_feature_gets_unique_webhook_secret(self, db: AsyncSession):
        """Each feature should get a unique webhook secret."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response1 = await client.post(
                "/api/v1/features/",
                json={
                    "name": "Feature 1",
                    "description": "Test 1",
                    "priority": 1,
                },
            )
            response2 = await client.post(
                "/api/v1/features/",
                json={
                    "name": "Feature 2",
                    "description": "Test 2",
                    "priority": 1,
                },
            )

        from sqlalchemy import select
        from app.models import Feature

        result1 = await db.execute(
            select(Feature).where(Feature.id == response1.json()["id"])
        )
        result2 = await db.execute(
            select(Feature).where(Feature.id == response2.json()["id"])
        )

        feature1 = result1.scalar_one()
        feature2 = result2.scalar_one()

        assert feature1.webhook_secret != feature2.webhook_secret
```

**Run tests** (should FAIL):
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_api_features.py::TestFeatureCreationWithWebhook -v
```

**Expected output**: Tests fail because webhook secret is not generated

2. **Implement webhook secret generation** (TDD GREEN phase)

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/api/features.py`:

```python
"""Feature API endpoints.

Provides CRUD operations for features and analysis workflow triggering.
"""

from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Feature, FeatureStatus
from app.schemas import FeatureCreate, FeatureUpdate, FeatureResponse
from app.services.github_service import GitHubService
from app.utils.webhook_security import generate_webhook_secret

router = APIRouter(prefix="/api/v1/features", tags=["features"])


def get_github_service() -> GitHubService:
    """Dependency for GitHub service."""
    return GitHubService(
        token=settings.github_token,
        repo=settings.github_repo,
    )


@router.post("", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    feature_in: FeatureCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new feature request.

    Args:
        feature_in: Feature creation data
        db: Database session

    Returns:
        The created feature
    """
    feature = Feature(
        id=str(uuid4()),
        name=feature_in.name,
        description=feature_in.description or "",
        priority=feature_in.priority,
        status=FeatureStatus.PENDING,
        webhook_secret=generate_webhook_secret(),  # Generate unique webhook secret
    )

    db.add(feature)
    await db.commit()
    await db.refresh(feature)

    return feature


# ... rest of the file remains unchanged ...
```

3. **Verify tests pass** (TDD GREEN phase)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_api_features.py::TestFeatureCreationWithWebhook -v
```

**Expected output**: All tests pass

4. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/api/features.py backend/tests/test_api_features.py
git commit -m "feat(backend): auto-generate webhook secret on feature creation

Each feature now gets a unique webhook secret for validating
incoming webhook callbacks. Secret is not exposed in API responses."
```

---

### Task 7: Update Trigger Analysis to Include Callback URL

**Duration**: 4 minutes

**Files to modify**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/api/features.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_api_features.py`

**Steps**:

1. **Write tests first** (TDD RED phase)

Add to `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_api_features.py`:

```python
"""Add these test methods to test_api_features.py"""


class TestTriggerAnalysisWithCallback:
    """Tests for trigger_analysis with callback URL."""

    @pytest.mark.asyncio
    async def test_trigger_analysis_includes_callback_url_when_webhook_base_url_set(
        self, db: AsyncSession, monkeypatch
    ):
        """Trigger analysis should include callback URL when webhook_base_url is configured."""
        # Create feature
        from app.models import Feature, FeatureStatus

        feature = Feature(
            id="test-feature-callback",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            webhook_secret="test-secret",
        )
        db.add(feature)
        await db.commit()

        # Mock settings to have webhook_base_url
        from app.config import settings

        monkeypatch.setattr(settings, "webhook_base_url", "https://api.example.com")

        # Mock GitHubService
        from unittest.mock import AsyncMock, patch

        mock_github_service = AsyncMock()
        mock_github_service.trigger_analysis_workflow.return_value = 12345

        with patch(
            "app.api.features.get_github_service", return_value=mock_github_service
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/features/{feature.id}/analyze"
                )

        assert response.status_code == 202

        # Verify callback URL was passed to GitHub service
        mock_github_service.trigger_analysis_workflow.assert_called_once()
        call_args = mock_github_service.trigger_analysis_workflow.call_args

        callback_url = call_args.kwargs.get("callback_url")
        assert callback_url is not None
        assert "https://api.example.com" in callback_url
        assert "/api/v1/webhooks/analysis-result" in callback_url

    @pytest.mark.asyncio
    async def test_trigger_analysis_skips_callback_url_when_webhook_base_url_not_set(
        self, db: AsyncSession, monkeypatch
    ):
        """Trigger analysis should not include callback URL when webhook_base_url is None."""
        # Create feature
        from app.models import Feature, FeatureStatus

        feature = Feature(
            id="test-feature-no-callback",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            webhook_secret="test-secret",
        )
        db.add(feature)
        await db.commit()

        # Mock settings to have no webhook_base_url
        from app.config import settings

        monkeypatch.setattr(settings, "webhook_base_url", None)

        # Mock GitHubService
        from unittest.mock import AsyncMock, patch

        mock_github_service = AsyncMock()
        mock_github_service.trigger_analysis_workflow.return_value = 12345

        with patch(
            "app.api.features.get_github_service", return_value=mock_github_service
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/features/{feature.id}/analyze"
                )

        assert response.status_code == 202

        # Verify callback URL was None
        mock_github_service.trigger_analysis_workflow.assert_called_once()
        call_args = mock_github_service.trigger_analysis_workflow.call_args

        callback_url = call_args.kwargs.get("callback_url")
        assert callback_url is None
```

**Run tests** (should FAIL):
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_api_features.py::TestTriggerAnalysisWithCallback -v
```

**Expected output**: Tests fail because callback URL is not generated

2. **Implement callback URL generation** (TDD GREEN phase)

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/api/features.py`:

Update the `trigger_analysis` function:

```python
@router.post("/{feature_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def trigger_analysis(
    feature_id: UUID,
    db: AsyncSession = Depends(get_db),
    github_service: GitHubService = Depends(get_github_service),
):
    """Trigger GitHub Actions workflow to analyze a feature.

    Args:
        feature_id: UUID of the feature to analyze
        db: Database session
        github_service: GitHub service for API calls

    Returns:
        Dict with workflow run_id and feature_id

    Raises:
        HTTPException: If feature not found or GitHub API fails
    """
    result = await db.execute(select(Feature).where(Feature.id == str(feature_id)))
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found",
        )

    try:
        # Construct callback URL if webhook_base_url is configured
        callback_url = None
        if settings.webhook_base_url:
            callback_url = f"{settings.webhook_base_url}/api/v1/webhooks/analysis-result"

        # Trigger the analysis workflow with callback URL
        run_id = await github_service.trigger_analysis_workflow(
            feature_id=feature_id,
            feature_description=feature.description,
            callback_url=callback_url,
        )

        # Update feature status and store workflow run ID
        feature.status = FeatureStatus.ANALYZING
        feature.analysis_workflow_run_id = str(run_id)

        await db.commit()
        await db.refresh(feature)

        return {
            "run_id": run_id,
            "feature_id": str(feature_id),
            "status": "analyzing",
            "callback_url": callback_url,  # Include in response for debugging
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger analysis workflow: {str(e)}",
        )
```

3. **Verify tests pass** (TDD GREEN phase)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_api_features.py::TestTriggerAnalysisWithCallback -v
```

**Expected output**: All tests pass

4. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/api/features.py backend/tests/test_api_features.py
git commit -m "feat(backend): include callback URL when triggering analysis

When webhook_base_url is configured, pass callback URL to GitHub
workflow. Workflow will POST results to this URL when complete.
Falls back to polling if webhook_base_url is not set."
```

---

### Task 8: Implement Polling Service

**Duration**: 5 minutes

**Files to create**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/services/polling_service.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_polling_service.py`

**Steps**:

1. **Write tests first** (TDD RED phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_polling_service.py`

```python
"""Tests for analysis polling service."""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feature, FeatureStatus
from app.services.polling_service import AnalysisPollingService


@pytest.fixture
def polling_service(db: AsyncSession):
    """Create polling service instance."""
    return AnalysisPollingService(db)


@pytest.fixture
async def analyzing_feature(db: AsyncSession) -> Feature:
    """Create a feature in ANALYZING status."""
    feature = Feature(
        id="test-analyzing-feature",
        name="Test Feature",
        description="Test description",
        status=FeatureStatus.ANALYZING,
        analysis_workflow_run_id="12345",
        webhook_secret="test-secret",
    )
    db.add(feature)
    await db.commit()
    await db.refresh(feature)
    return feature


@pytest.mark.asyncio
class TestAnalysisPollingService:
    """Tests for AnalysisPollingService."""

    async def test_get_features_needing_polling_returns_analyzing_features(
        self, polling_service, analyzing_feature
    ):
        """Should return features in ANALYZING status."""
        features = await polling_service.get_features_needing_polling()

        assert len(features) == 1
        assert features[0].id == analyzing_feature.id
        assert features[0].status == FeatureStatus.ANALYZING

    async def test_get_features_needing_polling_excludes_completed_features(
        self, polling_service, db: AsyncSession
    ):
        """Should not return features that are already COMPLETED."""
        feature = Feature(
            id="completed-feature",
            name="Completed Feature",
            description="Done",
            status=FeatureStatus.COMPLETED,
            analysis_workflow_run_id="99999",
        )
        db.add(feature)
        await db.commit()

        features = await polling_service.get_features_needing_polling()

        assert len(features) == 0

    async def test_get_features_needing_polling_excludes_recently_received_webhooks(
        self, polling_service, db: AsyncSession
    ):
        """Should not poll features that recently received webhooks."""
        # Feature received webhook 1 minute ago
        feature = Feature(
            id="webhook-received-feature",
            name="Webhook Received",
            description="Test",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="11111",
            webhook_received_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        db.add(feature)
        await db.commit()

        features = await polling_service.get_features_needing_polling()

        # Should be excluded because webhook was received recently
        feature_ids = [f.id for f in features]
        assert "webhook-received-feature" not in feature_ids

    async def test_get_features_needing_polling_excludes_timed_out_features(
        self, polling_service, db: AsyncSession
    ):
        """Should not poll features that have exceeded timeout."""
        # Feature created 20 minutes ago (beyond 15 minute timeout)
        old_timestamp = datetime.now(UTC) - timedelta(minutes=20)
        feature = Feature(
            id="timed-out-feature",
            name="Timed Out Feature",
            description="Test",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="22222",
            created_at=old_timestamp,
        )
        db.add(feature)
        await db.commit()

        features = await polling_service.get_features_needing_polling()

        # Should be excluded because it exceeded timeout
        feature_ids = [f.id for f in features]
        assert "timed-out-feature" not in feature_ids

    async def test_poll_workflow_status_updates_feature_when_completed(
        self, polling_service, analyzing_feature
    ):
        """Should download artifact and update feature when workflow completes."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "completed"
        mock_github_service.download_workflow_artifact.return_value = {
            "feature_id": analyzing_feature.id,
            "complexity": {"story_points": 5, "estimated_hours": 16},
            "metadata": {"workflow_run_id": "12345"},
        }

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_workflow_status(analyzing_feature)

        # Feature should be updated to COMPLETED
        assert analyzing_feature.status == FeatureStatus.COMPLETED
        assert analyzing_feature.last_polled_at is not None

        # Analysis should be created
        assert len(analyzing_feature.analyses) == 1

    async def test_poll_workflow_status_updates_feature_when_failed(
        self, polling_service, analyzing_feature
    ):
        """Should update feature to FAILED when workflow fails."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "failure"

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_workflow_status(analyzing_feature)

        # Feature should be updated to FAILED
        assert analyzing_feature.status == FeatureStatus.FAILED

    async def test_poll_workflow_status_updates_last_polled_timestamp(
        self, polling_service, analyzing_feature
    ):
        """Should update last_polled_at timestamp even if still in progress."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "in_progress"

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_workflow_status(analyzing_feature)

        # Should update timestamp even though still in progress
        assert analyzing_feature.last_polled_at is not None
        assert analyzing_feature.status == FeatureStatus.ANALYZING

    async def test_poll_all_analyzing_features_polls_multiple_features(
        self, polling_service, db: AsyncSession
    ):
        """Should poll all features in ANALYZING status."""
        features = [
            Feature(
                id=f"feature-{i}",
                name=f"Feature {i}",
                description="Test",
                status=FeatureStatus.ANALYZING,
                analysis_workflow_run_id=f"{1000 + i}",
            )
            for i in range(3)
        ]

        for feature in features:
            db.add(feature)
        await db.commit()

        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "in_progress"

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            polled_count = await polling_service.poll_all_analyzing_features()

        assert polled_count == 3

    async def test_poll_all_handles_errors_gracefully(
        self, polling_service, analyzing_feature
    ):
        """Should continue polling other features if one fails."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.side_effect = Exception(
            "GitHub API error"
        )

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            # Should not raise exception
            polled_count = await polling_service.poll_all_analyzing_features()

        # Should still count as attempted
        assert polled_count >= 0
```

**Run tests** (should FAIL):
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_polling_service.py -v
```

**Expected output**: Tests fail because service doesn't exist

2. **Implement polling service** (TDD GREEN phase)

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/services/polling_service.py`

```python
"""Polling service for checking GitHub workflow status and downloading results.

This service acts as a fallback mechanism when webhooks are not available
or fail to deliver. It periodically checks workflows in ANALYZING status
and downloads results when complete.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Feature, FeatureStatus, Analysis
from app.services.github_service import GitHubService, GitHubServiceError

logger = logging.getLogger(__name__)


class AnalysisPollingService:
    """Service for polling GitHub workflow status and downloading results."""

    def __init__(self, db: AsyncSession):
        """Initialize polling service.

        Args:
            db: Database session
        """
        self.db = db
        self.timeout_seconds = settings.analysis_polling_timeout_seconds

    async def get_features_needing_polling(self) -> List[Feature]:
        """Get features that need status polling.

        Returns features that are:
        - In ANALYZING status
        - Have not received webhook recently (last 5 minutes)
        - Have not exceeded timeout threshold
        - Have workflow_run_id set

        Returns:
            List of features needing polling
        """
        cutoff_time = datetime.now(UTC) - timedelta(seconds=self.timeout_seconds)
        webhook_grace_period = datetime.now(UTC) - timedelta(minutes=5)

        query = (
            select(Feature)
            .where(Feature.status == FeatureStatus.ANALYZING)
            .where(Feature.analysis_workflow_run_id.isnot(None))
            .where(Feature.created_at > cutoff_time)  # Not timed out
            .where(
                # Either never received webhook or received long ago
                (Feature.webhook_received_at.is_(None))
                | (Feature.webhook_received_at < webhook_grace_period)
            )
        )

        result = await self.db.execute(query)
        features = result.scalars().all()

        return list(features)

    async def poll_workflow_status(self, feature: Feature) -> None:
        """Poll status for a single feature's workflow.

        Args:
            feature: Feature to poll
        """
        if not feature.analysis_workflow_run_id:
            logger.warning(f"Feature {feature.id} has no workflow_run_id")
            return

        try:
            github_service = GitHubService(
                token=settings.github_token,
                repo=settings.github_repo,
            )

            # Update last polled timestamp
            feature.last_polled_at = datetime.now(UTC)

            # Check workflow status
            run_id = int(feature.analysis_workflow_run_id)
            status = await github_service.get_workflow_run_status(run_id)

            logger.info(
                f"Workflow {run_id} for feature {feature.id} status: {status}"
            )

            if status == "completed":
                # Download and process results
                await self._process_completed_workflow(feature, run_id, github_service)

            elif status in ["failure", "cancelled", "timed_out"]:
                # Mark feature as failed
                feature.status = FeatureStatus.FAILED

                # Create error analysis record
                analysis = Analysis(
                    feature_id=feature.id,
                    result={
                        "error": f"Workflow {status}",
                        "workflow_run_id": run_id,
                    },
                    tokens_used=0,
                    model_used="unknown",
                    completed_at=datetime.now(UTC),
                )
                self.db.add(analysis)

            # If status is "queued" or "in_progress", do nothing (keep polling)

            await self.db.commit()
            await github_service.close()

        except GitHubServiceError as e:
            logger.error(f"GitHub API error polling feature {feature.id}: {e}")
            # Don't update feature status on transient errors

        except Exception as e:
            logger.error(f"Unexpected error polling feature {feature.id}: {e}")

    async def _process_completed_workflow(
        self, feature: Feature, run_id: int, github_service: GitHubService
    ) -> None:
        """Process completed workflow by downloading artifact and storing results.

        Args:
            feature: Feature being analyzed
            run_id: Workflow run ID
            github_service: GitHub service instance
        """
        try:
            # Download artifact with feature-specific name
            artifact_name = f"feature-analysis-{feature.id}"
            result_data = await github_service.download_workflow_artifact(
                run_id, artifact_name=artifact_name
            )

            # Check if analysis had errors
            has_error = "error" in result_data

            # Update feature status
            feature.status = FeatureStatus.FAILED if has_error else FeatureStatus.COMPLETED

            # Create analysis record
            analysis = Analysis(
                feature_id=feature.id,
                result=result_data,
                tokens_used=0,  # TODO: Extract from metadata if available
                model_used=result_data.get("metadata", {}).get(
                    "model", "claude-3-5-sonnet-20241022"
                ),
                completed_at=datetime.now(UTC),
            )

            self.db.add(analysis)

            logger.info(
                f"Successfully processed completed workflow for feature {feature.id}"
            )

        except GitHubServiceError as e:
            logger.error(
                f"Failed to download artifact for feature {feature.id}: {e}"
            )
            feature.status = FeatureStatus.FAILED

            # Create error analysis record
            analysis = Analysis(
                feature_id=feature.id,
                result={
                    "error": f"Failed to download results: {str(e)}",
                    "workflow_run_id": run_id,
                },
                tokens_used=0,
                model_used="unknown",
                completed_at=datetime.now(UTC),
            )
            self.db.add(analysis)

    async def poll_all_analyzing_features(self) -> int:
        """Poll status for all features needing polling.

        Returns:
            Number of features polled
        """
        features = await self.get_features_needing_polling()

        logger.info(f"Polling {len(features)} features")

        for feature in features:
            try:
                await self.poll_workflow_status(feature)
            except Exception as e:
                logger.error(f"Error polling feature {feature.id}: {e}")
                # Continue with other features

        return len(features)
```

3. **Verify tests pass** (TDD GREEN phase)

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_polling_service.py -v
```

**Expected output**: All tests pass

4. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/services/polling_service.py backend/tests/test_polling_service.py
git commit -m "feat(backend): implement analysis polling service

Add AnalysisPollingService as fallback mechanism:
- Polls features in ANALYZING status
- Checks workflow status via GitHub API
- Downloads artifacts when workflow completes
- Updates feature status and creates Analysis records
- Handles errors gracefully with logging"
```

---

### Task 9: Add Background Task for Polling

**Duration**: 4 minutes

**Files to modify**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/main.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/requirements.txt`

**Files to create**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/tasks/__init__.py`
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/tasks/polling_task.py`

**Steps**:

1. **Add APScheduler dependency**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/requirements.txt`:

```text
# Add to existing requirements
apscheduler==3.10.4
```

**Install dependency**:
```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pip install apscheduler==3.10.4
```

2. **Create polling background task**

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/tasks/__init__.py`

```python
"""Background tasks."""
```

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/tasks/polling_task.py`

```python
"""Background task for polling analysis workflows."""

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import async_session_maker
from app.services.polling_service import AnalysisPollingService

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def poll_analyzing_features() -> None:
    """Background task to poll features in ANALYZING status.

    This runs periodically to check workflow status and download results
    for features that haven't received webhook callbacks.
    """
    logger.info("Starting polling task for analyzing features")

    try:
        async with async_session_maker() as db:
            polling_service = AnalysisPollingService(db)
            polled_count = await polling_service.poll_all_analyzing_features()

            logger.info(f"Polling task completed, polled {polled_count} features")

    except Exception as e:
        logger.error(f"Polling task failed: {e}", exc_info=True)


def start_polling_scheduler() -> AsyncIOScheduler:
    """Start the background polling scheduler.

    Returns:
        The scheduler instance
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return scheduler

    scheduler = AsyncIOScheduler()

    # Add job to poll every N seconds
    scheduler.add_job(
        poll_analyzing_features,
        trigger="interval",
        seconds=settings.analysis_polling_interval_seconds,
        id="poll_analyzing_features",
        name="Poll analyzing features for workflow results",
        replace_existing=True,
    )

    scheduler.start()

    logger.info(
        f"Started polling scheduler (interval: {settings.analysis_polling_interval_seconds}s)"
    )

    return scheduler


def stop_polling_scheduler() -> None:
    """Stop the background polling scheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Stopped polling scheduler")


@asynccontextmanager
async def polling_lifespan():
    """Context manager for polling scheduler lifecycle."""
    start_polling_scheduler()
    yield
    stop_polling_scheduler()
```

3. **Integrate polling task with FastAPI app lifecycle**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/app/main.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.features import router as features_router
from app.api.webhooks import router as webhooks_router
from app.tasks.polling_task import start_polling_scheduler, stop_polling_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events for background tasks.
    """
    # Startup: Start polling scheduler
    start_polling_scheduler()

    yield

    # Shutdown: Stop polling scheduler
    stop_polling_scheduler()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(features_router)
app.include_router(webhooks_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}
```

4. **Test the application starts correctly**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
# Start the server briefly to verify it starts without errors
timeout 5 uvicorn app.main:app --reload || true
```

**Expected output**: Server starts without errors, polling scheduler logs initialization

5. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/app/main.py backend/app/tasks/ backend/requirements.txt
git commit -m "feat(backend): add background polling task with APScheduler

Implement periodic polling task that:
- Runs every 30 seconds (configurable)
- Polls all features in ANALYZING status
- Automatically starts/stops with app lifecycle
- Uses APScheduler for reliable scheduling"
```

---

### Task 10: Add Integration Test for Dual Mechanism

**Duration**: 5 minutes

**Files to create**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_integration_dual_mechanism.py`

**Steps**:

1. **Write integration test**

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/backend/tests/test_integration_dual_mechanism.py`

```python
"""Integration tests for dual mechanism (webhook + polling)."""
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import Feature, FeatureStatus
from app.services.polling_service import AnalysisPollingService
from app.utils.webhook_security import compute_webhook_signature


@pytest.mark.asyncio
class TestDualMechanismIntegration:
    """Integration tests for webhook and polling working together."""

    async def test_webhook_path_receives_results_immediately(self, db: AsyncSession):
        """Primary path: webhook receives results immediately."""
        # 1. Create feature
        feature = Feature(
            id="webhook-test-feature",
            name="Webhook Test",
            description="Test webhook delivery",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="98765",
            webhook_secret="webhook-test-secret",
        )
        db.add(feature)
        await db.commit()

        # 2. Simulate webhook delivery from GitHub workflow
        payload = {
            "feature_id": feature.id,
            "complexity": {
                "story_points": 5,
                "estimated_hours": 16,
                "level": "Medium",
            },
            "metadata": {
                "workflow_run_id": "98765",
                "analyzed_at": datetime.now(UTC).isoformat(),
            },
        }

        payload_str = (
            '{"feature_id":"webhook-test-feature","complexity":{"story_points":5,'
            '"estimated_hours":16,"level":"Medium"},"metadata":{"workflow_run_id":'
            '"98765","analyzed_at":"2026-01-07T10:00:00+00:00"}}'
        )
        signature = compute_webhook_signature(payload_str, feature.webhook_secret)

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Feature-ID": feature.id,
                },
            )

        # 3. Verify webhook processed successfully
        assert response.status_code == 200

        # 4. Verify feature updated
        await db.refresh(feature)
        assert feature.status == FeatureStatus.COMPLETED
        assert feature.webhook_received_at is not None

        # 5. Verify polling won't touch this feature anymore
        polling_service = AnalysisPollingService(db)
        features_needing_poll = await polling_service.get_features_needing_polling()

        feature_ids = [f.id for f in features_needing_poll]
        assert feature.id not in feature_ids  # Already received webhook

    async def test_polling_path_when_webhook_fails(self, db: AsyncSession):
        """Fallback path: polling picks up when webhook doesn't arrive."""
        # 1. Create feature (simulating webhook URL not reachable)
        feature = Feature(
            id="polling-test-feature",
            name="Polling Test",
            description="Test polling fallback",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="55555",
            webhook_secret="polling-test-secret",
            # webhook_received_at is None - webhook never arrived
        )
        db.add(feature)
        await db.commit()

        # 2. Mock GitHub API to return completed workflow
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "completed"
        mock_github_service.download_workflow_artifact.return_value = {
            "feature_id": feature.id,
            "complexity": {
                "story_points": 8,
                "estimated_hours": 24,
                "level": "High",
            },
            "metadata": {
                "workflow_run_id": "55555",
            },
        }

        # 3. Run polling service
        polling_service = AnalysisPollingService(db)

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_workflow_status(feature)

        # 4. Verify feature updated via polling
        await db.refresh(feature)
        assert feature.status == FeatureStatus.COMPLETED
        assert feature.last_polled_at is not None
        assert len(feature.analyses) == 1

        # 5. Verify result stored correctly
        analysis = feature.analyses[0]
        assert analysis.result["complexity"]["story_points"] == 8

    async def test_polling_respects_webhook_received_features(self, db: AsyncSession):
        """Polling should skip features that already received webhooks."""
        # 1. Create feature that received webhook
        feature = Feature(
            id="skip-polling-feature",
            name="Skip Polling",
            description="Already received webhook",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="77777",
            webhook_secret="skip-test-secret",
            webhook_received_at=datetime.now(UTC),  # Just received webhook
        )
        db.add(feature)
        await db.commit()

        # 2. Check polling service doesn't include it
        polling_service = AnalysisPollingService(db)
        features = await polling_service.get_features_needing_polling()

        feature_ids = [f.id for f in features]
        assert feature.id not in feature_ids

    async def test_end_to_end_with_webhook_first_polling_never_needed(
        self, db: AsyncSession
    ):
        """End-to-end test: webhook arrives, polling never kicks in."""
        # 1. Trigger analysis (simulate)
        feature = Feature(
            id="e2e-webhook-feature",
            name="E2E Webhook Test",
            description="End to end webhook test",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="11111",
            webhook_secret="e2e-webhook-secret",
        )
        db.add(feature)
        await db.commit()

        # 2. Webhook arrives within seconds
        payload = {
            "feature_id": feature.id,
            "complexity": {"story_points": 3},
            "metadata": {"workflow_run_id": "11111"},
        }

        payload_str = (
            '{"feature_id":"e2e-webhook-feature","complexity":{"story_points":3},'
            '"metadata":{"workflow_run_id":"11111"}}'
        )
        signature = compute_webhook_signature(payload_str, feature.webhook_secret)

        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post(
                "/api/v1/webhooks/analysis-result",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Feature-ID": feature.id,
                },
            )

        # 3. Verify completed via webhook
        await db.refresh(feature)
        assert feature.status == FeatureStatus.COMPLETED

        # 4. Run polling task - should skip this feature
        polling_service = AnalysisPollingService(db)
        polled_count = await polling_service.poll_all_analyzing_features()

        # Feature should not be polled because webhook was received
        features_polled = await polling_service.get_features_needing_polling()
        feature_ids = [f.id for f in features_polled]
        assert feature.id not in feature_ids

    async def test_end_to_end_with_polling_as_fallback(self, db: AsyncSession):
        """End-to-end test: webhook fails, polling saves the day."""
        # 1. Trigger analysis (webhook URL unreachable - localhost scenario)
        feature = Feature(
            id="e2e-polling-feature",
            name="E2E Polling Test",
            description="End to end polling test",
            status=FeatureStatus.ANALYZING,
            analysis_workflow_run_id="22222",
            webhook_secret="e2e-polling-secret",
            # No webhook_received_at - webhook failed to deliver
        )
        db.add(feature)
        await db.commit()

        # 2. Simulate workflow completes but webhook can't reach server
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "completed"
        mock_github_service.download_workflow_artifact.return_value = {
            "feature_id": feature.id,
            "complexity": {"story_points": 13},
            "metadata": {"workflow_run_id": "22222"},
        }

        # 3. Polling task runs after 30 seconds
        polling_service = AnalysisPollingService(db)

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_all_analyzing_features()

        # 4. Verify feature completed via polling fallback
        await db.refresh(feature)
        assert feature.status == FeatureStatus.COMPLETED
        assert feature.last_polled_at is not None
        assert len(feature.analyses) == 1

        # 5. Verify polling downloaded the correct results
        analysis = feature.analyses[0]
        assert analysis.result["complexity"]["story_points"] == 13
```

2. **Run integration tests**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest tests/test_integration_dual_mechanism.py -v
```

**Expected output**: All integration tests pass

3. **Run full test suite to ensure nothing broke**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis/backend
pytest -v
```

**Expected output**: All tests pass

4. **Commit changes**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add backend/tests/test_integration_dual_mechanism.py
git commit -m "test(backend): add integration tests for dual mechanism

Add comprehensive end-to-end tests covering:
- Webhook primary path (immediate delivery)
- Polling fallback path (when webhook fails)
- Coordination between webhook and polling
- Complete user journey scenarios"
```

---

### Task 11: Update Documentation and Environment Setup

**Duration**: 3 minutes

**Files to create**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/docs/dual-mechanism-setup.md`

**Files to modify**:
- `/Users/boudydegeer/Code/@smith.ai/product-analysis/README.md`

**Steps**:

1. **Create setup documentation**

Create: `/Users/boudydegeer/Code/@smith.ai/product-analysis/docs/dual-mechanism-setup.md`

```markdown
# Dual Mechanism Setup Guide

This guide explains how to configure the dual mechanism (webhook + polling) for receiving GitHub workflow analysis results.

## Overview

The system uses two mechanisms to receive analysis results:

1. **Webhook (Primary)**: GitHub workflow POSTs results to your server immediately
2. **Polling (Fallback)**: Background task checks workflow status every 30 seconds

## Configuration

### Required Settings

Add these to your `.env` file:

```bash
# Webhooks - For production or ngrok
WEBHOOK_BASE_URL=https://api.yourapp.com  # Your public API URL
WEBHOOK_SECRET=your-random-webhook-secret-here

# Analysis Polling - Fallback mechanism
ANALYSIS_POLLING_INTERVAL_SECONDS=30  # Check every 30 seconds
ANALYSIS_POLLING_TIMEOUT_SECONDS=900  # Give up after 15 minutes
```

### Localhost Development (No Public URL)

For localhost development without webhooks:

```bash
# Leave WEBHOOK_BASE_URL empty
WEBHOOK_BASE_URL=

# Polling will be used as the only mechanism
ANALYSIS_POLLING_INTERVAL_SECONDS=30
ANALYSIS_POLLING_TIMEOUT_SECONDS=900
```

Results will be retrieved via polling (every 30 seconds).

### Localhost Development (With ngrok)

To test webhooks locally using ngrok:

1. Start ngrok:
```bash
ngrok http 8000
```

2. Set WEBHOOK_BASE_URL to your ngrok URL:
```bash
WEBHOOK_BASE_URL=https://abc123.ngrok.io
WEBHOOK_SECRET=your-random-webhook-secret
```

3. GitHub workflow will POST to: `https://abc123.ngrok.io/api/v1/webhooks/analysis-result`

### Production Deployment

For production:

```bash
WEBHOOK_BASE_URL=https://api.yourapp.com
WEBHOOK_SECRET=use-openssl-rand-hex-32-to-generate

# Optional: Adjust polling for your needs
ANALYSIS_POLLING_INTERVAL_SECONDS=60
ANALYSIS_POLLING_TIMEOUT_SECONDS=1800
```

## How It Works

### Webhook Flow (Primary)

```
1. User triggers analysis
   ↓
2. Backend calls GitHub API to start workflow
   - Includes callback_url: https://api.yourapp.com/api/v1/webhooks/analysis-result
   ↓
3. GitHub workflow runs analysis
   ↓
4. Workflow POSTs results to callback_url
   - Headers: X-Webhook-Signature, X-Feature-ID
   ↓
5. Backend validates signature, stores results
   - Updates feature status to COMPLETED/FAILED
   - Creates Analysis record
```

### Polling Flow (Fallback)

```
1. User triggers analysis
   ↓
2. Backend calls GitHub API to start workflow
   - No callback_url (or webhook fails)
   ↓
3. Background polling task runs every 30s
   ↓
4. Task finds features in ANALYZING status
   ↓
5. For each feature:
   - Check workflow status via GitHub API
   - If completed: Download artifact
   - Store results in database
```

## Security

### Webhook Signature Validation

Every webhook payload is validated using HMAC-SHA256:

1. Each feature gets a unique `webhook_secret` on creation
2. GitHub workflow computes signature: `HMAC-SHA256(payload, webhook_secret)`
3. Backend verifies signature matches
4. Invalid signatures are rejected (401 Unauthorized)

This prevents:
- Tampering with results
- Unauthorized result submissions
- Replay attacks

### Timing-Safe Comparison

Signature verification uses `hmac.compare_digest()` for timing-safe comparison, preventing timing attacks.

## Monitoring

### Check Polling Status

View logs for polling activity:

```bash
# Docker
docker logs product-analysis-backend | grep "Polling task"

# Local
tail -f logs/app.log | grep "Polling"
```

### Check Webhook Delivery

Webhooks are logged with:
- Feature ID
- Signature validation result
- Processing status

```bash
grep "webhook" logs/app.log
```

## Troubleshooting

### Webhook Not Receiving Results

**Symptom**: Feature stays in ANALYZING status, webhook never arrives

**Causes**:
1. `WEBHOOK_BASE_URL` not set correctly
2. Server not publicly accessible
3. GitHub can't reach your server (firewall, localhost)

**Solution**:
- Check `WEBHOOK_BASE_URL` in `.env`
- Verify server is publicly accessible: `curl https://api.yourapp.com/health`
- Use ngrok for local testing
- Polling will automatically pick up results as fallback

### Polling Not Working

**Symptom**: Feature stuck in ANALYZING, polling logs absent

**Causes**:
1. Polling scheduler not started
2. Database connection issue
3. GitHub API rate limits

**Solution**:
- Check logs for "Started polling scheduler"
- Verify database connectivity
- Check GitHub API rate limits: `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit`

### Both Mechanisms Failing

**Symptom**: No results after 15 minutes

**Causes**:
1. Workflow actually failed/timed out
2. GitHub API credentials invalid
3. Artifact not created

**Solution**:
- Check GitHub Actions workflow runs: https://github.com/YOUR_REPO/actions
- Verify `GITHUB_TOKEN` has correct permissions
- Check workflow logs for errors

## Testing

### Test Webhook Locally

```bash
# 1. Start backend
uvicorn app.main:app --reload

# 2. Create feature and get webhook secret from database
psql -d product_analysis -c "SELECT id, webhook_secret FROM features WHERE id = 'YOUR_FEATURE_ID';"

# 3. Send test webhook
curl -X POST http://localhost:8000/api/v1/webhooks/analysis-result \
  -H "Content-Type: application/json" \
  -H "X-Feature-ID: YOUR_FEATURE_ID" \
  -H "X-Webhook-Signature: COMPUTED_SIGNATURE" \
  -d '{"feature_id": "YOUR_FEATURE_ID", "complexity": {"story_points": 5}}'
```

### Test Polling

```python
# In backend/tests/
pytest tests/test_polling_service.py -v
```

## Performance Considerations

### Polling Interval

- **Default**: 30 seconds
- **Recommendation**: 30-60 seconds for production
- **Trade-off**: Lower = faster results, higher = less API calls

### Polling Timeout

- **Default**: 15 minutes (900 seconds)
- **Recommendation**: Match workflow timeout
- **After timeout**: Feature remains in ANALYZING (manual check needed)

### Webhook Grace Period

Polling skips features that received webhooks in the last 5 minutes. This prevents:
- Duplicate processing
- Race conditions
- Unnecessary API calls

## FAQ

**Q: Can I disable polling and only use webhooks?**
A: Not recommended. Polling provides reliability. However, you can set `ANALYSIS_POLLING_INTERVAL_SECONDS=3600` (1 hour) to minimize polling.

**Q: Can I disable webhooks and only use polling?**
A: Yes. Simply leave `WEBHOOK_BASE_URL` empty. Polling will be the only mechanism.

**Q: What happens if both webhook and polling process the same feature?**
A: The first to complete wins. Webhook grace period (5 minutes) prevents polling from running after webhook delivery.

**Q: How do I rotate webhook secrets?**
A: Update `WEBHOOK_SECRET` in `.env` and restart. New features will use new secret. Old features keep their individual secrets.
```

2. **Update main README**

Edit `/Users/boudydegeer/Code/@smith.ai/product-analysis/README.md` to add section about dual mechanism:

```markdown
<!-- Add this section after "Features" section -->

## Analysis Result Delivery

The platform uses a **dual mechanism** to reliably receive analysis results:

### Primary: Webhooks
- GitHub workflow POSTs results immediately upon completion
- Sub-second latency for result delivery
- Requires publicly accessible server

### Fallback: Polling
- Background task checks workflow status every 30 seconds
- Automatically downloads results when workflow completes
- Works without public server access (localhost development)

For setup instructions, see [Dual Mechanism Setup Guide](docs/dual-mechanism-setup.md).
```

3. **Commit documentation**

```bash
cd /Users/boudydegeer/Code/@smith.ai/product-analysis
git add docs/dual-mechanism-setup.md README.md
git commit -m "docs: add dual mechanism setup guide

Add comprehensive documentation covering:
- Configuration for localhost, ngrok, and production
- How webhook and polling mechanisms work
- Security validation details
- Monitoring and troubleshooting
- Performance considerations and FAQ"
```

---

## Summary

This implementation plan provides a robust dual mechanism for receiving GitHub workflow analysis results:

### ✅ Completed Tasks (11 total, ~40 minutes)

1. **Configuration** - Added settings for webhook and polling (2 min)
2. **Database Models** - Added tracking fields to Feature model (3 min)
3. **Webhook Schema** - Created validation schema for webhook payloads (3 min)
4. **Security Utilities** - Implemented HMAC signature validation (4 min)
5. **Webhook Endpoint** - Created secure webhook receiver (5 min)
6. **Feature Creation** - Auto-generate webhook secrets (3 min)
7. **Trigger Analysis** - Include callback URL when available (4 min)
8. **Polling Service** - Implemented fallback polling mechanism (5 min)
9. **Background Task** - Integrated polling with app lifecycle (4 min)
10. **Integration Tests** - End-to-end dual mechanism tests (5 min)
11. **Documentation** - Complete setup and troubleshooting guide (3 min)

### Key Features

✅ **Webhook Primary Path**
- Receives results immediately via HTTP POST
- HMAC-SHA256 signature validation
- Timing-safe comparison prevents attacks
- Unique secret per feature

✅ **Polling Fallback Path**
- Runs every 30 seconds (configurable)
- Checks workflow status via GitHub API
- Downloads artifacts when complete
- Skips features that received webhooks

✅ **Smart Coordination**
- Webhook has 5-minute grace period
- Polling respects webhook delivery
- No duplicate processing
- Handles race conditions

✅ **Environment Support**
- **Localhost**: Polling only (no webhook_base_url)
- **Localhost + ngrok**: Full webhook support
- **Production**: Webhook primary, polling fallback

✅ **Security**
- HMAC-SHA256 signatures
- Feature-specific secrets
- Timing-safe validation
- Comprehensive error handling

✅ **Testing**
- Unit tests for all components
- Integration tests for dual mechanism
- TDD approach (test first, then implement)
- Comprehensive test coverage

### Configuration Summary

```bash
# Production
WEBHOOK_BASE_URL=https://api.yourapp.com
WEBHOOK_SECRET=random-secret-here
ANALYSIS_POLLING_INTERVAL_SECONDS=60
ANALYSIS_POLLING_TIMEOUT_SECONDS=900

# Localhost (polling only)
WEBHOOK_BASE_URL=
ANALYSIS_POLLING_INTERVAL_SECONDS=30
```

### Next Steps

After executing this plan:

1. **Apply database migrations**: `alembic upgrade head`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Update `.env`** with configuration values
4. **Run tests**: `pytest -v`
5. **Start server**: `uvicorn app.main:app --reload`
6. **Verify polling logs** appear every 30 seconds
7. **Test with actual workflow** trigger

### Files Created/Modified

**Created (11 files)**:
- `backend/tests/test_config.py`
- `backend/app/schemas/webhook.py`
- `backend/tests/test_webhook_schemas.py`
- `backend/app/utils/webhook_security.py`
- `backend/tests/test_webhook_security.py`
- `backend/app/api/webhooks.py`
- `backend/tests/test_api_webhooks.py`
- `backend/app/services/polling_service.py`
- `backend/tests/test_polling_service.py`
- `backend/app/tasks/polling_task.py`
- `backend/tests/test_integration_dual_mechanism.py`
- `docs/dual-mechanism-setup.md`

**Modified (7 files)**:
- `backend/app/config.py`
- `backend/.env.example`
- `backend/app/models/feature.py`
- `backend/app/main.py`
- `backend/app/api/features.py`
- `backend/tests/test_api_features.py`
- `backend/requirements.txt`
- `README.md`

---

## Execution Strategy

This plan follows TDD and can be executed in three ways:

### Option 1: Sequential Execution (Recommended for Learning)
Execute tasks 1-11 in order, one at a time. Each task is self-contained with tests that verify correctness before moving forward.

### Option 2: Parallel Execution (Faster)
Tasks 1-4 can be done in parallel (configuration, models, schemas, security utilities). Then tasks 5-7 in parallel (webhook endpoint, feature updates). Finally 8-11 sequentially.

### Option 3: Automated Execution
Use the `executing-plans` skill to run all tasks automatically with review checkpoints after every 3 tasks.

**Recommended**: Start with Option 1 for first-time implementation to understand each component.
