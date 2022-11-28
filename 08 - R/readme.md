![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2F08+-+R&dt=readme.md)

# 08 - Custom Models: R
This series of notebooks highlights the use of Vertex AI for machine learning workflows with [R](https://www.r-project.org/).

## Environment Setup
If the directions in the main [readme.md](../readme.md) were followed then this enviornment is Python based with TensorFlow installed.  Some of the notebooks here will also be using R which requies either:
- an additional install to remain in this enviornment
- or, choose a notebook install with R already installed (recommended)

To add R:
- Open a Terminal: File > New > Terminal
- use [conda] to add both [R](https://anaconda.org/conda-forge/r) and the [R kernel](https://anaconda.org/conda-forge/r-irkernel) for Jupyter
    - `conda install -c r r-irkernel`
    - install packages with: `R -e 'install.packages(c("<package name>"), repos = "https://cran.us.r-project.org/")'`

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
ToDo
- [IP] 08Tools predictions online
    - waiting on bug fix - works for REST now (11/2/22), but not aiplatform (maybe update?)
- [X] 08Tools predictions custom
    - [X] serve with cloud run
    - [X] serve locally with docker
- [ ] finish writeups for round 1 of development
    - [ ] 08 notebook
    - [ ] 08b Script - notebook to script
    - [ ] 08b Training Job - custom container training job
    - [ ] 08b_gcs Script - notebook to script
    - [ ] 08b_gcs Training Job - custom container training job
    - [ ] 08Tools Prediction Custom
    - [ ] 08Tools GCS FUSE
- Planning
    - [ ] 08Tools predictions local
    - [ ] 08Tools predictions batch
    - [ ] 08c Custom Container Workflow with a Custom Job
    - [ ] 08i Custom Conatiner Workflow with Hyperparameter tuning job (l2, or elastic net)
    - [ ] Link to Tips for BigQuery with R
- links to incorporate
    - gcs fuse
        - https://cloud.google.com/blog/topics/developers-practitioners/cloud-storage-file-system-vertex-ai-workbench-notebooks
        - https://cloud.google.com/vertex-ai/docs/training/code-requirements#fuse
        - https://cloud.google.com/bigquery/docs/exporting-data#sql
