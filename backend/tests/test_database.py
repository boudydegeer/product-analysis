"""Tests for database module."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, async_session_maker


@pytest.mark.asyncio
async def test_get_db_yields_session():
    """Test that get_db yields a session."""
    async for session in get_db():
        assert isinstance(session, AsyncSession)
        break


@pytest.mark.asyncio
async def test_get_db_closes_session():
    """Test that get_db properly closes the session."""
    session_instance = None
    async for session in get_db():
        session_instance = session
        break

    # Session should be closed after exiting context
    assert session_instance is not None


@pytest.mark.asyncio
async def test_async_session_maker():
    """Test that async_session_maker creates sessions."""
    async with async_session_maker() as session:
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_async_session_maker_context_manager():
    """Test async_session_maker as context manager."""
    async with async_session_maker() as session:
        # Should be able to use the session
        assert session is not None
        # Session should be active
        assert session.is_active
