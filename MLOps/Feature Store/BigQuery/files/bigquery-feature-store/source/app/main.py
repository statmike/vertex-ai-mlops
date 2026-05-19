import os
import re
import time
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import bigquery_storage
from google.cloud.bigquery_storage import types as bqs_types
import pyarrow as pa

# --- Configuration from environment ---
BQ_PROJECT = os.environ['BQ_PROJECT']
BQ_DATASET = os.environ['BQ_DATASET']
BQ_TABLE = os.environ['BQ_TABLE']
FEATURE_COLUMNS = os.environ.get(
    'FEATURE_COLUMNS',
    'feature_float_1,feature_float_2,feature_float_3,feature_float_4,feature_float_5'
).split(',')
TABLE_PATH = f'projects/{BQ_PROJECT}/datasets/{BQ_DATASET}/tables/{BQ_TABLE}'


class FeatureSessionPool:
    def __init__(self, client, table, project, selected_fields, ttl_seconds=300):
        self.client = client
        self.table = table
        self.project = project
        self.selected_fields = selected_fields
        self.ttl_seconds = ttl_seconds
        self._cache = {}

    def get_session(self, row_restriction):
        self._evict_expired()
        if row_restriction in self._cache:
            return self._cache[row_restriction][0]
        session = self._create(row_restriction)
        self._cache[row_restriction] = (session, time.time())
        return session

    def _create(self, row_restriction):
        return self.client.create_read_session(
            request=dict(
                parent=f'projects/{self.project}',
                read_session=dict(
                    table=self.table,
                    data_format=bqs_types.DataFormat.ARROW,
                    read_options=dict(
                        selected_fields=self.selected_fields,
                        row_restriction=row_restriction,
                    ),
                ),
                max_stream_count=1,
            )
        )

    def _evict_expired(self):
        now = time.time()
        expired = [k for k, (_, t) in self._cache.items() if now - t > self.ttl_seconds]
        for k in expired:
            del self._cache[k]

    @property
    def cache_size(self):
        return len(self._cache)


# --- App ---
app = FastAPI(title='BigQuery Feature Store')
client = bigquery_storage.BigQueryReadClient()
pool = FeatureSessionPool(
    client=client,
    table=TABLE_PATH,
    project=BQ_PROJECT,
    selected_fields=['entity_group', 'entity_id'] + FEATURE_COLUMNS,
    ttl_seconds=300,
)

ENTITY_PATTERN = re.compile(r'^[A-Z]$')
ID_PATTERN = re.compile(r'^\d{6}$')


def read_features_sync(entity_group: str, entity_id: str) -> dict:
    restriction = f"entity_group = '{entity_group}' AND entity_id = '{entity_id}'"
    session = pool.get_session(restriction)
    if not session.streams:
        return {}
    reader = client.read_rows(session.streams[0].name)
    arrow_table = reader.to_arrow(session)
    if arrow_table.num_rows == 0:
        return {}
    return {col: arrow_table.column(col).to_pylist()[0] for col in arrow_table.column_names}


def read_features_batch_combined(entities: list[dict]) -> list[dict]:
    """Read multiple entities in a single ReadSession using a combined row_restriction.

    Builds: (entity_group, entity_id) IN (('A','000001'), ('B','000002'), ...)
    1 session + 1 stream instead of N — eliminates N-1 session creation roundtrips.
    """
    pairs = ', '.join(
        f"('{e['entity_group']}', '{e['entity_id']}')" for e in entities
    )
    restriction = f"(entity_group, entity_id) IN ({pairs})"

    session = client.create_read_session(
        request=dict(
            parent=f'projects/{BQ_PROJECT}',
            read_session=dict(
                table=TABLE_PATH,
                data_format=bqs_types.DataFormat.ARROW,
                read_options=dict(
                    selected_fields=['entity_group', 'entity_id'] + FEATURE_COLUMNS,
                    row_restriction=restriction,
                ),
            ),
            max_stream_count=1,
        )
    )
    if not session.streams:
        return []
    reader = client.read_rows(session.streams[0].name)
    arrow_table = reader.to_arrow(session)
    if arrow_table.num_rows == 0:
        return []
    return [
        {col: arrow_table.column(col).to_pylist()[i] for col in arrow_table.column_names}
        for i in range(arrow_table.num_rows)
    ]


@app.get('/features/{entity_group}/{entity_id}')
async def get_features(entity_group: str, entity_id: str):
    if not ENTITY_PATTERN.match(entity_group):
        raise HTTPException(400, 'entity_group must be a single uppercase letter')
    if not ID_PATTERN.match(entity_id):
        raise HTTPException(400, 'entity_id must be a 6-digit zero-padded number')
    features = await asyncio.to_thread(read_features_sync, entity_group, entity_id)
    if not features:
        raise HTTPException(404, 'Entity not found')
    return features


class BatchRequest(BaseModel):
    entities: list[dict]


@app.post('/features/batch')
async def get_features_batch(request: BatchRequest):
    """Per-entity batch: N individual reads via asyncio.gather."""
    for e in request.entities:
        if not ENTITY_PATTERN.match(e.get('entity_group', '')):
            raise HTTPException(400, f'Invalid entity_group: {e.get("entity_group")}')
        if not ID_PATTERN.match(e.get('entity_id', '')):
            raise HTTPException(400, f'Invalid entity_id: {e.get("entity_id")}')

    async def read_one(e):
        return await asyncio.to_thread(
            read_features_sync, e['entity_group'], e['entity_id']
        )

    results = await asyncio.gather(*[read_one(e) for e in request.entities])
    return {'features': [r for r in results if r]}


@app.post('/features/batch/combined')
async def get_features_batch_combined(request: BatchRequest):
    """Combined-restriction batch: 1 session for all entities."""
    for e in request.entities:
        if not ENTITY_PATTERN.match(e.get('entity_group', '')):
            raise HTTPException(400, f'Invalid entity_group: {e.get("entity_group")}')
        if not ID_PATTERN.match(e.get('entity_id', '')):
            raise HTTPException(400, f'Invalid entity_id: {e.get("entity_id")}')
    results = await asyncio.to_thread(read_features_batch_combined, request.entities)
    return {'features': results}


@app.get('/health')
async def health():
    return {
        'status': 'ok',
        'cached_sessions': pool.cache_size,
        'table': TABLE_PATH,
        'feature_columns': len(FEATURE_COLUMNS),
    }
