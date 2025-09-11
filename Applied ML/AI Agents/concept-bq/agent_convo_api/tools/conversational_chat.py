import os
from typing import Dict, List
from google.adk import tools
from google.cloud import geminidataanalytics_v1alpha as geminidataanalytics
from google.protobuf.json_format import MessageToDict, ParseDict
from google.genai.types import Part
from .utils.conversation_chat_helpers import show_message

async def conversational_chat(question: str, chart: bool, bigquery_tables: List[Dict[str, str]], tool_context: tools.ToolContext) -> str:
    """Answers a question using the Conversational Analytics API.
    This API can analyze data sources and respond with answers, tables, and even visual charts.

    Args:
        question: The user's question.
        chart: If the user is request a chart or other visual presentation or not.
        bigquery_tables (List[Dict[str, str]]): A list of dictionaries, each
            specifying a BigQuery table to be used as context for the question.
        tool_context: The execution context for the tool.

    Returns:
        The response from the Conversational Analytics API, either as a string or a message indicating an image artifact was created.

    Example:
    conversational_chat(
        question = "How many tsumani do we have records for?",
        chart = False,
        bigquery_tables = [
            {"project_id": "bigquery-public-data", "dataset_id": "noaa_tsunami", "table_id": "historical_runups"},
            {"project_id": "bigquery-public-data", "dataset_id": "noaa_tsunami", "table_id": "historical_source_event"},
        ]
    )
    """
    try:
        # Create a stable, hashable key from the list of datasource dictionaries
        # Sort outer list by project_id, then dataset_id, then table_id
        sorted_tables = sorted(bigquery_tables, key=lambda t: (t['project_id'], t['dataset_id'], t['table_id']))
        # Create a tuple of tuples of sorted items for each dictionary
        datasource_key = tuple(tuple(sorted(t.items())) for t in sorted_tables)

        # Get the main session dictionary from state
        sessions = tool_context.state.get('conversational_api_sessions', {})
        # Get the specific history for the current datasource key
        raw_history = sessions.get(datasource_key, [])
        # re-serialize these to their protobuf
        history = []
        for h in raw_history:
            message = geminidataanalytics.types.Message()
            ParseDict(h, message._pb)
            history.append(message)

        datasource = geminidataanalytics.DatasourceReferences(
            bq=dict(table_references = bigquery_tables)
        )

        context = geminidataanalytics.Context(
            system_instruction = 'Help users explore, analyze, and give details reports for the provided data sources.',
            datasource_references = datasource,
            options = dict(analysis = dict(python = dict(enabled = True)))
        )

        user_message = geminidataanalytics.Message(user_message=dict(text=question))

        request_payload = {
            "parent": f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/global",
            "messages": history + [user_message],
            "inline_context": context
        }

        conversation_client = geminidataanalytics.DataChatServiceClient()
        stream = conversation_client.chat(request=request_payload)
        responses = list(stream)

        if not responses:
            return 'No responses received from the API.'
        
        # Update the history for the current session
        history.extend(responses)
        history = [MessageToDict(m._pb, preserving_proto_field_name=True) for m in history]

        # Store the updated history back in the sessions dictionary
        sessions[datasource_key] = history
        tool_context.state['conversational_api_sessions'] = sessions

        # prepare response to question
        content = show_message(responses[-1])

        if not chart:
            return content

        chart_content = None
        chart_index = -1

        for i in range(len(responses) - 1, -1, -1):
            response_message = responses[i]
            if 'chart' in response_message.system_message:
                chart_content = show_message(response_message)
                chart_index = i
                break
        
        if chart_content and isinstance(chart_content, bytes):
            artifact_key = 'conversational_analytics_api_chart'
            artifact_part = Part.from_bytes(data=chart_content, mime_type='image/png')
            version = await tool_context.save_artifact(filename = artifact_key, artifact = artifact_part)
            
            if chart_index == len(responses) - 1:
                return f'Successfully generated a chart. It is available in the artifact with key (version = {version}): {artifact_key}'
            else:
                return f'{content}\nSuccessfully generated a chart. It is available in the artifact with key (version = {version}): {artifact_key}'
        
        else:
            return f'{content}\nNote: A chart was requested but not found in the response.'
            
    except Exception as e:
        return f"Error with tool `conversational_chat` during the API call. Error: {str(e)}"