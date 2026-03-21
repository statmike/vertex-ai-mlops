"""Conversational Analytics API tool for answering questions about BigQuery data.

Adapted from concept-bq/agent_convo_api/tools/conversational_chat.py.
"""

import json
import os

from google.adk import tools
from google.cloud import geminidataanalytics_v1alpha as geminidataanalytics
from google.genai.types import Part
from google.protobuf.json_format import MessageToDict, ParseDict

from .utils.conversational_analytics_api_helpers import (
    handle_data_response,
    handle_text_response,
    show_message,
)


async def conversational_chat(
    question: str,
    chart: bool,
    bigquery_tables: list[dict[str, str]],
    tool_context: tools.ToolContext,
) -> str:
    """Answer a question using the Conversational Analytics API.

    This API analyzes BigQuery data sources and responds with answers,
    data tables, and visual charts.

    Args:
        question: The user's question.
        chart: Whether the user is requesting a chart or other visual.
        bigquery_tables: A list of dicts, each with ``project_id``,
            ``dataset_id``, and ``table_id`` specifying a BigQuery table.
        tool_context: The ADK tool context for session state.

    Returns:
        The API response as text, or a message about a chart artifact.

    Example::

        conversational_chat(
            question="What providers have the largest bed sizes?",
            chart=False,
            bigquery_tables=[
                {"project_id": "my-project", "dataset_id": "bronze", "table_id": "ipsf_full"},
            ],
        )
    """
    try:
        # Create a stable key from the datasource list for session management
        sorted_tables = sorted(
            bigquery_tables,
            key=lambda t: (t["project_id"], t["dataset_id"], t["table_id"]),
        )
        datasource_key = json.dumps(sorted_tables, sort_keys=True)

        # Restore session history from state
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
                "Help users explore, analyze, and give detailed reports "
                "for the provided data sources."
            ),
            datasource_references=datasource,
            options=dict(analysis=dict(python=dict(enabled=True))),
        )

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

        # Update session history (non-critical — don't crash on serialization errors)
        try:
            history.extend(responses)
            history = [
                MessageToDict(m._pb, preserving_proto_field_name=True)
                for m in history
                if hasattr(m, "_pb") and m._pb is not None
            ]
            sessions[datasource_key] = history
            tool_context.state["conversational_api_sessions"] = sessions
        except Exception:
            pass  # session history won't persist but the answer still works

        # Selectively process responses for a clean chat experience.
        # The stream contains: schema resolution, data query planning,
        # generated SQL, data results, text (reasoning + answer + insights
        # + follow-ups), and chart messages.  We keep only the useful parts.
        content_parts = []
        for resp in responses:
            try:
                m = resp.system_message
                if "text" in m:
                    # Text: answer summaries, insights, follow-up suggestions
                    piece = handle_text_response(getattr(m, "text"))
                    if piece and piece.strip():
                        content_parts.append(piece.strip())
                elif "data" in m:
                    data_resp = getattr(m, "data")
                    if "result" in data_resp:
                        # Data result: the actual query results table
                        piece = handle_data_response(data_resp)
                        if piece and piece.strip():
                            content_parts.append(piece.strip())
                    # Skip data/query (planning) and data/generated_sql (verbose)
                # Skip schema responses (intermediate resolution)
                # Skip chart responses (handled separately below)
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
            artifact_key = "conversational_analytics_api_chart"
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
        return f"Error with tool `conversational_chat` during the API call. Error: {e}"
