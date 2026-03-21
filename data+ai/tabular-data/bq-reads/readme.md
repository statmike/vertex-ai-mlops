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
</table><br/><br/>

---
# BigQuery Reads

How to efficiently read BigQuery tables into pandas DataFrames for ML workflows.

## The Notebook

- **[bq-reads.ipynb](bq-reads.ipynb)** — Compares five approaches to reading BigQuery data into pandas, benchmarks multi-threaded storage reads, and provides cost/speed recommendations.

## Approaches Covered

| Approach | Runs a Query? | Cost | Parallel Reads? | Thread Control? |
|---|---|---|---|---|
| `client.query()` | Yes | Bytes scanned | Auto (Storage API download) | No |
| `client.list_rows()` | No | Storage reads* | No (sequential) | No |
| `pandas_gbq.read_gbq()` | Yes | Bytes scanned | Auto with `use_bqstorage_api` | No |
| BigFrames `read_gbq_table()` | No | Storage reads* | Yes (managed) | No |
| Storage Read API | No | Storage reads* | Yes (multi-stream) | Yes |

*\*Storage reads: free up to 300 TiB/month per billing account, then $1.10/TiB.*

## Key Takeaways

1. **Avoid unnecessary query costs** — if you're reading a whole table, use storage reads instead of `SELECT *`.
2. **BigFrames is the easy path** — storage reads with column pruning and filtering, managed for you. Competitive speed, zero query cost.
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
