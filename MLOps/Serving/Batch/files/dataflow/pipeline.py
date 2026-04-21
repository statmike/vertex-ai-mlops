"""Standalone Beam pipeline for sentiment batch inference."""
import subprocess, sys

# Fix package incompatibilities in the DataflowPythonJobOp launcher container
# (gcr.io/ml-pipeline/google-cloud-pipeline-components:2.22.0).
# The container has numpy/pandas ABI mismatches and broken apitools imports.
# Reinstall beam (with all deps) and pandas to get a consistent package set.
subprocess.check_call([
    sys.executable, '-m', 'pip', 'install', '-q',
    '--force-reinstall', 'apache-beam[gcp]', 'pandas',
])

import argparse, json, logging, os, tempfile

logging.basicConfig(level=logging.INFO)

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.ml.inference.base import ModelHandler, PredictionResult, RunInference


class SentimentModelHandler(ModelHandler):
    def __init__(self, model_gcs_uri):
        self._model_gcs_uri = model_gcs_uri

    def load_model(self):
        from transformers import pipeline as hf_pipeline
        from google.cloud import storage
        client = storage.Client()
        parts = self._model_gcs_uri.replace('gs://', '').split('/', 1)
        bkt = client.bucket(parts[0])
        prefix = parts[1]
        model_dir = tempfile.mkdtemp()
        for blob in bkt.list_blobs(prefix=prefix):
            rel = blob.name[len(prefix):].lstrip('/')
            if rel:
                local = os.path.join(model_dir, rel)
                os.makedirs(os.path.dirname(local), exist_ok=True)
                blob.download_to_filename(local)
        return hf_pipeline('sentiment-analysis', model=model_dir, tokenizer=model_dir)

    def run_inference(self, batch, model, inference_args=None):
        texts = [e['text'] for e in batch]
        results = model(texts)
        return [PredictionResult(example=e, inference=r) for e, r in zip(batch, results)]

    def batch_elements_kwargs(self):
        return {'min_batch_size': 1, 'max_batch_size': 32}


class PreprocessFn(beam.DoFn):
    def process(self, row):
        text = row.get('text', '')
        if isinstance(text, str):
            text = text.strip()
        if text:
            yield {'id': row.get('id', 0), 'text': text, 'category': row.get('category', '')}


class PostprocessFn(beam.DoFn):
    def process(self, prediction_result):
        element = prediction_result.example
        result = prediction_result.inference
        yield {
            'id': element['id'],
            'text': element['text'],
            'label': result['label'],
            'score': round(result['score'], 6),
            'model': 'distilbert',
        }


def run(argv=None):
    parser = argparse.ArgumentParser()
    # Note: --project is NOT declared here because DataflowPythonJobOp
    # auto-injects --project into the command. Declaring it here would
    # consume it via parse_known_args, preventing Beam from seeing it.
    parser.add_argument('--bq_dataset', required=True)
    parser.add_argument('--source_table', required=True)
    parser.add_argument('--output_table', required=True)
    parser.add_argument('--model_gcs_uri', required=True)
    known_args, pipeline_args = parser.parse_known_args(argv)

    # Get project from Beam pipeline options (auto-injected by the component)
    options = PipelineOptions(pipeline_args)
    project = options.get_all_options()['project']

    handler = SentimentModelHandler(known_args.model_gcs_uri)
    schema = 'id:INTEGER,text:STRING,label:STRING,score:FLOAT64,model:STRING'

    with beam.Pipeline(options=options) as p:
        (
            p
            | 'Read' >> beam.io.ReadFromBigQuery(
                query=f'SELECT id, text, category FROM `{project}.{known_args.bq_dataset}.{known_args.source_table}`',
                use_standard_sql=True,
            )
            | 'Preprocess' >> beam.ParDo(PreprocessFn())
            | 'Infer' >> RunInference(model_handler=handler)
            | 'Postprocess' >> beam.ParDo(PostprocessFn())
            | 'Write' >> beam.io.WriteToBigQuery(
                table=f'{project}:{known_args.bq_dataset}.{known_args.output_table}',
                schema=schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )


if __name__ == '__main__':
    run()
