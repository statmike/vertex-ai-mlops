![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Ftabular-data%2Fbq-reads&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/tabular-data/bq-reads/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/tabular-data/bq-reads/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/tabular-data/bq-reads/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/tabular-data/bq-reads/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/tabular-data/bq-reads/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/tabular-data/bq-reads/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/tabular-data/bq-reads/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery Reads

How to efficiently read BigQuery tables into pandas DataFrames for ML workflows.

## The Notebook

- **[bq-reads.ipynb](bq-reads.ipynb)** — Compares five approaches to reading BigQuery data into pandas, benchmarks multi-threaded storage reads, and provides cost/speed recommendations.

## Approaches Covered

| Approach | Data Access | Cost | Download Method | Thread Control |
|---|---|---|---|---|
| `client.query()` | Query engine | Bytes scanned ($6.25/TB) | Storage API (auto) | No |
| `client.list_rows()` | Storage layer | Storage reads* | REST (sequential) | No |
| `pandas_gbq.read_gbq()` | Query engine | Bytes scanned ($6.25/TB) | REST or Storage API | No |
| BigFrames `read_gbq_table()` | Storage layer | Storage reads* | Storage API (managed) | No (auto) |
| Storage Read API | Storage layer | Storage reads* | Storage API (multi-stream) | Yes |

*\*Storage reads: 300 TiB/month free per billing account, then $1.10/TiB.*

## Key Takeaways

1. **Avoid unnecessary query costs** — if you're reading a whole table, use storage reads instead of `SELECT *`.
2. **BigFrames is the easy path** — storage-layer reads with column pruning and filtering, managed for you. Competitive speed, no query cost.
3. **Storage Read API is the fast path** — parallel streams with `ThreadPoolExecutor` for maximum throughput. I/O-bound, so more threads than CPUs can help.
4. **`asyncio` is an alternative, not faster** — `asyncio.to_thread()` matches `ThreadPoolExecutor` performance. Choose based on application architecture.
5. **All ML frameworks benefit** — pandas is the universal bridge between BigQuery and ML (PyTorch, JAX, Keras, scikit-learn).

## Environment Setup

This folder uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
# From this directory (bq-reads/)
uv sync --group dev
uv run python -m ipykernel install --user --name bq-reads --display-name "BQ Reads"
```

Then select the **BQ Reads** kernel in your notebook editor. Alternatively, each notebook includes an inline install cell that works standalone in Colab, Vertex AI Workbench, or BigQuery Studio.
