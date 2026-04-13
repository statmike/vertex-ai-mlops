"""Chat websocket endpoint — proxies to Agent Engine and streams parsed events."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services import agent_engine, history
from ..services.event_parser import parse_event

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_ws(ws: WebSocket):
    """Websocket endpoint for chat interaction.

    Client sends: { "message": "...", "session_id": "..." }
    Server streams: parsed event dicts (type: transfer|thinking|text|data|chart|error)

    If no session_id is provided, a new session is created automatically.
    """
    await ws.accept()
    user_id = "ui_user"
    session_id = None

    try:
        while True:
            raw = await ws.receive_text()
            payload = json.loads(raw)
            message = payload.get("message", "").strip()

            if not message:
                await ws.send_json({"type": "error", "content": "Empty message"})
                continue

            # Create session on first message if needed
            if not session_id:
                session_id = payload.get("session_id")
            if not session_id:
                session = await agent_engine.create_session(user_id=user_id)
                session_id = session.get("id") or session.get("session_id", "")
                await ws.send_json({
                    "type": "status",
                    "content": "Session created",
                    "session_id": session_id,
                })

            # Store question in history for backfill
            history.append(session_id, {
                "type": "question", "content": message,
            }, source="text")

            # Signal query start
            await ws.send_json({
                "type": "status",
                "content": "Processing...",
                "session_id": session_id,
            })

            # Stream events from agent
            try:
                event_idx = 0
                async for raw_event in agent_engine.stream_query(
                    user_id=user_id,
                    session_id=session_id,
                    message=message,
                ):
                    event_idx += 1
                    parsed_events = parse_event(raw_event)
                    if parsed_events:
                        types = [e.get("type") for e in parsed_events]
                        logger.info("Event #%d → %s", event_idx, types)
                        for e in parsed_events:
                            if e.get("type") == "thinking":
                                logger.info(
                                    "  tool=%s args=%s",
                                    e.get("tool"), e.get("args"),
                                )
                            elif e.get("type") == "text":
                                logger.info(
                                    "  text: %.200s",
                                    e.get("content", ""),
                                )
                            elif e.get("type") == "transfer":
                                logger.info(
                                    "  transfer → %s",
                                    e.get("to", ""),
                                )
                    for event in parsed_events:
                        history.append(session_id, event, source="text")
                        await ws.send_json(event)

                # Signal query complete
                history.append(session_id, {
                    "type": "status", "content": "done",
                }, source="text")
                await ws.send_json({"type": "status", "content": "done"})

            except Exception as e:
                logger.error("Agent Engine error: %s", e, exc_info=True)
                await ws.send_json({
                    "type": "error",
                    "content": f"Agent error: {e}",
                })

    except WebSocketDisconnect:
        logger.info("Client disconnected (session: %s)", session_id)
    except Exception as e:
        logger.error("WebSocket error: %s", e, exc_info=True)
