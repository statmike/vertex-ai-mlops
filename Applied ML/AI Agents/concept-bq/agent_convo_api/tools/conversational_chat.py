import os
import pandas as pd
import json as json_lib
import altair as alt
import vl_convert as vlc
from IPython.display import display, HTML, Image

import proto
from google.protobuf.json_format import MessageToDict, MessageToJson

from google.adk import tools
from google.cloud import geminidataanalytics_v1alpha as geminidataanalytics

def handle_text_response(resp):
  parts = getattr(resp, 'parts')
  return '\n'.join(parts)

def display_schema(data):
  fields = getattr(data, 'fields')
  df = pd.DataFrame({
    "Column": map(lambda field: getattr(field, 'name'), fields),
    "Type": map(lambda field: getattr(field, 'type'), fields),
    "Description": map(lambda field: getattr(field, 'description', '-'), fields),
    "Mode": map(lambda field: getattr(field, 'mode'), fields)
  })
  return df.to_markdown()

def display_section_title(text):
  return f'<h2>{text}</h2>'

def format_bq_table_ref(table_ref):
  return '{}.{}.{}'.format(table_ref.project_id, table_ref.dataset_id, table_ref.table_id)

def display_datasource(datasource):
  source_name = format_bq_table_ref(getattr(datasource, 'bigquery_table_reference'))
  return source_name + '\n' + display_schema(datasource.schema)

def handle_schema_response(resp):
  if 'query' in resp:
    return resp.query.question
  elif 'result' in resp:
    response = display_section_title('Schema resolved')
    response += '\nData sources:\n'
    for datasource in resp.result.datasources:
      response += display_datasource(datasource)
    return response

def handle_data_response(resp):
  if 'query' in resp:
    query = resp.query
    response = display_section_title('Retrieval query')
    response += '\nQuery name: {}'.format(query.name)
    response += '\nQuestion: {}'.format(query.question)
    response += '\nData sources:\n'
    for datasource in query.datasources:
      response += display_datasource(datasource)
    return response
  elif 'generated_sql' in resp:
    response = display_section_title('SQL generated')
    response += '\n' + resp.generated_sql
    return response
  elif 'result' in resp:
    response = display_section_title('Data retrieved')
    fields = [field.name for field in resp.result.schema.fields]
    d = {}
    for el in resp.result.data:
      for field in fields:
        if field in d:
          d[field].append(el[field])
        else:
          d[field] = [el[field]]
    response += '\n' + pd.DataFrame(d).to_markdown()
    return response

def handle_chart_response(resp):
  def _value_to_dict(v):
    if isinstance(v, proto.marshal.collections.maps.MapComposite):
      return _map_to_dict(v)
    elif isinstance(v, proto.marshal.collections.RepeatedComposite):
      return [_value_to_dict(el) for el in v]
    elif isinstance(v, (int, float, str, bool)):
      return v
    else:
      return MessageToDict(v)

  def _map_to_dict(d):
    out = {}
    for k in d:
      if isinstance(d[k], proto.marshal.collections.maps.MapComposite):
        out[k] = _map_to_dict(d[k])
      else:
        out[k] = _value_to_dict(d[k])
    return out

  if 'query' in resp:
    return resp.query.instructions
  elif 'result' in resp:
    vegaConfig = resp.result.vega_config
    vegaConfig_dict = _map_to_dict(vegaConfig)
    chart = alt.Chart.from_json(json_lib.dumps(vegaConfig_dict))
    chart.width = 1200
    chart.height = alt.Undefined
    # Note: This will not display in the CLI, but shows how to handle chart responses.
    # In a notebook, you would use display(Image(data=png_bytes))
    return "Chart generated. Please render the Vega-Lite spec in a suitable environment."

def show_message(msg):
  m = msg.system_message
  if 'text' in m:
    return handle_text_response(getattr(m, 'text'))
  elif 'schema' in m:
    return handle_schema_response(getattr(m, 'schema'))
  elif 'data' in m:
    return handle_data_response(getattr(m, 'data'))
  elif 'chart' in m:
    return handle_chart_response(getattr(m, 'chart'))
  return '\n'

async def conversational_chat(question: str, bigquery_tables: list[str], tool_context: tools.ToolContext) -> str:
    """Answers a question using the Conversational Analytics API.

    Args:
        question: The user's question.
        bigquery_tables: A list of BigQuery tables in the format 'project.dataset.table'.
        tool_context: The execution context for the tool.

    Returns:
        The response from the Conversational Analytics API.
    """
    table_references = []
    for table in bigquery_tables:
        project_id, dataset_id, table_id = table.split('.')
        table_references.append(
            geminidataanalytics.BigQueryTableReference(
                project_id=project_id,
                dataset_id=dataset_id,
                table_id=table_id
            )
        )

    datasource = geminidataanalytics.DatasourceReferences(
        bq=dict(table_references=table_references)
    )

    context = geminidataanalytics.Context(
        system_instruction='Help users explore, analyze, and give details reports for the provided data sources.',
        datasource_references=datasource,
        options=dict(analysis=dict(python=dict(enabled=True)))
    )

    history = []
    for turn in tool_context.history():
        history.append(geminidataanalytics.Message(user_message=dict(text=turn.user_text)))
        # This assumes a simple history structure. ADK does not directly expose the system response of a previous turn.
        # For true stateless chat with history, a more complex history management would be needed outside the tool.

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
    
    final_response = ""
    for response in responses:
        final_response += show_message(response)

    return final_response
