![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fbigquery-context&file=temp.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/bigquery-context/temp.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/temp.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/temp.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/temp.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/temp.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/bigquery-context/temp.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/bigquery-context/temp.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
**Subject:** Table-discovery benchmark for NL2SQL — and a `search_entries` scope behavior to review

Hi [names],

Ahead of sharing the full benchmark, I wanted to introduce what it is and flag one Knowledge Catalog finding I think is worth your review directly.

**The benchmark.** I built an agentic NL2SQL system on BigQuery, where the make-or-break step is **table discovery** — given a natural-language question, find the right set of tables to answer it. Pick wrong and even perfect SQL is wrong. So I ran a controlled experiment comparing five discovery approaches over the same corpus:

1. **BQ metadata tools** — LLM inspects schemas via the BigQuery API.
2. **KC Search** — `search_entries` semantic search, scoped with `parent:`.
3. **KC Context** — feed the whole scoped corpus to a reranker (no search).
4. **Pre-Filter** — LLM shortlists from brief summaries, then reranks.
5. **Semantic Context** — semantic search + richer `lookup_context` metadata.

Each is scored on recall, rank quality, cost, and latency, with catalog enrichment (profiling → glossary → guidelines) isolated as a clean variable.

**The finding for your review.** The two search-based approaches carry a recall ceiling that traces to `search_entries`: **the `parent:` scope predicate isn't honored once a free-text question is combined with it under `semantic_search=True`.**

```python
request = dataplex_v1.SearchEntriesRequest(
    name=f"projects/{PROJECT}/locations/global",
    query=f"({question}) AND system=BIGQUERY AND parent:(datasets/{dataset})",
    page_size=20,
    semantic_search=True,
)
```

- `parent:` **alone** (no question): 15 raw / 15 in-scope / **0 out-of-scope** — enforceable.
- `parent:` **+ question**: a full page of 20, **mostly from unrelated datasets**; filtering to scope client-side leaves as few as ~5.

Things I tried, so you don't have to ask:

- **It isn't the parent syntax.** Two independently-valid forms — `parent:(datasets/{dataset})` and the full path `parent:(projects/{project}/datasets/{dataset})` — *both* return 15/15/0 when issued alone, and *both* leak identically once the question is ANDed in. `parent=` exact, the `bigquery:{project}.{dataset}` FQN form, `fully_qualified_name:`, and explicit `NOT`-negation all leak too (some over-restrict to 0 on other questions).
- **It isn't a name collision.** The out-of-scope results are entirely different datasets in this and other projects (e.g. `carrier_forecast`, `crossvalidation`, `bqml_2024`) — never a same-named copy of the scoped dataset. The predicate is being dropped, not matched loosely.
- **A wider page only adds pollution** — in-scope stays pinned at ~4 while out-of-scope grows linearly as `page_size` goes 20 → 100 (API caps at 100).

Self-contained probe attached (`probe_scope_filter.py`) — runs against the live catalog in ~2 min against any corpus.

**Why it matters.** This behavior is a direct driver of the recall gap in my results — sharpest on **multi-table questions where the join partners live in the same dataset**: the out-of-scope tables consume the page budget and crowd the in-scope partner out before reranking, so it's never recoverable. At scale, where search *must* subset before reranking, search recall becomes the pipeline's ceiling. Enforcing `parent:` here is the cheapest, highest-leverage fix and squarely in the catalog's control.

**Happy to share the full report as a follow-up** — methodology, per-category recall, cost/latency, and confidence intervals across all five approaches. For now I wanted the probe in your hands, since it's the piece you can reproduce independently.

A couple of questions:
1. Can `parent:` (and equivalent scope predicates) be honored when combined with a free-text query under `semantic_search=True`?
2. Would join-aware expansion via `lookup_context`'s `frequent_joins` be of interest? (The missing tables are always join partners — signal the catalog already has.)

Thanks — happy to walk through any of it live.

Best,
Mike

---
*Attachment: `probe_scope_filter.py`*
