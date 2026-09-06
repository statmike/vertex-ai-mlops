"""Plan and run the evaluation sweep, one cell at a time.

The sweep is a full factorial: every question, on every config, at every tier,
repeated `runs` times. At the default n=5 that is 12 x 8 x 2 x 5 = 960 cells
(docs/method.md).

This module **captures only**. No scoring happens here and none should: the
rubric will change, and re-running 960 live cells to try a new metric would be
absurd. `traces.Cell` is the contract handed to `build_results.py`.

Three properties the sweep depends on, all of them deliberate:

* **Strictly sequential.** `usage.py` accumulates into a module global and
  latency is a measured variable, so two cells in flight would blend both.
* **Written after every cell.** A sweep is hours long and gets interrupted.
  Each cell is durable the moment it finishes, so `--resume` never loses more
  than the cell in progress.
* **Failures are recorded, not dropped.** A cell that errors is an observation
  about that architecture. Dropping it would flatter whichever path crashes
  most (docs/method.md).
"""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import agents
import catalog_setup
import config
import mcp_clients
import toolbox_server
import traces

QUESTIONS_PATH = Path(config.PROJECT_ROOT) / "examples" / "questions.json"
# Raw captures, not the scored output. `results/raw/` is gitignored: 960 cells with
# full tool results is tens of MB and is reproducible with `make sweep`, whereas the
# scored tables and plots that land beside it are small and tracked.
RESULTS_PATH = Path(config.PROJECT_ROOT) / "results" / "raw" / "results.json"
DEFAULT_RUNS = 5


@dataclass(frozen=True)
class Question:
    """One battery question and the evidence a scorer will look for."""

    id: str
    category: str
    question: str
    evidence: dict[str, list[str]]
    golden_key: str


def load_questions(path: Path = QUESTIONS_PATH) -> list[Question]:
    """Read `questions.json`, failing loudly on an unknown field."""
    records = json.loads(path.read_text())
    return [Question(**record) for record in records]


@dataclass(frozen=True)
class Plan:
    """The exact list of cells a run will execute, in execution order."""

    questions: list[Question]
    config_keys: list[str]
    tiers: list[int]
    runs: int
    cells: list[tuple[Question, str, int, int]]

    def __len__(self) -> int:
        return len(self.cells)


def plan(
    questions: list[Question],
    config_keys: list[str],
    tiers: list[int],
    runs: int,
) -> Plan:
    """Enumerate cells in config-major order.

    Ordered config, then tier, then question, then replicate — so an interrupted
    sweep leaves *whole configs* finished rather than a thin slice of every one.
    A partial results file is then still comparable across the paths it covers,
    instead of being uninterpretable until the last cell lands.
    """
    cells = [
        (question, config_key, tier, run)
        for config_key in config_keys
        for tier in tiers
        for question in questions
        for run in range(1, runs + 1)
    ]
    return Plan(
        questions=questions, config_keys=config_keys, tiers=tiers, runs=runs, cells=cells
    )


def _git_commit() -> str:
    """The commit the sweep ran at, so a results file can be traced to code."""
    try:
        result = subprocess.run(  # noqa: S603, S607 - fixed args, no user input
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=config.PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def header(current: Plan) -> dict[str, Any]:
    """The reproducibility block stored alongside the cells (docs/method.md).

    `use_tier_sa` is here because it is the difference between a measured
    isolation boundary and none at all. A results file that does not say which
    it was cannot be interpreted later.
    """
    return {
        "started": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "project": config.PROJECT_ID,
        "agent_model": config.AGENT_MODEL,
        "model_location": config.MODEL_LOCATION,
        "temperature": agents.TEMPERATURE,
        "toolbox_version": toolbox_server.TOOLBOX_VERSION,
        "use_tier_sa": config.USE_TIER_SA,
        "runs": current.runs,
        "tiers": current.tiers,
        "configs": current.config_keys,
        "question_ids": [question.id for question in current.questions],
        "total_cells": len(current),
    }


async def measure_schemas(config_keys: list[str]) -> dict[str, dict[str, int]]:
    """Serialized size of each config's tool declarations, measured once per sweep.

    This is a *result*, not diagnostics. Tool schemas are re-sent on every turn,
    so their size sets a per-call floor on prompt tokens — and it turned out to
    predict observed cost almost exactly, with one vendor endpoint's
    `get_table_info` alone accounting for 65% of an arm's surface (Amendment A.1).
    Recorded in the header because it is a vendor detail that can change without
    notice, which would silently move every cost number in the report.
    """
    sizes: dict[str, dict[str, int]] = {}
    for key in config_keys:
        bound = None
        try:
            _agent, bound = agents.build(key, 1)
            chars = 0
            count = 0
            for toolset in bound.toolsets:
                for tool in await toolset.get_tools():
                    count += 1
                    chars += len(str(tool._get_declaration()))  # noqa: SLF001
            sizes[key] = {"tools": count, "schema_chars": chars}
        except Exception as e:  # noqa: BLE001 - a header is never worth failing a sweep over
            sizes[key] = {"error": 1, "detail": str(e)[:80]}  # type: ignore[dict-item]
        finally:
            if bound is not None:
                bound.close()
    return sizes


def to_cell(
    question: Question, config_key: str, tier: int, replicate: int, outcome: agents.Outcome
) -> traces.Cell:
    """One agent run, in the shape the capture stores and the scorer reads.

    A named function rather than a literal inside the sweep loop so that running
    a single cell by hand — the walkthrough notebook does exactly this — produces
    a record identical to one the sweep wrote, and scores through the same path.
    """
    return traces.Cell(
        cell_key=traces.cell_key(question.id, config_key, tier, replicate),
        question_id=question.id,
        category=question.category,
        question=question.question,
        config=config_key,
        tier=tier,
        run=replicate,
        answer=outcome.answer,
        tool_calls=outcome.tool_calls,
        usage=outcome.usage,
        latency_s=outcome.latency_s,
        error=outcome.error,
        started_at=outcome.started_at,
        ended_at=outcome.ended_at,
        attempts=outcome.attempts,
    )


def _fmt(seconds: float) -> str:
    """Compact duration, for a progress line that has to stay on one row."""
    if seconds < 90:
        return f"{seconds:.0f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 90:
        return f"{minutes}m{secs:02d}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h{mins:02d}m"


async def run(
    current: Plan,
    results_path: Path = RESULTS_PATH,
    resume: bool = False,
    dry_run: bool = False,
) -> dict[str, traces.Cell]:
    """Execute a plan, writing results after each cell.

    With `resume`, cells already present *and successful* are skipped; failed
    ones are re-run, which makes a resume pass self-healing rather than a way to
    make errors permanent.
    """
    cells = traces.load(results_path) if resume else {}
    meta = header(current)
    todo = [
        cell
        for cell in current.cells
        if not (
            resume
            and (found := cells.get(traces.cell_key(cell[0].id, cell[1], cell[2], cell[3])))
            and found.ok
        )
    ]

    skipped = len(current) - len(todo)
    print(f"{len(current)} cells planned, {skipped} already done, {len(todo)} to run")
    if dry_run:
        for question, config_key, tier, replicate in todo:
            print(f"  {traces.cell_key(question.id, config_key, tier, replicate)}")
        return cells

    meta["tool_schemas"] = await measure_schemas(current.config_keys)
    # Environment state, not code state: with these scans in place Path 3's
    # `lookup_context` adds a `qualityStatus` line per governed table, so captures
    # taken either side of provisioning are not comparable on Path 3 tier 1.
    # Measured here rather than in `header()` because it is a live call, and
    # `--dry-run` returns above.
    meta["quality_scans"] = catalog_setup.quality_scans_present()

    started = time.monotonic()
    for index, (question, config_key, tier, replicate) in enumerate(todo, start=1):
        key = traces.cell_key(question.id, config_key, tier, replicate)
        # Keep `config.SCOPE` in step with the cell, so anything reading it
        # resolves to this tier's dataset rather than the process default.
        config.set_active_tier(tier)

        outcome = await agents.ask(config_key, tier, question.question)
        cells[key] = to_cell(question, config_key, tier, replicate, outcome)
        traces.save(results_path, cells, meta)

        elapsed = time.monotonic() - started
        remaining = (elapsed / index) * (len(todo) - index)
        status = "ok " if cells[key].ok else "FAIL"
        print(
            f"[{index}/{len(todo)}] {status} {key}  "
            f"{outcome.latency_s:.1f}s  {len(outcome.tool_calls)} calls  "
            f"eta {_fmt(remaining)}"
        )
        if outcome.error:
            print(f"         {outcome.error[:160]}")

    print(f"\nDone in {_fmt(time.monotonic() - started)} — {results_path}")
    return cells


def summarize(cells: dict[str, traces.Cell]) -> str:
    """A short capture-health table. Not scoring — just what ran and what broke."""
    if not cells:
        return "No cells."

    lines = [f"{'config':<16} {'tier':>4} {'cells':>6} {'ok':>4} {'failed':>7} {'avg s':>7}"]
    for config_key in mcp_clients.CONFIG_KEYS:
        for tier in config.TIERS:
            group = [
                cell
                for cell in cells.values()
                if cell.config == config_key and cell.tier == tier
            ]
            if not group:
                continue
            ok = sum(1 for cell in group if cell.ok)
            avg = sum(cell.latency_s for cell in group) / len(group)
            lines.append(
                f"{config_key:<16} {tier:>4} {len(group):>6} {ok:>4} "
                f"{len(group) - ok:>7} {avg:>7.1f}"
            )
    return "\n".join(lines)
