"""Raw evaluation records and their JSON storage.

`run_battery.py` captures; `build_results.py` scores. These dataclasses are the
contract between the two, and they hold **no scores** — only what happened. That
split is deliberate: the rubric will change, and re-running 960 live cells to
try a new metric would be absurd (docs/method.md).

Everything a scorer could need must therefore be captured here, including tool
results, because a tool result is the only evidence that a governed rule ever
reached the agent (the acquisition half of docs/questions.md).
"""

import gzip
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Tool results are the acquisition evidence, so they are stored nearly whole.
# The cap exists only to stop a runaway `execute_sql` result from bloating the
# file; `lookup_context` on the governed corpus runs ~5 KB, well inside it.
RESULT_CHAR_LIMIT = 20_000


@dataclass
class ToolCall:
    """One tool invocation and its result, in order."""

    seq: int
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    is_error: bool = False
    # Wall clock inside the tool, so a cell's latency can be split into
    # time-in-model and time-in-tool. Without it a slow path cannot be told apart
    # from a slow *warehouse*, which is a different procurement conclusion
    # (Amendment A.3.2).
    duration_s: float = 0.0


@dataclass
class Cell:
    """One (question x config x tier x run) observation. Raw, never scored."""

    cell_key: str
    question_id: str
    category: str
    question: str
    config: str
    tier: int
    run: int
    answer: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    latency_s: float = 0.0
    error: str = ""
    # RFC3339 UTC. The join key to everything billed outside this process —
    # BigQuery jobs run under the tier SA, and CA's warehouse work runs under our
    # identity too. The sweep is sequential (§7), so a [started_at, ended_at]
    # window attributes jobs to a cell unambiguously. Cannot be backfilled: the
    # M3 capture can only ever be attributed in aggregate (Amendment A.2).
    started_at: str = ""
    ended_at: str = ""
    # How many times `agents.ask` had to try. >1 means quota backoff inflated
    # `latency_s` by up to ~300s, so latency is only comparable across cells with
    # `attempts == 1` (Amendment A.3.2).
    attempts: int = 1

    @property
    def ok(self) -> bool:
        """True when the cell produced an answer without erroring.

        `--resume` skips only successful cells, so a resume pass re-runs
        failures and is self-healing.
        """
        return not self.error and bool(self.answer.strip())

    def tool_names(self) -> list[str]:
        """The tool-name sequence, used for the Equivalence check (§9.2)."""
        return [call.name for call in self.tool_calls]


def cell_key(question_id: str, config: str, tier: int, run: int) -> str:
    """Stable identity for a cell. Must not change, or `--resume` loses its place."""
    return f"{question_id}|{config}|tier{tier}|run{run}"


def truncate(text: str) -> str:
    """Bound a tool result, marking it so a scorer never mistakes it for complete."""
    if len(text) <= RESULT_CHAR_LIMIT:
        return text
    return f"{text[:RESULT_CHAR_LIMIT]}\n...[truncated {len(text) - RESULT_CHAR_LIMIT} chars]"


# --- JSON storage ------------------------------------------------------------


def read_text(path: Path) -> str:
    """File contents, transparently gunzipped when the name ends in `.gz`.

    A capture is ~28 MB of JSON and ~3 MB gzipped. That difference decides
    whether the published file can live in the repo next to the report it backs,
    which is the whole point of publishing it — so every reader here goes through
    this rather than `Path.read_text`.
    """
    if path.suffix == ".gz":
        return gzip.decompress(path.read_bytes()).decode()
    return path.read_text()


def write_text(path: Path, text: str) -> None:
    """Counterpart to `read_text`. Compresses iff the name asks for it."""
    if path.suffix == ".gz":
        path.write_bytes(gzip.compress(text.encode(), compresslevel=9))
    else:
        path.write_text(text)


def load(path: Path) -> dict[str, Cell]:
    """Read `results.json` into cells keyed by `cell_key`. Missing file = empty."""
    if not path.exists():
        return {}
    raw = json.loads(read_text(path))
    cells = {}
    for record in raw.get("cells", []):
        calls = [ToolCall(**call) for call in record.pop("tool_calls", [])]
        cells[record["cell_key"]] = Cell(**record, tool_calls=calls)
    return cells


def save(path: Path, cells: dict[str, Cell], header: dict[str, Any]) -> None:
    """Write every cell plus the reproducibility header (docs/method.md).

    Rewrites the whole file each time rather than appending. At 960 cells the
    file is a few MB, and a single valid JSON document is worth far more than
    the saved I/O when the run is interrupted halfway.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"header": header, "cells": [asdict(cell) for cell in cells.values()]}
    write_text(path, json.dumps(payload, indent=2))


def locate(*candidates: Path) -> Path:
    """The first capture that exists, so one notebook serves two readers.

    Someone who cloned the repo has the published capture and nothing else;
    someone who ran a sweep has their own and wants to look at that. Ordering the
    candidates decides which wins, and raising rather than returning an empty
    dict means a missing file is an error at the top of the notebook instead of
    an empty table three cells later.
    """
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "No capture found. Looked for: "
        + ", ".join(str(path) for path in candidates)
        + ". Run `make smoke` or `make sweep`, or check out results/capture.json.gz."
    )


def read_header(path: Path) -> dict[str, Any]:
    """The reproducibility header from an existing results file, or empty."""
    if not path.exists():
        return {}
    header: dict[str, Any] = json.loads(read_text(path)).get("header", {})
    return header
