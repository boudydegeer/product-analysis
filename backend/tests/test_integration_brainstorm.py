"""Integration tests for brainstorm feature."""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.brainstorm import BrainstormSession, BrainstormMessage, MessageRole


class TestBrainstormIntegration:
    """End-to-end tests for brainstorm workflow."""

    @pytest.mark.asyncio
    async def test_complete_brainstorm_workflow(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test complete workflow: create session, send message, verify storage."""
        # Step 1: Create session
        create_data = {
            "title": "Mobile App Features",
            "description": "Brainstorm new features for mobile app",
        }
        response = await async_client.post("/api/v1/brainstorms", json=create_data)
        assert response.status_code == 201
        session_data = response.json()
        session_id = session_data["id"]

        # Step 2: Verify session in database
        result = await db_session.execute(
            select(BrainstormSession).where(BrainstormSession.id == session_id)
        )
        db_session_obj = result.scalar_one()
        assert db_session_obj.title == create_data["title"]

        # Step 3: Get session via API
        response = await async_client.get(f"/api/v1/brainstorms/{session_id}")
        assert response.status_code == 200
        assert response.json()["id"] == session_id

        # Step 4: List sessions
        response = await async_client.get("/api/v1/brainstorms")
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= 1
        assert any(s["id"] == session_id for s in sessions)

        # Step 5: Update session status
        update_data = {"status": "completed"}
        response = await async_client.put(
            f"/api/v1/brainstorms/{session_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        # Step 6: Delete session
        response = await async_client.delete(f"/api/v1/brainstorms/{session_id}")
        assert response.status_code == 204

        # Step 7: Verify deletion
        result = await db_session.execute(
            select(BrainstormSession).where(BrainstormSession.id == session_id)
        )
        assert result.scalar_one_or_none() is None
