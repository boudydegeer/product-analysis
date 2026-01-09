"""Comprehensive tests for brainstorm API endpoints to increase coverage."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brainstorm import BrainstormSession, BrainstormSessionStatus


class TestUpdateBrainstormErrors:
    """Tests for update brainstorm error cases."""

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, async_client: AsyncClient):
        """Test updating non-existent session returns 404."""
        update_data = {"title": "Updated Title"}
        response = await async_client.put(
            "/api/v1/brainstorms/nonexistent", json=update_data
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_session_partial_update(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test partial update only changes specified fields."""
        session = BrainstormSession(
            id="session-1",
            title="Original Title",
            description="Original description",
            status=BrainstormSessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()

        # Only update title
        update_data = {"title": "New Title Only"}
        response = await async_client.put(
            "/api/v1/brainstorms/session-1", json=update_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "New Title Only"
        assert result["description"] == "Original description"
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_update_session_all_fields(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating all fields at once."""
        session = BrainstormSession(
            id="session-1",
            title="Original",
            description="Original desc",
            status=BrainstormSessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()

        update_data = {
            "title": "New Title",
            "description": "New description",
            "status": "completed",
        }
        response = await async_client.put(
            "/api/v1/brainstorms/session-1", json=update_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "New Title"
        assert result["description"] == "New description"
        assert result["status"] == "completed"


class TestDeleteBrainstormErrors:
    """Tests for delete brainstorm error cases."""

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent session returns 404."""
        response = await async_client.delete("/api/v1/brainstorms/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_session_verifies_deletion(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that deleted session is actually removed from database."""
        session = BrainstormSession(
            id="session-to-delete", title="Test", description="Test desc"
        )
        db_session.add(session)
        await db_session.commit()

        # Delete the session
        response = await async_client.delete("/api/v1/brainstorms/session-to-delete")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await async_client.get("/api/v1/brainstorms/session-to-delete")
        assert get_response.status_code == 404


class TestListBrainstormsPagination:
    """Tests for brainstorm listing pagination."""

    @pytest.mark.asyncio
    async def test_list_sessions_pagination_skip(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test pagination with skip parameter."""
        for i in range(5):
            session = BrainstormSession(
                id=f"session-{i}",
                title=f"Session {i}",
                description=f"Description {i}",
            )
            db_session.add(session)
        await db_session.commit()

        response = await async_client.get("/api/v1/brainstorms?skip=2")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_sessions_pagination_limit(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test pagination with limit parameter."""
        for i in range(5):
            session = BrainstormSession(
                id=f"session-{i}",
                title=f"Session {i}",
                description=f"Description {i}",
            )
            db_session.add(session)
        await db_session.commit()

        response = await async_client.get("/api/v1/brainstorms?limit=2")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2


class TestBrainstormStatusValues:
    """Tests for different brainstorm session status values."""

    @pytest.mark.asyncio
    async def test_create_session_default_status(self, async_client: AsyncClient):
        """Test that new sessions default to ACTIVE status."""
        data = {
            "title": "New Session",
            "description": "Test description",
        }

        response = await async_client.post("/api/v1/brainstorms", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_update_session_to_completed_status(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating session status to completed."""
        session = BrainstormSession(
            id="session-1",
            title="Test Session",
            description="Test description",
            status=BrainstormSessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()

        update_data = {"status": "completed"}
        response = await async_client.put(
            "/api/v1/brainstorms/session-1", json=update_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_session_to_archived_status(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating session status to archived."""
        session = BrainstormSession(
            id="session-1",
            title="Test Session",
            description="Test description",
            status=BrainstormSessionStatus.COMPLETED,
        )
        db_session.add(session)
        await db_session.commit()

        update_data = {"status": "archived"}
        response = await async_client.put(
            "/api/v1/brainstorms/session-1", json=update_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "archived"


class TestCreateBrainstormEdgeCases:
    """Tests for brainstorm creation edge cases."""

    @pytest.mark.asyncio
    async def test_create_session_with_unicode(self, async_client: AsyncClient):
        """Test creating session with unicode characters."""
        data = {
            "title": "🚀 Rocket Session 🎯",
            "description": "Test with émojis and spëcial çharacters",
        }

        response = await async_client.post("/api/v1/brainstorms", json=data)

        assert response.status_code == 201
        result = response.json()
        assert "🚀" in result["title"]
