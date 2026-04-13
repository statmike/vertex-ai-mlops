"""Shared utility for calling the Conversational Analytics API.

Used by both ``conversational_chat`` (agent_convo) and ``meta_chat``
(agent_engineer) to avoid duplicating session management, response
processing, and chart handling logic.
"""

import base64
import json
import logging
import os

from google.adk import tools
from google.cloud import geminidataanalytics_v1alpha as geminidataanalytics
from google.genai.types import Part
from google.protobuf.json_format import MessageToDict, ParseDict

from .util_build_context import build_enriched_context
from .utils.conversational_analytics_api_helpers import (
    handle_chart_response,
    handle_data_response,
    handle_text_response,
)

logger = logging.getLogger(__name__)

# Cached gRPC client — avoid connection setup on every API call
_chat_client = None


def _get_chat_client():
    """Return a cached DataChatServiceClient."""
    global _chat_client
    if _chat_client is None:
        _chat_client = geminidataanalytics.DataChatServiceClient()
    return _chat_client


async def call_conversational_api(
    question: str,
    chart: bool,
    bigquery_tables: list[dict[str, str]],
    tool_context: tools.ToolContext,
    session_state_key: str,
    artifact_key: str,
    reranker_result: dict | None = None,
    system_instruction: str = "",
    thinking_mode: str | None = None,
) -> str:
    """Call the Conversational Analytics API with session management.

    Args:
        question: The user's question.
        chart: Whether the user is requesting a chart.
        bigquery_tables: List of dicts with ``project_id``, ``dataset_id``,
            ``table_id``.
        tool_context: The ADK tool context for session state.
        session_state_key: State key for storing session history
            (e.g. ``"conversational_api_sessions"`` or ``"meta_api_sessions"``).
        artifact_key: Key for saving chart artifacts.
        reranker_result: Optional reranker result dict for enriched context.
        system_instruction: Base system instruction for the API.
        thinking_mode: Optional override — ``"THINKING"`` or ``"FAST"``.
            If None, uses ``CONVO_THINKING_MODE`` from environment.

    Returns:
        JSON string with ``answer`` (human-readable for the LLM) and
        ``parts`` (typed list for rich UI rendering).
    """
    try:
        # Create a stable key from the datasource list for session management
        sorted_tables = sorted(
            bigquery_tables,
            key=lambda t: (t["project_id"], t["dataset_id"], t["table_id"]),
        )
        datasource_key = json.dumps(sorted_tables, sort_keys=True)

        # Restore session history from state
        sessions = tool_context.state.get(session_state_key, {})
        raw_history = sessions.get(datasource_key, [])
        history = []
        for h in raw_history:
            message = geminidataanalytics.types.Message()
            ParseDict(h, message._pb)
            history.append(message)

        # Build context — use enriched context from reranker if available
        if reranker_result:
            try:
                context_dict = build_enriched_context(
                    reranker_result,
                    system_instruction=system_instruction,
                )
                context = geminidataanalytics.Context()
                ParseDict(context_dict, context._pb)
                logger.info(
                    "Using enriched context from reranker (%d tables)",
                    len(reranker_result.get("ranked_tables", [])),
                )
            except Exception as e:
                logger.warning("Failed to build enriched context, falling back: %s", e)
                context = _build_plain_context(
                    bigquery_tables, system_instruction
                )
        else:
            context = _build_plain_context(bigquery_tables, system_instruction)

        user_message = geminidataanalytics.Message(
            user_message=dict(text=question)
        )

        # Determine thinking mode: use per-call override, else env var default
        from agent_orchestrator.config import CONVO_THINKING_MODE
        mode_str = (thinking_mode or CONVO_THINKING_MODE).upper()
        mode_enum = (
            geminidataanalytics.ChatRequest.ThinkingMode.FAST
            if mode_str == "FAST"
            else geminidataanalytics.ChatRequest.ThinkingMode.THINKING
        )

        request_payload = {
            "parent": f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/global",
            "messages": history + [user_message],
            "inline_context": context,
            "thinking_mode": mode_enum,
        }

        stream = _get_chat_client().chat(request=request_payload)
        responses = list(stream)

        if not responses:
            return "No responses received from the API."

        # Update session history (non-critical)
        try:
            history.extend(responses)
            history = [
                MessageToDict(m._pb, preserving_proto_field_name=True)
                for m in history
                if hasattr(m, "_pb") and m._pb is not None
            ]
            sessions[datasource_key] = history
            tool_context.state[session_state_key] = sessions
        except Exception:
            pass  # session history won't persist but the answer still works

        # Process responses into typed parts for rich UI rendering.
        # Each API message becomes a labeled part; text parts are also
        # collected into a plain-text ``answer`` for the LLM.
        parts: list[dict] = []
        text_pieces: list[str] = []

        for i, resp in enumerate(responses):
            try:
                m = resp.system_message

                # Log each message type for debugging
                msg_types = [
                    t for t in ("text", "data", "schema", "chart")
                    if t in m
                ]
                logger.info(
                    "API response[%d] types=%s", i, msg_types,
                )

                if "text" in m:
                    piece = handle_text_response(getattr(m, "text"))
                    if piece and piece.strip():
                        parts.append({"type": "text", "content": piece.strip()})
                        text_pieces.append(piece.strip())

                elif "data" in m:
                    data_resp = getattr(m, "data")
                    if "generated_sql" in data_resp:
                        sql = data_resp.generated_sql
                        parts.append({"type": "sql", "content": sql})
                    if "result" in data_resp:
                        piece = handle_data_response(data_resp)
                        if piece and piece.strip():
                            parts.append({"type": "data", "content": piece.strip()})
                            text_pieces.append(piece.strip())

                elif "chart" in m:
                    chart_resp = getattr(m, "chart")
                    logger.info(
                        "Chart response[%d]: has_query=%s has_result=%s",
                        i, "query" in chart_resp, "result" in chart_resp,
                    )

                    if "result" in chart_resp:
                        # Try to extract Vega-Lite spec for client-side rendering
                        from .utils.conversational_analytics_api_helpers import (
                            extract_vega_spec,
                        )
                        vega_spec = extract_vega_spec(chart_resp)
                        if vega_spec:
                            parts.append({
                                "type": "chart",
                                "vega_spec": vega_spec,
                            })
                            logger.info("Chart: Vega-Lite spec extracted")

                        # Also try server-side PNG rendering
                        chart_bytes = handle_chart_response(chart_resp)
                        if isinstance(chart_bytes, bytes):
                            artifact_part = Part.from_bytes(
                                data=chart_bytes, mime_type="image/png",
                            )
                            version = await tool_context.save_artifact(
                                filename=artifact_key, artifact=artifact_part,
                            )
                            b64 = base64.b64encode(chart_bytes).decode()
                            parts.append({
                                "type": "chart",
                                "image": f"data:image/png;base64,{b64}",
                            })
                            logger.info("Chart: PNG artifact saved (v%s)", version)
                        else:
                            logger.warning(
                                "Chart: PNG render returned %s: %s",
                                type(chart_bytes).__name__,
                                str(chart_bytes)[:200],
                            )
            except Exception as e:
                logger.warning("Error processing response[%d]: %s", i, e)
                continue

        answer = "\n\n".join(text_pieces) if text_pieces else "No content in API response."

        return json.dumps({"answer": answer, "parts": parts})

    except Exception as e:
        return f"Error during Conversational Analytics API call: {e}"


def _build_plain_context(
    bigquery_tables: list[dict[str, str]],
    system_instruction: str,
) -> "geminidataanalytics.Context":
    """Build a plain Context without reranker enrichment."""
    datasource = geminidataanalytics.DatasourceReferences(
        bq=dict(table_references=bigquery_tables)
    )
    return geminidataanalytics.Context(
        system_instruction=system_instruction or (
            "Help users explore, analyze, and give detailed reports "
            "for the provided data sources."
        ),
        datasource_references=datasource,
        options=dict(analysis=dict(python=dict(enabled=True))),
    )
