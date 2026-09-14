"""Raw evaluation records and their JSON storage.

`run_battery.py` captures; `build_results.py` scores. These dataclasses are the
contract between the two, and they hold **no scores** — only what happened. That
split is deliberate: the rubric will change, and re-running 1,800 live cells to
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
    #.
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
    # M3 capture can only ever be attributed in aggregate.
    started_at: str = ""
    ended_at: str = ""
    # How many times `agents.ask` had to try. >1 means quota backoff inflated
    # `latency_s` by up to ~300s, so latency is only comparable across cells with
    # `attempts == 1`.
    attempts: int = 1
    # What a service disclosed about its own work. Empty on every MCP arm, where
    # SQL already sits in a tool result and BigQuery jobs are attributed by the
    # window above. Populated by the direct Conversational Analytics arms, which
    # are the only place the service hands back its query plan and the job id
    # that ran it, making Path 4's BigQuery cost exact per cell rather than
    # estimated per block. Both default to empty so the
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

    Rewrites the whole file each time rather than appending. At 1,800 cells the
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


def comparable(value: object) -> str:
    """A hashable, order-stable rendering of a header value.

    Header fields hold lists (`tiers`, `configs`, `question_ids`) as well as
    scalars, and a list is unhashable. Sorting rather than preserving order is
    deliberate: two captures that declare the same tiers in a different order
    measured the same thing.

    `None` and `""` collapse to one value, which is what lets this family grow.
    Every field added to `MUST_AGREE` after a capture was taken is missing from
    that capture's header and reads as `None`; without this, adding
    `ca_thinking_mode` would have made the published capture permanently
    incomparable to everything measured against it — the guard would refuse the
    exact comparison it was added for. Both spellings mean *unset*, and unset is
    a real, checkable state: a capture that omitted the field and one that
    explicitly left it empty sent the same request.

    Lives here rather than in `compare.py` because `merge_headers` needs the
    same rule for the same reason: the published capture predates three of the
    fields in `MUST_AGREE`, and a merge that read "absent" as a disagreement
    with "empty" would refuse to add anything to it ever again.
    """
    if isinstance(value, list):
        return repr(sorted(str(item) for item in value))
    if value is None or value == "":
        return "<unset>"
    return repr(value)


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
    # What the integers in `tiers` mean. Ladder captures append rungs as tiers
    # 2, 3, 4 rather than renumbering, so shared integers keep
    # their published meaning — but a file that did renumber would pair `tier1`
    # against a different condition and report a finding. This field is what
    # makes that refusable instead of invisible.
    "tier_semantics",
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


def _ordered_union(sequences: Iterable[Iterable[str]]) -> list[str]:
    """Every element of every sequence, first-seen order, no repeats."""
    seen: list[str] = []
    for sequence in sequences:
        for item in sequence:
            if item not in seen:
                seen.append(item)
    return seen


def _question_sets(headers: list[dict[str, Any]]) -> list[set[str]]:
    """What each run asked, refusing a run that does not say.

    A header with no `question_ids` cannot be placed on the grid at all: there
    would be no way to tell a run that *extended* the factorial with new
    questions from a second run of the same cells. Refusing is the conservative
    reading, and every capture this repo has ever written records the field.
    """
    sets = []
    for header in headers:
        asked = header.get("question_ids")
        if not asked:
            raise ValueError(
                "cannot merge a capture whose header has no 'question_ids': "
                "without it, a run that adds questions and a second run of the "
                "same questions are indistinguishable."
            )
        sets.append(set(asked))
    return sets


def _runs_of(header: dict[str, Any]) -> list[dict[str, Any]]:
    """One header per sweep the file holds, flattening a capture that is already a merge.

    The published capture is itself a merge of two sweeps under two oracles
   . Merging *into* it therefore starts by taking it apart:
    treated as a single run it would arrive with no `goldens` of its own — a
    merged header deliberately carries none — and 1,800 cells would come out the
    far side ungradeable. Each record is re-inflated against the fields the
    parent holds for every run, so a run view is a header like any other.
    """
    runs = header.get("merged_from")
    if not isinstance(runs, list) or not runs:
        return [header]
    shared = {key: value for key, value in header.items() if key != "merged_from"}
    return [shared | run for run in runs]


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

    **A run may add arms, or add questions to arms already captured, and nothing
    else.** The second is what lets the three anchored re-issues land inside the
    published factorial instead of beside it. Both are bounded by one rule: the
    runs must *tile* the arm-by-question grid — disjoint, and complete. Anything
    that overlaps is two observations of one cell; anything that leaves a hole
    is a ragged grid about to be published as a factorial.
    """
    if not headers:
        return {}
    if len(headers) == 1:
        return dict(headers[0])

    # A capture that is already a merge enters as its constituent sweeps, so the
    # oracle each one froze stays attached to the arms and questions it graded.
    headers = [run for header in headers for run in _runs_of(header)]
    base = headers[0]
    for field_name in MUST_AGREE:
        # `question_ids` is checked below instead, under a rule this loop cannot
        # express: a run may *add* questions to arms already captured, which is
        # how the anchored re-issues reach the published factorial without
        # re-running the twelve. The check that replaces this one is stricter
        # where it matters — the runs must still tile a complete grid. It stays
        # in `MUST_AGREE` because the *comparator* differences two captures cell
        # by cell and must still refuse two that asked different things.
        if field_name == "question_ids":
            continue
        values = {comparable(header.get(field_name)) for header in headers}
        if len(values) > 1:
            raise ValueError(
                f"cannot merge captures that disagree on {field_name!r}: "
                f"{sorted(values)}. These runs measured different things."
            )
    question_sets = _question_sets(headers)

    merged = {key: value for key, value in base.items() if key not in PER_RUN}
    merged["started"] = min(str(header.get("started", "")) for header in headers)
    # Kept at the top level only when every run agrees, so the report's one-line
    # summary stays a fact. When they disagree it exists per run and nowhere else.
    scans = {header.get("quality_scans") for header in headers}
    if len(scans) == 1:
        merged["quality_scans"] = scans.pop()

    configs: list[str] = []
    claimed: dict[str, set[str]] = {}
    schemas: dict[str, Any] = {}
    for header, questions in zip(headers, question_sets, strict=True):
        for key in header.get("configs", []):
            # An arm may appear in two runs only when they asked *different*
            # questions — that extends the factorial rather than re-running it,
            # and `merge_cells` still refuses any cell key that repeats. Same arm
            # asking the same question in two runs is the case this has always
            # caught: two observations of one cell landing in one denominator.
            repeated = claimed.get(key, set()) & questions
            if repeated:
                raise ValueError(
                    f"config {key!r} appears in more than one capture asking "
                    f"{sorted(repeated)}; merging would mix two runs of the same arm "
                    "into one denominator"
                )
            if key not in configs:
                configs.append(key)
            claimed.setdefault(key, set()).update(questions)
        schemas.update(header.get("tool_schemas") or {})
    merged["configs"] = configs
    merged["question_ids"] = _ordered_union(
        header.get("question_ids") or [] for header in headers
    )
    # The runs have to *tile* the grid, not merely avoid colliding on it. Each
    # covers its own arms times its own questions, the loop above proved those
    # patches are disjoint, so a merge is a complete factorial exactly when the
    # areas add up to the whole. Without this, two runs that each asked a
    # different question of a different arm would merge into a 2x2 grid holding
    # two cells and publish it as a factorial.
    covered = sum(
        len(header.get("configs", [])) * len(questions)
        for header, questions in zip(headers, question_sets, strict=True)
    )
    if covered != len(configs) * len(merged["question_ids"]):
        raise ValueError(
            f"these captures do not tile a factorial: {covered} arm-question pairs "
            f"across {len(configs)} arms and {len(merged['question_ids'])} question_ids. "
            "A run may add arms, or add question_ids to every arm already present, "
            "but a merge that leaves some arm never asked some question would "
            "publish a ragged grid as a complete one."
        )
    merged["tool_schemas"] = schemas
    merged["total_cells"] = sum(int(header.get("total_cells", 0)) for header in headers)
    merged["merged_from"] = [
        {
            "git_commit": header.get("git_commit", "unknown"),
            "started": header.get("started", ""),
            "configs": list(header.get("configs", [])),
            # Which questions this run's oracle is authoritative for. An arm can
            # now appear in two runs, so the arm alone no longer says which
            # frozen block grades a cell — see `goldens_by_cell`.
            "question_ids": list(header.get("question_ids", [])),
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


def goldens_by_cell(
    header: dict[str, Any], pairs: Iterable[tuple[str, str]]
) -> dict[tuple[str, str], dict[str, Any]]:
    """The frozen oracle for each (arm, question), omitting any pair with none.

    One entry per arm *and question* rather than one per capture, because a
    merged capture has one oracle per **run**, and (arm, question) is what
    identifies the run a cell came from. Arm alone used to be enough; it stopped
    being enough when `merge_headers` started allowing a run that adds questions
    to arms already captured.

    Keying this finely also disposes of a hazard that would otherwise arrive
    with those runs. `battery.freeze_oracle` freezes **all** of `golden.GOLDENS`
    regardless of `--questions`, so a run that asked three questions still
    carries fifteen values, twelve of them re-measured days later and drifted
    against the run that actually asked them. Those twelve are never reachable
    here: a golden key is only ever looked up through the question that uses it,
    and that question routes to its own run's block.

    An unmerged capture answers with its single `goldens` block for every pair
    asked about, so the published capture re-scores exactly as it did before
    this existed. Same for a merged run written before `question_ids` was
    recorded per run: it answers for every question, which is what it meant when
    arms could not overlap. The caller passes the pairs it actually holds rather
    than trusting the header, so a cell present in the capture but missing from
    the header cannot silently come back unscored.
    """
    runs = header.get("merged_from")
    if isinstance(runs, list) and runs:
        available: dict[tuple[str, str], dict[str, Any]] = {}
        for run in runs:
            if not run.get("goldens"):
                continue
            asked = run.get("question_ids") or header.get("question_ids") or []
            for config_key in run.get("configs", []):
                for question_id in asked:
                    available[(config_key, question_id)] = run["goldens"]
        return {pair: available[pair] for pair in pairs if pair in available}
    frozen = header.get("goldens")
    if not frozen:
        return {}
    return {pair: frozen for pair in pairs}


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
