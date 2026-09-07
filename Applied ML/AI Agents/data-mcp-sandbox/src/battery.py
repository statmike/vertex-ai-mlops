"""Plan and run the evaluation sweep, one cell at a time.

The sweep is a full factorial: every question, on every config, at every tier,
repeated `runs` times. At the default n=5 that is 12 x 12 x 2 x 5 = 1,440 cells
(docs/method.md).

This module **captures only**. No scoring happens here and none should: the
rubric will change, and re-running 1,440 live cells to try a new metric would be
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
import ca_direct
import catalog_setup
import config
import golden
import mcp_clients
import toolbox_server
import traces

QUESTIONS_PATH = Path(config.PROJECT_ROOT) / "examples" / "questions.json"
# Raw captures, not the scored output. `results/raw/` is gitignored: 1,440 cells with
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

    `ca_thinking_mode` and `ca_model` are recorded even on sweeps with no direct
    arm, where they change nothing. A field that appears only when it mattered is
    a field a reader has to reason about the absence of, and `compare.align`
    treats a missing value and an unset one as the same thing anyway.

    `ca_model` is a constant `""` today — the enum has exactly one selectable
    value, so there is nothing to choose and the request omits the field
    (Amendment C.4). It is recorded, and in `MUST_AGREE`, so that the day a
    second value appears the guard is already in place rather than being invented
    after a capture has silently mixed two of them.
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
        "ca_thinking_mode": config.CA_THINKING_MODE,
        "ca_model": ca_direct.CA_MODEL,
        "runs": current.runs,
        "tiers": current.tiers,
        "configs": current.config_keys,
        "question_ids": [question.id for question in current.questions],
        "total_cells": len(current),
    }


async def ask(config_key: str, tier: int, question: str) -> agents.Outcome:
    """Run one cell on whichever transport the arm uses.

    The dispatch lives here rather than inside `agents.ask` because `ca_direct`
    imports `agents` for the `Outcome` shape and the retry policy; having
    `agents` reach back would be a cycle. The battery is the one module that
    already knows about both, so it is the cycle-free place to choose.
    """
    if mcp_clients.is_direct(config_key):
        return await ca_direct.ask(config_key, tier, question)
    return await agents.ask(config_key, tier, question)


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
        if mcp_clients.is_direct(key):
            sizes[key] = ca_direct.tool_surface(key)
            continue
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
        emitted_sql=outcome.emitted_sql,
        bq_job_ids=outcome.bq_job_ids,
    )


# How stale a carried-over oracle may be before a resume says so. Four of the
# twelve golden values are trailing windows anchored at build time, and the
# measured drift is ~2% a day against a 0.5% tolerance — so a day is roughly
# where "the same answer" stops being true.
ORACLE_STALE_HOURS = 24


def freeze_oracle(current: Plan, results_path: Path, resume: bool) -> dict[str, Any]:
    """The oracle to grade this sweep by, resolved now or carried from the file.

    Resolved at sweep **start**, which is the whole point: the corpus anchors
    its timestamps to build time, so `SELECT` answers move with the calendar and
    an oracle frozen at export time describes a different day than the cells it
    grades. The published capture carries ~24h of exactly that skew.

    A resume keeps the oracle the file already has. The alternative — re-freezing
    — would regrade the cells captured on day one against day two's answers,
    which is the same error moved from export into resume. What a resume cannot
    fix is that its *new* cells really did run later, so when the carried oracle
    is old this says so rather than pretending one number covers both.
    """
    if resume:
        existing = traces.read_header(results_path)
        frozen = existing.get("goldens")
        if frozen:
            since = _hours_since(existing.get("goldens_frozen_at", ""))
            stale = f", {since:.0f}h ago" if since is not None else ""
            print(f"oracle: carried over from the interrupted run{stale}")
            if since is not None and since >= ORACLE_STALE_HOURS:
                print(
                    f"         WARNING: that oracle is {since / 24:.1f} days old and four "
                    "golden values are trailing windows.\n"
                    "         Cells added by this resume are graded against the older "
                    "day. Start a fresh sweep for a clean oracle."
                )
            return {
                "goldens": frozen,
                "goldens_frozen_at": existing.get("goldens_frozen_at", ""),
            }
        print("oracle: the interrupted run froze none, resolving now")

    print(f"oracle: resolving {len(golden.GOLDENS)} goldens against tiers "
          f"{', '.join(str(tier) for tier in current.tiers)}")
    return {
        "goldens": golden.freeze(current.tiers),
        "goldens_frozen_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def _hours_since(timestamp: str) -> float | None:
    """Age of an RFC3339 timestamp in hours, or None when it cannot be read."""
    try:
        then = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return None
    return (datetime.now(UTC) - then).total_seconds() / 3600


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

    # Before anything is spent. Resolving the oracle needs BigQuery, and finding
    # out it is unreachable should cost seconds at cell 0 rather than produce a
    # 25-hour capture nobody can grade.
    meta.update(freeze_oracle(current, results_path, resume))

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

        outcome = await ask(config_key, tier, question.question)
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
