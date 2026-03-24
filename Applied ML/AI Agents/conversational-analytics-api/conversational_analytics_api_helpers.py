# Mostly a copy from documentation: https://cloud.google.com/gemini/docs/conversational-analytics-api/build-agent-sdk#define_helper_functions
# include modification of `handle_chart_response` that returns png files using package vl_convert 

import pandas as pd
import json as json_lib

import proto
from google.protobuf.json_format import MessageToDict

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
  return df.to_string(index=False)

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
    response += '\n' + pd.DataFrame(d).to_string(index=False)
    return response

def _value_to_dict(v):
  """Recursively convert proto-plus values to plain Python dicts."""
  if v is None:
    return None
  if isinstance(v, proto.marshal.collections.maps.MapComposite):
    return _map_to_dict(v)
  elif isinstance(v, proto.marshal.collections.RepeatedComposite):
    return [_value_to_dict(el) for el in v]
  elif isinstance(v, (int, float, str, bool)):
    return v
  else:
    try:
      return MessageToDict(v)
    except Exception:
      return str(v)


def _map_to_dict(d):
  """Recursively convert proto-plus MapComposite to plain dict."""
  out = {}
  for k in d:
    if isinstance(d[k], proto.marshal.collections.maps.MapComposite):
      out[k] = _map_to_dict(d[k])
    else:
      out[k] = _value_to_dict(d[k])
  return out


def extract_vega_spec(resp):
  """Extract a Vega-Lite spec dict from a chart response, or None."""
  if 'result' not in resp:
    return None
  try:
    vega_config = resp.result.vega_config
    spec = _map_to_dict(vega_config)
    spec['width'] = 1200
    spec.pop('height', None)
    return spec
  except Exception:
    return None


def handle_chart_response(resp):
  if 'query' in resp:
    return resp.query.instructions
  elif 'result' in resp:
    spec = extract_vega_spec(resp)
    if spec:
      try:
        import vl_convert as vlc
        return vlc.vegalite_to_png(vl_spec=spec)
      except ImportError:
        return "[Chart generated — vl_convert not installed for PNG rendering]"
      except Exception as e:
        return f"[Chart generated but rendering failed: {e}]"
    return "[Chart response received but could not extract spec]"

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

def find_responses_by_type(responses, message_type):
  """Find all system_message responses of a given type.

  The API response stream contains a mix of message types in
  non-deterministic order. Use this to filter by type instead
  of relying on positional indexing.

  Args:
      responses: List of Message objects from the API stream.
      message_type: One of 'text', 'schema', 'data', 'chart'.

  Returns:
      List of matching Message objects.
  """
  matches = []
  for resp in responses:
    try:
      if message_type in resp.system_message:
        matches.append(resp)
    except (AttributeError, TypeError):
      continue
  return matches

def find_chart(responses):
  """Extract the rendered chart (PNG bytes) from a response list.

  Searches backwards through responses for a chart result and
  renders it to PNG via vl_convert.

  Returns:
      bytes (PNG image data) or None if no chart found.
  """
  for resp in reversed(responses):
    try:
      m = resp.system_message
      if 'chart' in m:
        result = handle_chart_response(getattr(m, 'chart'))
        if isinstance(result, bytes):
          return result
    except (AttributeError, TypeError):
      continue
  return None
