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

import config
import corpus
import golden
import scoring

QUESTIONS_PATH = Path(config.PROJECT_ROOT) / "examples" / "questions.json"


def corpus_names() -> set[str]:
    """Every table and column name an evidence term is allowed to reference."""
    return {t.name for t in corpus.CORPUS} | {
        c.name for t in corpus.CORPUS for c in t.columns
    }


def problems(path: Path = QUESTIONS_PATH) -> list[str]:
    """Every inconsistency found, as readable lines. Empty means coherent.

    Returns rather than raises so a caller can print all of them at once. An
    adapter who has renamed a table wants the whole list, not the first item
    followed by eleven more runs.
    """
    found: list[str] = []
    questions = json.loads(path.read_text())
    known = corpus_names()

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


def report() -> bool:
    """Print the findings. True when everything agrees."""
    found = problems()
    if not found:
        print(
            f"    Coherent: {len(corpus.CORPUS)} tables, {len(golden.GOLDENS)} goldens, "
            f"{len(json.loads(QUESTIONS_PATH.read_text()))} questions."
        )
        return True
    print(f"    {len(found)} problem(s) between corpus.py, golden.py and questions.json:")
    for line in found:
        print(f"      - {line}")
    return False
