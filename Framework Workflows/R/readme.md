![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FR&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/R/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/R/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
</table><br/><br/>

---
# R Language
> You are here: `vertex-ai-mlops/Framework Workflows/R/readme.md`

This series of notebooks will cover workign with [R](https://www.r-project.org/) in Vertex AI.


**Workflows:**

This repository also has a series of notebook based workflows for R that can be reviewed here: [../../08 - R](../../08%20-%20R/readme.md).  These workflows will be reviewed, updated, and migrated to this folder in the coming months.

- [R on Vertex AI Pipelines](./R%20on%20Vertex%20AI%20Pipelines.ipynb)
    - Read more about Vertex AI Pipelines in this repositories [MLOps](../../MLOps/readme.md) section, specifically the [Orchestration With Pipelines](../../MLOps/Pipelines/readme.md) content.
    - While pipelines are compiled KFP or TFX code which originates in Python it is possible to create container based components with KFP
    - This workflow shows how to use a pre-built container that has R on it to easily run an R script by providing minimal inputs:
        - The text of the R script
        - A list of required libraries to run the script.  It will automatically make sure the packages are installed.
        - A list of arguments to pass to the script when it runs.
        - An output path in GCS that will be available to the R script as a local enviroment variable named `AIP_MODEL_DIR` similar to how Vertex AI Custom Training Jobs work.
    - The simple pipeline runs on Vertex AI with the permission of the provided service account which means the R script can interact with GCP services.  The example script used in this notebook:
        - Reads data from Google Cloud BigQuery
            - the project, dataset, and table are provided as command line arguments created from the pipeline inputs
            - the variables to exclude and the split of data to read are provided as commoand line arguments created from the pipeline inputs
        - Builds a GLM model in R
            - The target variable name is provided as a command line argument created from the pipeline inputs
        - Saves the resulting model as `model.rds`
        - Stores the `model.rds` folder in GCS at the location provided as an input to the pipeline.
