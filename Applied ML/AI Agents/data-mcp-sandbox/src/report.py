"""Turn scored cells into the tables a reader can act on.

Aggregation follows docs/method.md: **median + IQR** for the per-config tables,
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

import config
import cost as cost_module
import judge as judge_module
import mcp_clients
import scoring
import service_tokens
import traces

DASH = "--"
# The fourth coverage state. Named once so the table cell and the legend that
# explains it cannot drift out of agreement.
SERVICE_ONLY = "service only"


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


def table(headers: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    rule = "|" + "|".join("---" for _ in headers) + "|"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([line, rule, *body])


def _tiers_in(scores: dict[str, scoring.Score]) -> list[int]:
    """Every tier the capture holds, in ladder reading order.

    Read off the capture, never off `config.TIERS`: a report is rendered from a
    file, and the reader's `LADDER` env var says nothing about what that file
    contains. This was `(0, 1)`, which is not a filter but a silent truncation —
    a five-rung capture rendered as a two-tier one, three rungs missing from
    every table below and nothing anywhere saying so.

    Ordered by `RUNG_ORDER` because the tier integers are append-only and
    deliberately not monotone (see config.py); sorting by the integer would print
    the ladder in the order 0, 1, 2, 3, 4 with rung 4 second.
    """
    return sorted({score.tier for score in scores.values()}, key=config.rung_key)


def _is_ladder(scores: dict[str, scoring.Score]) -> bool:
    """Whether this capture is a ladder — asked of the capture, not the environment."""
    return bool({score.tier for score in scores.values()} - {0, 1})


def _tier_head(scores: dict[str, scoring.Score]) -> str:
    """What the tier column is called. Two tiers have no ladder to be a position in."""
    return "rung" if _is_ladder(scores) else "tier"


def _tier_cell(scores: dict[str, scoring.Score], tier: int) -> str:
    """A tier's cell in a table.

    A ladder prints the rung. The integers are not monotone, so a column reading
    0, 2, 3, 4, 1 invites the reader to draw the trend in file order and get it
    backwards. Nothing is lost: `rungs()` maps rung to `cell_key` once, above.
    """
    if not _is_ladder(scores):
        return str(tier)
    return str(config.rung_of(tier)) if tier in config.RUNG_ORDER else f"?{tier}"


def _arms(scores: dict[str, scoring.Score]) -> list[tuple[str, int]]:
    """Every (config, tier) present, in canonical config order then rung order."""
    seen = {(score.config, score.tier) for score in scores.values()}
    return [
        (key, tier)
        for key in mcp_clients.CONFIG_KEYS
        for tier in _tiers_in(scores)
        if (key, tier) in seen
    ]


def _group(scores: dict[str, scoring.Score], key: str, tier: int) -> list[scoring.Score]:
    return [s for s in scores.values() if s.config == key and s.tier == tier]


def _per(total: float | None, correct: int, present: object = True) -> float | None:
    """`total` per correct answer, or `None` if that ratio would be a fiction.

    Three ways it is a fiction, and all three print `--`: nothing was measured
    (`total is None`), the pass that would have measured it never ran (`present`
    falsy), or the arm got nothing right. That last one matters most — dividing by
    zero correct answers yields `inf`, which sorts to the *bottom* of a
    most-expensive list and so reads as the exact opposite of what happened.
    """
    if total is None or not present or not correct:
        return None
    return total / correct


def _no_local_model(group: list[scoring.Score]) -> bool:
    """True when nothing in this arm ever called a model *in this process*.

    The direct-API arms hand the whole question to Conversational Analytics and
    read back an answer; no local turn happens, so `usage.py` correctly records
    zero. Reporting that zero as a token count would make the least visible arm
    look like the cheapest one — the exact accounting artifact `cost.py` exists
    to prevent. Derived from the capture rather than from a list of arm names,
    so a future transport that behaves the same way is covered without an edit.

    `model_calls is None` means *not recorded*, and never satisfies this — a
    capture or a `scores.json` predating the field must keep its token numbers.
    """
    return bool(group) and all(s.model_calls == 0 for s in group)


def _coverage(entries: list[cost_module.CellCost], no_local_model: bool = False) -> str:
    """How complete an arm's cost picture is. Four states, never collapsed.

    `--` (no attribution pass ran) is not the same as `full` (everything this
    sweep can see, it saw), and neither is the same as `floor` (a service spent
    money on our behalf and did not tell us how much). `service only` is the
    strongest form of `floor`: not an understatement of the model bill but the
    whole of it, because the caller never ran a model.
    """
    if no_local_model:
        return SERVICE_ONLY
    if not entries:
        return DASH
    return "floor" if any(e.service_side_unmeasured for e in entries) else "full"


# --- tables ------------------------------------------------------------------


def rungs(scores: dict[str, scoring.Score]) -> str:
    """What each rung of the ladder carries. Printed once, so the tables stay narrow.

    Empty for a two-tier capture: there is no ladder to be a position in, and a
    legend explaining that tier 0 is tier 0 is noise. The `cell key` column is
    what makes the append-don't-renumber scheme legible — it is the only place
    the raw integer appears, and anyone reading `traces.cell_key` needs it.
    """
    if not _is_ladder(scores):
        return ""
    rows = [
        [
            _tier_cell(scores, tier),
            f"`tier{tier}`",
            config.TIER_LABELS.get(tier, "unknown tier"),
            ", ".join(config.RUNG_CHANNELS.get(tier, ())) or "nothing",
        ]
        for tier in _tiers_in(scores)
    ]
    return "\n\n".join([
        table(["rung", "cell key", "increment", "carries"], rows),
        "Rungs are cumulative and the tier integers are append-only, so they are "
        "not in rung order — `tier1` is the top rung, not the second. Every table "
        "below is sorted by rung.",
    ])


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
            key, _tier_cell(scores, tier), str(len(group)), str(len(answered)),
            str(len(group) - len(answered)),
            str(sum(1 for s in group if s.attempts > 1)),
            fmt(rate(group, lambda s: s.ca_leak), ".0%"),
        ])
    return table(
        ["config", _tier_head(scores), "attempted", "scored", "failed", "quota-retried", "CA leak"],
        rows,
    )


def accuracy(scores: dict[str, scoring.Score]) -> str:
    """Correctness, over cells *attempted*. Failures count against the arm."""
    rows = []
    for key, tier in _arms(scores):
        group = _group(scores, key, tier)
        rows.append([
            key, _tier_cell(scores, tier), str(len(group)),
            fmt(rate(group, lambda s: s.correct), ".0%"),
            fmt(rate(group, lambda s: s.sprang_trap), ".0%"),
            fmt(rate(group, lambda s: s.used_distractor), ".0%"),
        ])
    return table(["config", _tier_head(scores), "n", "correct", "sprang trap", "used decoy"], rows)


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
            key, _tier_cell(scores, tier), str(len(group)),
            fmt(rate(group, lambda s: not s.acquisition_observable), ".0%"),
            fmt(rate(inspectable, lambda s: s.acquired), ".0%"),
            fmt(rate(inspectable, lambda s: s.application_loss), ".0%"),
        ])
    return table(
        ["config", _tier_head(scores), "n", "opaque", "acquired", "application loss"], rows
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
            key, _tier_cell(scores, tier),
            fmt(rate(group, lambda s: not s.evidence_observable), ".0%"),
            fmt(recall), fmt(recall_iqr), fmt(precision),
        ])
    return table(
        ["config", _tier_head(scores), "no query disclosed", "recall (median)", "IQR", "precision"],
        rows,
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
            key, _tier_cell(scores, tier), str(len(clean)), str(len(group) - len(clean)),
            fmt(median, ".1f"), fmt(iqr, ".1f"), fmt(calls, ".1f"),
        ])
    return table(
        ["config", _tier_head(scores), "clean cells", "excluded", "median s", "IQR", "tool calls"],
        rows,
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
        # An arm with no local model turn has no token measurement at all, so
        # its three token columns are absent rather than zero.
        absent = _no_local_model(group)
        tokens, tokens_iqr = median_iqr(float(s.total_tokens) for s in group)
        thoughts, _ = median_iqr(float(s.thought_tokens) for s in group)
        mib, _ = median_iqr(e.bytes_billed / 2**20 for e in entries)
        usd = [e.total_usd for e in entries if e.total_usd is not None]
        rows.append([
            key, _tier_cell(scores, tier),
            DASH if absent else fmt(tokens, ".0f"),
            DASH if absent else fmt(tokens_iqr, ".0f"),
            DASH if absent else fmt(thoughts, ".0f"),
            fmt(mib, ".1f"),
            fmt(st.mean(usd) if usd else None, ".5f"),
            _coverage(entries, absent),
        ])
    note = (
        f"\n\nPrices: {prices.source or 'none supplied'}"
        f"{f' (verified {prices.verified})' if prices.verified else ''}. "
        "Token rates are unset unless a `prices.json` supplies them, so a `--` in "
        "the USD column means *unpriced*, not free. Dollars are the only derived "
        "number in this report and the only one that depends on a rate card, "
        "which is why every other column is in units consumed.\n\n"
        "The last column is how complete the picture is. **full** means everything "
        "this sweep spent, it saw. **floor** means the arm also spent model tokens "
        "server-side that the API never reported back — Conversational Analytics "
        "runs its own Gemini loop on our behalf. A floor is a lower bound, not a "
        "total, and it is not small: `make service-tokens` meters it from Cloud "
        f"Monitoring and finds `{service_tokens.MEASURED_ARM}` consumed "
        f"{service_tokens.MEASURED_UNDERSTATEMENT}x the tokens recorded here."
    )
    # Only explain a state the table actually contains. A legend for an absent
    # state is noise, and adding it unconditionally would have rewritten the
    # published report's prose without a single number moving.
    if any(row[-1] == SERVICE_ONLY for row in rows):
        note += (
            f" **{SERVICE_ONLY}** means the arm never called a model in this "
            "process at all — the direct-API arms hand the question to the "
            "service and read back an answer — so its token columns read `--`. "
            "That is absent, not free; the model spend is entirely on the meter "
            "this report cannot see."
        )
    return table(
        ["config", _tier_head(scores), "tokens (median)", "IQR", "thoughts", "MiB billed",
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
            key, _tier_cell(scores, tier), str(len(judged)),
            *[
                fmt(
                    sum(1 for v in judged if v.adherence == value) / len(judged),
                    ".0%",
                )
                for value in judge_module.ADHERENCE_VALUES
            ],
        ])
    return table(["config", _tier_head(scores), "n", *judge_module.ADHERENCE_VALUES], rows)


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
    return table(
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

    **Reported in units consumed, not money.** Tokens in, tokens out, seconds,
    BigQuery jobs and the bytes they scanned — five things a reader can check
    against their own invoice. Dollars are a *derived* number that needs a rate
    card, and rates differ by region, edition and committed-use discount, so a
    USD column is the one figure here that is guaranteed wrong for most readers.
    It still exists (`prices.json`, opt-in) but it is no longer the headline.

    Input and output are split because they neither cost nor behave alike: output
    is several times the price of input on every published rate card, and it is
    the column that moves when an arm starts reasoning instead of retrieving.
    Summed, those two effects hide each other.
    """
    rows = []
    for key, tier in _arms(scores):
        group = _group(scores, key, tier)
        entries = [costs[s.cell_key] for s in group if s.cell_key in costs]
        correct = sum(1 for s in group if s.correct)
        mib = sum(e.bytes_billed for e in entries) / 2**20 if entries else None
        has = entries or None
        absent = _no_local_model(group)
        rows.append([
            key, _tier_cell(scores, tier),
            fmt(rate(group, lambda s: s.correct), ".0%"),
            # Tokens and seconds come off the capture (`group`), not the cost pass
            # (`entries`), so `--no-cost` still yields a usage table rather than a
            # row of dashes. Only the warehouse columns need the attribution pass.
            # Tokens-per-correct is the column a reader ranks arms on, which is
            # why an arm with no local model turn must not print a 0 into it.
            DASH if absent else fmt(_per(sum(s.prompt_tokens for s in group), correct), ".0f"),
            DASH if absent else fmt(_per(sum(s.output_tokens for s in group), correct), ".0f"),
            fmt(_per(sum(s.latency_s for s in group), correct), ".0f"),
            fmt(_per(sum(e.bq_jobs for e in entries), correct, has), ".1f"),
            fmt(_per(mib, correct), ".1f"),
            _coverage(entries, absent),
        ])
    return table(
        ["config", _tier_head(scores), "accuracy (mean)", "tokens in / correct",
         "tokens out / correct", "sec / correct", "BQ jobs / correct",
         "MiB / correct", "coverage"],
        rows,
    )


def _scan_state(meta: dict[str, Any]) -> str:
    """How the capture header answers "did this sandbox's DQ scans exist?".

    Three states, not two. A header written before `quality_scans` was recorded
    cannot claim the scans were absent — it simply did not look, and saying
    "no" would report an unmeasured thing as a zero.
    """
    return _scan_word(meta.get("quality_scans", "missing"))


def _scan_word(present: object) -> str:
    if present is True:
        return "present"
    if present is False:
        return "absent"
    return "not recorded"


def _scan_states(meta: dict[str, Any]) -> str:
    """The scan state per run, for a merged capture whose runs disagree.

    A merged capture can straddle the day the scans were provisioned. Printing
    one word for it would say something untrue about half its cells, and the
    half it is untrue about is the half a reader cares about — the Path 3 arms.

    Keyed by commit rather than by arm: `provenance` runs immediately before
    this in the same sentence and has just spelled out which arms each commit
    produced, so naming them again costs a line of arm keys to say nothing new.
    """
    runs = meta.get("merged_from")
    if not isinstance(runs, list) or not runs:
        return _scan_state(meta)
    if "quality_scans" in meta:
        return _scan_state(meta)
    return "; ".join(
        f"{_scan_word(run.get('quality_scans'))} for `{run.get('git_commit')}`"
        for run in runs
    )


def provenance(meta: dict[str, Any]) -> str:
    """Which code produced these cells, and when.

    A single-run capture has one answer and prints it. A merged one has several,
    and printing the first would attribute every cell to code that never ran
    most of them — so `traces.merge_headers` drops the top-level `git_commit`
    and leaves `merged_from` in its place, which this expands into one clause
    per run. Arms are named rather than counted because that is the question a
    reader actually has: *which* numbers came from which commit.
    """
    runs = meta.get("merged_from")
    if not isinstance(runs, list) or not runs:
        return f"commit `{meta.get('git_commit')}`, started {meta.get('started')}"
    parts = [
        f"`{run.get('git_commit')}` ({', '.join(run.get('configs', []))}, "
        f"started {run.get('started')})"
        for run in runs
    ]
    return f"merged from {len(runs)} runs: " + "; ".join(parts)


def _reads_context(config_key: str) -> bool:
    """Whether this arm can call `lookup_context`, and so can see a scan verdict.

    Derived from the arm's own tool surface rather than from `path == 3`, so an
    arm that gains or loses the tool changes this answer instead of contradicting
    it. An arm this does not know about is treated as not reading context: a
    capture can name an arm the current code has dropped, and warning about a
    row that is not in the report helps nobody.
    """
    arm = mcp_clients.CONFIGS.get(config_key)
    if arm is None:
        return False
    tools = list(arm.toolbox_tools)
    tools += [tool for allowed in arm.managed_urls.values() for tool in allowed]
    return "lookup_context" in tools


def _scan_note(meta: dict[str, Any]) -> str:
    """Warn when a capture cannot say which Path 3 environment it was taken in.

    `lookup_context` renders a `qualityStatus` line per governed table only when
    these scans exist, so two captures either side of them being provisioned are
    not comparable on Path 3 tier 1 — on all three Path 3 arms, since all three
    call it. Empty when the header says, because then the reader already has the
    answer.

    Not `search_dq_scans`, which is the obvious guess and is wrong: the tier
    identities hold no `dataplex.datascans.*` permission, so every scan tool is
    denied either side of provisioning (docs/reproducing.md).
    """
    if meta.get("quality_scans") in (True, False):
        return ""
    runs = meta.get("merged_from")
    if not isinstance(runs, list) or not runs:
        scope = (
            "This capture predates the `quality_scans` header field, so it "
            "cannot state whether this sandbox's Dataplex data-quality scans "
            "existed when it ran."
        )
    else:
        # A merged capture can straddle the provisioning, so only some of its
        # arms are affected — and of those, only the ones that call
        # `lookup_context` at all. Naming them is worth more than the blanket
        # warning, because the reader's next move is to decide which rows to
        # distrust and the unnamed ones are fine.
        affected = sorted(
            {
                config_key
                for run in runs
                if run.get("quality_scans") not in (True, False)
                for config_key in run.get("configs", [])
                if _reads_context(config_key)
            }
        )
        if not affected:
            return ""
        scope = (
            f"The {', '.join(affected)} cells predate the `quality_scans` "
            "header field, so this capture cannot state whether this sandbox's "
            "Dataplex data-quality scans existed when they ran."
        )
    return (
        f"> **Path 3 comparability.** {scope} That matters for Path 3 tier 1 "
        "only: with the scans in place `lookup_context` adds a `qualityStatus` "
        "line per governed table, and all three Path 3 arms call it. Do not merge "
        "tier-1 Path 3 cells from this capture with cells from a fresh "
        "`make setup`, which now creates them. See `docs/reproducing.md`.\n"
    )


def headline_note(costs: dict[str, cost_module.CellCost]) -> str:
    """Why the headline table must not be read as a cost ranking.

    The `coverage` column already says which arms are floors, but a column value
    is easy to skim past when the numbers next to it are the smallest on the
    page — and they are exactly the smallest *because* they are incomplete. The
    one arm that has been metered moved from cheapest to third most expensive on
    correction, so the floors are not a rounding error and sorting by the token
    columns produces a ranking that is upside down at the top.

    Derived from the data rather than written down, so an arm that stops being a
    floor (or a new one that starts) changes this text instead of contradicting
    it. Returns empty when nothing is a floor, because then there is no caveat.
    """
    floors = sorted({
        entry.config for entry in costs.values() if entry.service_side_unmeasured
    })
    if not floors:
        return ""
    named = ", ".join(f"`{arm}`" for arm in floors)
    return (
        f"**Do not sort this table by the cost columns.** {named} carry "
        f"`floor` coverage: they spend model tokens server-side that the API "
        f"never reports, so their figures are lower bounds and every other "
        f"arm's are totals. Comparing them directly compares two different "
        f"quantities. The gap is not small — `make service-tokens` meters "
        f"`{service_tokens.MEASURED_ARM}` from Cloud Monitoring at "
        f"{service_tokens.MEASURED_ACTUAL_PER_CELL:,} tokens per cell against "
        f"the {service_tokens.MEASURED_RECORDED_PER_CELL:,} recorded here, a "
        f"{service_tokens.MEASURED_UNDERSTATEMENT}x understatement that moves "
        f"it from the cheapest arm to the third most expensive. The floors are "
        f"left uncorrected in the table on purpose: the meter attributes by "
        f"time block, not per cell, and splitting a block across cells that "
        f"vary in turn count would invent a distribution. Two honest numbers "
        f"in two places beat one fused number that hides which half was "
        f"inferred.\n\n"
        f"Accuracy, latency and the BigQuery columns are unaffected — those "
        f"are measured client-side for every arm."
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

    ladder_legend = rungs(scores)

    sections = [
        "# Results",
        "",
        f"Model `{meta.get('agent_model')}` at temperature {meta.get('temperature')}, "
        f"{meta.get('runs')} replicates, tier fence "
        f"{'on' if meta.get('use_tier_sa') else 'OFF'}, {provenance(meta)}. "
        f"Dataplex quality scans: {_scan_states(meta)}.",
        "",
        _scan_note(meta),
        # Stated rather than left to be counted off the tables: a capture from a
        # partial or narrowed sweep looks exactly like a full one once it is
        # scored, and every rate below is a fraction of *this* denominator.
        f"{len(scores)} cells scored across "
        f"{len({(s.config, s.tier) for s in scores.values()})} arm/tier pairs."
        # Appended rather than added as its own section: `rungs` is empty for a
        # two-tier capture, and an empty section would put a stray blank line
        # into the published report for a feature it is not using.
        + (f"\n\n{ladder_legend}" if ladder_legend else ""),
        "",
        "## Headline",
        "",
        headline(scores, costs),
        "",
        headline_note(costs),
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
            table(["config", "tools", "schema chars"], schema_rows),
        ]
    return "\n".join(sections) + "\n"
