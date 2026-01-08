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
