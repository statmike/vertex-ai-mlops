"""Module-level catalog data — populated once at startup via context cache.

Separated from agent.py to avoid circular imports with the tools package.
The context cache handles the actual data fetching (Dataplex lookupContext
with BQ table_documentation fallback). This module provides the
``_catalog_data`` and ``_catalog_summary`` interfaces that the reranker
callback and agent instruction builder depend on.
"""

import json
import logging

logger = logging.getLogger(__name__)

# Module-level catalog data — populated once at startup by _load_catalog()
_catalog_data: dict[str, dict] = {}  # full_ref → full metadata
_catalog_summary: str = ""           # compact text for the agent instruction


def _load_catalog() -> None:
    """Pre-load the catalog from the shared context cache.

    Produces two outputs stored in module globals:

    * ``_catalog_data`` — structured dict keyed by fully-qualified table ref.
      Each entry has: ``full_ref``, ``dataset``, ``table_name``, ``columns``,
      ``relationships``, ``description``.
    * ``_catalog_summary`` — compact text for the shortlist reranker pass.
    """
    global _catalog_data, _catalog_summary

    try:
        from agent_context.context_cache import (
            get_all_briefs,
            get_brief_summary,
            get_table_ids,
            populate_cache,
        )
        from agent_context.context_cache.cache import _CACHE

        # Populate the cache (runs lookupContext or table_documentation)
        populate_cache()

        if not _CACHE:
            return

        # Build _catalog_data from the cache
        for full_id, tc in _CACHE.items():
            parts = full_id.split(".")
            if len(parts) != 3:
                continue

            _catalog_data[full_id] = {
                "full_ref": full_id,
                "dataset": parts[1],
                "table_name": parts[2],
                "columns": tc.columns,
                "relationships": {},
                "description": tc.description,
            }

            # Try to extract relationships from detailed JSON
            try:
                detailed = json.loads(tc.detailed)
                if "relationships" in detailed:
                    _catalog_data[full_id]["relationships"] = detailed["relationships"]
            except (json.JSONDecodeError, KeyError):
                pass

        # Build compact summary from the cache
        _catalog_summary = get_brief_summary()

        logger.info(
            "Catalog loaded from context cache: %d table(s).", len(_catalog_data)
        )

    except Exception as e:
        logger.warning("Failed to load catalog from context cache: %s", e)


# Pre-load once at import time — this runs when adk web starts
_load_catalog()
