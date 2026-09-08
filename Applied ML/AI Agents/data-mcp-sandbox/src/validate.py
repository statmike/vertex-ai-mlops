"""Check that the corpus, the oracle, and the questions still agree.

These three describe the same experiment from three angles — `corpus.py` says what
the tables are, `golden.py` says what the right answer is, `questions.json` says
what to ask — and they are joined by *name*, not by anything a type checker sees.
Adapting the sandbox to your own warehouse means editing all three, and the
failure modes are quiet:

* A `golden_key` that matches no golden resolves to `None`, which is a **legitimate
  state** for a prose question. So a typo is indistinguishable from intent, and
  every cell for that question scores wrong. You find out after paying for the
  sweep.
* An evidence term that matches no column can never be recalled, so the arm's
  evidence score is a floor forever — a false finding, not an error.

Both are the "unmeasured reported as zero" mistake the rest of this project takes
pains to avoid, arriving by typo. This module is the offline, no-credentials check
that turns them into a message before anything is provisioned or spent.

Run it with `make validate`. `scripts/setup.py` calls it first and refuses to
provision an incoherent set.
"""

import json
from pathlib import Path

import compare
import config
import corpus
import golden
import lookml
import scoring

QUESTIONS_PATH = Path(config.PROJECT_ROOT) / "examples" / "questions.json"


def corpus_names() -> set[str]:
    """Every table and column name an evidence term is allowed to reference."""
    return {t.name for t in corpus.CORPUS} | {
        c.name for t in corpus.CORPUS for c in t.columns
    }


def looker_problems() -> list[str]:
    """The corpus -> LookML seam, which only Path 2 and `p4_looker_ca` depend on.

    `lookml.render_all()` walks `corpus.CORPUS` and looks each table up in two
    hand-maintained dicts. A table these do not cover raises `KeyError` — loud,
    but only once you reach `make lookml`, which is after BigQuery is provisioned.
    Checking here moves that to the free offline step.

    Kept separate from `problems()` because a BigQuery-only adapter running with
    SKIP_LOOKER has no reason to be blocked by it.
    """
    found: list[str] = []
    for table in corpus.CORPUS:
        if table.name not in lookml.VIEW_NAMES:
            found.append(
                f"lookml.VIEW_NAMES has no view name for table {table.name!r}, "
                "so render_all() raises KeyError"
            )
        key = lookml.PRIMARY_KEYS.get(table.name)
        if not key:
            found.append(
                f"lookml.PRIMARY_KEYS has no primary key for table {table.name!r}. "
                "Without one Looker cannot use symmetric aggregates and a summed "
                "measure fans out across the join, silently inflating it."
            )
        elif key not in {c.name for c in table.columns}:
            found.append(
                f"lookml.PRIMARY_KEYS[{table.name!r}] is {key!r}, which is not a "
                f"column of that table"
            )
        for column in table.columns:
            if column.type not in lookml.LOOKER_TYPES and column.type not in lookml.TIME_TYPES:
                found.append(
                    f"{table.name}.{column.name} is {column.type}, which lookml.py "
                    "cannot render. Add it to LOOKER_TYPES or TIME_TYPES."
                )

    views = set(lookml.VIEW_NAMES.values())
    if config.LOOKER_EXPLORE not in views:
        found.append(
            f"config.LOOKER_EXPLORE is {config.LOOKER_EXPLORE!r}, which is not one of "
            f"the generated views {sorted(views)}. The Explore would reference nothing."
        )
    return found


def ladder_problems() -> list[str]:
    """Check the governance ladder is a ladder before anything is provisioned.

    `RUNG_CHANNELS` is a hand-written table joined to the provisioning code by
    string, which is the same join this module exists to police everywhere else.
    Its failures are the quiet kind: a rung that carries the wrong channels does
    not error, it produces a step of zero and reads as *"this increment of
    governance does not pay"* — a false finding at the end of a 25.8-hour sweep
    rather than a message before it starts.

    Runs whether or not the ladder is enabled. The table is wrong the same way
    either way, and the run that discovers it should not be the expensive one.
    """
    found: list[str] = []
    order, channels = config.RUNG_ORDER, config.RUNG_CHANNELS

    if set(order) != set(channels):
        found.append(
            f"ladder: RUNG_ORDER covers tiers {sorted(order)} but RUNG_CHANNELS "
            f"defines {sorted(channels)}"
        )
    if len(set(order)) != len(order):
        found.append(f"ladder: RUNG_ORDER repeats a tier: {order}")

    # The published tiers keep their published meaning, or every existing capture
    # is silently re-interpreted: 1,440 shipped cells are keyed on tier0/tier1.
    if order and order[0] != 0:
        found.append(f"ladder: rung 0 must be tier 0 (the published control), not {order[0]}")
    if order and order[-1] != 1:
        found.append(
            f"ladder: the top rung must be tier 1 (the published governed tier), not {order[-1]}"
        )
    if channels.get(0):
        found.append(f"ladder: tier 0 is the ungoverned control but carries {channels[0]}")
    if set(channels.get(1, ())) != set(config.CHANNELS):
        found.append(
            "ladder: tier 1 must carry every channel — it is the published governed "
            f"tier, and the ladder's top rung has to reproduce it. Missing: "
            f"{sorted(set(config.CHANNELS) - set(channels.get(1, ())))}"
        )

    for tier, names in channels.items():
        unknown = [name for name in names if name not in config.CHANNELS]
        if unknown:
            found.append(f"ladder: tier {tier} names unknown channels {unknown}")
        if len(set(names)) != len(names):
            found.append(f"ladder: tier {tier} repeats a channel: {names}")

    # Cumulative, and strictly so. A rung that adds nothing is a rung that costs
    # 432 cells to measure a step that cannot exist.
    for lower, upper in zip(order, order[1:], strict=False):
        below, above = set(channels.get(lower, ())), set(channels.get(upper, ()))
        if not below < above:
            found.append(
                f"ladder: tier {upper} (rung {config.rung_of(upper)}) must add to tier "
                f"{lower} (rung {config.rung_of(lower)}) and carry everything it has. "
                f"Has {sorted(above)}, below has {sorted(below)}"
            )

    if set(order) - {0, 1} != set(config.LADDER_RUNGS):
        found.append(
            f"ladder: LADDER_RUNGS says the ladder adds {sorted(config.LADDER_RUNGS)} but "
            f"RUNG_ORDER adds {sorted(set(order) - {0, 1})}. `estimate.rate_for` prices "
            "off LADDER_RUNGS, so a rung missing from it is priced at the worst arm on "
            "the table and one wrongly in it is priced off a tier it does not resemble."
        )

    # The capture this config would produce has to be comparable to the published
    # one, or the ladder's replication check is impossible — and that is decided
    # by a table in `compare.py`, edited separately from the name here. Renaming
    # the scheme without adding the pair is not an error at capture time, at merge
    # time, or at export time. It surfaces as a refusal from `compare_captures.py`
    # after the sweep, which is the most expensive possible moment to find out.
    scheme = config.tier_semantics()
    if scheme and 0 not in compare.shared_tiers(["", scheme]):
        found.append(
            f"ladder: tier vocabulary {scheme!r} is not declared compatible with the "
            "published scheme in `compare.SEMANTICS_SHARE`, so no capture taken with "
            "this config could be compared against the published one on any tier. Add "
            f"`frozenset({{'', {scheme!r}}}): (0, 1)` if tiers 0 and 1 still mean what "
            "they mean there."
        )

    # Looker is excluded from the ladder by design — a shared instance this
    # project is a guest on. A rung that reached it would be adding content to
    # someone else's Looker, which is the one thing this project must never do.
    strays = [tier for tier in config.LOOKER_TIERS if tier not in (0, 1)]
    if strays:
        found.append(f"ladder: LOOKER_TIERS must stay (0, 1); the ladder cannot reach {strays}")

    return found


def problems(path: Path = QUESTIONS_PATH, include_looker: bool = True) -> list[str]:
    """Every inconsistency found, as readable lines. Empty means coherent.

    Returns rather than raises so a caller can print all of them at once. An
    adapter who has renamed a table wants the whole list, not the first item
    followed by eleven more runs.
    """
    found: list[str] = []
    questions = json.loads(path.read_text())
    known = corpus_names()

    found += ladder_problems()

    # --- corpus internal consistency ---
    # Tier-1 governance is built from these, so a gap here silently weakens the
    # governed arm rather than failing.
    for table in corpus.CORPUS:
        if table.name not in corpus.GUIDELINES:
            found.append(f"corpus: table {table.name!r} has no entry in GUIDELINES")
        for column in table.columns:
            if not column.description.strip():
                found.append(
                    f"corpus: {table.name}.{column.name} has no description, "
                    "so tier 1 would publish nothing for it"
                )

    # --- questions -> goldens ---
    seen: set[str] = set()
    for question in questions:
        qid = question.get("id", "")
        if not qid:
            found.append(f"questions: an entry has no id: {question}")
            continue
        if qid in seen:
            found.append(f"questions: duplicate id {qid!r}")
        seen.add(qid)

        if not question.get("question", "").strip():
            found.append(f"{qid}: empty question text")
        if not question.get("category", "").strip():
            found.append(f"{qid}: empty category")

        # An empty key is the explicit way to say "prose question, no oracle".
        # A non-empty key that resolves to nothing is the typo this exists for.
        key = question.get("golden_key", "")
        if key and key not in golden.BY_KEY:
            found.append(
                f"{qid}: golden_key {key!r} matches no golden. "
                f"Add it to golden.GOLDENS, or use \"\" for a question with no "
                f"numeric answer. Known keys: {sorted(golden.BY_KEY)}"
            )

        evidence = question.get("evidence", {})
        if not evidence.get("must_have"):
            found.append(
                f"{qid}: no must_have evidence terms, so evidence recall is "
                "vacuously perfect for this question"
            )
        for bucket in ("must_have", "nice_to_have", "distractor"):
            for term in evidence.get(bucket, []):
                if term not in known:
                    found.append(
                        f"{qid}: evidence {bucket} term {term!r} is not a table or "
                        "column in corpus.CORPUS, so it can never be matched"
                    )

    # --- scoring -> corpus ---
    # `rules_for()` decides which governed rule a question depends on by matching
    # the columns its evidence names against these sets. A renamed column makes
    # the match empty, and acquisition is then reported as *not applicable* for
    # every governed question — which reads as "this experiment has no governance
    # to acquire" rather than as a broken mapping.
    for rule, triggers in scoring.RULE_TRIGGERS.items():
        for name in sorted(triggers - known):
            found.append(
                f"scoring.RULE_TRIGGERS[{rule!r}] names column {name!r}, which is "
                "not in corpus.CORPUS. Acquisition scoring for that rule is dead."
            )

    if include_looker:
        found.extend(looker_problems())

    # --- goldens -> questions ---
    # Not an error: an oracle entry with no question is dead weight, but it is
    # also exactly what a half-finished adaptation looks like, so say it.
    orphans = sorted(set(golden.BY_KEY) - {q.get("golden_key", "") for q in questions})
    if orphans:
        found.append(
            f"goldens defined but asked by no question: {orphans}. "
            "Harmless, but usually means a question was renamed or not written yet."
        )

    return found


def report(include_looker: bool = True) -> bool:
    """Print the findings. True when everything agrees."""
    found = problems(include_looker=include_looker)
    if not found:
        scope = "+ LookML views" if include_looker else "LookML not checked"
        print(
            f"    Coherent: {len(corpus.CORPUS)} tables, {len(golden.GOLDENS)} goldens, "
            f"{len(json.loads(QUESTIONS_PATH.read_text()))} questions ({scope})."
        )
        return True
    print(f"    {len(found)} problem(s) between corpus.py, golden.py and questions.json:")
    for line in found:
        print(f"      - {line}")
    return False
