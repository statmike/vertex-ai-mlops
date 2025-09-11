import pandas as pd
import json as json_lib
import altair as alt
import vl_convert as vlc

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
    return vlc.vegalite_to_png(vl_spec=chart.to_dict())

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
