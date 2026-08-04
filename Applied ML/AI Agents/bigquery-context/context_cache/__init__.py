"""Shared context cache — brief and detailed table metadata for all in-scope tables.

Auto-populated at module import time.  Used by approaches 3, 4, and 5.
"""

from .cache import (
    get_all_briefs,
    get_all_detailed,
    get_detailed_for_tables,
    get_table_ids,
    repopulate_for_tier,
)

__all__ = [
    "get_all_briefs",
    "get_all_detailed",
    "get_detailed_for_tables",
    "get_table_ids",
    "repopulate_for_tier",
]
