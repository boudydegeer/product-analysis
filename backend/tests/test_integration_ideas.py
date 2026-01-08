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
