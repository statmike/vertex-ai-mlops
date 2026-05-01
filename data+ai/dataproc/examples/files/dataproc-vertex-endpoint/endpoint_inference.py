"""PySpark inference via Vertex AI Endpoint -- no ML libs needed on workers."""
import argparse

from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf, col, lit, round as spark_round
from pyspark.sql.types import StructType, StructField, StringType, FloatType
import pandas as pd


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--bq_dataset', required=True)
    parser.add_argument('--source_table', required=True)
    parser.add_argument('--output_table', required=True)
    parser.add_argument('--endpoint_id', required=True)
    parser.add_argument('--region', default='us-central1')
    parser.add_argument('--model_name', default='distilbert-endpoint')
    parser.add_argument('--temp_bucket', required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.appName('endpoint-inference').getOrCreate()
    spark.conf.set('temporaryGcsBucket', args.temp_bucket)

    # Read from BigQuery
    df = spark.read.format('bigquery') \
        .option('table', f'{args.project}.{args.bq_dataset}.{args.source_table}') \
        .load() \
        .select('id', 'text', 'category')

    # Capture args for use inside UDF (closures must reference simple values)
    endpoint_id = args.endpoint_id
    project = args.project
    region = args.region

    schema = StructType([
        StructField('label', StringType()),
        StructField('score', FloatType()),
    ])

    # Cache the endpoint client across UDF calls within the same executor
    _endpoint_cache = {}

    @pandas_udf(schema)
    def endpoint_udf(texts: pd.Series) -> pd.DataFrame:
        """Call Vertex AI Endpoint for inference."""
        if endpoint_id not in _endpoint_cache:
            from google.cloud import aiplatform
            aiplatform.init(project=project, location=region)
            _endpoint_cache[endpoint_id] = aiplatform.Endpoint(endpoint_id)

        ep = _endpoint_cache[endpoint_id]
        instances = [{'text': t} for t in texts.tolist()]
        response = ep.predict(instances=instances)

        results = [{'label': p['label'], 'score': p['score']} for p in response.predictions]
        return pd.DataFrame(results)

    # Apply inference and format output
    result_df = df.withColumn('prediction', endpoint_udf(col('text')))
    output_df = result_df.select(
        col('id'),
        col('text'),
        col('category'),
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
