![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2F08+-+R%2Fdepricated&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/08%20-%20R/depricated/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# OLDER CONTENT TO REMOVE FOLLOWS:

---
**IDE - Alternative**

This repository currently uses JupyterHub hosted as a Vertex AI Workbench Instance.  An alternative R native IDE is avialable through [Cloud Workstations](https://cloud.google.com/workstations/docs/overview) with a [Posit Workbench](https://cloud.google.com/workstations/docs/develop-code-using-posit-workbench-rstudio) (requires a Posit Workbench license key).

---

## Environment Setup
If the directions in the main [readme.md](../readme.md) were followed then this enviornment is Python based with TensorFlow installed.  Some of the notebooks here will also be using R which requies adding R.  For this it is recommend to use [Vertex AI Workbench Instances](https://cloud.google.com/vertex-ai/docs/workbench/instances/introduction).  Here is how:
- Console > Vertex AI > Workbench > Instances - [direct link](https://console.cloud.google.com/vertex-ai/workbench/instances)
- Create a new instance - [instructions](https://cloud.google.com/vertex-ai/docs/workbench/instances/create)
- Once it is started, click the `Open JupyterLab` link.
- Add R: [Add A conda Environment](https://cloud.google.com/vertex-ai/docs/workbench/instances/add-environment)
    - Open A terminal window within JupyterLab
    - run: `conda create -n r-env r-essentials r-base`
    - run: `conda activate r-env`
    - (optional) run: `conda info --envs`
    - install additional packages like:
        - `conda install -c conda-forge r-bigrquery`

## Notebooks:
- [08 - Vertex AI Custom Model - R - in Notebook](./08%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20in%20Notebook.ipynb)
    - uses an R kernel to build a model in the notebook
- [08b Script - Vertex AI Custom Model - R - Notebook to Script](08b%20Script%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20Notebook%20to%20Script.ipynb)
    - uses a Python kernel to construct the model script and test by running it locally (requires R)
- [08b Training Job - Vertex AI Custom Model - R - Training Pipeline With Custom Container](./08b%20Training%20Job%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20Training%20Pipeline%20With%20Custom%20Container.ipynb)
    - uses a Python kernel to create a Vertex AI Training job to run the R script and deploy for online and batch serving of predictions
- [08b_gcs Script - Vertex AI Custom Model - R - Notebook to Script](08b%20Script%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20Notebook%20to%20Script.ipynb)
    - uses a Python kernel to construct the model script and test by running it locally (requires R)
    - modification of 08b Script that reads data from GCS using the GCS FUSE after exporting from BigQuery to GCS
- [08b_gcs Training Job - Vertex AI Custom Model - R - Training Pipeline With Custom Container](./08b%20Training%20Job%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20Training%20Pipeline%20With%20Custom%20Container.ipynb)
    - uses a Python kernel to create a Vertex AI Training job to run the R script and deploy for online and batch serving of predictions
    - run the modified script from 08b_gcs that reads data from GCS using GCS FUSE after exporting from BigQuery to GCS
- [08Tools - Prediction - Custom](./08Tools%20-%20Prediction%20-%20Custom.ipynb)
    - use the custom container created in `08b Training Job` to create a custom model server: testing locally in the notebook environment, and in production with Cloud Run
- [08Tools - GCS FUSE](./08Tools%20-%20GCS%20FUSE.ipynb)
    - walkthrough of readining large tables from BigQuery into R by first exporting the GCS and then reading them directly with GCS FUSE mount
    
    
---

- links to incorporate
    - gcs fuse
        - https://cloud.google.com/blog/topics/developers-practitioners/cloud-storage-file-system-vertex-ai-workbench-notebooks
        - https://cloud.google.com/vertex-ai/docs/training/code-requirements#fuse
        - https://cloud.google.com/bigquery/docs/exporting-data#sql
