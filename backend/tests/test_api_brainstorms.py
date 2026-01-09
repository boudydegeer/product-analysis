"""Tests for brainstorm API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brainstorm import BrainstormSession


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
        """Test creating session without title uses default title."""
        data = {"description": "Test description"}

        response = await async_client.post("/api/v1/brainstorms", json=data)

        # Title is optional, defaults to "New Brainstorm"
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "New Brainstorm"
        assert result["description"] == "Test description"


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
