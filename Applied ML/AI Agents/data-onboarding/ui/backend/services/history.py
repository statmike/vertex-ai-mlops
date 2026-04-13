"""In-memory event history per session — supports backfill when toggling panels."""

import threading
import time

_history: dict[str, list[dict]] = {}
_lock = threading.Lock()
_counter: dict[str, int] = {}


def append(session_id: str, event: dict, source: str = "text") -> None:
    """Store a parsed event with source tag and sequential index."""
    with _lock:
        _counter.setdefault(session_id, 0)
        _counter[session_id] += 1
        entry = {
            **event,
            "_source": source,
            "_index": _counter[session_id],
            "_ts": time.time(),
        }
        _history.setdefault(session_id, []).append(entry)


def get_all(session_id: str) -> list[dict]:
    """Return all events for a session (for backfill)."""
    with _lock:
        return list(_history.get(session_id, []))


def clear(session_id: str) -> None:
    """Clear history for a session."""
    with _lock:
        _history.pop(session_id, None)
        _counter.pop(session_id, None)
