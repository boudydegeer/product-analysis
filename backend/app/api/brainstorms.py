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
from app.models.codebase_exploration import CodebaseExploration, CodebaseExplorationStatus
from app.schemas.brainstorm import (
    BrainstormSessionCreate,
    BrainstormSessionUpdate,
    BrainstormSessionResponse,
)
from app.services.brainstorming_service import BrainstormingService
from app.services.codebase_exploration_service import CodebaseExplorationService

logger = logging.getLogger(__name__)
logger.warning("*" * 60)
logger.warning("🔥 BRAINSTORMS.PY LOADED - VERSION 3.0 WITH FULL LOGGING")
logger.warning("*" * 60)

router = APIRouter(prefix="/api/v1/brainstorms", tags=["brainstorms"])


def extract_json_from_markdown(text: str) -> str:
    """Extract JSON from markdown code blocks or raw JSON in text.

    Args:
        text: Text that may contain JSON in markdown code blocks or as raw JSON

    Returns:
        Extracted JSON string or original text if no JSON found
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

    # Try to find raw JSON object with "blocks" array (not in code blocks)
    # This handles cases where Claude outputs text before the JSON
    # Pattern: find { then "blocks" with any content until the final closing }
    raw_json_pattern = r'(\{[^{}]*"blocks"[^{}]*\:[\s\S]*\][\s\S]*\})'
    match = re.search(raw_json_pattern, text, re.MULTILINE | re.DOTALL)

    if match:
        return match.group(1)

    # Return as-is if no JSON found
    return text


def normalize_block(block: dict) -> dict:
    """Normalize block structure for frontend compatibility.

    Converts Claude's 'content' property to 'text' for text blocks,
    as the frontend expects 'text' property.

    Args:
        block: Block dictionary from Claude's response

    Returns:
        Normalized block with 'text' property for text blocks
    """
    if block.get("type") == "text":
        # Convert 'content' to 'text' if present
        if "content" in block and "text" not in block:
            block["text"] = block.pop("content")
        # Ensure text is a string
        if "text" in block and not isinstance(block["text"], str):
            block["text"] = str(block["text"])
    return block


async def handle_tool_call(
    tool_name: str,
    tool_input: dict,
    session_id: str,
    message_id: str,
    db: AsyncSession,
    websocket: WebSocket
) -> dict:
    """Dispatch tool calls to appropriate handlers.

    Args:
        tool_name: Name of the tool being called.
        tool_input: Input parameters for the tool.
        session_id: ID of the brainstorming session.
        message_id: ID of the message that triggered the tool call.
        db: Database session.
        websocket: WebSocket connection for sending status updates.

    Returns:
        Dict containing tool execution result.
    """
    if tool_name == "explore_codebase":
        return await handle_explore_codebase(
            tool_input, session_id, message_id, db, websocket
        )
    # Add more tool handlers here as needed
    return {"error": f"Unknown tool: {tool_name}"}


async def handle_explore_codebase(
    tool_input: dict,
    session_id: str,
    message_id: str,
    db: AsyncSession,
    websocket: WebSocket
) -> dict:
    """Handle explore_codebase tool call.

    Creates an exploration record, triggers the GitHub workflow, and sends
    status updates via WebSocket.

    Args:
        tool_input: Input parameters containing query, scope, and focus.
        session_id: ID of the brainstorming session.
        message_id: ID of the message that triggered the exploration.
        db: Database session.
        websocket: WebSocket connection for sending status updates.

    Returns:
        Dict containing exploration_id, status, and message.
    """
    exploration_service = CodebaseExplorationService()

    # Generate exploration ID
    exploration_id = exploration_service.generate_exploration_id()

    # Create exploration record
    exploration = CodebaseExploration(
        id=exploration_id,
        session_id=session_id,
        message_id=message_id,
        query=tool_input.get("query", ""),
        scope=tool_input.get("scope", "full"),
        focus=tool_input.get("focus", "patterns"),
        status=CodebaseExplorationStatus.PENDING
    )
    db.add(exploration)
    await db.commit()

    # Trigger GitHub workflow
    try:
        result = await exploration_service.trigger_exploration(
            db=db,
            exploration_id=exploration_id,
            query=tool_input.get("query", ""),
            scope=tool_input.get("scope", "full"),
            focus=tool_input.get("focus", "patterns"),
            session_id=session_id,
            message_id=message_id
        )

        # Update exploration with workflow info
        # workflow_run_id from GitHub is an integer, but the DB column expects a string
        workflow_run_id = result.get("workflow_run_id")
        exploration.workflow_run_id = str(workflow_run_id) if workflow_run_id is not None else None
        exploration.workflow_url = result.get("workflow_url")
        exploration.status = CodebaseExplorationStatus.INVESTIGATING
        await db.commit()

        # Send WebSocket message to frontend
        await websocket.send_json({
            "type": "tool_executing",
            "tool_name": "explore_codebase",
            "exploration_id": exploration_id,
            "status": "investigating",
            "message": "Investigating codebase..."
        })

        logger.info(
            f"[TOOL] Started codebase exploration: {exploration_id}, "
            f"workflow_run_id={result.get('workflow_run_id')}"
        )

        return {
            "exploration_id": exploration_id,
            "status": "investigating",
            "message": "Codebase exploration started. Results will be available shortly."
        }
    except Exception as e:
        exploration.status = CodebaseExplorationStatus.FAILED
        exploration.error_message = str(e)
        await db.commit()

        logger.error(f"[TOOL] Codebase exploration failed: {exploration_id}, error={e}")

        return {"error": str(e)}


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

            # Main message loop
            while True:
                data = await websocket.receive_json()
                logger.info(f"[WS] Received: {data['type']}")

                if data["type"] == "user_message":
                    await handle_user_message(websocket, db, session_id, data["content"])

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

    # Stream Claude response
    await stream_claude_response(websocket, db, session_id)


async def handle_interaction(
    websocket: WebSocket,
    db,
    session_id: str,
    block_id: str,
    value: str | list[str],
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

    # Stream Claude response
    await stream_claude_response(websocket, db, session_id)


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

    logger.warning(f"[WS] 🔍 Before conversation_summary join - type: {type(conversation_summary)}, length: {len(conversation_summary)}")
    for i, part in enumerate(conversation_summary):
        logger.warning(f"[WS] 🔍 conversation_summary[{i}] type={type(part)}, value={repr(part)[:200]}")
    conversation_text = "\n".join(conversation_summary)
    logger.warning("[WS] Conversation summary joined successfully")

    # Generate title and description using Claude
    try:
        async with BrainstormingService(
            api_key=settings.anthropic_api_key,
            db=db
        ) as service:
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
):
    """Stream Claude's response block-by-block."""
    # Get conversation history
    result = await db.execute(
        select(BrainstormMessage)
        .where(BrainstormMessage.session_id == session_id)
        .order_by(BrainstormMessage.created_at)
    )
    messages = result.scalars().all()

    logger.warning(f"[WS] 🔍 Retrieved {len(messages)} messages from DB")
    for i, msg in enumerate(messages):
        logger.warning(f"[WS] 🔍 Message {i}: role={msg.role}, content type={type(msg.content)}, content={repr(msg.content)[:300]}")

    # Convert to format for Claude
    conversation = []
    for msg in messages:
        if msg.role == "user":
            # Extract text from blocks
            text_parts = []
            logger.warning(f"[WS] 🔍 Processing user message with {len(msg.content.get('blocks', []))} blocks")
            for i, block in enumerate(msg.content.get("blocks", [])):
                logger.warning(f"[WS] 🔍 Block {i}: type={block.get('type')}, keys={list(block.keys())}, full={repr(block)[:200]}")
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
                    value = block.get('value', '')
                    # Ensure value is a string
                    if isinstance(value, list):
                        value = ', '.join(str(v) for v in value)
                    elif not isinstance(value, str):
                        value = str(value)
                    text_parts.append(f"Selected: {value}")

            # Final safety check: ensure all items in text_parts are strings
            logger.warning(f"[WS] 🔍 Before user text_parts join - type: {type(text_parts)}, length: {len(text_parts)}")
            for i, part in enumerate(text_parts):
                logger.warning(f"[WS] 🔍 text_parts[{i}] type={type(part)}, value={repr(part)[:200]}")
            text_parts = [str(part) if not isinstance(part, str) else part for part in text_parts]
            logger.warning(f"[WS] 🔍 After conversion - text_parts types: {[type(p) for p in text_parts]}")
            joined_content = " ".join(text_parts)
            logger.warning(f"[WS] ✅ User content joined successfully: {joined_content[:100]}")
            conversation.append({"role": "user", "content": joined_content})
        else:
            # For assistant, combine all text blocks
            text_parts = []
            logger.warning(f"[WS] 🔍 Processing assistant message with {len(msg.content.get('blocks', []))} blocks")
            for i, b in enumerate(msg.content.get("blocks", [])):
                logger.warning(f"[WS] 🔍 Block {i}: type={b.get('type')}, keys={list(b.keys())}, full={repr(b)[:200]}")
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

            # Final safety check: ensure all items in text_parts are strings
            logger.warning(f"[WS] 🔍 Before assistant text_parts join - type: {type(text_parts)}, length: {len(text_parts)}")
            for i, part in enumerate(text_parts):
                logger.warning(f"[WS] 🔍 text_parts[{i}] type={type(part)}, value={repr(part)[:200]}")
            text_parts = [str(part) if not isinstance(part, str) else part for part in text_parts]
            logger.warning(f"[WS] 🔍 After conversion - text_parts types: {[type(p) for p in text_parts]}")
            if text_parts:
                joined_content = " ".join(text_parts)
                logger.warning(f"[WS] ✅ Assistant content joined successfully: {joined_content[:100]}")
                conversation.append({"role": "assistant", "content": joined_content})

    # Stream from Claude
    message_id = str(uuid4())
    collected_blocks = []

    # Create service with database session for tool loading
    async with BrainstormingService(
        api_key=settings.anthropic_api_key,
        db=db,
        agent_name="brainstorm"
    ) as service:
        try:
            # Use the new stream_with_tool_detection for tool handling
            full_response = ""

            # Guard: Track if we've already triggered a tool for this response
            # to prevent duplicate workflow triggers
            tool_already_triggered = False

            async for chunk in service.stream_with_tool_detection(conversation):
                if chunk.type == "text" and chunk.content:
                    full_response += chunk.content
                elif chunk.type == "tool_use" and chunk.tool_use:
                    # Claude wants to use a tool
                    tool_req = chunk.tool_use
                    logger.warning(
                        f"[WS] Tool use detected: {tool_req.tool_name}, "
                        f"id={tool_req.tool_id}, input={tool_req.tool_input}"
                    )

                    # Guard: Skip if we've already triggered a tool for this response
                    if tool_already_triggered:
                        logger.warning(
                            f"[WS] Skipping duplicate tool trigger for {tool_req.tool_name} "
                            f"(already triggered for this response)"
                        )
                        continue

                    if tool_req.tool_name == "explore_codebase":
                        tool_already_triggered = True

                        # Notify frontend about tool execution
                        await websocket.send_json({
                            "type": "tool_executing",
                            "tool_name": "explore_codebase",
                            "tool_id": tool_req.tool_id,
                            "status": "started",
                            "message": "Investigating codebase..."
                        })

                        # Execute the tool
                        tool_result = await handle_tool_call(
                            tool_name=tool_req.tool_name,
                            tool_input=tool_req.tool_input,
                            session_id=session_id,
                            message_id=message_id,
                            db=db,
                            websocket=websocket
                        )

                        logger.warning(f"[WS] Tool result: {tool_result}")

                        # Continue conversation with tool result
                        # Note: For async tools like explore_codebase, the result
                        # contains exploration_id and status, not actual findings.
                        # The actual results come via webhook/polling later.
                        # For now, we'll inform Claude about the initiated exploration.

                        tool_continuation = ""
                        async for cont_chunk in service.continue_with_tool_result(
                            tool_id=tool_req.tool_id,
                            tool_result=tool_result
                        ):
                            if cont_chunk.type == "text" and cont_chunk.content:
                                tool_continuation += cont_chunk.content
                            elif cont_chunk.type == "tool_use":
                                # Nested tool use - log but don't handle recursively for now
                                logger.warning(
                                    f"[WS] Nested tool use detected: {cont_chunk.tool_use}"
                                )

                        if tool_continuation:
                            full_response = tool_continuation
                    else:
                        logger.warning(f"[WS] Unknown tool: {tool_req.tool_name}")

                elif chunk.type == "complete":
                    logger.info("[WS] Stream complete signal received")
                    break

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

                    # Normalize block structure for frontend compatibility
                    block = normalize_block(block)

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
