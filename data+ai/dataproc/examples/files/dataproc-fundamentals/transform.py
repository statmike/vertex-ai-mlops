"""Simple PySpark transform — reads from BigQuery, adds columns, writes back."""
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import upper, col, size, split


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--bq_dataset', required=True)
    parser.add_argument('--source_table', required=True)
    parser.add_argument('--output_table', required=True)
    parser.add_argument('--temp_bucket', required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.appName('simple-transform').getOrCreate()
    spark.conf.set('temporaryGcsBucket', args.temp_bucket)

    df = spark.read.format('bigquery') \
        .option('table', f'{args.project}.{args.bq_dataset}.{args.source_table}') \
        .load()

    result = df.select(
        col('id'),
        col('text'),
        upper(col('category')).alias('category_upper'),
        size(split(col('text'), ' ')).alias('word_count'),
    )

    result.write.format('bigquery') \
        .option('table', f'{args.project}.{args.bq_dataset}.{args.output_table}') \
        .mode('overwrite') \
        .save()

    print(f'Results written to {args.project}.{args.bq_dataset}.{args.output_table}')


if __name__ == '__main__':
    run()
