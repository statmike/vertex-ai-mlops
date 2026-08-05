"""Core wrapper around the Conversational Analytics API (inline, stateless).

We pass BigQuery tables as *inline* datasource references on every chat call
rather than creating a persisted data agent — the simplest pattern to demo and
the one that needs no extra provisioning. Session history is kept in ADK tool
state, keyed by the set of tables, so multi-turn follow-ups work.

Client library: google-cloud-geminidataanalytics (v1alpha surface).
"""

import json
import os

from google.cloud import geminidataanalytics_v1alpha as geminidataanalytics
from google.protobuf.json_format import MessageToDict, ParseDict

from .utils.response_helpers import handle_data_response, handle_text_response

_chat_client: geminidataanalytics.DataChatServiceClient | None = None


def _get_chat_client() -> geminidataanalytics.DataChatServiceClient:
    """Return a cached DataChatServiceClient (gRPC connection reuse)."""
    global _chat_client
    if _chat_client is None:
        _chat_client = geminidataanalytics.DataChatServiceClient()
    return _chat_client


async def call_conversational_api(
    question: str,
    bigquery_tables: list[dict[str, str]],
    tool_context,
    system_instruction: str = "",
) -> str:
    """Answer a question over BigQuery tables via the Conversational Analytics API.

    Args:
        question: The user's natural-language question.
        bigquery_tables: List of {project_id, dataset_id, table_id} dicts.
        tool_context: ADK tool context (used for multi-turn session history).
        system_instruction: Optional persona/behavior for the data agent.

    Returns:
        A text answer (may include a small rendered data table).
    """
    try:
        # Stable per-datasource key so follow-up turns reuse the same history.
        sorted_tables = sorted(
            bigquery_tables, key=lambda t: (t["project_id"], t["dataset_id"], t["table_id"])
        )
        datasource_key = json.dumps(sorted_tables, sort_keys=True)

        sessions = tool_context.state.get("conversational_api_sessions", {})
        raw_history = sessions.get(datasource_key, [])
        history = []
        for h in raw_history:
            message = geminidataanalytics.types.Message()
            ParseDict(h, message._pb)
            history.append(message)

        datasource = geminidataanalytics.DatasourceReferences(
            bq=dict(table_references=bigquery_tables)
        )
        context = geminidataanalytics.Context(
            system_instruction=(
                system_instruction
                or "Help users explore and analyze the provided retail data sources."
            ),
            datasource_references=datasource,
            options=dict(analysis=dict(python=dict(enabled=True))),
        )
        user_message = geminidataanalytics.Message(user_message=dict(text=question))

        request_payload = {
            "parent": f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/global",
            "messages": history + [user_message],
            "inline_context": context,
        }

        stream = _get_chat_client().chat(request=request_payload)
        responses = list(stream)
        if not responses:
            return "No response received from the Conversational Analytics API."

        # Persist history for follow-ups (non-critical — never crash on this).
        try:
            history.extend(responses)
            sessions[datasource_key] = [
                MessageToDict(m._pb, preserving_proto_field_name=True)
                for m in history
                if hasattr(m, "_pb") and m._pb is not None
            ]
            tool_context.state["conversational_api_sessions"] = sessions
        except Exception:
            pass

        parts: list[str] = []
        for resp in responses:
            try:
                m = resp.system_message
                if "text" in m:
                    piece = handle_text_response(m.text)
                elif "data" in m and "result" in m.data:
                    piece = handle_data_response(m.data)
                else:
                    piece = None
                if piece and piece.strip():
                    parts.append(piece.strip())
            except Exception:
                continue

        return "\n\n".join(parts) if parts else "No content in the API response."

    except Exception as e:  # noqa: BLE001 — return a clean message to the model
        return f"Error calling the Conversational Analytics API: {e}"
