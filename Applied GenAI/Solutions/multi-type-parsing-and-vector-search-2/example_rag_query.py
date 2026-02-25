"""Minimal RAG pipeline: retrieve from Vector Search 2.0 and generate a cited response with Gemini.

Usage:
    uv run python example_rag_query.py
    uv run python example_rag_query.py "What methods handle seasonal patterns?"
"""

import sys

from pydantic import BaseModel
from google.cloud import vectorsearch_v1beta
from google import genai
from google.genai.types import GenerateContentConfig
from config import PROJECT_ID, REGION, FAST_GEMINI_MODEL, VS_COLLECTION_COMBINED

# --- Clients ---

vs_client = vectorsearch_v1beta.VectorSearchServiceClient()
search_client = vectorsearch_v1beta.DataObjectSearchServiceClient()
genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=REGION)

COMBINED = f'projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_COMBINED}'

# --- Read collection schema ---

collection = vs_client.get_collection(name=COMBINED)
schema_props = collection.data_schema['properties']

all_fields = list(schema_props.keys())
text_fields = [name for name, spec in schema_props.items() if spec.get('type') == 'string']

print(f'Collection: {VS_COLLECTION_COMBINED}')
print(f'Schema fields ({len(all_fields)}): {", ".join(sorted(all_fields))}')

# --- Collection count ---

count = search_client.aggregate_data_objects(
    vectorsearch_v1beta.AggregateDataObjectsRequest(parent=COMBINED, aggregate='COUNT')
)
print(f'DataObjects: {int(count.aggregate_results[0]["count"])}')

# --- Query ---

query = sys.argv[1] if len(sys.argv) > 1 else 'What machine learning methods work best for demand forecasting?'
print(f'\nQuery: {query}')

# --- Retrieve (hybrid semantic + text RRF) ---

output = vectorsearch_v1beta.OutputFields(data_fields=all_fields)

response = search_client.batch_search_data_objects(
    vectorsearch_v1beta.BatchSearchDataObjectsRequest(
        parent=COMBINED,
        searches=[
            vectorsearch_v1beta.Search(
                semantic_search=vectorsearch_v1beta.SemanticSearch(
                    search_text=query,
                    search_field='text_content_embedding',
                    task_type='QUESTION_ANSWERING',
                    top_k=5,
                    output_fields=output,
                )
            ),
            vectorsearch_v1beta.Search(
                text_search=vectorsearch_v1beta.TextSearch(
                    search_text=query,
                    data_field_names=text_fields,
                    top_k=5,
                    output_fields=output,
                )
            ),
        ],
        combine=vectorsearch_v1beta.BatchSearchDataObjectsRequest.CombineResultsOptions(
            ranker=vectorsearch_v1beta.Ranker(
                rrf=vectorsearch_v1beta.ReciprocalRankFusion(weights=[1.0, 1.0])
            )
        ),
    )
)
results = list(response.results[0].results) if response.results else []
print(f'Retrieved: {len(results)} chunks\n')

# --- Format context ---

blocks = []
for i, r in enumerate(results, 1):
    data = r.data_object.data
    chunk_id = data.get('chunk_id', 'unknown')
    source_type = data.get('source_type', 'unknown')
    header = f'[Source {i}] (chunk_id: {chunk_id}, type: {source_type})'

    # Include all non-empty fields as metadata
    meta_lines = []
    for field in all_fields:
        if field in ('chunk_id', 'source_type', 'text_content'):
            continue  # already in header or shown as body
        val = data.get(field)
        if val is None or val == '' or val == [] or val == 0:
            continue
        if isinstance(val, list):
            val = ', '.join(str(v) for v in val)
        meta_lines.append(f'{field}: {val}')

    meta = '\n'.join(meta_lines)
    text = data.get('text_content', '')
    if meta:
        blocks.append(f'{header}\n{meta}\n{text}')
    else:
        blocks.append(f'{header}\n{text}')

context = '\n\n'.join(blocks)

# --- Structured response schema ---


class Claim(BaseModel):
    statement: str
    source_numbers: list[int]


class GroundedResponse(BaseModel):
    claims: list[Claim]


# --- Generate ---

grounded = GroundedResponse.model_validate_json(
    genai_client.models.generate_content(
        model=FAST_GEMINI_MODEL,
        contents=f'Sources:\n\n{context}\n\nQuestion: {query}',
        config=GenerateContentConfig(
            system_instruction=(
                'You are a technical assistant. Answer the user\'s question based ONLY on '
                'the provided source documents. If the sources don\'t contain enough '
                'information, say so.\n\n'
                'Rules:\n'
                '- Break your answer into individual claims, each with its supporting source numbers\n'
                '- Every claim must cite at least one source\n'
                '- If multiple sources support a claim, include all source numbers\n'
                '- Synthesize across sources rather than summarizing each one separately\n'
                '- Keep claims concise and technical'
            ),
            response_mime_type='application/json',
            response_schema=GroundedResponse,
        ),
    ).text
)

# --- Display ---

print('--- Response ---\n')
paragraphs = []
for claim in grounded.claims:
    citations = '[' + ','.join(str(n) for n in claim.source_numbers) + ']'
    paragraphs.append(f'{claim.statement} {citations}')
print(' '.join(paragraphs))

print('--- Sources ---\n')
cited = {n for claim in grounded.claims for n in claim.source_numbers}
for i, r in enumerate(results, 1):
    data = r.data_object.data
    marker = '*' if i in cited else ' '
    print(f'  {marker} Source {i}: {data.get("chunk_id", "")} ({data.get("source_type", "")})')
