![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Ftabular-data&file=readme.md)
<!--- header table --->
<table>
<tr>
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/tabular-data/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
</table><br/><br/>

---
# Tabular Data

Reading tabular data efficiently is a foundational step for any ML workflow. BigQuery is a natural home for structured data on GCP, but **how** you read from it matters — both for cost and speed.

This section explores different approaches to reading BigQuery tables into pandas (the universal interchange format for ML frameworks), with a focus on storage-layer reads that avoid unnecessary query costs.

## Contents

- **[BigQuery Reads](bq-reads/)** — Compare five approaches to reading BigQuery tables into pandas: query-based reads, `list_rows()`, `pandas-gbq`, BigFrames, and the BigQuery Storage Read API. Includes multi-threaded benchmarks and cost analysis.
