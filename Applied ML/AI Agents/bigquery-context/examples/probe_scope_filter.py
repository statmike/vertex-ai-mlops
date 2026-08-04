"""Probe: how to make the Knowledge Catalog ``parent:`` scope predicate bind.

This script documents a query-construction bug we hit and corrected, so the fix
is reproducible against the live catalog.

**The bug.** Our search callbacks scoped results with
``f"({question}) AND system=BIGQUERY AND parent:(datasets/{ds})"``. That query
returned a full page of tables from *unrelated* datasets — the ``parent:``
predicate appeared to be ignored. We first suspected an API gap.

**The cause.** It is the **parentheses around the free-text question**. Wrapping
the natural-language question in ``(...)`` makes the query parser silently drop
the ``parent:`` predicate. The ``AND`` connectors are harmless, and
``parent:(datasets/…)`` parentheses are fine — only parenthesizing the *question*
text breaks it. The corrected bare form enforces scope perfectly::

    query = f"{question} system=BIGQUERY parent:datasets/{ds}"

**The result after the fix.** Semantic search returns a small, already-pruned,
already-ranked in-scope set (3–9 tables for our questions) with zero out-of-scope
pollution, and it surfaces the required join partners: across the benchmark's
multi-table questions, 8 of 9 retrieve *all* their must-have tables **before any
rerank**. Search is doing discovery *and* ranking.

What this script demonstrates (against the ``tier3`` corpus of 15 in-scope tables):

- **Isolation table** — six variants that differ only in parentheses / ``AND``
  placement. Every leaking variant wraps the question in ``(...)``; every clean
  variant does not. This pinpoints the parenthesized question as the sole trigger.
- **Must-have coverage** — for each multi-table question, whether the corrected
  bare query retrieves the ground-truth ``must_have`` tables. 8/9 retrieve all;
  the lone miss (``multi-disp-q3``, "per capita") is a genuine relevance gap where
  the needed population table shares no salient term with the question.
- **The ``scope`` request field** is project/org-level only (a dataset-level ref
  is rejected with 400), so dataset scoping must go through the ``parent:``
  predicate — the bare form is the way to do it.
- **Result count is governed by search's internal relevance cutoff, not by
  ``page_size``.** ``page_size`` max is 1000; the corrected query returns far
  fewer than the budget, varying by question. ``SearchEntriesRequest`` exposes no
  threshold parameter and ``SearchEntriesResult`` returns no relevance score, so
  the cutoff is neither visible nor tunable from the client.

Run from the project root (defaults to tier3, matching the notebook story)::

    uv run python examples/probe_scope_filter.py
    ACTIVE_TIER=2 uv run python examples/probe_scope_filter.py   # any tier

This is a *diagnostic*, not part of the scored benchmark — it reads the live
catalog and prints tables; it writes nothing.
"""

import json
import os
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from google.cloud import dataplex_v1  # noqa: E402

import config  # noqa: E402

# Match the notebook's default tier unless the environment overrides it.
_TIER = int(os.getenv("ACTIVE_TIER", "3"))
config.set_active_tier(_TIER)

from config import (  # noqa: E402
    GOOGLE_CLOUD_PROJECT,
    get_datasets,
    is_table_in_scope,
)

QUESTIONS_FILE = Path(__file__).parent / "questions.json"

# Two multi-table questions used for the isolation table. Both previously
# "leaked" under the parenthesized-question query; both are clean under the bare
# form.
QUESTIONS = {
    "bikeshare (related)": (
        "Which bike share stations have the highest average trip duration, "
        "and where are they located?"
    ),
    "airquality (related)": (
        "Which US counties have the worst annual air quality, and what are their boundaries?"
    ),
}


def _search(client, name: str, query: str, semantic: bool, page_size: int):
    """Run one search_entries call; return (raw, in_scope, out_of_scope)."""
    request = dataplex_v1.SearchEntriesRequest(
        name=name, query=query, page_size=page_size, semantic_search=semantic
    )
    raw = in_scope = out_scope = 0
    for result in client.search_entries(request=request):
        raw += 1
        fqn = result.dataplex_entry.fully_qualified_name or ""
        parts = fqn.rsplit(".", 2)
        if len(parts) >= 2 and is_table_in_scope(parts[-2], parts[-1]):
            in_scope += 1
        else:
            out_scope += 1
    return raw, in_scope, out_scope


def _in_scope_tables(client, name: str, query: str, page_size: int = 20) -> list[str]:
    """Return the short names of in-scope tables the query retrieves, in order."""
    request = dataplex_v1.SearchEntriesRequest(
        name=name, query=query, page_size=page_size, semantic_search=True
    )
    tables = []
    for result in client.search_entries(request=request):
        fqn = result.dataplex_entry.fully_qualified_name or ""
        parts = fqn.rsplit(".", 2)
        if len(parts) >= 2 and is_table_in_scope(parts[-2], parts[-1]):
            tables.append(parts[-1])
    return tables


def _isolation_formulations(question: str, ds: str) -> dict[str, str]:
    """Six variants differing only in parentheses / AND placement (all sem=T).

    The single factor that flips the result is whether the *question* is wrapped
    in parentheses — not the AND connectors, and not the parent-value parens.
    """
    return {
        "A before: (question) AND … AND parent:(ds)": f"({question}) AND system=BIGQUERY AND parent:(datasets/{ds})",
        "B no question-parens, keep AND": f"{question} AND system=BIGQUERY AND parent:datasets/{ds}",
        "C keep question-parens, no AND": f"({question}) system=BIGQUERY parent:(datasets/{ds})",
        "D after: bare (no parens, no AND)": f"{question} system=BIGQUERY parent:datasets/{ds}",
        "E parens on parent VALUE only, no AND": f"{question} system=BIGQUERY parent:(datasets/{ds})",
        "F parens on QUESTION only, no AND": f"({question}) system=BIGQUERY parent:datasets/{ds}",
    }


def _load_multi_table_questions() -> list[dict]:
    """Load the benchmark's multi-table questions + graded ground truth."""
    if not QUESTIONS_FILE.exists():
        return []
    questions = json.loads(QUESTIONS_FILE.read_text())
    return [q for q in questions if q.get("category", "").startswith("multi")]


def main() -> None:
    client = dataplex_v1.CatalogServiceClient()
    name = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global"
    ds = get_datasets()[0]

    print(f"parent:-scope probe — tier {_TIER}, scoped dataset '{ds}'")
    print(f"Endpoint: {name}\n")

    # --- Isolation: which change makes parent: bind? ---
    print("=== Isolation — only parenthesizing the QUESTION breaks scope ===")
    print("  'out' > 0 means the parent: predicate was dropped and out-of-scope")
    print("  tables leaked in. Compare A/C/F (question in parens → leak) with")
    print("  B/D/E (question not in parens → clean).\n")
    for qlabel, question in QUESTIONS.items():
        print(f"  {qlabel}: {question}")
        print(f"    {'variant':44} {'raw':>4} {'in':>4} {'out':>4}")
        for vname, query in _isolation_formulations(question, ds).items():
            raw, ins, out = _search(client, name, query, True, 20)
            flag = "  <- LEAK" if out > 0 else ""
            print(f"    {vname:44} {raw:4} {ins:4} {out:4}{flag}")
        print()

    # --- Must-have coverage under the corrected bare query ---
    print("=== Must-have coverage — bare query, before any rerank ===")
    print("  Does the corrected query retrieve the ground-truth must_have tables?\n")
    multi = _load_multi_table_questions()
    if not multi:
        print("  (questions.json not found — skipping coverage check)\n")
    else:
        all_hit = 0
        for q in multi:
            must = q.get("relevance", {}).get("must_have", [])
            query = f"{q['question']} system=BIGQUERY parent:datasets/{ds}"
            got = _in_scope_tables(client, name, query)
            hit = [t for t in must if t in got]
            miss = [t for t in must if t not in got]
            status = "ALL" if not miss else ("NONE" if not hit else "PARTIAL")
            if not miss:
                all_hit += 1
            print(
                f"  {q['id']:14} [{q['category']:22}] {status} ({len(hit)}/{len(must)} must_have)"
            )
            if miss:
                print(f"    missing: {miss}   (retrieved {len(got)} in-scope)")
        print(
            f"\n  {all_hit}/{len(multi)} multi-table questions retrieve ALL "
            "must_have tables pre-rerank.\n"
        )

    # --- The scope= request field is project/org level, not dataset level ---
    print("=== The `scope` request field is project/org-level only ===")
    q = QUESTIONS["bikeshare (related)"]
    bare = f"{q} system=BIGQUERY parent:datasets/{ds}"
    raw, ins, out = _search(client, name, bare, True, 20)
    print(f"  bare parent: predicate (dataset scope)        raw={raw:3} in={ins:3} out={out:3}")
    try:
        req = dataplex_v1.SearchEntriesRequest(
            name=name,
            query=f"{q} system=BIGQUERY",
            page_size=20,
            semantic_search=True,
            scope=f"projects/{GOOGLE_CLOUD_PROJECT}/datasets/{ds}",
        )
        list(client.search_entries(request=req))
        print("  scope=dataset-level ref                       (accepted — unexpected)")
    except Exception as e:  # noqa: BLE001 — we want to show the API's rejection
        print(
            f"  scope=dataset-level ref                       REJECTED: "
            f"{str(e).splitlines()[0][:60]}"
        )
    print("  => dataset scoping must go through the parent: predicate.\n")

    # --- Result count is search's internal cutoff, not page_size ---
    print("=== Result count is governed by relevance, not page_size ===")
    print("  The bare query returns fewer than page_size; raising the budget does")
    print("  not add in-scope tables (page_size max is 1000; no threshold param")
    print("  exists and no relevance score is returned).")
    print(f"  {'page_size':>10} {'raw':>4} {'in':>4} {'out':>4}")
    for ps in (20, 50, 100):
        raw, ins, out = _search(client, name, bare, True, ps)
        print(f"  {ps:10} {raw:4} {ins:4} {out:4}")


if __name__ == "__main__":
    main()
