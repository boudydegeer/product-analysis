"""Tests for codebase exploration polling service."""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.models.codebase_exploration import CodebaseExploration, CodebaseExplorationStatus
from app.services.polling_service import AnalysisPollingService


# Test database setup - SQLite in-memory with async
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestingAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Get a test database session."""
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.fixture
def polling_service(db_session: AsyncSession):
    """Create polling service instance."""
    return AnalysisPollingService(db_session)


@pytest.fixture
async def investigating_exploration(db_session: AsyncSession) -> CodebaseExploration:
    """Create an exploration in INVESTIGATING status."""
    exploration = CodebaseExploration(
        id="exp-test001",
        session_id="session-123",
        message_id="msg-456",
        query="How does authentication work?",
        scope="backend",
        focus="security",
        status=CodebaseExplorationStatus.INVESTIGATING,
        workflow_run_id="12345",
        workflow_url="https://github.com/owner/repo/actions/runs/12345",
    )
    db_session.add(exploration)
    await db_session.commit()
    await db_session.refresh(exploration)
    return exploration


@pytest.mark.asyncio
class TestExplorationPolling:
    """Tests for exploration polling functionality."""

    async def test_poll_finds_investigating_explorations(
        self, polling_service, investigating_exploration, db_session: AsyncSession
    ):
        """Should find explorations in INVESTIGATING status."""
        explorations = await polling_service.get_explorations_needing_polling()

        assert len(explorations) == 1
        assert explorations[0].id == investigating_exploration.id
        assert explorations[0].status == CodebaseExplorationStatus.INVESTIGATING

    async def test_poll_excludes_completed_explorations(
        self, polling_service, db_session: AsyncSession
    ):
        """Should not return explorations that are already COMPLETED."""
        exploration = CodebaseExploration(
            id="exp-completed",
            session_id="session-456",
            message_id="msg-789",
            query="What APIs exist?",
            status=CodebaseExplorationStatus.COMPLETED,
            workflow_run_id="99999",
            completed_at=datetime.now(UTC),
        )
        db_session.add(exploration)
        await db_session.commit()

        explorations = await polling_service.get_explorations_needing_polling()

        assert len(explorations) == 0

    async def test_poll_excludes_failed_explorations(
        self, polling_service, db_session: AsyncSession
    ):
        """Should not return explorations that are FAILED."""
        exploration = CodebaseExploration(
            id="exp-failed",
            session_id="session-789",
            message_id="msg-012",
            query="Test query",
            status=CodebaseExplorationStatus.FAILED,
            workflow_run_id="88888",
            error_message="Workflow failed",
        )
        db_session.add(exploration)
        await db_session.commit()

        explorations = await polling_service.get_explorations_needing_polling()

        assert len(explorations) == 0

    async def test_poll_excludes_pending_explorations(
        self, polling_service, db_session: AsyncSession
    ):
        """Should not poll explorations still in PENDING status."""
        exploration = CodebaseExploration(
            id="exp-pending",
            session_id="session-101",
            message_id="msg-202",
            query="Pending query",
            status=CodebaseExplorationStatus.PENDING,
        )
        db_session.add(exploration)
        await db_session.commit()

        explorations = await polling_service.get_explorations_needing_polling()

        assert len(explorations) == 0

    async def test_poll_excludes_explorations_without_workflow_run_id(
        self, polling_service, db_session: AsyncSession
    ):
        """Should not poll explorations without workflow_run_id."""
        exploration = CodebaseExploration(
            id="exp-no-workflow",
            session_id="session-303",
            message_id="msg-404",
            query="Query without workflow",
            status=CodebaseExplorationStatus.INVESTIGATING,
            workflow_run_id=None,  # No workflow ID
        )
        db_session.add(exploration)
        await db_session.commit()

        explorations = await polling_service.get_explorations_needing_polling()

        assert len(explorations) == 0

    async def test_poll_updates_completed_exploration(
        self, polling_service, investigating_exploration, db_session: AsyncSession
    ):
        """Should download artifact and update exploration when workflow completes."""
        mock_results = {
            "exploration_id": investigating_exploration.id,
            "summary": "Found authentication implementation",
            "files_found": ["auth.py", "security.py"],
            "patterns": ["JWT authentication"],
            "code_examples": [{"file": "auth.py", "snippet": "def verify_token()"}],
            "recommendations": ["Add rate limiting"],
        }

        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "completed"
        mock_github_service.download_workflow_artifact.return_value = mock_results
        mock_github_service.close = AsyncMock()

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_exploration_status(investigating_exploration)

        # Refresh to get updated values
        await db_session.refresh(investigating_exploration)

        # Exploration should be updated to COMPLETED
        assert investigating_exploration.status == CodebaseExplorationStatus.COMPLETED
        assert investigating_exploration.results is not None
        assert investigating_exploration.results["summary"] == "Found authentication implementation"
        assert investigating_exploration.formatted_context is not None
        assert "auth.py" in investigating_exploration.formatted_context
        assert investigating_exploration.completed_at is not None

    async def test_poll_handles_failed_workflow(
        self, polling_service, investigating_exploration, db_session: AsyncSession
    ):
        """Should update exploration to FAILED when workflow fails."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "failure"
        mock_github_service.close = AsyncMock()

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_exploration_status(investigating_exploration)

        # Refresh to get updated values
        await db_session.refresh(investigating_exploration)

        # Exploration should be updated to FAILED
        assert investigating_exploration.status == CodebaseExplorationStatus.FAILED
        assert investigating_exploration.error_message == "Workflow failure"

    async def test_poll_handles_cancelled_workflow(
        self, polling_service, investigating_exploration, db_session: AsyncSession
    ):
        """Should update exploration to FAILED when workflow is cancelled."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "cancelled"
        mock_github_service.close = AsyncMock()

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_exploration_status(investigating_exploration)

        await db_session.refresh(investigating_exploration)

        assert investigating_exploration.status == CodebaseExplorationStatus.FAILED
        assert "cancelled" in investigating_exploration.error_message.lower()

    async def test_poll_handles_no_results(
        self, polling_service, investigating_exploration, db_session: AsyncSession
    ):
        """Should mark exploration as FAILED when workflow completes but no results found."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "completed"
        mock_github_service.download_workflow_artifact.return_value = None
        mock_github_service.close = AsyncMock()

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_exploration_status(investigating_exploration)

        await db_session.refresh(investigating_exploration)

        # Should be FAILED because no results
        assert investigating_exploration.status == CodebaseExplorationStatus.FAILED
        assert "No results found" in investigating_exploration.error_message

    async def test_poll_handles_errors_gracefully(
        self, polling_service, investigating_exploration, db_session: AsyncSession
    ):
        """Should handle GitHub API errors gracefully without crashing."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.side_effect = Exception(
            "GitHub API error"
        )
        mock_github_service.close = AsyncMock()

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            # Should not raise exception
            await polling_service.poll_exploration_status(investigating_exploration)

        # Exploration status should remain unchanged on transient errors
        await db_session.refresh(investigating_exploration)
        assert investigating_exploration.status == CodebaseExplorationStatus.INVESTIGATING

    async def test_poll_handles_workflow_still_in_progress(
        self, polling_service, investigating_exploration, db_session: AsyncSession
    ):
        """Should leave exploration unchanged when workflow still in progress."""
        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "in_progress"
        mock_github_service.close = AsyncMock()

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            await polling_service.poll_exploration_status(investigating_exploration)

        await db_session.refresh(investigating_exploration)

        # Status should remain INVESTIGATING
        assert investigating_exploration.status == CodebaseExplorationStatus.INVESTIGATING
        # Results should still be None
        assert investigating_exploration.results is None

    async def test_poll_all_investigating_explorations(
        self, polling_service, db_session: AsyncSession
    ):
        """Should poll all explorations in INVESTIGATING status."""
        # Create multiple investigating explorations
        explorations = []
        for i in range(3):
            exploration = CodebaseExploration(
                id=f"exp-multi-{i}",
                session_id=f"session-{i}",
                message_id=f"msg-{i}",
                query=f"Query {i}",
                status=CodebaseExplorationStatus.INVESTIGATING,
                workflow_run_id=f"{1000 + i}",
            )
            db_session.add(exploration)
            explorations.append(exploration)
        await db_session.commit()

        mock_github_service = AsyncMock()
        mock_github_service.get_workflow_run_status.return_value = "in_progress"
        mock_github_service.close = AsyncMock()

        with patch(
            "app.services.polling_service.GitHubService",
            return_value=mock_github_service,
        ):
            polled_count = await polling_service.poll_all_investigating_explorations()

        assert polled_count == 3

    async def test_poll_exploration_skips_without_workflow_run_id(
        self, polling_service, db_session: AsyncSession
    ):
        """Should skip exploration without workflow_run_id."""
        exploration = CodebaseExploration(
            id="exp-no-run-id",
            session_id="session-skip",
            message_id="msg-skip",
            query="Query without run ID",
            status=CodebaseExplorationStatus.INVESTIGATING,
            workflow_run_id=None,
        )
        db_session.add(exploration)
        await db_session.commit()

        # Should not raise and should skip
        await polling_service.poll_exploration_status(exploration)

        # Status should remain unchanged
        await db_session.refresh(exploration)
        assert exploration.status == CodebaseExplorationStatus.INVESTIGATING

    async def test_poll_excludes_timed_out_explorations(
        self, polling_service, db_session: AsyncSession
    ):
        """Should not poll explorations that have exceeded timeout."""
        # Create exploration created 20 minutes ago (beyond 15 minute timeout)
        old_timestamp = datetime.now(UTC) - timedelta(minutes=20)
        exploration = CodebaseExploration(
            id="exp-timed-out",
            session_id="session-timeout",
            message_id="msg-timeout",
            query="Timed out query",
            status=CodebaseExplorationStatus.INVESTIGATING,
            workflow_run_id="77777",
            created_at=old_timestamp,
        )
        db_session.add(exploration)
        await db_session.commit()

        explorations = await polling_service.get_explorations_needing_polling()

        # Should be excluded because it exceeded timeout
        exploration_ids = [e.id for e in explorations]
        assert "exp-timed-out" not in exploration_ids


@pytest.mark.asyncio
class TestExplorationPollingTask:
    """Tests for the exploration polling background task."""

    async def test_poll_pending_explorations_task(self, db_session: AsyncSession):
        """Test the background task polls all pending explorations."""
        # Create investigating exploration
        exploration = CodebaseExploration(
            id="exp-task-test",
            session_id="session-task",
            message_id="msg-task",
            query="Task test query",
            status=CodebaseExplorationStatus.INVESTIGATING,
            workflow_run_id="55555",
        )
        db_session.add(exploration)
        await db_session.commit()

        mock_service = AsyncMock()
        mock_service.poll_all_investigating_explorations.return_value = 1

        # Mock the async session context manager
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = db_session
        mock_session.__aexit__.return_value = None

        mock_session_maker = MagicMock(return_value=mock_session)

        with patch("app.tasks.polling_task.async_session_maker", mock_session_maker):
            with patch(
                "app.tasks.polling_task.AnalysisPollingService",
                return_value=mock_service,
            ):
                from app.tasks.polling_task import poll_pending_explorations

                await poll_pending_explorations()

        mock_service.poll_all_investigating_explorations.assert_called_once()
