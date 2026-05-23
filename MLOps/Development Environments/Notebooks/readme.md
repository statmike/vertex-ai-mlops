![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FDevelopment+Environments%2FNotebooks&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%20Environments/Notebooks/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
</table><br/><br/>

---
# Notebooks
> You are here: `vertex-ai-mlops/MLOps/Development Environments/Notebooks/readme.md`

Jupyter notebooks are a popular development interface for ML practitioners. While interactive use is common, programmatic management of notebooks enables automation, testing, and integration with MLOps workflows.

This section demonstrates how to manage notebooks as code — listing, downloading, modifying, and executing them via cloud APIs.

---
## Notebooks

| Notebook | Description |
|---|---|
| [Colab Enterprise - Notebook Management](./Colab%20Enterprise%20-%20Notebook%20Management.ipynb) | Programmatic notebook management with Colab Enterprise — list and download notebooks via the Dataform API, modify notebook cells as JSON, execute notebooks via the Vertex AI NotebookExecutionJob API, and retrieve results from GCS. Covers authentication, runtime template discovery, execution polling, and cell-level timing analysis. |

---
## Documentation

Google Cloud offers several managed notebook environments:

| Environment | Description |
|---|---|
| [Colab Enterprise](https://cloud.google.com/colab/docs/introduction) | Google Cloud's managed notebook environment for teams with enterprise security, IAM integration, and managed runtimes |
| [Colab Enterprise in BigQuery](https://cloud.google.com/bigquery/docs/notebooks-introduction) | The same Colab Enterprise notebooks, accessed through BigQuery Studio — notebooks are BigQuery Studio code assets powered by Dataform and run on Colab Enterprise runtimes |
| [Colab](https://colab.research.google.com/) | Google's free, hosted Jupyter notebook environment — available to anyone with a Google account |
| [Vertex AI Workbench](https://cloud.google.com/vertex-ai/docs/workbench/introduction) | Managed JupyterLab instances on Google Cloud with deep integration into Vertex AI services |

---
