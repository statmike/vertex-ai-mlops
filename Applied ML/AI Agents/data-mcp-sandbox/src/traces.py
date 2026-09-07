"""Raw evaluation records and their JSON storage.

`run_battery.py` captures; `build_results.py` scores. These dataclasses are the
contract between the two, and they hold **no scores** — only what happened. That
split is deliberate: the rubric will change, and re-running 1,440 live cells to
try a new metric would be absurd (docs/method.md).

Everything a scorer could need must therefore be captured here, including tool
results, because a tool result is the only evidence that a governed rule ever
reached the agent (the acquisition half of docs/questions.md).
"""

import gzip
import json
from collections.abc import Iterable
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
    # What a service disclosed about its own work. Empty on every MCP arm, where
    # SQL already sits in a tool result and BigQuery jobs are attributed by the
    # window above. Populated by the direct Conversational Analytics arms, which
    # are the only place the service hands back its query plan and the job id
    # that ran it, making Path 4's BigQuery cost exact per cell rather than
    # estimated per block (Amendment B.4.2). Both default to empty so the
    # published capture, written before these fields existed, still deserializes
    # and re-scores unchanged.
    emitted_sql: list[str] = field(default_factory=list)
    bq_job_ids: list[str] = field(default_factory=list)

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

    Rewrites the whole file each time rather than appending. At 1,440 cells the
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


# --- Merging two captures ------------------------------------------------------

# Header fields that must agree before two captures may be merged, because the
# report renders exactly one value for each and a merged file would silently
# publish one run's setting as if it covered both. `runs`, `tiers` and
# `question_ids` are here for the same reason a denominator is: a report over
# cells captured at different replicate counts is not a factorial any more.
MUST_AGREE = (
    "project",
    "agent_model",
    "model_location",
    "temperature",
    "toolbox_version",
    "use_tier_sa",
    "ca_thinking_mode",
    "ca_model",
    "runs",
    "tiers",
    "question_ids",
)

# Not on that list, because it legitimately differs and the difference is worth
# publishing rather than refusing. `quality_scans` says whether this sandbox's
# Dataplex scans existed, which changes what `lookup_context` returns on Path 3
# tier 1 and nothing else; a Path 4 run taken after they were provisioned is
# perfectly comparable to a Path 1-3 run taken before. So it moves per-run
# instead, and `report._scan_state` says which runs had them.
PER_RUN = (
    "git_commit",
    "started",
    "configs",
    "total_cells",
    "goldens",
    "goldens_frozen_at",
    "quality_scans",
)


def merge_headers(headers: list[dict[str, Any]]) -> dict[str, Any]:
    """One header describing several runs, refusing to flatten what differs.

    The fields in `MUST_AGREE` are checked rather than picked, because picking
    is how a merged capture comes to claim the wrong model or the wrong tier
    fence. Everything that legitimately differs is unioned: `configs` and
    `tool_schemas` grow, `total_cells` is recomputed, and `started` takes the
    earliest.

    `git_commit` is the one field that cannot be unioned honestly — different
    cells were produced by different code — so it is *replaced* by
    `merged_from`, a per-run record of commit, start and arm list. `report.py`
    prints that list instead of a single commit whenever it is present, and the
    top-level `git_commit` is dropped so nothing downstream can read one
    run's commit as the whole capture's provenance.

    **`goldens` moves the same way, and for a sharper reason.** Four of this
    corpus's oracle values are trailing-window aggregates over data anchored at
    build time, so the right answer *moves with the calendar* — the active-user
    count was measured drifting 2,671 → 2,786 across the two days between the
    published sweep and the direct-API one (`docs/adapting.md`). Carrying the
    base run's frozen oracle onto a later run's cells would grade correct
    answers as wrong, at 4% drift against a 0.5% tolerance, and would publish
    that as the new arm being inaccurate. Each run therefore keeps the oracle
    that was true when it ran, and no top-level `goldens` survives to be applied
    to cells it does not belong to.
    """
    if not headers:
        return {}
    if len(headers) == 1:
        return dict(headers[0])

    base = headers[0]
    for field_name in MUST_AGREE:
        values = {json.dumps(header.get(field_name), sort_keys=True) for header in headers}
        if len(values) > 1:
            raise ValueError(
                f"cannot merge captures that disagree on {field_name!r}: "
                f"{sorted(values)}. These runs measured different things."
            )

    merged = {key: value for key, value in base.items() if key not in PER_RUN}
    merged["started"] = min(str(header.get("started", "")) for header in headers)
    # Kept at the top level only when every run agrees, so the report's one-line
    # summary stays a fact. When they disagree it exists per run and nowhere else.
    scans = {header.get("quality_scans") for header in headers}
    if len(scans) == 1:
        merged["quality_scans"] = scans.pop()

    configs: list[str] = []
    schemas: dict[str, Any] = {}
    for header in headers:
        for key in header.get("configs", []):
            if key in configs:
                raise ValueError(
                    f"config {key!r} appears in more than one capture; merging would "
                    "mix two runs of the same arm into one denominator"
                )
            configs.append(key)
        schemas.update(header.get("tool_schemas") or {})
    merged["configs"] = configs
    merged["tool_schemas"] = schemas
    merged["total_cells"] = sum(int(header.get("total_cells", 0)) for header in headers)
    merged["merged_from"] = [
        {
            "git_commit": header.get("git_commit", "unknown"),
            "started": header.get("started", ""),
            "configs": list(header.get("configs", [])),
            "total_cells": header.get("total_cells", 0),
            "quality_scans": header.get("quality_scans"),
            # Absent rather than empty when the run never froze one, so the
            # scorer can tell "this run has no oracle" from "this run's oracle
            # was empty" and refuse rather than silently resolve today's.
            **({"goldens": header["goldens"]} if header.get("goldens") else {}),
            # Travels with the oracle it timestamps. On its own it would be a
            # date with nothing to date; alongside `started` it is the only way a
            # reader can see how far the grading drifted from the grading run.
            **(
                {"goldens_frozen_at": header["goldens_frozen_at"]}
                if header.get("goldens_frozen_at")
                else {}
            ),
        }
        for header in headers
    ]
    return merged


def goldens_by_config(
    header: dict[str, Any], configs: Iterable[str]
) -> dict[str, dict[str, Any]]:
    """The frozen oracle for each of `configs`, omitting any arm that has none.

    One entry per arm rather than one per capture, because a merged capture has
    one oracle per *run* and the arms are how a cell knows which run it came
    from (`merge_headers` refuses to put an arm in two runs, which is what makes
    that lookup total).

    An unmerged capture answers with its single `goldens` block for every arm
    asked about, so the published capture re-scores exactly as it did before
    this existed. The caller passes the arms it actually holds rather than
    trusting the header's `configs` list, so an arm present in the cells but
    missing from the header cannot silently come back unscored.
    """
    runs = header.get("merged_from")
    if isinstance(runs, list) and runs:
        available = {
            config_key: run["goldens"]
            for run in runs
            if run.get("goldens")
            for config_key in run.get("configs", [])
        }
        return {key: available[key] for key in configs if key in available}
    frozen = header.get("goldens")
    if not frozen:
        return {}
    return {config_key: frozen for config_key in configs}


def merge_cells(captures: list[dict[str, Cell]]) -> dict[str, Cell]:
    """Every cell from every capture, refusing a key that appears twice.

    A duplicate is not a merge conflict to resolve quietly — it means the same
    (question, arm, tier, run) was observed twice, and choosing one silently
    would let a re-run replace a recorded failure with a success. Re-running a
    failed cell is what `--resume` is for, in place, against the same file.
    """
    merged: dict[str, Cell] = {}
    for cells in captures:
        overlap = sorted(set(cells) & set(merged))
        if overlap:
            raise ValueError(
                f"{len(overlap)} cell key(s) appear in more than one capture, "
                f"starting with {overlap[0]!r}. Use --resume to re-run cells in place."
            )
        merged.update(cells)
    return merged
