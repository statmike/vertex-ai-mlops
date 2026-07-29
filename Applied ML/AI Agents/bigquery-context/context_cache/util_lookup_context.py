"""SDK client for the Knowledge Catalog ``lookup_context`` API.

``lookup_context`` is available in the ``google-cloud-dataplex`` SDK (>=2.20.0)
via ``CatalogServiceClient.lookup_context``.  The feature is **preview**.
Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026); the API namespace remains ``dataplex`` (``dataplex_v1``).

The context capsule returned per entry bundles schema + descriptions +
per-column profiling stats and — when the catalog is enriched — glossary terms,
``frequent_joins`` join hints, sample SQL queries, and usage statistics.

The preview JSON capsule wraps entries as ``{"resources": [...]}``, keys the
entry path on ``resource`` (not ``name``), and reports profiling stats inline on
each column.  We normalize that back to a flat array of entries — each with a
``name`` field and nested ``dataProfile`` — so the cache and reranker see one
stable shape and this module is the only place that tracks the capsule format.

See: https://cloud.google.com/dataplex/docs/retrieve-data-context
"""

import json

from google.cloud import dataplex_v1

from config import BQ_LOCATION, GOOGLE_CLOUD_PROJECT

# lookupContext options is a protobuf map<string,string>, so every value is a
# string and the format is lowercase (yaml | xml | json; default yaml).
#
# Runtime-verify (preview API): the budget key is ambiguous — the REST/proto
# reference documents ``context_budget`` while a Google Python sample uses
# ``budget``; both take a *string* value. We omit budget entirely for now (full
# capsule). If capsules get too large, add ``"context_budget": "<n>"`` here and
# confirm which key the server honors. ``all_schema_fields`` ("true"/"false") is
# also documented but unverified.

_client: dataplex_v1.CatalogServiceClient | None = None

# Profiling stats the preview capsule reports inline on each schema column. We
# fold them back under a nested ``dataProfile`` object (see _normalize_resource).
_PROFILE_FIELDS = ("nullRatio", "distinctValues", "sampleValues")


def _get_client() -> dataplex_v1.CatalogServiceClient:
    global _client
    if _client is None:
        _client = dataplex_v1.CatalogServiceClient()
    return _client


def _normalize_column(col: dict) -> dict:
    """Fold a capsule column's inline profiling stats under ``dataProfile``.

    The preview ``lookup_context`` capsule reports ``nullRatio`` /
    ``distinctValues`` / ``sampleValues`` inline on each column. The cache
    (brief-vs-detailed split) and the reranker prompt both key on a nested
    ``dataProfile`` object, so we regroup them here and leave every other
    column key (``name``, ``type``, ``description``, ``mode``, plus any future
    enrichment key such as glossary ``related_terms``) untouched.
    """
    out = {}
    profile = {}
    for key, value in col.items():
        if key in _PROFILE_FIELDS:
            profile[key] = value
        else:
            out[key] = value
    if profile:
        out["dataProfile"] = profile
    return out


def _normalize_resource(resource: dict) -> dict:
    """Reshape one preview-capsule resource into the flat entry the cache expects.

    The preview API returns ``{"resources": [{...}]}`` where each resource keys
    the entry path on ``resource`` (with ``catalogEntry`` / ``simpleName``
    alongside) rather than ``name``. Downstream code (``cache.py``,
    ``bigquery_context.ipynb``) expects a flat entry with a ``name`` field and
    nested per-column ``dataProfile``. We remap the entry-path key to ``name``,
    normalize the columns, and pass every other key (including catalog
    enrichments like glossary terms, ``frequent_joins``, and ``guidelines``)
    straight through so new capsule fields flow to the reranker automatically.
    """
    out = {}
    for key, value in resource.items():
        if key == "schema" and isinstance(value, list):
            out["schema"] = [_normalize_column(col) for col in value]
        else:
            out[key] = value
    # Provide the ``name`` field the cache indexes on (old REST capsule key).
    if "name" not in out:
        out["name"] = resource.get("resource") or resource.get("catalogEntry", "")
    return out


def lookup_context(
    entry_names: list[str],
    format: str = "JSON",
) -> str:
    """Call the Knowledge Catalog lookupContext API for a batch of entries.

    Args:
        entry_names: Catalog entry names (max 10 per call). Format:
            projects/{project}/locations/{location}/entryGroups/@bigquery/
            entries/bigquery.googleapis.com/projects/{project}/datasets/{dataset}/tables/{table}
        format: Response format — "JSON", "YAML", or "XML" (case-insensitive).

    Returns:
        The context string from the API (LLM-ready formatted metadata). For
        "JSON" this is normalized to a JSON-array string (one flat entry per
        requested resource, with ``name`` and nested ``dataProfile``) so the
        cache and reranker see the capsule shape they expect. Non-JSON formats
        are returned verbatim.
    """
    client = _get_client()

    request = dataplex_v1.LookupContextRequest(
        name=(
            f"projects/{GOOGLE_CLOUD_PROJECT}"
            f"/locations/{BQ_LOCATION.lower()}"
        ),
        resources=entry_names,
        options={"format": format.lower()},
    )

    response = client.lookup_context(request=request)
    context = response.context or ""

    if format.upper() != "JSON" or not context:
        return context

    # The preview capsule wraps entries as {"resources": [...]}, keys the entry
    # path on ``resource``, and reports profiling stats inline per column. The
    # rest of the codebase (built against the earlier REST capsule) expects a
    # flat array of entries with a ``name`` field and nested ``dataProfile`` —
    # normalize here so that boundary is the only place that knows the shape.
    parsed = json.loads(context)
    resources = parsed.get("resources", []) if isinstance(parsed, dict) else parsed
    normalized = [_normalize_resource(r) for r in resources]
    return json.dumps(normalized)


def lookup_context_batched(
    entry_names: list[str],
    batch_size: int = 10,
    format: str = "JSON",
) -> str:
    """Call lookupContext in batches (API limit is 10 entries per call).

    Args:
        entry_names: All catalog entry names to look up.
        batch_size: Max entries per API call (default 10, the API max).
        format: Response format — "JSON", "YAML", or "XML".

    Returns:
        For JSON format: a single JSON array string with all entries merged.
        For other formats: concatenated context strings from all batches.
    """
    all_context = []

    for i in range(0, len(entry_names), batch_size):
        batch = entry_names[i : i + batch_size]
        context = lookup_context(batch, format=format)
        if context:
            all_context.append(context)

    if not all_context:
        return "[]" if format == "JSON" else ""

    if format == "JSON":
        merged = []
        for ctx in all_context:
            merged.extend(json.loads(ctx))
        return json.dumps(merged, indent=2)

    return "\n".join(all_context)
