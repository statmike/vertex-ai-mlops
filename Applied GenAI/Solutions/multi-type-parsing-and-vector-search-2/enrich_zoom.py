"""Semantic enrichment for Zoom transcript chunks using LangExtract."""

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

prompt = "Extract discussion topics and action items or decisions from meeting transcript chunks."

examples = [
    lx.data.ExampleData(
        text="Sarah (Lead): We need to benchmark ARIMA against Prophet on the Q4 data. David, can you set that up?\nDavid (Statistician): Sure, I'll have results by Friday.",
        extractions=[
            lx.data.Extraction(extraction_class="topic", extraction_text="benchmark ARIMA against Prophet",
                attributes={"name": "model comparison"}),
            lx.data.Extraction(extraction_class="action_item", extraction_text="I'll have results by Friday",
                attributes={"description": "Benchmark ARIMA vs Prophet on Q4 data", "owner": "David"}),
        ]
    )
]

# --- Add columns if they don't exist ---

table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_zoom_chunks"

for col in ["topics", "action_items"]:
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
print(f"\nFound {len(rows)} Zoom chunks to enrich")

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
        action_items = []
        for e in result.extractions:
            attrs = e.attributes or {}
            if e.extraction_class == "topic":
                val = attrs.get("name", e.extraction_text)
                if val and val not in topics:
                    topics.append(val)
            elif e.extraction_class == "action_item":
                val = attrs.get("description", e.extraction_text)
                if val and val not in action_items:
                    action_items.append(val)

        # Update BQ row
        update = f"""
            UPDATE `{table_ref}`
            SET topics = @topics, action_items = @action_items
            WHERE chunk_id = @chunk_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("topics", "STRING", topics),
                bigquery.ArrayQueryParameter("action_items", "STRING", action_items),
                bigquery.ScalarQueryParameter("chunk_id", "STRING", row.chunk_id),
            ]
        )
        bq.query(update, job_config=job_config).result()
        enriched += 1
        print(f"  {row.chunk_id}: {len(topics)} topics, {len(action_items)} action items")

    except Exception as e:
        errors += 1
        print(f"  {row.chunk_id}: ERROR - {e}")

print(f"\nDone: {enriched} enriched, {errors} errors")
