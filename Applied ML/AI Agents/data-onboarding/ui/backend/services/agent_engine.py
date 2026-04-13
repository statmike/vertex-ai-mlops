"""Agent client — proxies chat queries to either a local ADK runner or Agent Engine.

Controlled by AGENT_MODE env var:
    "local"        — imports root_agent directly, runs via ADK Runner
    "agent_engine" — calls the deployed agent via Vertex AI SDK

Voice mode uses the same agent with Runner.run_live() for bidirectional
audio streaming via the Gemini Live API.
"""

import logging
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

from ..config import AGENT_MODE, VOICE_MODEL

logger = logging.getLogger(__name__)

# Add the project root so agent_chat/agent_convo/agent_voice are importable.
# This must happen at module level — before any lazy init — because the voice
# route imports from agent_voice at call time, not just at runner init time.
_project_root = Path(__file__).resolve().parents[3]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# ---------------------------------------------------------------------------
# Local mode — ADK Runner
# ---------------------------------------------------------------------------

_runner = None
_voice_runner = None
_session_service = None
_APP_NAME = "data_onboarding_chat"


def _get_runner():
    """Lazy-initialize the ADK Runner and InMemorySessionService."""
    global _runner, _session_service
    if _runner is None:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        from agent_chat.agent import root_agent

        if _session_service is None:
            _session_service = InMemorySessionService()
        _runner = Runner(
            agent=root_agent,
            app_name=_APP_NAME,
            session_service=_session_service,
        )
        logger.info("ADK Runner initialized (local mode)")
    return _runner


def _event_to_dict(event) -> dict:
    """Normalize an ADK Event object to the dict format the parser expects."""
    result = {
        "author": event.author,
    }

    # Actions — transfer, state_delta, artifact_delta
    if event.actions:
        actions = {}
        if event.actions.transfer_to_agent:
            actions["transfer_to_agent"] = event.actions.transfer_to_agent
        if event.actions.state_delta:
            actions["state_delta"] = dict(event.actions.state_delta)
        if event.actions.artifact_delta:
            actions["artifact_delta"] = dict(event.actions.artifact_delta)
        if actions:
            result["actions"] = actions

    # Content — role + parts (text, function_call, function_response)
    if event.content:
        content = {"role": event.content.role or ""}
        parts = []
        for part in (event.content.parts or []):
            p = {}
            if part.text is not None:
                p["text"] = part.text
            if part.function_call:
                p["functionCall"] = {
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args or {}),
                }
            if part.function_response:
                resp = part.function_response.response or {}
                p["functionResponse"] = {
                    "name": part.function_response.name,
                    "response": dict(resp) if hasattr(resp, 'items') else {"result": resp},
                }
            if p:
                parts.append(p)
        content["parts"] = parts
        result["content"] = content

    return result


async def create_voice_session(user_id: str) -> dict:
    """Create a session for the voice runner (always local).

    The voice runner uses run_live() which only works locally, so its
    sessions must live in the local InMemorySessionService regardless
    of AGENT_MODE.
    """
    global _session_service
    if _session_service is None:
        from google.adk.sessions import InMemorySessionService
        _session_service = InMemorySessionService()
    session = await _session_service.create_session(
        app_name=_APP_NAME, user_id=user_id,
    )
    return {"id": session.id}


async def _local_create_session(user_id: str) -> dict:
    runner = _get_runner()
    session = await _session_service.create_session(
        app_name=_APP_NAME, user_id=user_id,
    )
    return {"id": session.id}


async def _local_list_sessions(user_id: str) -> list[dict]:
    await _get_runner()  # ensure initialized
    result = await _session_service.list_sessions(
        app_name=_APP_NAME, user_id=user_id,
    )
    return [{"id": s.id} for s in (result.sessions if result.sessions else [])]


async def _local_delete_session(user_id: str, session_id: str) -> None:
    await _get_runner()  # ensure initialized
    await _session_service.delete_session(
        app_name=_APP_NAME, user_id=user_id, session_id=session_id,
    )


async def _local_stream_query(
    user_id: str, session_id: str, message: str,
) -> AsyncGenerator[dict, None]:
    from google.genai import types

    runner = _get_runner()
    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=message)],
    )
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        yield _event_to_dict(event)


# ---------------------------------------------------------------------------
# Local mode — Voice (Live API)
# ---------------------------------------------------------------------------


def _get_voice_runner():
    """Lazy-initialize a Runner for voice mode using agent_voice.

    agent_voice is a standalone agent with a single tool (ask_data_question)
    that bridges to agent_chat via text-mode Runner internally. This avoids
    cloning the entire agent_chat tree and patching it for the live model's
    context window.

    In local mode: injects the shared text Runner and session service into
    the bridge tool so voice and text modes share the same agent_chat session.

    In agent_engine mode: only initializes the session service (no local text
    runner needed — the bridge tool calls the deployed VAE agent directly).
    """
    global _voice_runner, _session_service
    if _voice_runner is None:
        from google.adk.models.google_llm import Gemini
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        from agent_voice.tools.function_tool_ask_data import init_bridge

        if AGENT_MODE == "local":
            # Local mode: initialize text runner and share with bridge tool
            _get_runner()
            init_bridge(
                runner=_runner,
                session_service=_session_service,
                app_name=_APP_NAME,
            )
        else:
            # Agent Engine mode: only need a session service for voice sessions.
            # The bridge tool will call the deployed VAE agent via _run_remote().
            # Share the remote agent handle to avoid aiohttp connector issues
            # when the bridge creates its own vertexai.Client inside run_live().
            if _session_service is None:
                _session_service = InMemorySessionService()
            init_bridge(
                session_service=_session_service,
                app_name=_APP_NAME,
                remote_agent=_get_agent(),
            )

        from agent_voice.agent import root_agent as voice_agent

        voice_root = voice_agent.clone(
            update={"model": Gemini(model=VOICE_MODEL)},
        )
        _voice_runner = Runner(
            agent=voice_root,
            app_name=_APP_NAME,
            session_service=_session_service,
        )
        logger.info("Voice Runner initialized (model=%s, mode=%s)", VOICE_MODEL, AGENT_MODE)
    return _voice_runner


async def _local_stream_live(user_id, session_id, live_request_queue):
    """Run the agent in live mode, yielding raw Event objects."""
    from google.adk.agents.run_config import RunConfig
    from google.genai import types

    runner = _get_voice_runner()

    run_config = RunConfig(
        response_modalities=["AUDIO"],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )

    async for event in runner.run_live(
        user_id=user_id,
        session_id=session_id,
        live_request_queue=live_request_queue,
        run_config=run_config,
    ):
        yield event


# ---------------------------------------------------------------------------
# Agent Engine mode — Vertex AI SDK
# ---------------------------------------------------------------------------

_client = None
_agent = None


def _get_agent():
    """Lazy-initialize the Vertex AI client and agent handle."""
    global _client, _agent
    if _agent is None:
        import vertexai
        from ..config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT, get_resource_name

        vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
        _client = vertexai.Client(
            project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION,
        )
        _agent = _client.agent_engines.get(name=get_resource_name())
        logger.info("Connected to Agent Engine: %s", get_resource_name())
    return _agent


async def _remote_create_session(user_id: str) -> dict:
    agent = _get_agent()
    session = await agent.async_create_session(user_id=user_id)
    return session


async def _remote_list_sessions(user_id: str) -> list[dict]:
    agent = _get_agent()
    result = await agent.async_list_sessions(user_id=user_id)
    return [{"id": s.id} for s in result.sessions] if result.sessions else []


async def _remote_delete_session(user_id: str, session_id: str) -> None:
    agent = _get_agent()
    await agent.async_delete_session(user_id=user_id, session_id=session_id)


async def _remote_stream_query(
    user_id: str, session_id: str, message: str,
) -> AsyncGenerator[dict, None]:
    agent = _get_agent()
    async for event in agent.async_stream_query(
        user_id=user_id, session_id=session_id, message=message,
    ):
        yield event


# ---------------------------------------------------------------------------
# Public interface — delegates based on AGENT_MODE
# ---------------------------------------------------------------------------

async def create_session(user_id: str) -> dict:
    if AGENT_MODE == "local":
        return await _local_create_session(user_id)
    return await _remote_create_session(user_id)


async def list_sessions(user_id: str) -> list[dict]:
    if AGENT_MODE == "local":
        return await _local_list_sessions(user_id)
    return await _remote_list_sessions(user_id)


async def delete_session(user_id: str, session_id: str) -> None:
    if AGENT_MODE == "local":
        return await _local_delete_session(user_id, session_id)
    return await _remote_delete_session(user_id, session_id)


async def stream_query(
    user_id: str, session_id: str, message: str,
) -> AsyncGenerator[dict, None]:
    if AGENT_MODE == "local":
        async for event in _local_stream_query(user_id, session_id, message):
            yield event
    else:
        async for event in _remote_stream_query(user_id, session_id, message):
            yield event


async def stream_live(user_id, session_id, live_request_queue):
    """Run the agent in live (voice) mode. Local mode only.

    Yields raw ADK Event objects for the voice WebSocket route to handle.
    """
    async for event in _local_stream_live(
        user_id, session_id, live_request_queue,
    ):
        yield event
