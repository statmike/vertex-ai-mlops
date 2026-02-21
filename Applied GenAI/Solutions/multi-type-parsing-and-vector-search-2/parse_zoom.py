"""Parse Zoom VTT from GCS: sliding window chunking with Gemini rolling summary → BigQuery."""

from google.cloud import bigquery, storage
from google import genai
from config import (
    PROJECT_ID, REGION, GEMINI_MODEL,
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX, BQ_LOCATION,
    GCS_BUCKET, GCS_ROOT,
)
import re
from datetime import datetime, timezone

# --- Clients ---

bq = bigquery.Client(project=BQ_PROJECT)
gcs = storage.Client(project=PROJECT_ID)
gemini = genai.Client(vertexai=True, project=PROJECT_ID, location=REGION)

# --- Config ---

# A "cue" is the basic unit of a WebVTT transcript: a timestamp range paired with
# a speaker label and their spoken text. Each cue represents one uninterrupted
# segment of dialogue (e.g., "00:01:05.000 --> 00:01:12.000\nSarah: Let's review the data.").
WINDOW_SIZE = 15  # cues per chunk
OVERLAP = 5       # cues of overlap between chunks

# --- Get VTT source files, detect which need (re)processing ---

table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_zoom_chunks"

source_query = f"""
SELECT s.uri, s.updated AS source_updated
FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_source` s
WHERE s.content_type = 'text/vtt'
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

print(f"Found {len(source_rows)} VTT files, {len(files_to_process)} need processing")

# --- Parse VTT into cue list ---

def parse_vtt(text: str) -> list[dict]:
    """Parse WebVTT text into a list of cues (timestamp + speaker + spoken text)."""
    cues = []
    lines = text.strip().splitlines()
    i = 0
    while i < len(lines):
        # Look for timestamp lines
        match = re.match(r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})", lines[i])
        if match:
            start, end = match.group(1), match.group(2)
            i += 1
            # Collect text lines until blank line
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            full_text = " ".join(text_lines)

            # Split speaker from text
            speaker_match = re.match(r"^(.+?):\s*(.+)$", full_text)
            if speaker_match:
                speaker = speaker_match.group(1)
                content = speaker_match.group(2)
            else:
                speaker = "Unknown"
                content = full_text

            cues.append({"start": start, "end": end, "speaker": speaker, "text": content})
        else:
            i += 1
    return cues

# --- Convert timestamp string to seconds ---

def ts_to_seconds(ts: str) -> float:
    parts = ts.split(":")
    h, m = int(parts[0]), int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s

# --- Sliding window chunking ---

def create_windows(cues: list[dict]) -> list[list[dict]]:
    """Create overlapping windows from cue list."""
    windows = []
    start = 0
    while start < len(cues):
        window = cues[start:start + WINDOW_SIZE]
        windows.append(window)
        start += WINDOW_SIZE - OVERLAP
    return windows

# --- Gemini rolling summary ---

def rolling_summary(previous_text: str, current_text: str) -> str:
    """Use Gemini to generate a 15-word rolling summary for context."""
    try:
        response = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"""You are summarizing a meeting transcript for context continuity.
Previous context:
{previous_text[:1000]}

Current segment:
{current_text[:1000]}

Write a single summary sentence of at most 15 words capturing the key topic being discussed.
Return ONLY the summary sentence, nothing else.""",
        )
        return response.text.strip()
    except Exception as e:
        print(f"  Summary failed: {e}")
        return "Continuing discussion"

# --- Target table ---

schema = [
    bigquery.SchemaField("chunk_id", "STRING"),
    bigquery.SchemaField("source_uri", "STRING"),
    bigquery.SchemaField("text_content", "STRING"),
    bigquery.SchemaField("speaker_list", "STRING", mode="REPEATED"),
    bigquery.SchemaField("timestamp_start", "FLOAT"),
    bigquery.SchemaField("timestamp_end", "FLOAT"),
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
    vtt_text = blob.download_as_text()

    # Parse and window
    cues = parse_vtt(vtt_text)
    windows = create_windows(cues)
    print(f"  {len(cues)} cues → {len(windows)} windows")

    previous_window_text = ""
    rows = []

    for i, window in enumerate(windows):
        # Build window text
        window_text = "\n".join(f"{c['speaker']}: {c['text']}" for c in window)
        speakers = list(dict.fromkeys(c["speaker"] for c in window))  # unique, ordered

        # Rolling summary (skip first window)
        summary = ""
        if i > 0 and previous_window_text:
            summary = rolling_summary(previous_window_text, window_text)

        # Prepend summary to text
        text_content = f"[Summary: {summary}] {window_text}" if summary else window_text

        rows.append({
            "chunk_id": f"zoom_{blob_path.split('/')[-1].replace('.vtt', '')}_{i:03d}",
            "source_uri": uri,
            "text_content": text_content,
            "speaker_list": speakers,
            "timestamp_start": ts_to_seconds(window[0]["start"]),
            "timestamp_end": ts_to_seconds(window[-1]["end"]),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })
        previous_window_text = window_text

    # Delete existing chunks for this file, then insert new ones
    delete_query = f"DELETE FROM `{table_ref}` WHERE source_uri = '{uri}'"
    bq.query(delete_query).result()

    job = bq.load_table_from_json(rows, table_ref, job_config=bigquery.LoadJobConfig(schema=schema))
    job.result()
    print(f"  Loaded {len(rows)} rows for {uri.split('/')[-1]}")

# --- Summary ---
total = bq.query(f"SELECT COUNT(*) as n FROM `{table_ref}`").result()
print(f"\nTotal rows in {table_ref}: {list(total)[0].n}")
