"""Turn scored cells into the tables a reader can act on.

Aggregation follows DESIGN.md §9.4: **median + IQR** for the per-config tables,
**means** for the headline. Medians saturate at 1.0 on the easy categories and
hide the tail — the ceiling effect `bigquery-context` documents — so a median-only
report would show eight identical arms.

Two rules are enforced everywhere and are the difference between a report and a
sales sheet:

* **The denominator is cells attempted, not cells that survived.** An arm that
  crashes on a third of its cells and aces the rest is not a 100% arm. Every
  table prints attempted alongside scored.
* **Unmeasured prints as `--`, never as 0.** Evidence on an opaque path,
  acquisition behind a generative service, and a component with no price are all
  absent measurements, and a zero in their place is a false claim.
"""

import statistics as st
from collections.abc import Callable, Iterable
from typing import Any

import cost as cost_module
import judge as judge_module
import mcp_clients
import scoring
import traces

DASH = "--"


def fmt(value: float | None, spec: str = ".2f") -> str:
    """Format a number, or `--` if it was never measured."""
    return DASH if value is None else format(value, spec)


def rate(items: Iterable[Any], predicate: Callable[[Any], bool]) -> float | None:
    """Fraction of items satisfying `predicate`, or None over an empty set."""
    values = list(items)
    return sum(1 for item in values if predicate(item)) / len(values) if values else None


def median_iqr(values: Iterable[float]) -> tuple[float | None, float | None]:
    """Median and interquartile range. IQR is None below four points."""
    data = sorted(values)
    if not data:
        return None, None
    if len(data) < 4:
        return st.median(data), None
    quartiles = st.quantiles(data, n=4)
    return st.median(data), quartiles[2] - quartiles[0]


def _table(headers: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    rule = "|" + "|".join("---" for _ in headers) + "|"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([line, rule, *body])


def _arms(scores: dict[str, scoring.Score]) -> list[tuple[str, int]]:
    """Every (config, tier) present, in the canonical config order."""
    seen = {(score.config, score.tier) for score in scores.values()}
    return [
        (key, tier)
        for key in mcp_clients.CONFIG_KEYS
        for tier in (0, 1)
        if (key, tier) in seen
    ]


def _group(scores: dict[str, scoring.Score], key: str, tier: int) -> list[scoring.Score]:
    return [s for s in scores.values() if s.config == key and s.tier == tier]


def _coverage(entries: list[cost_module.CellCost]) -> str:
    """How complete an arm's cost picture is. Three states, never collapsed to two.

    `--` (no attribution pass ran) is not the same as `full` (everything this
    sweep can see, it saw), and neither is the same as `floor` (a service spent
    money on our behalf and did not tell us how much).
    """
    if not entries:
        return DASH
    return "floor" if any(e.service_side_unmeasured for e in entries) else "full"


# --- tables ------------------------------------------------------------------


def capture_health(scores: dict[str, scoring.Score]) -> str:
    """What ran and what broke, per arm. Read this before any other table.

    Uneven residual failures across arms mean the factorial is not clean, and
    every accuracy number below has a different denominator than it looks like
    (DEV_NOTES 2026-09-02).
    """
    rows = []
    for key, tier in _arms(scores):
        group = _group(scores, key, tier)
        answered = [s for s in group if s.answered]
        rows.append([
            key, str(tier), str(len(group)), str(len(answered)),
            str(len(group) - len(answered)),
            str(sum(1 for s in group if s.attempts > 1)),
            fmt(rate(group, lambda s: s.ca_leak), ".0%"),
        ])
    return _table(
        ["config", "tier", "attempted", "scored", "failed", "quota-retried", "CA leak"], rows
    )


def accuracy(scores: dict[str, scoring.Score]) -> str:
    """Correctness, over cells *attempted*. Failures count against the arm."""
    rows = []
    for key, tier in _arms(scores):
        group = _group(scores, key, tier)
        rows.append([
            key, str(tier), str(len(group)),
            fmt(rate(group, lambda s: s.correct), ".0%"),
            fmt(rate(group, lambda s: s.sprang_trap), ".0%"),
            fmt(rate(group, lambda s: s.used_distractor), ".0%"),
        ])
    return _table(["config", "tier", "n", "correct", "sprang trap", "used decoy"], rows)


def acquisition(scores: dict[str, scoring.Score]) -> str:
    """The §9.1 split. `--` means the arm cannot be inspected, not that it failed.

    Tier 0 reading 0% is the design working, not a defect: there is no governed
    description at tier 0, so there is nothing to acquire and every miss is an
    acquisition failure by construction.
    """
    rows = []
    for key, tier in _arms(scores):
        group = [s for s in _group(scores, key, tier) if s.rules_required]
        inspectable = [s for s in group if s.acquisition_observable]
        rows.append([
            key, str(tier), str(len(group)),
            fmt(rate(group, lambda s: not s.acquisition_observable), ".0%"),
            fmt(rate(inspectable, lambda s: s.acquired), ".0%"),
            fmt(rate(inspectable, lambda s: s.application_loss), ".0%"),
        ])
    return _table(
        ["config", "tier", "n", "opaque", "acquired", "application loss"], rows
    )


def evidence(scores: dict[str, scoring.Score]) -> str:
    """Did the query use the governed fields? `--` where no query is disclosed."""
    rows = []
    for key, tier in _arms(scores):
        group = _group(scores, key, tier)
        observed = [s for s in group if s.evidence_observable and s.evidence_recall is not None]
        recall, recall_iqr = median_iqr(s.evidence_recall for s in observed)  # type: ignore[misc]
        precision, _ = median_iqr(
            s.evidence_precision for s in observed if s.evidence_precision is not None
        )
        rows.append([
            key, str(tier),
            fmt(rate(group, lambda s: not s.evidence_observable), ".0%"),
            fmt(recall), fmt(recall_iqr), fmt(precision),
        ])
    return _table(
        ["config", "tier", "no query disclosed", "recall (median)", "IQR", "precision"], rows
    )


def latency(scores: dict[str, scoring.Score]) -> str:
    """Wall clock, over single-attempt cells only.

    A quota-retried cell carries up to ~300s of backoff sleep in `latency_s`.
    Pooling those with clean cells publishes a fake number, so they are excluded
    and counted in a column of their own (Amendment A.3.2).
    """
    rows = []
    for key, tier in _arms(scores):
        group = _group(scores, key, tier)
        clean = [s for s in group if s.attempts == 1 and s.answered]
        median, iqr = median_iqr(s.latency_s for s in clean)
        calls, _ = median_iqr(float(s.tool_calls) for s in clean)
        rows.append([
            key, str(tier), str(len(clean)), str(len(group) - len(clean)),
            fmt(median, ".1f"), fmt(iqr, ".1f"), fmt(calls, ".1f"),
        ])
    return _table(
        ["config", "tier", "clean cells", "excluded", "median s", "IQR", "tool calls"], rows
    )


def spend(
    scores: dict[str, scoring.Score],
    costs: dict[str, cost_module.CellCost],
    prices: cost_module.Prices,
) -> str:
    """The three cost components, never summed across a measured/unmeasured line."""
    rows = []
    for key, tier in _arms(scores):
        group = _group(scores, key, tier)
        entries = [costs[s.cell_key] for s in group if s.cell_key in costs]
        # Tokens come off the capture, warehouse bytes off the attribution pass.
        # Keeping them independent means `--no-cost` still yields a token table
        # instead of a table of zeros that reads as "this arm was free".
        tokens, tokens_iqr = median_iqr(float(s.total_tokens) for s in group)
        thoughts, _ = median_iqr(float(s.thought_tokens) for s in group)
        mib, _ = median_iqr(e.bytes_billed / 2**20 for e in entries)
        usd = [e.total_usd for e in entries if e.total_usd is not None]
        rows.append([
            key, str(tier), fmt(tokens, ".0f"), fmt(tokens_iqr, ".0f"),
            fmt(thoughts, ".0f"),
            fmt(mib, ".1f"),
            fmt(st.mean(usd) if usd else None, ".5f"),
            _coverage(entries),
        ])
    note = (
        f"\n\nPrices: {prices.source or 'none supplied'}"
        f"{f' (verified {prices.verified})' if prices.verified else ''}. "
        "Token rates are unset unless a `prices.json` supplies them, so a `--` in "
        "the USD column means *unpriced*, not free. A `yes` in the last column "
        "means the arm also spent money this sweep cannot see: Conversational "
        "Analytics runs its own Gemini calls and does not report them."
    )
    return _table(
        ["config", "tier", "tokens (median)", "IQR", "thoughts", "MiB billed",
         "USD (mean)", "unmeasured spend"],
        rows,
    ) + note


def adherence(
    scores: dict[str, scoring.Score], verdicts: dict[str, judge_module.Verdict]
) -> str:
    """How the judge read the reasoning. `unclear` is a property of the path.

    An arm with a high `unclear` share is not badly behaved — it is one that does
    not show its work, which is a different and separately interesting result.
    """
    rows = []
    for key, tier in _arms(scores):
        group = [s for s in _group(scores, key, tier) if s.cell_key in verdicts]
        if not group:
            continue
        judged = [verdicts[s.cell_key] for s in group]
        rows.append([
            key, str(tier), str(len(judged)),
            *[
                fmt(
                    sum(1 for v in judged if v.adherence == value) / len(judged),
                    ".0%",
                )
                for value in judge_module.ADHERENCE_VALUES
            ],
        ])
    return _table(["config", "tier", "n", *judge_module.ADHERENCE_VALUES], rows)


def equivalence(
    cells: dict[str, traces.Cell], scores: dict[str, scoring.Score], pairs: list[tuple[str, str]]
) -> str:
    """Do two ways of reaching the same server behave the same?

    `same verdict` is the column that decides a procurement question. Two arms
    that reach identical correctness through different tool sequences are
    interchangeable in practice, whatever their traces look like.
    """
    rows = []
    for left, right in pairs:
        result = scoring.compare_arms(cells, scores, left, right)
        if not result.pairs:
            continue
        rows.append([
            left, right, str(result.pairs),
            fmt(result.fraction("same_sequence"), ".0%"),
            fmt(result.fraction("same_value"), ".0%"),
            fmt(result.fraction("same_verdict"), ".0%"),
        ])
    return _table(
        ["config A", "config B", "pairs", "same tool sequence", "same value", "same verdict"],
        rows,
    )


def headline(
    scores: dict[str, scoring.Score], costs: dict[str, cost_module.CellCost]
) -> str:
    """Means, per §9.4, and the metric that matters: what a correct answer costs.

    Cost per *correct answer* rather than per cell, because an arm that is cheap
    and wrong is not cheap. An arm with zero correct answers reports `--`; a
    division by zero here would silently print `inf` and sort to the bottom of a
    "most expensive" list, which reads as the opposite of what happened.
    """
    rows = []
    for key, tier in _arms(scores):
        group = _group(scores, key, tier)
        entries = [costs[s.cell_key] for s in group if s.cell_key in costs]
        correct = sum(1 for s in group if s.correct)
        tokens = sum(s.total_tokens for s in group)
        mib = sum(e.bytes_billed for e in entries) / 2**20 if entries else None
        usd = [e.total_usd for e in entries if e.total_usd is not None]
        rows.append([
            key, str(tier),
            fmt(rate(group, lambda s: s.correct), ".0%"),
            fmt(tokens / correct if correct else None, ".0f"),
            fmt(mib / correct if mib is not None and correct else None, ".1f"),
            fmt(sum(usd) / correct if usd and correct else None, ".5f"),
            _coverage(entries),
        ])
    return _table(
        ["config", "tier", "accuracy (mean)", "tokens / correct", "MiB / correct",
         "USD / correct", "coverage"],
        rows,
    )


# --- assembly ----------------------------------------------------------------

DEFAULT_PAIRS = [
    ("p1_managed", "p1_toolbox"),
    ("p2_managed", "p2_toolbox"),
    ("p3_managed", "p3_toolbox"),
    ("p1_managed", "p1_matched"),
    ("p3_managed", "p3_matched"),
    ("p4_bq_ca", "p4_looker_ca"),
]


def build(
    cells: dict[str, traces.Cell],
    scores: dict[str, scoring.Score],
    costs: dict[str, cost_module.CellCost],
    verdicts: dict[str, judge_module.Verdict],
    prices: cost_module.Prices,
    meta: dict[str, object],
) -> str:
    """The whole report, in reading order: what ran, then what it did, then cost."""
    schemas = meta.get("tool_schemas") or {}
    schema_rows = [
        [key, str(value.get("tools", "")), str(value.get("schema_chars", ""))]
        for key, value in sorted(
            schemas.items(), key=lambda kv: -int(kv[1].get("schema_chars", 0) or 0)
        )
    ] if isinstance(schemas, dict) else []

    sections = [
        "# Results",
        "",
        f"Model `{meta.get('agent_model')}` at temperature {meta.get('temperature')}, "
        f"{meta.get('runs')} replicates, tier fence "
        f"{'on' if meta.get('use_tier_sa') else 'OFF'}, commit `{meta.get('git_commit')}`, "
        f"started {meta.get('started')}.",
        "",
        # Stated rather than left to be counted off the tables: a capture from a
        # partial or narrowed sweep looks exactly like a full one once it is
        # scored, and every rate below is a fraction of *this* denominator.
        f"{len(scores)} cells scored across "
        f"{len({(s.config, s.tier) for s in scores.values()})} arm/tier pairs.",
        "",
        "## Headline",
        "",
        headline(scores, costs),
        "",
        "## Capture health",
        "",
        capture_health(scores),
        "",
        "**CA leak** is not a bug in the run — it is a property of the surface "
        "being measured. `ask_data_insights` ships inside the Toolbox BigQuery "
        "toolset, so `p1_toolbox` and `p3_toolbox` can reach Conversational "
        "Analytics and become Path 4 for that cell. The arms are reported as "
        "shipped rather than trimmed to be hermetic, so this column says how "
        "often it happened instead of hiding it.",
        "",
        "## Accuracy",
        "",
        accuracy(scores),
        "",
        "## Acquisition vs application",
        "",
        acquisition(scores),
        "",
        "## Evidence",
        "",
        evidence(scores),
        "",
        "## Latency",
        "",
        latency(scores),
        "",
        "## Cost",
        "",
        spend(scores, costs, prices),
        "",
        "## Semantic adherence (judged)",
        "",
        adherence(scores, verdicts),
        "",
        "## Equivalence",
        "",
        equivalence(cells, scores, DEFAULT_PAIRS),
    ]
    if schema_rows:
        sections += [
            "",
            "## Tool surface",
            "",
            "Schemas are re-sent on every turn, so their size is a per-call floor "
            "on prompt tokens. Measured live at sweep time, because a vendor can "
            "change them without notice.",
            "",
            _table(["config", "tools", "schema chars"], schema_rows),
        ]
    return "\n".join(sections) + "\n"
