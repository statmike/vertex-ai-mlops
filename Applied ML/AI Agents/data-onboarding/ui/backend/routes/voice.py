"""Voice WebSocket endpoint — bidirectional audio streaming via ADK Live API.

Client sends:
    Binary frames — raw PCM audio (Int16, 16kHz, mono)
    JSON text     — {"type": "start"/"stop"/"text"/"init", ...}

Server sends:
    Binary frames — PCM audio response chunks from the model
    JSON text     — transcripts, thinking steps, text_event (for text panel),
                    voice_question, status updates
"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.genai import types

from ..services import agent_engine, history
from ..services.event_parser import parse_event

logger = logging.getLogger(__name__)

router = APIRouter()

AUDIO_MIME = "audio/pcm;rate=16000"


@router.websocket("/ws/voice")
async def voice_ws(ws: WebSocket):
    """Bidirectional voice streaming endpoint.

    1. On connect: create voice session, wait for shared session ID
    2. Receive loop: forward audio/commands from browser to LiveRequestQueue
    3. Send loop: forward audio/events from agent to browser
    4. Text event loop: forward parsed agent_chat events to text panel
    5. On disconnect: clean up queues
    """
    await ws.accept()
    user_id = "ui_user"

    # Import here to avoid loading ADK at module level
    from google.adk.agents.live_request_queue import LiveRequestQueue

    live_queue = LiveRequestQueue()
    session_id = None
    shared_session_id = None

    try:
        # Create voice session locally (voice runner is always local via run_live)
        session = await agent_engine.create_voice_session(user_id=user_id)
        session_id = session.get("id") or session.get("session_id", "")
        await ws.send_json({
            "type": "status",
            "content": "Voice session ready",
            "session_id": session_id,
        })
        logger.info("Voice session created: %s", session_id)

        # Wait for init message with shared session ID
        try:
            init_raw = await asyncio.wait_for(ws.receive_text(), timeout=10.0)
            init_msg = json.loads(init_raw)
            if init_msg.get("type") == "init":
                shared_session_id = init_msg.get("session_id", "")
                logger.info(
                    "Voice WS: shared session = %s", shared_session_id
                )
        except (asyncio.TimeoutError, json.JSONDecodeError):
            logger.warning("Voice WS: no init message received, proceeding without shared session")

        # Seed voice session state with the shared session ID so the bridge
        # tool reuses the same agent_chat session as the text route.
        if shared_session_id:
            await _seed_voice_session_state(
                user_id, session_id, shared_session_id,
            )

        # Register event queue and set shared session ID on bridge tool
        event_queue = None
        text_event_task = None
        if shared_session_id:
            from agent_voice.tools.function_tool_ask_data import (
                init_bridge, register_event_queue,
            )
            # Set the shared session ID and history getter so the bridge
            # tool can look up prior answers from the text chat
            init_bridge(
                shared_session_id=shared_session_id,
                history_getter=history.get_all,
            )
            event_queue = register_event_queue(shared_session_id)
            text_event_task = asyncio.create_task(
                _text_event_loop(ws, shared_session_id, event_queue)
            )

        # Start the agent live loop as a background task
        send_task = asyncio.create_task(
            _send_loop(ws, user_id, session_id, live_queue, shared_session_id)
        )

        # Receive loop — runs until disconnect
        try:
            await _receive_loop(ws, live_queue)
        finally:
            live_queue.close()
            send_task.cancel()
            if text_event_task:
                text_event_task.cancel()
            try:
                await send_task
            except asyncio.CancelledError:
                pass
            if text_event_task:
                try:
                    await text_event_task
                except asyncio.CancelledError:
                    pass

    except WebSocketDisconnect:
        logger.info("Voice client disconnected (session: %s)", session_id)
    except Exception as e:
        logger.error("Voice WebSocket error: %s", e, exc_info=True)
    finally:
        live_queue.close()
        # Clean up event queue
        if shared_session_id:
            from agent_voice.tools.function_tool_ask_data import unregister_event_queue
            unregister_event_queue(shared_session_id)


async def _seed_voice_session_state(user_id, session_id, shared_session_id):
    """Seed the voice session state so bridge tool finds the shared session ID.

    Voice sessions are always local (InMemorySessionService) regardless of
    AGENT_MODE, so we can seed state directly.
    """
    try:
        from ..services.agent_engine import _session_service, _APP_NAME
        if _session_service:
            session = await _session_service.get_session(
                app_name=_APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            if session:
                session.state["text_session_id"] = shared_session_id
                logger.info(
                    "Seeded voice session %s with text_session_id=%s",
                    session_id, shared_session_id,
                )
    except Exception as e:
        logger.warning("Failed to seed voice session state: %s", e)


async def _receive_loop(ws: WebSocket, live_queue):
    """Read frames from the browser and forward to the agent."""
    while True:
        msg = await ws.receive()

        if msg["type"] == "websocket.disconnect":
            break

        # Binary frame — raw PCM audio
        if "bytes" in msg and msg["bytes"]:
            audio_blob = types.Blob(
                data=msg["bytes"],
                mime_type=AUDIO_MIME,
            )
            live_queue.send_realtime(audio_blob)

        # Text frame — JSON command
        elif "text" in msg and msg["text"]:
            try:
                cmd = json.loads(msg["text"])
                cmd_type = cmd.get("type", "")

                if cmd_type == "start":
                    live_queue.send_activity_start()
                elif cmd_type == "stop":
                    live_queue.send_activity_end()
                elif cmd_type == "text":
                    # Text message fallback (e.g., typed in voice mode)
                    text = cmd.get("message", "").strip()
                    if text:
                        content = types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=text)],
                        )
                        live_queue.send_content(content)
                elif cmd_type == "close":
                    break
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid voice command: %s", msg["text"][:200])


async def _send_loop(
    ws: WebSocket, user_id: str, session_id: str, live_queue,
    shared_session_id: str | None = None,
):
    """Read events from the agent and forward to the browser."""
    try:
        async for event in agent_engine.stream_live(
            user_id=user_id,
            session_id=session_id,
            live_request_queue=live_queue,
        ):
            try:
                await _forward_event(ws, event, shared_session_id)
            except Exception as e:
                logger.warning("Error forwarding event: %s", e)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error("Voice send loop error: %s", e, exc_info=True)
        try:
            await ws.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass


async def _forward_event(ws: WebSocket, event, shared_session_id=None):
    """Convert an ADK Event into WebSocket frames for the browser."""

    # Audio blobs — send as binary frames
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.inline_data and part.inline_data.data:
                if "audio" in (part.inline_data.mime_type or ""):
                    await ws.send_bytes(part.inline_data.data)

    # Input transcription (what the user said)
    if event.input_transcription and event.input_transcription.text:
        await ws.send_json({
            "type": "transcript_in",
            "text": event.input_transcription.text,
            "partial": getattr(event, "partial", False) or False,
        })

    # Output transcription (what the agent said)
    if event.output_transcription and event.output_transcription.text:
        await ws.send_json({
            "type": "transcript_out",
            "text": event.output_transcription.text,
            "partial": getattr(event, "partial", False) or False,
        })

    # Function calls — thinking indicators + voice_question for text panel
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.function_call:
                tool_name = part.function_call.name
                await ws.send_json({
                    "type": "thinking",
                    "tool": tool_name,
                    "label": _tool_label(tool_name),
                })

                # When ask_data_question is called, send the question
                # to the frontend so the text panel can create an entry
                if tool_name == "ask_data_question" and shared_session_id:
                    question = ""
                    args = part.function_call.args
                    if args:
                        question = (
                            args.get("question", "")
                            if hasattr(args, "get")
                            else str(args)
                        )
                    if question:
                        # Store question in history for backfill
                        history.append(shared_session_id, {
                            "type": "question",
                            "content": question,
                        }, source="voice")
                        await ws.send_json({
                            "type": "voice_question",
                            "question": question,
                        })

    # Turn complete
    if event.turn_complete:
        await ws.send_json({"type": "turn_complete"})

    # Interrupted (user spoke over the agent)
    if event.interrupted:
        await ws.send_json({"type": "interrupted"})


async def _text_event_loop(
    ws: WebSocket,
    shared_session_id: str,
    queue: asyncio.Queue,
):
    """Read raw agent_chat events from the bridge tool's queue, parse them,
    store in history, and forward to the frontend as text_event messages."""
    try:
        while True:
            raw_event = await queue.get()

            # None signals end of a question's event stream
            if raw_event is None:
                # Send a synthetic "done" for the text panel
                done_event = {"type": "status", "content": "done"}
                history.append(shared_session_id, done_event, source="voice")
                await ws.send_json({
                    "type": "text_event",
                    "event": done_event,
                })
                continue

            # Parse raw event into frontend event types
            try:
                parsed_events = parse_event(raw_event)
            except Exception as e:
                logger.warning("Text event parse error: %s", e)
                continue

            for event in parsed_events:
                history.append(shared_session_id, event, source="voice")
                try:
                    await ws.send_json({
                        "type": "text_event",
                        "event": event,
                    })
                except Exception:
                    return

    except asyncio.CancelledError:
        return
    except Exception as e:
        logger.error("Text event loop error: %s", e, exc_info=True)


def _tool_label(tool_name: str) -> str:
    """Human-readable label for a tool call."""
    labels = {
        "ask_data_question": "Querying the data system...",
        "rerank_tables": "Finding relevant tables...",
        "conversational_chat": "Analyzing data...",
        "meta_chat": "Checking pipeline metadata...",
        "search_context": "Searching documentation...",
        "get_table_columns": "Looking up column details...",
        "list_all_tables": "Listing available tables...",
    }
    return labels.get(tool_name, f"Running {tool_name}...")
