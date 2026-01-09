"""Comprehensive tests for ideas API endpoints to increase coverage."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea import Idea, IdeaStatus, IdeaPriority


class TestListIdeasFiltering:
    """Tests for idea filtering and pagination."""

    @pytest.mark.asyncio
    async def test_list_ideas_filter_by_priority(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering ideas by priority."""
        idea1 = Idea(
            id="idea-high",
            title="High Priority Idea",
            description="High priority",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.HIGH,
        )
        idea2 = Idea(
            id="idea-low",
            title="Low Priority Idea",
            description="Low priority",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.LOW,
        )
        db_session.add_all([idea1, idea2])
        await db_session.commit()

        response = await async_client.get("/api/v1/ideas?priority=high")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_list_ideas_filter_by_status_and_priority(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering ideas by both status and priority."""
        idea1 = Idea(
            id="idea-1",
            title="Idea 1",
            description="Desc 1",
            status=IdeaStatus.APPROVED,
            priority=IdeaPriority.HIGH,
        )
        idea2 = Idea(
            id="idea-2",
            title="Idea 2",
            description="Desc 2",
            status=IdeaStatus.APPROVED,
            priority=IdeaPriority.LOW,
        )
        idea3 = Idea(
            id="idea-3",
            title="Idea 3",
            description="Desc 3",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.HIGH,
        )
        db_session.add_all([idea1, idea2, idea3])
        await db_session.commit()

        response = await async_client.get("/api/v1/ideas?status=approved&priority=high")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["id"] == "idea-1"

    @pytest.mark.asyncio
    async def test_list_ideas_pagination_skip(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test pagination with skip parameter."""
        for i in range(5):
            idea = Idea(
                id=f"idea-{i}",
                title=f"Idea {i}",
                description=f"Description {i}",
                status=IdeaStatus.BACKLOG,
                priority=IdeaPriority.MEDIUM,
            )
            db_session.add(idea)
        await db_session.commit()

        response = await async_client.get("/api/v1/ideas?skip=2")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_ideas_pagination_limit(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test pagination with limit parameter."""
        for i in range(5):
            idea = Idea(
                id=f"idea-{i}",
                title=f"Idea {i}",
                description=f"Description {i}",
                status=IdeaStatus.BACKLOG,
                priority=IdeaPriority.MEDIUM,
            )
            db_session.add(idea)
        await db_session.commit()

        response = await async_client.get("/api/v1/ideas?limit=2")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2


class TestUpdateIdeaErrors:
    """Tests for update idea error cases."""

    @pytest.mark.asyncio
    async def test_update_idea_not_found(self, async_client: AsyncClient):
        """Test updating non-existent idea returns 404."""
        update_data = {"title": "Updated Title"}
        response = await async_client.put("/api/v1/ideas/nonexistent", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_idea_partial_update(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test partial update only changes specified fields."""
        idea = Idea(
            id="idea-1",
            title="Original Title",
            description="Original description",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.MEDIUM,
        )
        db_session.add(idea)
        await db_session.commit()

        # Only update title
        update_data = {"title": "New Title Only"}
        response = await async_client.put("/api/v1/ideas/idea-1", json=update_data)

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "New Title Only"
        assert result["description"] == "Original description"
        assert result["status"] == "backlog"
        assert result["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_update_idea_all_fields(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating all fields at once."""
        idea = Idea(
            id="idea-1",
            title="Original",
            description="Original desc",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.LOW,
        )
        db_session.add(idea)
        await db_session.commit()

        update_data = {
            "title": "New Title",
            "description": "New description",
            "status": "approved",
            "priority": "critical",
        }
        response = await async_client.put("/api/v1/ideas/idea-1", json=update_data)

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "New Title"
        assert result["description"] == "New description"
        assert result["status"] == "approved"
        assert result["priority"] == "critical"


class TestDeleteIdeaErrors:
    """Tests for delete idea error cases."""

    @pytest.mark.asyncio
    async def test_delete_idea_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent idea returns 404."""
        response = await async_client.delete("/api/v1/ideas/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_idea_verifies_deletion(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that deleted idea is actually removed from database."""
        idea = Idea(
            id="idea-to-delete",
            title="Test",
            description="Test desc",
            status=IdeaStatus.BACKLOG,
            priority=IdeaPriority.MEDIUM,
        )
        db_session.add(idea)
        await db_session.commit()

        # Delete the idea
        response = await async_client.delete("/api/v1/ideas/idea-to-delete")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await async_client.get("/api/v1/ideas/idea-to-delete")
        assert get_response.status_code == 404


class TestCreateIdeaWithDefaultPriority:
    """Tests for idea creation with default priority."""

    @pytest.mark.asyncio
    async def test_create_idea_without_priority_uses_default(
        self, async_client: AsyncClient
    ):
        """Test creating idea without priority uses MEDIUM as default."""
        data = {
            "title": "No Priority Idea",
            "description": "This has no priority specified",
        }

        response = await async_client.post("/api/v1/ideas", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_create_idea_with_all_priority_values(
        self, async_client: AsyncClient
    ):
        """Test creating ideas with all valid priority values."""
        priorities = ["low", "medium", "high", "critical"]

        for priority in priorities:
            data = {
                "title": f"Idea with {priority} priority",
                "description": f"Priority: {priority}",
                "priority": priority,
            }

            response = await async_client.post("/api/v1/ideas", json=data)

            assert response.status_code == 201
            result = response.json()
            assert result["priority"] == priority


class TestListIdeasMultipleStatuses:
    """Tests for listing ideas with different statuses."""

    @pytest.mark.asyncio
    async def test_list_ideas_all_statuses(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test creating ideas with all valid status values."""
        statuses = [
            IdeaStatus.BACKLOG,
            IdeaStatus.UNDER_REVIEW,
            IdeaStatus.APPROVED,
            IdeaStatus.REJECTED,
            IdeaStatus.IMPLEMENTED,
        ]

        # Create idea for each status
        for idx, status in enumerate(statuses):
            idea = Idea(
                id=f"idea-{status.value}",
                title=f"Idea {status.value}",
                description=f"Status: {status.value}",
                status=status,
                priority=IdeaPriority.MEDIUM,
            )
            db_session.add(idea)
        await db_session.commit()

        # Get all ideas
        response = await async_client.get("/api/v1/ideas")

        assert response.status_code == 200
        result = response.json()
        assert len(result) == len(statuses)

        # Verify each status exists
        result_statuses = {item["status"] for item in result}
        expected_statuses = {status.value for status in statuses}
        assert result_statuses == expected_statuses


class TestCreateIdeaEdgeCases:
    """Tests for idea creation edge cases."""

    @pytest.mark.asyncio
    async def test_create_idea_with_unicode(self, async_client: AsyncClient):
        """Test creating idea with unicode characters."""
        data = {
            "title": "🎨 Design System Overhaul",
            "description": "Implement a new design system with émojis and spëcial çharacters",
        }

        response = await async_client.post("/api/v1/ideas", json=data)

        assert response.status_code == 201
        result = response.json()
        assert "🎨" in result["title"]
