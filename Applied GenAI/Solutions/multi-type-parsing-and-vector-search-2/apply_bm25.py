"""Apply BM25 sparse embeddings to chunks in BigQuery and Vector Search 2.0.

Step 7b: Loads a trained BM25 model from BigQuery (vocabulary + parameters),
computes sparse embeddings for chunks that need updating, and writes the results
to BQ chunk tables and VS2 DataObjects.

Schema updates are handled automatically:
- BQ: adds bm25_indices, bm25_values, bm25_text, bm25_model_version columns if missing
- VS2: adds bm25_embedding sparse vector field to collection vector_schema if missing

A chunk needs updating when:
- bm25_model_version IS NULL (never embedded)
- bm25_model_version < target version (stale embedding from older model)

The target version defaults to the latest model in BQ but can be overridden with
--version to apply a specific (or previous) model version for rollback.

Usage:
    uv run python apply_bm25.py              # apply latest model version
    uv run python apply_bm25.py --version 1  # apply (or rollback to) version 1
    uv run python apply_bm25.py --all        # re-embed all chunks (ignore version check)
"""

import argparse
import string
from collections import Counter

import nltk
from google.cloud import bigquery, vectorsearch_v1beta
from google.protobuf.field_mask_pb2 import FieldMask
from config import (
    PROJECT_ID, REGION,
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX,
    VS_COLLECTION_REDDIT, VS_COLLECTION_ZOOM, VS_COLLECTION_PDF, VS_COLLECTION_COMBINED,
    BM25_NGRAMS,
)

# --- Args ---

parser = argparse.ArgumentParser(description="Apply BM25 sparse embeddings to chunks.")
parser.add_argument('--version', type=int, default=None,
                    help='BM25 model version to apply (default: latest)')
parser.add_argument('--all', action='store_true',
                    help='Re-embed all chunks regardless of current version')
args = parser.parse_args()

# --- NLTK setup ---

nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)

lemmatizer = nltk.stem.WordNetLemmatizer()
stop_words = set(nltk.corpus.stopwords.words('english'))

# --- Clients ---

bq = bigquery.Client(project=BQ_PROJECT)
vs_client = vectorsearch_v1beta.VectorSearchServiceClient()
do_client = vectorsearch_v1beta.DataObjectServiceClient()


# --- BM25 functions ---

def chunk_prep(text, ngrams=BM25_NGRAMS):
    """Preprocess text for BM25: lowercase, remove punctuation, tokenize,
    lemmatize, remove stopwords, generate n-grams."""
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    tokens = nltk.tokenize.word_tokenize(text)
    unigrams = [lemmatizer.lemmatize(t) for t in tokens
                if len(t) > 1 and t not in stop_words]
    if ngrams >= 2:
        all_grams = unigrams.copy()
        for n in range(2, ngrams + 1):
            all_grams.extend(' '.join(g) for g in zip(*[unigrams[i:] for i in range(n)]))
        return all_grams
    return unigrams


def build_bm25_text(row, source_type):
    """Construct BM25 input: text_content + enrichment tags (Approach B)."""
    parts = [row.text_content]
    if row.topics:
        parts.extend(row.topics)
    if source_type == 'reddit' and row.methods_mentioned:
        parts.extend(row.methods_mentioned)
    elif source_type == 'zoom' and row.action_items:
        parts.extend(row.action_items)
    elif source_type == 'pdf' and row.functions_referenced:
        parts.extend(row.functions_referenced)
    return ' '.join(parts)


def create_bm25_sparse_embedding(text, vocab_map, idf_map, k1, b, avgdl):
    """Compute BM25 sparse embedding using stored model parameters.

    No BM25Okapi object needed — the scoring function is reconstructed from
    the vocabulary (term → index), IDF values, and model parameters stored in BQ.
    """
    tokens = chunk_prep(text)
    term_freqs = Counter(tokens)
    doc_len = len(tokens)

    indices, values = [], []
    for term, freq in term_freqs.items():
        if term not in vocab_map:
            continue
        idf = idf_map[term]
        score = idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * doc_len / avgdl))
        indices.append(vocab_map[term])
        values.append(score)
    return indices, values


# =============================================================================
# 1. Load BM25 model from BigQuery
# =============================================================================

print("=" * 60)
print("1. Loading BM25 model from BigQuery")
print("=" * 60)

model_table = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_bm25_model"
vocab_table = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_bm25_vocabulary"

# Determine target version
if args.version is not None:
    target_version = args.version
    model_rows = list(bq.query(
        f"SELECT * FROM `{model_table}` WHERE model_version = {target_version}"
    ).result())
    if not model_rows:
        print(f"  ERROR: Model version {target_version} not found in {model_table}")
        exit(1)
    model_meta = model_rows[0]
else:
    model_rows = list(bq.query(
        f"SELECT * FROM `{model_table}` ORDER BY model_version DESC LIMIT 1"
    ).result())
    if not model_rows:
        print(f"  ERROR: No BM25 models found. Run build_bm25.py first.")
        exit(1)
    model_meta = model_rows[0]
    target_version = model_meta.model_version

print(f"  Target version: {target_version}")
print(f"  Trained at: {model_meta.trained_at}")
print(f"  Parameters: k1={model_meta.k1}, b={model_meta.b}, epsilon={model_meta.epsilon}")
print(f"  Corpus: {model_meta.corpus_size} chunks, Vocab: {model_meta.vocab_size} terms, avgdl: {model_meta.avgdl:.1f}")

# Load vocabulary for this version
vocab_rows = list(bq.query(
    f"SELECT term, term_index, idf FROM `{vocab_table}` WHERE model_version = {target_version}"
).result())
vocab_map = {row.term: row.term_index for row in vocab_rows}
idf_map = {row.term: row.idf for row in vocab_rows}

print(f"  Loaded {len(vocab_map)} vocabulary terms")

# Model parameters for scoring
k1 = model_meta.k1
b = model_meta.b
avgdl = model_meta.avgdl

# =============================================================================
# 2. Find chunks needing update
# =============================================================================

print("\n" + "=" * 60)
print("2. Reading chunks from BigQuery")
print("=" * 60)

sources = [
    {
        "table": f"{BQ_TABLE_PREFIX}_reddit_chunks",
        "source_type": "reddit",
        "select": "chunk_id, text_content, topics, methods_mentioned, bm25_model_version",
    },
    {
        "table": f"{BQ_TABLE_PREFIX}_zoom_chunks",
        "source_type": "zoom",
        "select": "chunk_id, text_content, topics, action_items, bm25_model_version",
    },
    {
        "table": f"{BQ_TABLE_PREFIX}_pdf_chunks",
        "source_type": "pdf",
        "select": "chunk_id, text_content, topics, functions_referenced, bm25_model_version",
    },
]

# Add BM25 columns to each table if they don't exist (idempotent)
bm25_columns = [
    ("bm25_indices", "ARRAY<INT64>"),
    ("bm25_values", "ARRAY<FLOAT64>"),
    ("bm25_text", "STRING"),
    ("bm25_model_version", "INT64"),
]

for src in sources:
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{src['table']}"
    for col_name, col_type in bm25_columns:
        try:
            bq.query(f"ALTER TABLE `{table_ref}` ADD COLUMN {col_name} {col_type}").result()
            print(f"  Added column {col_name} to {src['source_type']}")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                pass
            else:
                raise

# Read chunks and filter to those needing update
chunks_to_update = []
skipped = 0

for src in sources:
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{src['table']}"
    query = f"SELECT {src['select']} FROM `{table_ref}`"
    rows = list(bq.query(query).result())

    for row in rows:
        current_version = row.bm25_model_version if hasattr(row, 'bm25_model_version') else None

        if not args.all and current_version is not None and current_version >= target_version:
            skipped += 1
            continue

        bm25_text = build_bm25_text(row, src["source_type"])
        chunks_to_update.append({
            "chunk_id": row.chunk_id,
            "source_type": src["source_type"],
            "bm25_text": bm25_text,
        })

    type_count = sum(1 for c in chunks_to_update if c["source_type"] == src["source_type"])
    print(f"  {src['source_type']}: {type_count} to update, {len(rows) - type_count} up-to-date")

print(f"  Total: {len(chunks_to_update)} chunks to update, {skipped} already current")

if not chunks_to_update:
    print("\n  All chunks are up-to-date. Nothing to do.")
    exit(0)

# =============================================================================
# 3. Compute sparse embeddings
# =============================================================================

print("\n" + "=" * 60)
print("3. Computing sparse embeddings")
print("=" * 60)

for chunk in chunks_to_update:
    indices, values = create_bm25_sparse_embedding(
        chunk["bm25_text"], vocab_map, idf_map, k1, b, avgdl
    )
    chunk["bm25_indices"] = indices
    chunk["bm25_values"] = values

n_terms = [len(c["bm25_indices"]) for c in chunks_to_update]
print(f"  Computed {len(chunks_to_update)} embeddings")
print(f"  Non-zero terms per chunk: min={min(n_terms)}, max={max(n_terms)}, avg={sum(n_terms)/len(n_terms):.1f}")

# =============================================================================
# 4. Update BigQuery chunk tables
# =============================================================================

print("\n" + "=" * 60)
print("4. Updating BigQuery chunk tables")
print("=" * 60)

bq_tables = {
    "reddit": f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_reddit_chunks",
    "zoom": f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_zoom_chunks",
    "pdf": f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_pdf_chunks",
}

updated = {stype: 0 for stype in bq_tables}
for chunk in chunks_to_update:
    table_ref = bq_tables[chunk["source_type"]]
    update_query = f"""
        UPDATE `{table_ref}`
        SET bm25_indices = @indices,
            bm25_values = @values,
            bm25_text = @bm25_text,
            bm25_model_version = @version
        WHERE chunk_id = @chunk_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("indices", "INT64", chunk["bm25_indices"]),
            bigquery.ArrayQueryParameter("values", "FLOAT64", chunk["bm25_values"]),
            bigquery.ScalarQueryParameter("bm25_text", "STRING", chunk["bm25_text"]),
            bigquery.ScalarQueryParameter("version", "INT64", target_version),
            bigquery.ScalarQueryParameter("chunk_id", "STRING", chunk["chunk_id"]),
        ]
    )
    bq.query(update_query, job_config=job_config).result()
    updated[chunk["source_type"]] += 1

for stype, count in updated.items():
    print(f"  {stype}: {count} chunks updated")

# =============================================================================
# 5. Ensure bm25_embedding field exists on each collection's vector schema
# =============================================================================

print("\n" + "=" * 60)
print("5. Checking collection vector schemas for bm25_embedding")
print("=" * 60)

collections = {
    "reddit": f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_REDDIT}",
    "zoom": f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_ZOOM}",
    "pdf": f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_PDF}",
    "combined": f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_COMBINED}",
}

for label, collection_name in collections.items():
    collection = vs_client.get_collection(
        vectorsearch_v1beta.GetCollectionRequest(name=collection_name)
    )
    if "bm25_embedding" in collection.vector_schema:
        print(f"  {label}: bm25_embedding already exists")
    else:
        print(f"  {label}: adding bm25_embedding sparse vector field...")
        collection.vector_schema["bm25_embedding"] = vectorsearch_v1beta.VectorField(
            sparse_vector=vectorsearch_v1beta.SparseVectorField()
        )
        operation = vs_client.update_collection(
            vectorsearch_v1beta.UpdateCollectionRequest(
                collection=collection,
                update_mask=FieldMask(paths=["vector_schema.bm25_embedding"]),
            )
        )
        operation.result()
        print(f"  {label}: bm25_embedding added")

# =============================================================================
# 6. Update VS2 DataObjects with sparse vectors
# =============================================================================

print("\n" + "=" * 60)
print("6. Updating Vector Search 2.0 DataObjects")
print("=" * 60)

BATCH_SIZE = 1000

# Update per-type collections
for stype in ["reddit", "zoom", "pdf"]:
    parent = collections[stype]
    type_chunks = [c for c in chunks_to_update if c["source_type"] == stype]
    if not type_chunks:
        continue

    requests = []
    for chunk in type_chunks:
        requests.append(vectorsearch_v1beta.UpdateDataObjectRequest(
            data_object={
                "name": f"{parent}/dataObjects/{chunk['chunk_id']}",
                "vectors": {
                    "bm25_embedding": {
                        "sparse": {
                            "values": chunk["bm25_values"],
                            "indices": chunk["bm25_indices"],
                        }
                    }
                },
            },
            update_mask=FieldMask(paths=["vectors"]),
        ))

    for i in range(0, len(requests), BATCH_SIZE):
        batch = requests[i:i + BATCH_SIZE]
        do_client.batch_update_data_objects(
            vectorsearch_v1beta.BatchUpdateDataObjectsRequest(
                parent=parent, requests=batch
            )
        )

    print(f"  {stype}: {len(requests)} DataObjects updated")

# Update combined collection (all updated chunks)
parent = collections["combined"]
requests = []
for chunk in chunks_to_update:
    requests.append(vectorsearch_v1beta.UpdateDataObjectRequest(
        data_object={
            "name": f"{parent}/dataObjects/{chunk['chunk_id']}",
            "vectors": {
                "bm25_embedding": {
                    "sparse": {
                        "values": chunk["bm25_values"],
                        "indices": chunk["bm25_indices"],
                    }
                }
            },
        },
        update_mask=FieldMask(paths=["vectors"]),
    ))

for i in range(0, len(requests), BATCH_SIZE):
    batch = requests[i:i + BATCH_SIZE]
    do_client.batch_update_data_objects(
        vectorsearch_v1beta.BatchUpdateDataObjectsRequest(
            parent=parent, requests=batch
        )
    )

print(f"  combined: {len(requests)} DataObjects updated")

# =============================================================================
# Done
# =============================================================================

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
print(f"  Applied model version: {target_version}")
print(f"  Chunks updated: {len(chunks_to_update)}")
print(f"  BQ tables: 3 chunk tables updated")
print(f"  VS2: 4 collections checked/updated")
