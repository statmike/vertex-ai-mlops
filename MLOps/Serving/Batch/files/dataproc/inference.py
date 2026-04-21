"""Standalone PySpark script for sentiment batch inference on Dataproc Serverless."""
import argparse
import os
import tempfile

from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf, col, lit, round as spark_round
from pyspark.sql.types import StructType, StructField, StringType, FloatType
import pandas as pd

# Module-level model cache — persists across UDF calls within the same executor
_model_cache = {}


def get_model(model_gcs_uri):
    """Load model from GCS, caching after first load per executor."""
    if model_gcs_uri not in _model_cache:
        from transformers import pipeline as hf_pipeline
        from google.cloud import storage

        client = storage.Client()
        parts = model_gcs_uri.replace('gs://', '').split('/', 1)
        bkt = client.bucket(parts[0])
        prefix = parts[1]
        model_dir = tempfile.mkdtemp()
        for blob in bkt.list_blobs(prefix=prefix):
            rel = blob.name[len(prefix):].lstrip('/')
            if rel:
                local = os.path.join(model_dir, rel)
                os.makedirs(os.path.dirname(local), exist_ok=True)
                blob.download_to_filename(local)
        # Load tokenizer explicitly — DistilBERT doesn't accept token_type_ids
        # but some transformers versions (e.g. runtime 2.2) generate them
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        if 'token_type_ids' in tokenizer.model_input_names:
            tokenizer.model_input_names.remove('token_type_ids')
        _model_cache[model_gcs_uri] = hf_pipeline(
            'sentiment-analysis', model=model_dir, tokenizer=tokenizer
        )
    return _model_cache[model_gcs_uri]


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--bq_dataset', required=True)
    parser.add_argument('--source_table', required=True)
    parser.add_argument('--output_table', required=True)
    parser.add_argument('--model_gcs_uri', required=True)
    parser.add_argument('--model_name', default='distilbert')
    parser.add_argument('--temp_bucket', required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.appName('batch-inference').getOrCreate()
    spark.conf.set('temporaryGcsBucket', args.temp_bucket)

    # Read from BigQuery
    df = spark.read.format('bigquery') \
        .option('table', f'{args.project}.{args.bq_dataset}.{args.source_table}') \
        .load() \
        .select('id', 'text', 'category')

    # Define sentiment UDF with struct return type
    model_uri = args.model_gcs_uri

    schema = StructType([
        StructField('label', StringType()),
        StructField('score', FloatType()),
    ])

    @pandas_udf(schema)
    def sentiment_udf(texts: pd.Series) -> pd.DataFrame:
        pipe = get_model(model_uri)
        results = pipe(texts.tolist(), batch_size=32)
        return pd.DataFrame(results)

    # Apply inference and format output
    result_df = df.withColumn('prediction', sentiment_udf(col('text')))
    output_df = result_df.select(
        col('id'),
        col('text'),
        col('prediction.label').alias('label'),
        spark_round(col('prediction.score'), 6).alias('score'),
        lit(args.model_name).alias('model'),
    )

    # Write to BigQuery
    output_df.write.format('bigquery') \
        .option('table', f'{args.project}.{args.bq_dataset}.{args.output_table}') \
        .mode('overwrite') \
        .save()

    print(f'Results written to {args.project}.{args.bq_dataset}.{args.output_table}')


if __name__ == '__main__':
    run()
