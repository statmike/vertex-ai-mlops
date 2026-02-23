"""Semantic enrichment for PDF document chunks using LangExtract."""

import langextract as lx
from google.cloud import bigquery
from config import (
    PROJECT_ID,
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX,
    FAST_GEMINI_MODEL,
)

# --- Clients ---

bq = bigquery.Client(project=BQ_PROJECT)

# LangExtract Vertex AI auth params
lm_params = {"vertexai": True, "project": PROJECT_ID, "location": "global"}

# --- Extraction schema ---

prompt = "Extract BigQuery ML functions and technical concepts from documentation chunks."

examples = [
    lx.data.ExampleData(
        text="# The CREATE MODEL statement for ARIMA PLUS\n\nUse the CREATE MODEL statement to create a time series model with automatic seasonality detection.",
        extractions=[
            lx.data.Extraction(extraction_class="sql_function", extraction_text="CREATE MODEL",
                attributes={"name": "CREATE MODEL"}),
            lx.data.Extraction(extraction_class="topic", extraction_text="time series model",
                attributes={"name": "time series modeling"}),
            lx.data.Extraction(extraction_class="topic", extraction_text="automatic seasonality detection",
                attributes={"name": "seasonality detection"}),
        ]
    )
]

# --- Add columns if they don't exist ---

table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_pdf_chunks"

for col in ["topics", "functions_referenced"]:
    try:
        bq.query(f"ALTER TABLE `{table_ref}` ADD COLUMN {col} ARRAY<STRING>").result()
        print(f"Added column: {col}")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print(f"Column already exists: {col}")
        else:
            raise

# --- Read chunks ---

query = f"SELECT chunk_id, text_content FROM `{table_ref}`"
rows = list(bq.query(query).result())
print(f"\nFound {len(rows)} PDF chunks to enrich")

# --- Enrich each chunk ---

enriched = 0
errors = 0

for row in rows:
    try:
        result = lx.extract(
            text_or_documents=row.text_content,
            prompt_description=prompt,
            examples=examples,
            model_id=FAST_GEMINI_MODEL,
            language_model_params=lm_params,
        )

        # Aggregate extractions into tag lists
        topics = []
        functions = []
        for e in result.extractions:
            attrs = e.attributes or {}
            val = attrs.get("name", e.extraction_text)
            if e.extraction_class == "topic" and val and val not in topics:
                topics.append(val)
            elif e.extraction_class == "sql_function" and val and val not in functions:
                functions.append(val)

        # Update BQ row
        update = f"""
            UPDATE `{table_ref}`
            SET topics = @topics, functions_referenced = @functions
            WHERE chunk_id = @chunk_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("topics", "STRING", topics),
                bigquery.ArrayQueryParameter("functions", "STRING", functions),
                bigquery.ScalarQueryParameter("chunk_id", "STRING", row.chunk_id),
            ]
        )
        bq.query(update, job_config=job_config).result()
        enriched += 1
        print(f"  {row.chunk_id}: {len(topics)} topics, {len(functions)} functions")

    except Exception as e:
        errors += 1
        print(f"  {row.chunk_id}: ERROR - {e}")

print(f"\nDone: {enriched} enriched, {errors} errors")
