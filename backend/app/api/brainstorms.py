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
)
from app.schemas.brainstorm import (
    BrainstormSessionCreate,
    BrainstormSessionUpdate,
    BrainstormSessionResponse,
)
from app.services.brainstorming_service import BrainstormingService
from app.services.agent_factory import AgentFactory
from app.services.tools_service import ToolsService

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
        title=session_in.title or "New Brainstorm",
        description=session_in.description or "",
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

            # Initialize services for dynamic tools
            tools_service = ToolsService(db)
            agent_factory = AgentFactory(db, tools_service)

            # Main message loop
            while True:
                data = await websocket.receive_json()
                logger.info(f"[WS] Received: {data['type']}")

                if data["type"] == "user_message":
                    await handle_user_message(websocket, db, session_id, data["content"], agent_factory)

                elif data["type"] == "interaction":
                    logger.info(f"[WS] Interaction data received: {data}")
                    block_id = data.get("block_id")
                    value = data.get("value")

                    if not block_id:
                        logger.error(f"[WS] Missing block_id in interaction: {data}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Missing block_id in interaction"
                        })
                        continue

                    await handle_interaction(
                        websocket, db, session_id,
                        block_id, value,
                        agent_factory
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
            except Exception:
                pass


async def handle_user_message(
    websocket: WebSocket,
    db,
    session_id: str,
    content: str,
    agent_factory: AgentFactory
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
    await db.refresh(user_message)
    logger.info("[WS] Saved user message")

    # Send the saved user message back to client
    await websocket.send_json({
        "type": "user_message_saved",
        "message": {
            "id": user_message.id,
            "session_id": user_message.session_id,
            "role": user_message.role,
            "content": user_message.content,
            "created_at": user_message.created_at.isoformat(),
            "updated_at": user_message.updated_at.isoformat()
        }
    })

    # Stream Claude response with dynamic tools
    await stream_claude_response(websocket, db, session_id, agent_factory)


async def handle_interaction(
    websocket: WebSocket,
    db,
    session_id: str,
    block_id: str,
    value: str | list[str],
    agent_factory: AgentFactory
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
    await db.refresh(interaction_message)
    logger.info("[WS] Saved interaction")

    # Send the saved interaction message back to client
    await websocket.send_json({
        "type": "user_message_saved",
        "message": {
            "id": interaction_message.id,
            "session_id": interaction_message.session_id,
            "role": interaction_message.role,
            "content": interaction_message.content,
            "created_at": interaction_message.created_at.isoformat(),
            "updated_at": interaction_message.updated_at.isoformat()
        }
    })

    # Stream Claude response with dynamic tools
    await stream_claude_response(websocket, db, session_id, agent_factory)


async def auto_generate_session_metadata(db, session_id: str, messages: list):
    """Auto-generate title and description based on conversation context.

    Only generates if:
    - Session still has default title ("New Brainstorm")
    - There are at least 2 user messages (enough context)
    """
    # Get session
    result = await db.execute(
        select(BrainstormSession).where(BrainstormSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session or session.title != "New Brainstorm":
        return  # Already has a custom title

    # Count user messages
    user_message_count = sum(1 for msg in messages if msg.role == "user")
    if user_message_count < 2:
        return  # Not enough context yet

    # Extract conversation text
    conversation_summary = []
    for msg in messages[:4]:  # Use first 4 messages for context
        if msg.role == "user":
            for block in msg.content.get("blocks", []):
                if block["type"] == "text":
                    # Defensive: ensure text is a string
                    text_value = block.get("text", "")
                    if isinstance(text_value, dict):
                        text_value = json.dumps(text_value)
                    elif not isinstance(text_value, str):
                        text_value = str(text_value)
                    conversation_summary.append(f"User: {text_value}")
        elif msg.role == "assistant":
            for block in msg.content.get("blocks", []):
                if block["type"] == "text" and "text" in block:
                    # Defensive: ensure text is a string
                    text_value = block.get("text", "")
                    if isinstance(text_value, dict):
                        text_value = json.dumps(text_value)
                    elif not isinstance(text_value, str):
                        text_value = str(text_value)
                    conversation_summary.append(f"Assistant: {text_value[:200]}")

    conversation_text = "\n".join(conversation_summary)

    # Generate title and description using Claude
    try:
        async with BrainstormingService(api_key=settings.anthropic_api_key) as service:
            prompt = f"""Based on this brainstorming conversation, generate a concise title (max 50 chars) and brief description (max 150 chars).

Conversation:
{conversation_text}

Return ONLY a JSON object with this exact format:
{{"title": "...", "description": "..."}}"""

            full_response = ""
            async for chunk in service.stream_brainstorm_message([{"role": "user", "content": prompt}]):
                full_response += chunk

            # Extract JSON
            json_text = extract_json_from_markdown(full_response)
            metadata = json.loads(json_text)

            # Update session
            session.title = metadata.get("title", "New Brainstorm")[:200]
            session.description = metadata.get("description", "")
            await db.commit()

            logger.info(f"[AUTO] Generated metadata for session {session_id}: {session.title}")

    except Exception as e:
        logger.warning(f"[AUTO] Failed to generate metadata: {e}")
        # Not critical, just log and continue


async def stream_claude_response(
    websocket: WebSocket,
    db,
    session_id: str,
    agent_factory: AgentFactory
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
                    # Defensive: ensure text is a string
                    text_value = block.get("text", "")
                    if isinstance(text_value, dict):
                        logger.warning(f"[WS] User message block has dict text: {text_value}")
                        text_value = json.dumps(text_value)
                    elif not isinstance(text_value, str):
                        logger.warning(f"[WS] User message block has non-string text: {type(text_value)}")
                        text_value = str(text_value)
                    text_parts.append(text_value)
                elif block["type"] == "interaction_response":
                    text_parts.append(f"Selected: {block['value']}")
            conversation.append({"role": "user", "content": " ".join(text_parts)})
        else:
            # For assistant, combine all text blocks
            text_parts = []
            for b in msg.content.get("blocks", []):
                if b["type"] == "text" and "text" in b:
                    # Defensive: ensure text is a string
                    text_value = b.get("text", "")
                    if isinstance(text_value, dict):
                        logger.warning(f"[WS] Assistant message block has dict text: {text_value}")
                        text_value = json.dumps(text_value)
                    elif not isinstance(text_value, str):
                        logger.warning(f"[WS] Assistant message block has non-string text: {type(text_value)}")
                        text_value = str(text_value)
                    text_parts.append(text_value)
            if text_parts:
                conversation.append({"role": "assistant", "content": " ".join(text_parts)})

    # Stream from Claude
    message_id = str(uuid4())
    collected_blocks = []

    # Create service with agent factory
    async with BrainstormingService(
        api_key=settings.anthropic_api_key,
        agent_factory=agent_factory,
        agent_name="brainstorm"
    ) as service:
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
                    # Ensure block has an id
                    if "id" not in block:
                        block["id"] = str(uuid4())

                    logger.info(f"[WS] Sending block: type={block.get('type')}, id={block.get('id')}")

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

            # Auto-generate title/description if still default and we have enough context
            await auto_generate_session_metadata(db, session_id, messages + [assistant_message])

            # Signal completion
            await websocket.send_json({
                "type": "stream_complete",
                "message_id": message_id
            })
            logger.info("[WS] Stream complete")

        except Exception as e:
            logger.error(f"[WS] Error streaming: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": f"Streaming error: {str(e)}"
            })
