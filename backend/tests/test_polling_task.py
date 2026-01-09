"""Tests for polling_task scheduler functions."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.tasks.polling_task import (
    poll_analyzing_features,
    start_polling_scheduler,
    stop_polling_scheduler,
    scheduler,
)


@pytest.mark.asyncio
async def test_poll_analyzing_features_success(monkeypatch):
    """Test successful polling task execution."""
    # Mock the polling service
    mock_service = AsyncMock()
    mock_service.poll_all_analyzing_features.return_value = 3

    # Mock the async_session_maker context manager
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    mock_session_maker = MagicMock(return_value=mock_session)

    # Patch the imports
    with patch("app.tasks.polling_task.async_session_maker", mock_session_maker):
        with patch("app.tasks.polling_task.AnalysisPollingService", return_value=mock_service):
            await poll_analyzing_features()

    # Verify service was called
    mock_service.poll_all_analyzing_features.assert_called_once()


@pytest.mark.asyncio
async def test_poll_analyzing_features_error(monkeypatch):
    """Test polling task handles errors gracefully."""
    # Mock the polling service to raise error
    mock_service = AsyncMock()
    mock_service.poll_all_analyzing_features.side_effect = Exception("Test error")

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    mock_session_maker = MagicMock(return_value=mock_session)

    # Should not raise, just log error
    with patch("app.tasks.polling_task.async_session_maker", mock_session_maker):
        with patch("app.tasks.polling_task.AnalysisPollingService", return_value=mock_service):
            await poll_analyzing_features()  # Should not raise


def test_start_polling_scheduler():
    """Test starting the polling scheduler."""
    from unittest.mock import patch, MagicMock
    import app.tasks.polling_task
    app.tasks.polling_task.scheduler = None

    # Mock the AsyncIOScheduler to avoid event loop issues
    mock_scheduler = MagicMock()
    mock_scheduler.running = True
    mock_scheduler.get_jobs.return_value = [MagicMock(id="poll_analyzing_features")]

    with patch("app.tasks.polling_task.AsyncIOScheduler", return_value=mock_scheduler):
        scheduler = start_polling_scheduler()

        assert scheduler is not None
        assert scheduler.running is True
        mock_scheduler.start.assert_called_once()

    # Cleanup
    app.tasks.polling_task.scheduler = None


def test_start_polling_scheduler_already_running():
    """Test starting scheduler when already running returns existing instance."""
    from unittest.mock import patch, MagicMock
    import app.tasks.polling_task
    app.tasks.polling_task.scheduler = None

    mock_scheduler = MagicMock()
    mock_scheduler.running = True

    with patch("app.tasks.polling_task.AsyncIOScheduler", return_value=mock_scheduler):
        scheduler1 = start_polling_scheduler()
        scheduler2 = start_polling_scheduler()

        # Should return same instance
        assert scheduler1 is scheduler2

    # Cleanup
    app.tasks.polling_task.scheduler = None


def test_stop_polling_scheduler():
    """Test stopping the polling scheduler."""
    from unittest.mock import patch, MagicMock
    import app.tasks.polling_task
    app.tasks.polling_task.scheduler = None

    mock_scheduler = MagicMock()

    with patch("app.tasks.polling_task.AsyncIOScheduler", return_value=mock_scheduler):
        start_polling_scheduler()
        stop_polling_scheduler()

        mock_scheduler.shutdown.assert_called_once()
        assert app.tasks.polling_task.scheduler is None


def test_stop_polling_scheduler_not_running():
    """Test stopping scheduler when not running doesn't error."""
    import app.tasks.polling_task
    app.tasks.polling_task.scheduler = None

    # Should not raise
    stop_polling_scheduler()
    assert app.tasks.polling_task.scheduler is None


@pytest.mark.asyncio
async def test_polling_lifespan():
    """Test polling lifespan context manager."""
    from app.tasks.polling_task import polling_lifespan
    import app.tasks.polling_task

    app.tasks.polling_task.scheduler = None

    async with polling_lifespan():
        # Scheduler should be running
        assert app.tasks.polling_task.scheduler is not None
        assert app.tasks.polling_task.scheduler.running is True

    # Scheduler should be stopped
    assert app.tasks.polling_task.scheduler is None
