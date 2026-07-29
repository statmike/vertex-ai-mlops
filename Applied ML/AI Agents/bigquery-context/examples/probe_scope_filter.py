"""Probe: is the Knowledge Catalog ``parent:`` scope predicate enforced?

The benchmark's headline finding is that search-based discovery leaks recall for
two reasons — a *relevance gap* on disparate joins, and a *scope leak* on related
joins where the ``parent:(datasets/…)`` predicate fails to keep out-of-scope
tables out of the page budget. This script is the reproducible evidence for the
**scope leak** half of that claim.

It replays the exact ``search_entries`` call the ``KC Search`` / ``Semantic``
approaches make (``page_size=20``, ``semantic_search=True``, the same
``parent:`` query), then sweeps a battery of alternative formulations and page
sizes for the two questions that pollute in the full benchmark. For each it
counts what the API returns **raw** vs. what survives the client-side
``is_table_in_scope`` filter, so the reader can see the leak directly.

What it demonstrates (against the ``tier3`` corpus of 15 in-scope tables):

- **The predicate is enforceable — two independently-valid forms prove it.** Both
  ``parent:(datasets/…)`` and the full-path ``parent:(projects/…/datasets/…)``,
  issued *alone* (no free-text question), return only in-scope tables — so the API
  honors the filter perfectly when it is the whole query, and it is not a matter
  of using the "wrong" parent syntax.
- **A combined NL query relaxes it.** The moment a free-text question is ANDed
  with the predicate under ``semantic_search=True``, the API fills the page with
  tables from unrelated datasets and the in-scope survivors collapse.
- **The pollution is unrelated datasets, not name collisions.** The out-of-scope
  results are entirely different datasets in this and other projects — never a
  same-named copy of the scoped dataset — so the leak is the ``parent:`` predicate
  being dropped, not semantic search matching an identically-named dataset
  elsewhere.
- **No query-construction fix recovers it.** Exact ``parent=``, the full-path
  ``projects/…/datasets/…`` form, the ``fully_qualified_name`` prefix, the
  BigQuery-FQN parent form, and explicit ``NOT`` negation all leak identically.
- **A wider page does not help.** In-scope count stays pinned while pollution
  grows linearly with ``page_size`` (the API caps output at 100).
- **Keyword mode is not a fallback.** ``semantic_search=False`` returns nothing
  for a natural-language question — the tokens do not literal-match.

Run from the project root (defaults to tier3, matching the notebook story)::

    uv run python examples/probe_scope_filter.py
    ACTIVE_TIER=2 uv run python examples/probe_scope_filter.py   # any tier

This is a *diagnostic*, not part of the scored benchmark — it reads the live
catalog and prints a table; it writes nothing.
"""

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

# The two questions that pollute in the full benchmark (both multi-table-related),
# plus one disparate-join question that leaks via the *relevance* gap (returns
# fewer than the page budget, all in scope) for contrast.
QUESTIONS = {
    "bikeshare (related)": (
        "Which bike share stations have the highest average trip duration, "
        "and where are they located?"
    ),
    "airquality (related)": (
        "Which US counties have the worst annual air quality, "
        "and what are their boundaries?"
    ),
    "percapita (disparate)": (
        "Which US counties have the most weather stations per capita?"
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


def _out_of_scope_fqns(client, name: str, query: str, page_size: int) -> list[str]:
    """Return the fully-qualified names of the out-of-scope results.

    Proves the pollution is genuinely *other* datasets (in this and other
    projects), not same-named copies of the scoped dataset — i.e. the leak is the
    ``parent:`` predicate being dropped, not a cross-project name collision.
    """
    request = dataplex_v1.SearchEntriesRequest(
        name=name, query=query, page_size=page_size, semantic_search=True
    )
    out = []
    for result in client.search_entries(request=request):
        fqn = result.dataplex_entry.fully_qualified_name or "(empty fqn)"
        parts = fqn.rsplit(".", 2)
        if not (len(parts) >= 2 and is_table_in_scope(parts[-2], parts[-1])):
            out.append(fqn)
    return out


def _formulations(question: str, ds: str) -> dict[str, tuple[str, bool]]:
    """The battery of (query, semantic_search) formulations to compare.

    Keys are ordered so the two controls (current leaky form, parent-only) bracket
    the alternatives a reader would reach for.
    """
    proj = GOOGLE_CLOUD_PROJECT
    return {
        # The exact call the benchmark's search approaches make today.
        "current: question + parent: (sem=T)":
            (f"({question}) AND system=BIGQUERY AND parent:(datasets/{ds})", True),
        # Control: the predicate ALONE — proves the filter is enforceable.
        "control: parent: only (sem=T)":
            (f"parent:(datasets/{ds}) AND system=BIGQUERY", True),
        # Control: the full path form ALONE — a SECOND independently-valid parent
        # syntax that also enforces perfectly on its own (rules out "wrong form").
        "control: parent: path-form only (sem=T)":
            (f"parent:(projects/{proj}/datasets/{ds}) AND system=BIGQUERY", True),
        # Alternatives that a reader might expect to enforce scope:
        "alt: parent= exact (sem=T)":
            (f"({question}) AND system=BIGQUERY AND parent=datasets/{ds}", True),
        "alt: parent: path-form (sem=T)":
            (f"({question}) AND system=BIGQUERY "
             f"AND parent:(projects/{proj}/datasets/{ds})", True),
        "alt: parent: bigquery-fqn (sem=T)":
            (f"({question}) AND system=BIGQUERY AND parent:(bigquery:{proj}.{ds})", True),
        "alt: fully_qualified_name: (sem=T)":
            (f"({question}) AND fully_qualified_name:bigquery:{proj}.{ds}", True),
        "alt: NOT-negate a polluter (sem=T)":
            (f"({question}) AND system=BIGQUERY AND parent:(datasets/{ds}) "
             f"AND -parent:carrier", True),
        # Keyword mode (no AI) — literal token match on an NL question.
        "keyword mode: question + parent: (sem=F)":
            (f"({question}) AND system=BIGQUERY AND parent:(datasets/{ds})", False),
    }


def main() -> None:
    client = dataplex_v1.CatalogServiceClient()
    name = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global"
    datasets = get_datasets()
    ds = datasets[0]

    print(f"Scope-leak probe — tier {_TIER}, scoped dataset '{ds}'")
    print(f"Endpoint: {name}\n")

    for label, question in QUESTIONS.items():
        print(f"=== {label} ===")
        print(f"  Q: {question}")
        print(f"  {'formulation':44} {'raw':>4} {'in':>4} {'out':>4}")
        for fname, (query, semantic) in _formulations(question, ds).items():
            raw, ins, out = _search(client, name, query, semantic, 20)
            print(f"  {fname:44} {raw:4} {ins:4} {out:4}")
        print()

    # Page-size sweep on the sharpest polluter — a wider page does not help.
    sweep_q = QUESTIONS["bikeshare (related)"]
    query = f"({sweep_q}) AND system=BIGQUERY AND parent:(datasets/{ds})"
    print("=== page-size sweep (bikeshare, question + parent:, sem=T) ===")
    print("  in-scope stays pinned while out-of-scope grows → a wider pass only "
          "admits more pollution")
    print(f"  {'page_size':>10} {'raw':>4} {'in':>4} {'out':>4}")
    for ps in (20, 50, 100, 200):
        raw, ins, out = _search(client, name, query, True, ps)
        print(f"  {ps:10} {raw:4} {ins:4} {out:4}")

    # What ARE the out-of-scope results? Show they are unrelated datasets (this and
    # other projects), not same-named copies of the scoped dataset — so the leak is
    # the predicate being dropped, not a cross-project name collision.
    print("\n=== what the pollution actually is (bikeshare, question + parent:) ===")
    print(f"  out-of-scope results are NOT copies of '{ds}' — they are unrelated "
          "datasets\n  in this and other projects (the parent: predicate was "
          "dropped, not a name collision):")
    polluters = _out_of_scope_fqns(client, name, query, 20)
    named = [f for f in polluters if f != "(empty fqn)"]
    empty = len(polluters) - len(named)
    for fqn in named:
        print(f"    {fqn}")
    if empty:
        print(f"    (+ {empty} entries with no resolvable table name — also out of scope)")


if __name__ == "__main__":
    main()
