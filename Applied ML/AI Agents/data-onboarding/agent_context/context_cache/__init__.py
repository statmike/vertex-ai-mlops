"""Context cache — pre-fetched table metadata with brief and detailed views.

Populated once at module import time. Both views are derived from the
Dataplex lookupContext API (JSON format) when available, with a fallback
to the existing BQ ``table_documentation`` approach.

- **brief**: schema columns with name, type, and description only
- **detailed**: full JSON including dataProfile stats (nullRatio, distinctValues, sampleValues)

Keyed by ``project.dataset.table``.
"""

from .cache import (
    get_all_briefs,
    get_all_detailed,
    get_brief_summary,
    get_detailed_for_tables,
    get_table_columns_from_cache,
    get_table_ids,
    is_cached,
    populate_cache,
)

__all__ = [
    "get_all_briefs",
    "get_all_detailed",
    "get_brief_summary",
    "get_detailed_for_tables",
    "get_table_columns_from_cache",
    "get_table_ids",
    "is_cached",
    "populate_cache",
]
