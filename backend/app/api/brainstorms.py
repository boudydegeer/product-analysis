"""Brainstorm sessions API endpoints."""
import json
import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
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


@router.get("/{session_id}/stream")
async def stream_brainstorm(
    session_id: str,
    message: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream brainstorm conversation with Claude.

    Args:
        session_id: Session ID
        message: User message
        db: Database session

    Returns:
        SSE stream of Claude's response

    Raises:
        HTTPException: If session not found or API key not configured
    """
    # CRITICAL: This log MUST appear if function is called
    logger.warning("=" * 80)
    logger.warning(f"[ENDPOINT] ✨ STREAM ENDPOINT CALLED - SESSION: {session_id}")
    logger.warning(f"[ENDPOINT] MESSAGE: {message[:100]}")
    logger.warning("=" * 80)

    # Verify session exists
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brainstorm session {session_id} not found",
        )

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anthropic API key not configured",
        )

    # Save user message
    user_message = BrainstormMessage(
        id=str(uuid4()),
        session_id=session_id,
        role=MessageRole.USER,
        content=message,
    )
    db.add(user_message)
    await db.commit()
    logger.warning("[CHECKPOINT 1] User message saved to DB")

    # Build conversation history
    messages = [
        {"role": msg.role.value, "content": msg.content} for msg in session.messages
    ]
    messages.append({"role": "user", "content": message})
    logger.warning(f"[CHECKPOINT 2] Built conversation history with {len(messages)} messages")

    # Import async_session_maker at function level to ensure proper DB access
    from app.database import async_session_maker
    logger.warning("[CHECKPOINT 3] Imported async_session_maker")

    # Stream response
    async def event_generator():
        logger.warning("[CHECKPOINT 4] Inside event_generator function")
        """Generate SSE events."""
        assistant_content = ""
        assistant_saved = False

        try:
            logger.warning(f"[CHECKPOINT 4.1] About to create BrainstormingService")
            logger.warning(f"[CHECKPOINT 4.2] API key present: {bool(settings.anthropic_api_key)}")
            logger.warning(f"[CHECKPOINT 4.3] Messages count: {len(messages)}")

            async with BrainstormingService(
                api_key=settings.anthropic_api_key
            ) as brainstorm_service:
                logger.warning(f"[CHECKPOINT 4.4] BrainstormingService context entered")
                logger.warning(f"[CHECKPOINT 4.5] About to call stream_brainstorm_message")
                chunk_count = 0
                async for chunk in brainstorm_service.stream_brainstorm_message(
                    messages
                ):
                    chunk_count += 1
                    assistant_content += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            logger.info(f"[STREAM] Stream completed for session {session_id}, chunks: {chunk_count}, content length: {len(assistant_content)}")

            # Save assistant message using a new database session
            # The original db session is closed after the response is returned
            if assistant_content:
                async with async_session_maker() as save_db:
                    try:
                        assistant_message = BrainstormMessage(
                            id=str(uuid4()),
                            session_id=session_id,
                            role=MessageRole.ASSISTANT,
                            content=assistant_content,
                        )
                        save_db.add(assistant_message)
                        await save_db.commit()
                        assistant_saved = True
                        logger.info(
                            f"✓ Saved assistant message {assistant_message.id} for session {session_id}"
                        )
                    except Exception as save_error:
                        logger.error(
                            f"✗ Failed to save assistant message for session {session_id}: {save_error}",
                            exc_info=True
                        )
                        await save_db.rollback()
                        # Continue anyway to send 'done' event to frontend
            else:
                logger.warning(f"No assistant content to save for session {session_id}")

            # Send done event with save status
            yield f"data: {json.dumps({'type': 'done', 'saved': assistant_saved})}\n\n"
            logger.info(f"Stream completed and done event sent for session {session_id}")

        except Exception as e:
            logger.error(f"[STREAM] ✗ Error streaming brainstorm for session {session_id}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            logger.info(f"[STREAM] Event generator finished for session {session_id}")

    logger.warning("[CHECKPOINT 5] About to return StreamingResponse")
    logger.info(f"[STREAM] Returning StreamingResponse for session {session_id}")

    response = StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
    logger.warning("[CHECKPOINT 6] StreamingResponse created, returning now")
    return response


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
            try:
                response_data = json.loads(full_response)
                blocks = response_data.get("blocks", [])

                # Send blocks incrementally
                for block in blocks:
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "message_id": message_id,
                        "block": block
                    })
                    collected_blocks.append(block)

            except json.JSONDecodeError:
                # Fallback: treat as plain text
                logger.warning("[WS] Claude response not valid JSON, treating as text")
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
