"""Batch inference with mapPartitions — lower-level alternative."""
import argparse
import os
import tempfile

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType

# Module-level model cache — same pattern as Pandas UDF version
_model_cache = {}


def get_model(model_gcs_uri):
    """Load model from GCS, caching after first load per executor."""
    if model_gcs_uri not in _model_cache:
        from transformers import pipeline as hf_pipeline, AutoTokenizer
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

    spark = SparkSession.builder.appName('map-partitions-inference').getOrCreate()
    spark.conf.set('temporaryGcsBucket', args.temp_bucket)

    # Read from BigQuery
    df = spark.read.format('bigquery') \
        .option('table', f'{args.project}.{args.bq_dataset}.{args.source_table}') \
        .load() \
        .select('id', 'text', 'category')

    model_uri = args.model_gcs_uri
    model_name = args.model_name

    def predict_partition(iterator):
        """Process each partition: load model once, predict row by row."""
        pipe = get_model(model_uri)
        for row in iterator:
            result = pipe(row.text)[0]
            yield (
                row.id,
                row.text,
                row.category,
                result['label'],
                round(result['score'], 6),
                model_name,
            )

    output_schema = StructType([
        StructField('id', IntegerType()),
        StructField('text', StringType()),
        StructField('category', StringType()),
        StructField('label', StringType()),
        StructField('score', FloatType()),
        StructField('model', StringType()),
    ])

    # mapPartitions operates on the RDD, returns tuples
    results_rdd = df.rdd.mapPartitions(predict_partition)
    output_df = spark.createDataFrame(results_rdd, schema=output_schema)

    # Write to BigQuery
    output_df.write.format('bigquery') \
        .option('table', f'{args.project}.{args.bq_dataset}.{args.output_table}') \
        .mode('overwrite') \
        .save()

    print(f'Results written to {args.project}.{args.bq_dataset}.{args.output_table}')


if __name__ == '__main__':
    run()
