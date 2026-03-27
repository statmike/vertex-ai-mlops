"""Shared utility for calling the Conversational Analytics API.

Used by both ``conversational_chat`` (agent_convo) and ``meta_chat``
(agent_engineer) to avoid duplicating session management, response
processing, and chart handling logic.
"""

import json
import logging
import os

from google.adk import tools
from google.cloud import geminidataanalytics_v1alpha as geminidataanalytics
from google.genai.types import Part
from google.protobuf.json_format import MessageToDict, ParseDict

from .util_build_context import build_enriched_context
from .utils.conversational_analytics_api_helpers import (
    handle_data_response,
    handle_text_response,
    show_message,
)

logger = logging.getLogger(__name__)


async def call_conversational_api(
    question: str,
    chart: bool,
    bigquery_tables: list[dict[str, str]],
    tool_context: tools.ToolContext,
    session_state_key: str,
    artifact_key: str,
    reranker_result: dict | None = None,
    system_instruction: str = "",
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

    Returns:
        The API response as text, or a message about a chart artifact.
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

        request_payload = {
            "parent": f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/global",
            "messages": history + [user_message],
            "inline_context": context,
        }

        conversation_client = geminidataanalytics.DataChatServiceClient()
        stream = conversation_client.chat(request=request_payload)
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

        # Process responses — keep only useful parts
        content_parts = []
        for resp in responses:
            try:
                m = resp.system_message
                if "text" in m:
                    piece = handle_text_response(getattr(m, "text"))
                    if piece and piece.strip():
                        content_parts.append(piece.strip())
                elif "data" in m:
                    data_resp = getattr(m, "data")
                    if "result" in data_resp:
                        piece = handle_data_response(data_resp)
                        if piece and piece.strip():
                            content_parts.append(piece.strip())
            except Exception:
                continue
        content = "\n\n".join(content_parts) if content_parts else "No content in API response."

        if not chart:
            return content

        # Look for chart in responses
        chart_content = None
        chart_index = -1
        for i in range(len(responses) - 1, -1, -1):
            response_message = responses[i]
            if "chart" in response_message.system_message:
                chart_content = show_message(response_message)
                chart_index = i
                break

        if chart_content and isinstance(chart_content, bytes):
            artifact_part = Part.from_bytes(
                data=chart_content, mime_type="image/png"
            )
            version = await tool_context.save_artifact(
                filename=artifact_key, artifact=artifact_part
            )

            if chart_index == len(responses) - 1:
                return (
                    f"Successfully generated a chart. It is available in the "
                    f"artifact with key (version = {version}): {artifact_key}"
                )
            else:
                return (
                    f"{content}\nSuccessfully generated a chart. It is available "
                    f"in the artifact with key (version = {version}): {artifact_key}"
                )
        else:
            return f"{content}\nNote: A chart was requested but not found in the response."

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
