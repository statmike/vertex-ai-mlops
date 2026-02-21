"""Parse Reddit JSON from GCS: tree flattening, SNR filtering, VLM image enrichment → BigQuery."""

from google.cloud import bigquery, storage
from google import genai
from config import (
    PROJECT_ID, REGION, GEMINI_MODEL,
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX, BQ_LOCATION,
    GCS_BUCKET, GCS_ROOT,
)
import json
from datetime import datetime, timezone

# --- Clients ---

bq = bigquery.Client(project=BQ_PROJECT)
gcs = storage.Client(project=PROJECT_ID)
gemini = genai.Client(vertexai=True, project=PROJECT_ID, location=REGION)

# --- Config ---

SHORT_RESPONSE_THRESHOLD = 15  # min tokens to keep non-top-level comments
SHORT_RESPONSE_MODE = "rollup"  # "drop" to discard short replies, "rollup" to merge into parent chunk
MAX_DEPTH = 100  # max parent chain depth to walk (safety limit for malformed data)

# --- Get Reddit source files, detect which need (re)processing ---

table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_reddit_chunks"

source_query = f"""
SELECT s.uri, s.updated AS source_updated
FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_source` s
WHERE s.content_type = 'application/json'
"""
source_rows = list(bq.query(source_query).result())

# Check which files already have up-to-date chunks
try:
    processed_query = f"""
    SELECT source_uri, MAX(processed_at) as last_processed
    FROM `{table_ref}`
    GROUP BY source_uri
    """
    processed = {row.source_uri: row.last_processed for row in bq.query(processed_query).result()}
except Exception:
    processed = {}

# Only process files that are new or updated since last processing
files_to_process = []
for row in source_rows:
    last = processed.get(row.uri)
    if last is None or row.source_updated > last:
        files_to_process.append(row.uri)
    else:
        print(f"Skipping (up to date): {row.uri.split('/')[-1]}")

print(f"Found {len(source_rows)} Reddit files, {len(files_to_process)} need processing")

# --- Tree flattening: build path from root to each comment ---

def build_comment_tree(post: dict) -> list[dict]:
    """Flatten comment tree into path-based chunks.

    Each comment becomes a chunk with its conversational lineage:
      THREAD: <post title> | PARENT: <immediate parent, truncated> | COMMENT: <body>

    The parent chain is walked up to MAX_DEPTH levels. Comments are stored flat
    with comment_id/parent_id references — this function reconstructs the path
    from each comment back to the thread root.

    Short non-top-level comments (below SHORT_RESPONSE_THRESHOLD tokens) are
    handled based on SHORT_RESPONSE_MODE:
      - "drop": discard them entirely
      - "rollup": append their text to the nearest ancestor's chunk as | REPLY: ...
    """
    comments_by_id = {c["comment_id"]: c for c in post["comments"]}
    chunks = []
    short_comments = []  # collected when mode is "rollup"

    def get_path(comment_id: str) -> list[str]:
        """Walk up the parent chain to build the path (bounded by MAX_DEPTH)."""
        path = []
        current = comment_id
        depth = 0
        while current and current in comments_by_id and depth < MAX_DEPTH:
            path.append(comments_by_id[current]["body"])
            current = comments_by_id[current].get("parent_id")
            depth += 1
        path.reverse()
        return path

    for comment in post["comments"]:
        # SNR filter: short non-top-level comments
        token_count = len(comment["body"].split())
        is_top_level = comment["parent_id"] is None
        if not is_top_level and token_count < SHORT_RESPONSE_THRESHOLD:
            if SHORT_RESPONSE_MODE == "rollup":
                short_comments.append(comment)
            continue

        path = get_path(comment["comment_id"])
        path_text = f"THREAD: {post['title']}"
        if len(path) > 1:
            path_text += f" | PARENT: {path[-2][:200]}"
        path_text += f" | COMMENT: {comment['body']}"

        chunks.append({
            "comment": comment,
            "text_content": path_text,
        })

    # Rollup: merge short replies into nearest ancestor chunk
    if SHORT_RESPONSE_MODE == "rollup" and short_comments:
        chunk_by_id = {c["comment"]["comment_id"]: c for c in chunks}
        for comment in short_comments:
            # Walk up to find nearest ancestor that has its own chunk
            current = comment["parent_id"]
            depth = 0
            while current and current not in chunk_by_id and depth < MAX_DEPTH:
                current = comments_by_id[current].get("parent_id") if current in comments_by_id else None
                depth += 1
            if current and current in chunk_by_id:
                chunk_by_id[current]["text_content"] += f" | REPLY: {comment['body']}"

    return chunks

# --- VLM image description via Gemini ---

def describe_image(image_url: str, comment_body: str) -> str:
    """Use Gemini to generate a description of an image anchored to comment context."""
    try:
        response = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"""Describe this image in detail, anchoring your description to the context
of this Reddit comment: "{comment_body[:500]}"
Image URL: {image_url}
Provide a dense, factual description in 2-3 sentences.""",
        )
        return response.text.strip()
    except Exception as e:
        print(f"  VLM failed for {image_url}: {e}")
        return ""

# --- Target table ---

table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_reddit_chunks"

schema = [
    bigquery.SchemaField("chunk_id", "STRING"),
    bigquery.SchemaField("source_uri", "STRING"),
    bigquery.SchemaField("text_content", "STRING"),
    bigquery.SchemaField("subreddit", "STRING"),
    bigquery.SchemaField("timestamp_unix", "INTEGER"),
    bigquery.SchemaField("karma", "INTEGER"),
    bigquery.SchemaField("is_image_description", "BOOLEAN"),
    bigquery.SchemaField("processed_at", "TIMESTAMP"),
]

# Create table if it doesn't exist
table = bigquery.Table(table_ref, schema=schema)
bq.create_table(table, exists_ok=True)

# --- Process each file (delete old chunks, insert new) ---

for uri in files_to_process:
    print(f"Processing: {uri}")

    # Read file from GCS
    blob_path = uri.replace(f"gs://{GCS_BUCKET}/", "")
    blob = gcs.bucket(GCS_BUCKET).blob(blob_path)
    post = json.loads(blob.download_as_text())

    # Flatten and chunk
    chunks = build_comment_tree(post)
    print(f"  {len(chunks)} chunks after filtering")

    rows = []
    for i, chunk in enumerate(chunks):
        comment = chunk["comment"]
        is_image = bool(comment.get("image_url"))

        # VLM enrichment for image comments
        image_desc = ""
        if is_image:
            image_desc = describe_image(comment["image_url"], comment["body"])
            print(f"  Image enrichment for comment {comment['comment_id']}")

        text = chunk["text_content"]
        if image_desc:
            text += f" | IMAGE: {image_desc}"

        rows.append({
            "chunk_id": f"red_{blob_path.split('/')[-1].replace('.json', '')}_{i:03d}",
            "source_uri": uri,
            "text_content": text,
            "subreddit": post["subreddit"],
            "timestamp_unix": comment.get("created_utc", 0),
            "karma": comment["score"],
            "is_image_description": is_image,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })

    # Delete existing chunks for this file, then insert new ones
    delete_query = f"DELETE FROM `{table_ref}` WHERE source_uri = '{uri}'"
    bq.query(delete_query).result()

    job = bq.load_table_from_json(rows, table_ref, job_config=bigquery.LoadJobConfig(schema=schema))
    job.result()
    print(f"  Loaded {len(rows)} rows for {uri.split('/')[-1]}")

# --- Summary ---
total = bq.query(f"SELECT COUNT(*) as n FROM `{table_ref}`").result()
print(f"\nTotal rows in {table_ref}: {list(total)[0].n}")
