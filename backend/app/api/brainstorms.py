"""Brainstorm sessions API endpoints."""
import json
import logging
import re
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, async_session_maker
from app.models.brainstorm import (
    BrainstormSession,
    BrainstormSessionStatus,
    BrainstormMessage,
    MessageRole,
)
from app.schemas.brainstorm import (
    BrainstormSessionCreate,
    BrainstormSessionUpdate,
    BrainstormSessionResponse,
)
from app.services.brainstorming_service import BrainstormingService

logger = logging.getLogger(__name__)
logger.warning("*" * 60)
logger.warning("🔥 BRAINSTORMS.PY LOADED - VERSION 3.0 WITH FULL LOGGING")
logger.warning("*" * 60)

router = APIRouter(prefix="/api/v1/brainstorms", tags=["brainstorms"])


def extract_json_from_markdown(text: str) -> str:
    """Extract JSON from markdown code blocks if present.

    Args:
        text: Text that may contain JSON in markdown code blocks

    Returns:
        Extracted JSON string or original text if no code blocks found
    """
    # Try to find JSON in ```json ... ``` blocks
    json_block_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    match = re.search(json_block_pattern, text, re.MULTILINE | re.DOTALL)

    if match:
        return match.group(1)

    # Try to find JSON in ```...``` blocks (without language specifier)
    code_block_pattern = r'```\s*(\{[\s\S]*?\})\s*```'
    match = re.search(code_block_pattern, text, re.MULTILINE | re.DOTALL)

    if match:
        return match.group(1)

    # Return as-is if no code blocks found
    return text


@router.get("/debug/version")
async def debug_version():
    """Debug endpoint to check if code is loaded."""
    return {"version": "2.0-WITH-LOGGING", "status": "active"}


@router.post(
    "",
    response_model=BrainstormSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/",
    response_model=BrainstormSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_brainstorm_session(
    session_in: BrainstormSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> BrainstormSession:
    """Create a new brainstorm session.

    Args:
        session_in: Session data
        db: Database session

    Returns:
        Created brainstorm session
    """
    session = BrainstormSession(
        id=str(uuid4()),
        title=session_in.title,
        description=session_in.description,
        status=BrainstormSessionStatus.ACTIVE,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"Created brainstorm session: {session.id}")
    return session


@router.get("", response_model=list[BrainstormSessionResponse])
@router.get("/", response_model=list[BrainstormSessionResponse])
async def list_brainstorm_sessions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[BrainstormSession]:
    """List all brainstorm sessions.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of brainstorm sessions
    """
    result = await db.execute(
        select(BrainstormSession)
        .offset(skip)
        .limit(limit)
        .order_by(BrainstormSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return list(sessions)


@router.get("/{session_id}", response_model=BrainstormSessionResponse)
async def get_brainstorm_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> BrainstormSession:
    """Get a specific brainstorm session.

    Args:
        session_id: Session ID
        db: Database session

    Returns:
        Brainstorm session

    Raises:
        HTTPException: If session not found
    """
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brainstorm session {session_id} not found",
        )

    return session


@router.put("/{session_id}", response_model=BrainstormSessionResponse)
async def update_brainstorm_session(
    session_id: str,
    session_update: BrainstormSessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> BrainstormSession:
    """Update a brainstorm session.

    Args:
        session_id: Session ID
        session_update: Update data
        db: Database session

    Returns:
        Updated session

    Raises:
        HTTPException: If session not found
    """
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brainstorm session {session_id} not found",
        )

    # Update fields
    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status":
            value = BrainstormSessionStatus(value)
        setattr(session, field, value)

    await db.commit()
    await db.refresh(session)

    logger.info(f"Updated brainstorm session: {session_id}")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brainstorm_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a brainstorm session.

    Args:
        session_id: Session ID
        db: Database session

    Raises:
        HTTPException: If session not found
    """
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brainstorm session {session_id} not found",
        )

    await db.delete(session)
    await db.commit()

    logger.info(f"Deleted brainstorm session: {session_id}")


@router.websocket("/ws/{session_id}")
async def websocket_brainstorm(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for interactive brainstorming."""
    await websocket.accept()
    logger.info(f"[WS] Client connected to session {session_id}")

    # Independent database session
    async with async_session_maker() as db:
        try:
            # Verify session exists and is active
            result = await db.execute(
                select(BrainstormSession).where(BrainstormSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found"
                })
                await websocket.close()
                return

            if session.status != "active":
                await websocket.send_json({
                    "type": "error",
                    "message": "Session is not active"
                })
                await websocket.close()
                return

            # Main message loop
            while True:
                data = await websocket.receive_json()
                logger.info(f"[WS] Received: {data['type']}")

                if data["type"] == "user_message":
                    await handle_user_message(websocket, db, session_id, data["content"])

                elif data["type"] == "interaction":
                    await handle_interaction(
                        websocket, db, session_id,
                        data["block_id"], data["value"]
                    )

        except WebSocketDisconnect:
            logger.info(f"[WS] Client disconnected from session {session_id}")
        except Exception as e:
            logger.error(f"[WS] Error: {e}", exc_info=True)
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except:
                pass


async def handle_user_message(
    websocket: WebSocket,
    db,
    session_id: str,
    content: str
):
    """Handle user text message."""
    # Save user message to database
    user_message = BrainstormMessage(
        id=str(uuid4()),
        session_id=session_id,
        role="user",
        content={
            "blocks": [{
                "id": str(uuid4()),
                "type": "text",
                "text": content
            }]
        }
    )
    db.add(user_message)
    await db.commit()
    logger.info(f"[WS] Saved user message")

    # Stream Claude response
    await stream_claude_response(websocket, db, session_id)


async def handle_interaction(
    websocket: WebSocket,
    db,
    session_id: str,
    block_id: str,
    value: str | list[str]
):
    """Handle user interaction with button/select."""
    # Save interaction as user message
    interaction_message = BrainstormMessage(
        id=str(uuid4()),
        session_id=session_id,
        role="user",
        content={
            "blocks": [{
                "id": str(uuid4()),
                "type": "interaction_response",
                "block_id": block_id,
                "value": value
            }]
        }
    )
    db.add(interaction_message)
    await db.commit()
    logger.info(f"[WS] Saved interaction")

    # Stream Claude response
    await stream_claude_response(websocket, db, session_id)


async def stream_claude_response(
    websocket: WebSocket,
    db,
    session_id: str
):
    """Stream Claude's response block-by-block."""
    # Get conversation history
    result = await db.execute(
        select(BrainstormMessage)
        .where(BrainstormMessage.session_id == session_id)
        .order_by(BrainstormMessage.created_at)
    )
    messages = result.scalars().all()

    # Convert to format for Claude
    conversation = []
    for msg in messages:
        if msg.role == "user":
            # Extract text from blocks
            text_parts = []
            for block in msg.content.get("blocks", []):
                if block["type"] == "text":
                    text_parts.append(block["text"])
                elif block["type"] == "interaction_response":
                    text_parts.append(f"Selected: {block['value']}")
            conversation.append({"role": "user", "content": " ".join(text_parts)})
        else:
            # For assistant, combine all text blocks
            text_parts = [
                b["text"] for b in msg.content.get("blocks", [])
                if b["type"] == "text"
            ]
            if text_parts:
                conversation.append({"role": "assistant", "content": " ".join(text_parts)})

    # Stream from Claude
    message_id = str(uuid4())
    collected_blocks = []

    async with BrainstormingService(api_key=settings.anthropic_api_key) as service:
        try:
            # Claude returns JSON string
            full_response = ""
            async for chunk in service.stream_brainstorm_message(conversation):
                full_response += chunk

            # Parse JSON response
            response_data = None
            try:
                # Extract JSON from markdown code blocks if present
                json_text = extract_json_from_markdown(full_response)
                response_data = json.loads(json_text)
                blocks = response_data.get("blocks", [])

                # Send blocks incrementally
                for block in blocks:
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "message_id": message_id,
                        "block": block
                    })
                    collected_blocks.append(block)

            except json.JSONDecodeError as e:
                # Fallback: treat as plain text
                logger.warning(f"[WS] Claude response not valid JSON: {e}, treating as text")
                text_block = {
                    "id": str(uuid4()),
                    "type": "text",
                    "text": full_response
                }
                await websocket.send_json({
                    "type": "stream_chunk",
                    "message_id": message_id,
                    "block": text_block
                })
                collected_blocks.append(text_block)

            # Save to database
            assistant_message = BrainstormMessage(
                id=message_id,
                session_id=session_id,
                role="assistant",
                content={
                    "blocks": collected_blocks,
                    "metadata": response_data.get("metadata", {}) if isinstance(response_data, dict) else {}
                }
            )
            db.add(assistant_message)
            await db.commit()

            # Signal completion
            await websocket.send_json({
                "type": "stream_complete",
                "message_id": message_id
            })
            logger.info(f"[WS] Stream complete")

        except Exception as e:
            logger.error(f"[WS] Error streaming: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": f"Streaming error: {str(e)}"
            })
