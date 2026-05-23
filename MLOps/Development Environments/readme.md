![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FDevelopment+Environments&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%20Environments/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%2520Environments/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%2520Environments/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%2520Environments/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%2520Environments/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Development%20Environments/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Development%20Environments/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Development Environments
> You are here: `vertex-ai-mlops/MLOps/Development Environments/readme.md`

Development environments are where ML practitioners write, test, and iterate on code. Google Cloud offers several managed notebook environments — each with different capabilities for collaboration, execution, and integration with ML services.

This section covers programmatic management of these environments: automating notebook workflows, managing execution at scale, and integrating notebook operations into broader MLOps pipelines.

---
## Content Overview

| Section | Notebooks | Description |
|---|---|---|
| [Notebooks](./Notebooks/readme.md) | 1 | Programmatic management of notebooks in cloud environments — listing, downloading, modifying, executing, and retrieving results via APIs |

---
## Documentation

For an overview of Google Cloud developer tools, see [Use developer tools](https://cloud.google.com/docs/get-started/developer-tools).

### Notebook Environments

| Environment | Description |
|---|---|
| [Colab Enterprise](https://cloud.google.com/colab/docs/introduction) | Google Cloud's managed notebook environment for teams with enterprise security, IAM integration, and managed runtimes |
| [Colab Enterprise in BigQuery](https://cloud.google.com/bigquery/docs/notebooks-introduction) | The same Colab Enterprise notebooks, accessed through BigQuery Studio — notebooks are BigQuery Studio code assets powered by Dataform and run on Colab Enterprise runtimes |
| [Colab](https://colab.research.google.com/) | Google's free, hosted Jupyter notebook environment — available to anyone with a Google account |
| [Vertex AI Workbench](https://cloud.google.com/vertex-ai/docs/workbench/introduction) | Managed JupyterLab instances on Google Cloud with deep integration into Vertex AI services |

### IDEs and Development Environments

| Environment | Description |
|---|---|
| [Cloud Workstations](https://cloud.google.com/workstations/docs/overview) | Managed, customizable development environments accessible from a browser, local IDE, or SSH — administrators can create templates with preconfigured tools, packages, and security policies for teams |
| [Cloud Shell](https://cloud.google.com/shell/docs) | Browser-based shell environment with 5 GB persistent storage, pre-installed tools (gcloud CLI, Docker, Terraform), and a built-in code editor — available at no cost to any Google Cloud user |
| [Cloud Code](https://cloud.google.com/code/docs) | IDE extensions for VS Code and JetBrains that integrate Google Cloud APIs, documentation, and deployment workflows directly into your editor — pre-installed on Cloud Workstations and Cloud Shell |
| [Local IDE + gcloud CLI](https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment) | Use any local editor or IDE with the gcloud CLI and Google Cloud client libraries, authenticated via Application Default Credentials (ADC) with `gcloud auth application-default login` |

---
