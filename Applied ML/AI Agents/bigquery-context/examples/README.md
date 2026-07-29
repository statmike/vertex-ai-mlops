![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fbigquery-context%2Fexamples&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/bigquery-context/examples/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/examples/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/examples/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/examples/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/examples/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/bigquery-context/examples/README.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/bigquery-context/examples/README.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# NL2SQL retrieval benchmark

A factorial experiment comparing five BigQuery table-discovery approaches for
NL2SQL, isolating **catalog enrichment** as the independent variable. This is the
rigorous counterpart to the notebook's single-run story — read the project
[`readme.md`](../readme.md) for the challenge framing and per-approach spec cards.

## What it measures

- **Independent variable:** enrichment tier (0 schema → 1 +profiling → 2
  +glossary → 3 +guidelines). `scripts/setup.py` replicates the identical corpus
  into one dataset per tier, so tier is decoupled from topic.
- **Design:** approach (5) × tier (4) × question (~18) × run (n=5). Each
  approach-run is **isolated** (its own `InMemoryRunner`, one at a time), so
  latency and reranker token cost carry no parallel-contention artifact.
- **Graded ground truth:** every question tags tables `must_have` /
  `nice_to_have` / `distractor` (see [`GROUND_TRUTH.md`](GROUND_TRUTH.md)), which
  makes precision and rank-quality metrics meaningful and lets trap questions
  penalize approaches that fall for lookalike distractor tables.

## Files

| File | Role |
|---|---|
| `questions.json` | ~18 questions across `single-table`, `multi-table-related`, `multi-table-disparate`, `trap` categories, each with a graded `relevance` map. |
| `GROUND_TRUTH.md` | The corpus, the grading rubric, and how each distractor is baited. |
| `run_questions.py` | Factorial harness. Sweeps tier × approach × question × run, scoping each run to one tier, writing raw cells to `results/results.json`. |
| `build_results.py` | Scores cells, computes median+IQR and paired bootstrap CIs, renders plots, and writes `results.md`. |
| `probe_scope_filter.py` | Diagnostic (not scored): replays the `search_entries` call across query formulations + page sizes to demonstrate the `parent:` scope leak. Reads the live catalog, prints a table. |
| `results/results.json` | Raw approach-run cells (auto-generated) plus a reproducibility header. |
| `results/plots/` | Generated PNGs: discovery-vs-final recall, recall-vs-tier, nDCG-by-category, latency/cost. |
| `results.md` | The generated report. |

## Prerequisites

Provision the tier datasets first (from the project root):

```bash
uv run python scripts/setup.py
```

## Running

```bash
# Quick smoke — one question, all tiers, n=2 (verifies wiring + scoping)
uv run python examples/run_questions.py --runs 2 --id single-q1

# Full factorial (n=5, all tiers, all approaches, all questions) — resumable
uv run python examples/run_questions.py
uv run python examples/run_questions.py --resume     # skip completed cells

# Useful filters (all repeatable / combinable)
uv run python examples/run_questions.py --tier 2 --approach kc_context
uv run python examples/run_questions.py --category trap

# Score → report + plots
uv run python examples/build_results.py
uv run python examples/build_results.py --no-plots    # tables only
```

The full run is ~1,800 isolated approach-runs against live Gemini and is
resumable — rerun with `--resume` if interrupted. `run_questions.py` only reads
raw outputs; all scoring lives in `build_results.py`, so you can re-score without
re-running the benchmark.

## Reading the report

`results.md` is ordered for a single scan, leading with the finding:

1. **Headline — where recall actually leaks** — the finding. Recall decomposed
   into **discovery** (was the must-have table in the candidate set?) vs **final**
   (did it survive the reranker's top-5?), using means so the tail is visible past
   the median ceiling. The gap is **rerank loss**. `discovery_vs_final.png` plots
   it; the by-category table isolates it to the join questions.
2. **Summary metrics** — median metrics per approach across everything. These
   saturate at 100% on this easy corpus — that ceiling is *why* the headline uses
   means.
3. **Enrichment response** — final recall by approach × tier. Flat here: recall is
   bounded by discovery, not by the metadata the reranker sees, so enrichment
   doesn't move top-5 recall on this corpus. `recall_vs_tier.png` shows it with
   IQR bands.
4. **Rank quality by category** — nDCG@5, including the `trap` category where a
   low score means an approach ranked a distractor.
5. **Cost & latency** — isolated p50/p95 latency and exact reranker token cost.
6. **Paired comparison** — bootstrap CIs vs the `bq_tools` baseline.
7. **Methodology footer** — models, temperature, n, package versions, corpus size.
