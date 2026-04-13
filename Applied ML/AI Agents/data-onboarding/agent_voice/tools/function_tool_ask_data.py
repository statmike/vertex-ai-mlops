"""Bridge tool — delegates data questions to agent_chat.

Supports two modes controlled by ``AGENT_MODE`` env var:

- **local** (default): imports agent_chat directly, runs via ADK Runner
- **agent_engine**: calls the deployed agent_chat on Vertex AI Agent Engine

Both modes return a voice-ready summary for the live model to narrate.
When an event queue is registered (by the voice route), raw events are
pushed to it in real-time for the text panel to render.

Cross-channel awareness: before calling agent_chat, checks the shared
history store for prior answers (from text or voice) to avoid redundant
round-trips for questions already answered in the session.
"""

import asyncio
import logging
import os

from google.adk import tools

logger = logging.getLogger(__name__)

# Mode: "local" (ADK Runner) or "agent_engine" (deployed on VAE)
_AGENT_MODE = os.environ.get("AGENT_MODE", "local")

# Lazy-initialized backends
_runner = None
_session_service = None
_remote_agent = None
_APP_NAME = "agent_voice_bridge"
_shared_session_id = None  # Set by init_bridge() for session sharing
_history_getter = None     # Callable(session_id) → list[dict], set by init_bridge()

# Lightweight model for voice summarization (simple task, no thinking needed)
_SUMMARY_MODEL = os.environ.get("VOICE_SUMMARY_MODEL", "gemini-2.5-flash-lite")

# Cached genai client for summarization
_genai_client = None

# ---------------------------------------------------------------------------
# Event queue registry — voice route registers a queue per shared session
# so raw agent_chat events can stream to the text panel in real-time.
# ---------------------------------------------------------------------------

_event_queues: dict[str, asyncio.Queue] = {}


def register_event_queue(text_session_id: str) -> asyncio.Queue:
    """Register and return an event queue for a shared session."""
    q: asyncio.Queue = asyncio.Queue()
    _event_queues[text_session_id] = q
    logger.info("Event queue registered for session: %s", text_session_id)
    return q


def unregister_event_queue(text_session_id: str) -> None:
    """Remove the event queue for a session."""
    _event_queues.pop(text_session_id, None)
    logger.info("Event queue unregistered for session: %s", text_session_id)


# ---------------------------------------------------------------------------
# Bridge initialization — called by agent_engine.py to share runner/sessions
# ---------------------------------------------------------------------------


def init_bridge(runner=None, session_service=None, app_name=None,
                remote_agent=None, shared_session_id=None,
                history_getter=None):
    """Inject shared resources so the bridge tool reuses existing connections.

    Called by agent_engine.py so the bridge tool shares:
    - Local mode: the same Runner and InMemorySessionService as text chat
    - Agent Engine mode: the same remote agent handle (avoids aiohttp issues)
    - Both modes: the shared session ID for event queue routing
    - history_getter: callable(session_id) → list[dict] for cross-channel lookup
    """
    global _runner, _session_service, _APP_NAME, _remote_agent, _shared_session_id
    global _history_getter
    if runner is not None:
        _runner = runner
        logger.info("Bridge: using shared text Runner")
    if session_service is not None:
        _session_service = session_service
        logger.info("Bridge: using shared session service")
    if app_name is not None:
        _APP_NAME = app_name
    if remote_agent is not None:
        _remote_agent = remote_agent
        logger.info("Bridge: using shared remote agent handle")
    if shared_session_id is not None:
        _shared_session_id = shared_session_id
        logger.info("Bridge: using shared session ID: %s", shared_session_id)
    if history_getter is not None:
        _history_getter = history_getter
        logger.info("Bridge: cross-channel history lookup enabled")


# ---------------------------------------------------------------------------
# Event conversion — ADK Event objects → dicts for the event queue
# ---------------------------------------------------------------------------


def _check_shared_history(question_lower: str) -> str | None:
    """Check the shared history store for a prior answer to this question.

    Scans the history for the shared session to find question→answer pairs.
    If the same question was already asked (via text or voice), returns the
    full text answer without re-running agent_chat.

    Uses the history_getter injected via init_bridge() to avoid cross-layer
    import issues.
    """
    if not _shared_session_id or not _history_getter:
        return None

    try:
        events = _history_getter(_shared_session_id)
        if not events:
            return None

        # Walk through events looking for question → answer sequences
        current_question = None
        for ev in events:
            if ev.get("type") == "question":
                current_question = (ev.get("content") or "").strip().lower()
            elif (ev.get("type") == "text"
                  and ev.get("is_answer")
                  and current_question
                  and current_question == question_lower):
                answer = ev.get("content", "").strip()
                if answer:
                    logger.info(
                        "History match: q=%.60s → answer=%d chars",
                        question_lower, len(answer),
                    )
                    return answer

    except Exception as e:
        logger.debug("History check failed: %s", e)

    return None


def _event_to_dict(event) -> dict:
    """Convert an ADK Event to the dict format that parse_event expects."""
    result = {"author": event.author or ""}

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

    if event.content:
        content = {"role": event.content.role or ""}
        parts = []
        for part in event.content.parts or []:
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
                    "response": dict(resp) if hasattr(resp, "items") else {"result": resp},
                }
            if p:
                parts.append(p)
        content["parts"] = parts
        result["content"] = content

    return result


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------


def _get_genai_client():
    """Return a cached genai Client for voice summarization."""
    global _genai_client
    if _genai_client is None:
        from google import genai

        _genai_client = genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
            location=os.environ.get("TOOL_MODEL_LOCATION", "") or "us-central1",
        )
    return _genai_client


def _get_text_runner():
    """Lazy-initialize a text-mode Runner for agent_chat (local mode).

    If init_bridge() was called, _runner is already set and this is a no-op.
    """
    global _runner, _session_service
    if _runner is None:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        from agent_chat.agent import root_agent

        _session_service = InMemorySessionService()
        _runner = Runner(
            agent=root_agent,
            app_name=_APP_NAME,
            session_service=_session_service,
        )
        logger.info("Text-mode Runner initialized for agent_voice bridge (local)")
    return _runner


def _get_remote_agent():
    """Lazy-initialize a handle to the deployed agent_chat on VAE."""
    global _remote_agent
    if _remote_agent is None:
        import vertexai

        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        resource_id = os.environ.get("AGENT_ENGINE_RESOURCE_ID", "")

        if not resource_id:
            raise RuntimeError(
                "AGENT_ENGINE_RESOURCE_ID not set. "
                "Required when AGENT_MODE=agent_engine."
            )

        if "/" in resource_id:
            resource_name = resource_id
        else:
            resource_name = (
                f"projects/{project}/locations/{location}"
                f"/reasoningEngines/{resource_id}"
            )

        vertexai.init(project=project, location=location)
        client = vertexai.Client(project=project, location=location)
        _remote_agent = client.agent_engines.get(name=resource_name)
        logger.info("Remote agent_chat initialized for agent_voice bridge (VAE: %s)", resource_name)
    return _remote_agent


async def _summarize_for_voice(question: str, full_answer: str) -> str:
    """Condense a detailed text answer into a short voice-friendly summary.

    Uses a lightweight model (flash-lite) so the call adds ~1-2s, but the
    voice model receives a concise answer that keeps its context small.
    """
    from google.genai import types

    prompt = (
        f"The user asked: \"{question}\"\n\n"
        f"The data system returned this answer:\n\n{full_answer}\n\n"
        "Condense this into a brief voice response (2-4 sentences). Rules:\n"
        "- Lead with the key finding and one specific number.\n"
        "- Mention that detailed results, SQL, and charts are visible "
        "in the text panel.\n"
        "- Skip SQL queries, column names, technical formatting.\n"
        "- Use natural speech — no bullet points or markdown.\n"
        "- If a chart was generated, mention it: "
        "\"I've sent a chart to the text panel.\"\n"
        "- Be conversational — this will be spoken aloud."
    )

    try:
        client = _get_genai_client()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=_SUMMARY_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            ),
        )
        summary = response.text.strip()
        if summary:
            logger.info(
                "Voice summary: %d chars → %d chars",
                len(full_answer),
                len(summary),
            )
            return summary
    except Exception as e:
        logger.warning("Voice summarization failed, using raw answer: %s", e)

    # Fallback: truncate the raw answer
    if len(full_answer) > 1500:
        return full_answer[:1500] + "..."
    return full_answer


async def _try_derive_answer(
    question: str, qa_history: list[dict],
) -> str | None:
    """Check if a new question can be answered from prior Q&A pairs.

    Uses a lightweight model (flash-lite, ~0.5s) to avoid a full agent_chat
    round-trip (~8-12s) for derivable questions like:
      - "how many tables?" after listing tables
      - "which was highest?" after showing a ranking
      - "what about state X?" when prior answer included that state

    Returns a voice-ready answer if derivable, None otherwise.
    """
    from google.genai import types

    # Build context from recent Q&A pairs
    context_lines = []
    for entry in qa_history[-3:]:  # Last 3 for relevance
        context_lines.append(f"Q: {entry['question']}")
        context_lines.append(f"A: {entry['answer']}")
    context = "\n".join(context_lines)

    prompt = (
        f"Prior conversation:\n{context}\n\n"
        f"New question: \"{question}\"\n\n"
        "Can you answer the new question using ONLY the information in the "
        "prior answers above? Rules:\n"
        "- If YES: respond with a natural 1-2 sentence voice answer.\n"
        "- If NO (needs new data, different tables, or information not present): "
        "respond with exactly: NO\n"
        "- Be strict — only answer if the information is clearly present.\n"
        "- Do not guess or extrapolate beyond what the prior answers state."
    )

    try:
        client = _get_genai_client()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=_SUMMARY_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            ),
        )
        result = response.text.strip()
        if result and result.upper() != "NO" and len(result) > 5:
            logger.info(
                "Derivability check: answered from cache (%d chars)",
                len(result),
            )
            return result
    except Exception as e:
        logger.debug("Derivability check failed: %s", e)

    return None


def _add_follow_up_context(question: str, qa_history: list[dict]) -> str:
    """Add brief session context so the orchestrator identifies follow-ups.

    When voice asks a follow-up question, the orchestrator may not have
    enough context from the question alone to know tables are already loaded.
    Including the recent question history lets it skip the reranker for
    genuine follow-ups on the same dataset.

    Only adds context when there IS recent history — first questions pass
    through unmodified.
    """
    if not qa_history:
        return question

    # Include last 2 questions as brief context
    recent = qa_history[-2:]
    lines = [f"- {e['question']}" for e in recent]
    context = "\n".join(lines)
    return (
        f"Session context (previous questions):\n{context}\n\n"
        f"New question: {question}"
    )


async def ask_data_question(
    question: str,
    tool_context: tools.ToolContext,
) -> str:
    """Ask a data question and get an answer from the analytics system.

    Delegates the question to the full multi-agent data analytics system,
    which finds the right tables, runs SQL, and returns an answer.
    The answer is summarized for voice before being returned.

    Use this for ALL data questions: values, statistics, trends, charts,
    column definitions, table documentation, pipeline metadata, etc.

    Args:
        question: The data question to answer.
        tool_context: The ADK tool context.

    Returns:
        A voice-friendly summary of the answer.
    """
    # Guard: if already processing a question, don't start another
    if tool_context.state.get("_ask_data_pending"):
        logger.info("Voice bridge: skipping duplicate call (already processing)")
        return "I'm still working on your previous question. One moment."

    # Guard: check conversation cache for repeats and near-repeats
    qa_history = tool_context.state.get("_qa_history", [])
    q_lower = question.strip().lower()

    # Common rephrasings asking to repeat the last answer
    repeat_phrases = [
        "repeat that", "say that again", "what did you say",
        "one more time", "say it again", "come again",
    ]
    if qa_history and any(p in q_lower for p in repeat_phrases):
        logger.info("Voice bridge: returning cached answer for repeat-request")
        return qa_history[-1]["answer"]

    # Exact repeat of any recent question
    for entry in qa_history:
        if q_lower == entry["question"].strip().lower():
            logger.info("Voice bridge: returning cached answer for exact repeat")
            return entry["answer"]

    # Cross-channel check: look for prior answers in the shared history store
    # (covers questions answered via text chat before voice was activated)
    history_answer = _check_shared_history(q_lower)
    if history_answer:
        logger.info("Voice bridge: found answer in shared history (cross-channel)")
        summary = await _summarize_for_voice(question, history_answer)
        qa_history.append({"question": question.strip(), "answer": summary})
        if len(qa_history) > 5:
            qa_history.pop(0)
        tool_context.state["_qa_history"] = qa_history
        return summary

    # Derivability check: can a prior answer answer this new question?
    # Uses flash-lite (~0.5s) to avoid a full agent_chat round-trip (~8-12s)
    # for questions like "how many tables?" after "what tables do you have?"
    if qa_history:
        derived = await _try_derive_answer(question, qa_history)
        if derived:
            logger.info("Voice bridge: derived answer from prior Q&A cache")
            qa_history.append({"question": question.strip(), "answer": derived})
            if len(qa_history) > 5:
                qa_history.pop(0)
            tool_context.state["_qa_history"] = qa_history
            return derived

    tool_context.state["_ask_data_pending"] = True

    # Enrich question with session context so the orchestrator can
    # identify follow-ups and skip the reranker when appropriate.
    enriched = _add_follow_up_context(question, qa_history)

    try:
        if _AGENT_MODE == "agent_engine":
            raw_answer = await _run_remote(enriched, tool_context)
        else:
            raw_answer = await _run_local(enriched, tool_context)

        if not raw_answer:
            return "I wasn't able to get an answer. Could you try rephrasing?"

        # Summarize the full answer into a voice-friendly format
        answer = await _summarize_for_voice(question, raw_answer)

        # Store in conversation cache (keep last 5)
        qa_history.append({"question": question.strip(), "answer": answer})
        if len(qa_history) > 5:
            qa_history.pop(0)
        tool_context.state["_qa_history"] = qa_history

        return answer

    finally:
        tool_context.state["_ask_data_pending"] = False


async def _run_local(question: str, tool_context: tools.ToolContext) -> str:
    """Run agent_chat locally via ADK Runner."""
    from google.genai import types

    runner = _get_text_runner()

    # Get the shared text session ID — check module-level override first
    text_session_id = (
        _shared_session_id
        or tool_context.state.get("text_session_id")
    )
    if not text_session_id:
        session = await _session_service.create_session(
            app_name=_APP_NAME,
            user_id="ui_user",
        )
        text_session_id = session.id
        logger.info("Created text session: %s", text_session_id)
    tool_context.state["text_session_id"] = text_session_id

    new_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=question)],
    )

    # Look up event queue for real-time streaming to text panel
    queue = _event_queues.get(text_session_id)

    # Run agent_chat and collect the final text answer
    final_text = ""

    async for event in runner.run_async(
        user_id="ui_user",
        session_id=text_session_id,
        new_message=new_message,
    ):
        # Push raw event to queue for the text panel
        if queue:
            try:
                event_dict = _event_to_dict(event)
                await queue.put(event_dict)
            except Exception:
                pass

        # Log progress for debugging
        if event.actions and event.actions.transfer_to_agent:
            logger.info("Voice bridge: transfer to %s", event.actions.transfer_to_agent)
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    logger.info("Voice bridge: tool call %s", part.function_call.name)

        # Collect the last text response as the final answer
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text and part.text.strip():
                    if not part.function_call and not part.function_response:
                        final_text = part.text.strip()

    # Signal completion to the queue
    if queue:
        await queue.put(None)

    return final_text


async def _run_remote(question: str, tool_context: tools.ToolContext) -> str:
    """Run agent_chat on deployed VAE agent via async_stream_query."""
    agent = _get_remote_agent()

    # Get the shared text session ID — check module-level override first
    # (set by init_bridge), then session state, then create a new one
    text_session_id = (
        _shared_session_id
        or tool_context.state.get("text_session_id")
    )
    if not text_session_id:
        session = await agent.async_create_session(user_id="voice_user")
        text_session_id = session.get("id") or session.get("session_id", "")
        logger.info("Created remote session: %s", text_session_id)
    tool_context.state["text_session_id"] = text_session_id

    # Look up event queue for real-time streaming to text panel
    queue = _event_queues.get(text_session_id)

    # Stream events from deployed agent_chat
    final_text = ""

    async for event in agent.async_stream_query(
        user_id="ui_user",
        session_id=text_session_id,
        message=question,
    ):
        # Push raw event to queue for the text panel (already a dict)
        if queue:
            try:
                await queue.put(event)
            except Exception:
                pass

        # Remote events are dicts, not ADK Event objects
        actions = event.get("actions") or {}
        content = event.get("content") or {}
        author = event.get("author", "")

        if actions.get("transfer_to_agent"):
            logger.info("Voice bridge: transfer to %s", actions["transfer_to_agent"])

        parts = content.get("parts") or []
        for part in parts:
            if not isinstance(part, dict):
                continue
            fc = part.get("functionCall") or part.get("function_call")
            if fc:
                logger.info("Voice bridge: tool call %s", fc.get("name", ""))
            text = part.get("text", "")
            if text and text.strip() and not fc:
                fr = part.get("functionResponse") or part.get("function_response")
                if not fr:
                    final_text = text.strip()

    # Signal completion to the queue
    if queue:
        await queue.put(None)

    return final_text
