"""Spark Structured Streaming with ML inference on Dataproc."""
import argparse
import os
import tempfile
import time

from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf, col, lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType
import pandas as pd

# Module-level model cache — persists across foreachBatch calls within the same executor
_model_cache = {}


def get_model(model_gcs_uri):
    """Load model from GCS, caching after first load."""
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
        # Load tokenizer explicitly — DistilBERT doesn't accept token_type_ids
        # but some transformers versions (e.g. runtime 2.2) generate them
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
    parser.add_argument('--output_table', required=True)
    parser.add_argument('--model_gcs_uri', required=True)
    parser.add_argument('--model_name', default='distilbert')
    parser.add_argument('--temp_bucket', required=True)
    parser.add_argument('--input_path', required=True)
    parser.add_argument('--checkpoint_path', required=True)
    parser.add_argument('--trigger_interval', default='30 seconds')
    parser.add_argument('--run_duration', type=int, default=0,
                        help='Stop after N seconds (0=run forever)')
    args = parser.parse_args()

    spark = SparkSession.builder.appName('streaming-inference').getOrCreate()
    spark.conf.set('temporaryGcsBucket', args.temp_bucket)

    # Input schema for JSON files
    input_schema = StructType([
        StructField('id', IntegerType()),
        StructField('text', StringType()),
        StructField('category', StringType()),
    ])

    # Sentiment UDF — downloads model from GCS on first call, caches in executor memory
    model_uri = args.model_gcs_uri
    pred_schema = StructType([
        StructField('label', StringType()),
        StructField('score', FloatType()),
    ])

    @pandas_udf(pred_schema)
    def sentiment_udf(texts: pd.Series) -> pd.DataFrame:
        pipe = get_model(model_uri)
        results = pipe(texts.tolist(), batch_size=32)
        return pd.DataFrame(results)

    # Read stream from GCS — monitors the directory for new JSON files
    stream_df = spark.readStream.format('json') \
        .schema(input_schema) \
        .load(args.input_path)

    def process_batch(batch_df, batch_id):
        """Apply ML inference and write each micro-batch to BigQuery."""
        if batch_df.isEmpty():
            print(f'Batch {batch_id}: empty, skipping')
            return

        count = batch_df.count()
        print(f'Batch {batch_id}: processing {count} rows')

        # Apply sentiment model via Pandas UDF
        result_df = batch_df.withColumn('prediction', sentiment_udf(col('text')))
        output_df = result_df.select(
            col('id'),
            col('text'),
            col('category'),
            col('prediction.label').alias('label'),
            col('prediction.score').cast('float').alias('score'),
            lit(args.model_name).alias('model'),
            current_timestamp().alias('processed_at'),
        )

        # Write micro-batch to BigQuery using the standard connector
        output_df.write.format('bigquery') \
            .option('table', f'{args.project}.{args.bq_dataset}.{args.output_table}') \
            .mode('append') \
            .save()
        print(f'Batch {batch_id}: wrote {count} rows to BigQuery')

    # Start the streaming query
    query = stream_df.writeStream \
        .foreachBatch(process_batch) \
        .option('checkpointLocation', args.checkpoint_path) \
        .trigger(processingTime=args.trigger_interval) \
        .start()

    print(f'Streaming started. Trigger: {args.trigger_interval}')
    print(f'Input: {args.input_path}')
    print(f'Checkpoint: {args.checkpoint_path}')

    if args.run_duration > 0:
        print(f'Will stop after {args.run_duration} seconds')
        # awaitTermination timeout is in seconds (not milliseconds)
        query.awaitTermination(timeout=args.run_duration)
        query.stop()
        print('Streaming stopped (duration reached)')
    else:
        query.awaitTermination()


if __name__ == '__main__':
    run()
