![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2F08+-+R&dt=readme.md)

# /08 - R/readme.md

This series of notebooks highlights the use of Vertex AI for machine learning workflows that use [R](https://www.r-project.org/).

---
## R Development Environments

- R With Vertex AI Workbench Instances (used in this repository)
    - Within Vertex AI there are Jupyter notebook-based development environments called [Vertex AI Workbench Instances](https://cloud.google.com/vertex-ai/docs/workbench/instances/introduction)
    - It is very easy to add **R** to these environments by [adding a conda environment](https://cloud.google.com/vertex-ai/docs/workbench/instances/add-environment)

- R With Cloud Workstations
    - [Cloud Workstations](https://cloud.google.com/workstations/docs/overview) are managed development environments on Google Cloud
        - The concept of workstations has three layers:
            - A cluster: a group of workstations in a particular region and VPC network
            - Configurations: templates for each type of workstation that might be needed, each with specification for the virtual machine, storage, container, IDE or Editor.  Access can be limited with IAM controls as well.
            - Workstations: A deployment of a configuration
        - When setting up workstation configuration there are a number or [preconfigured IDEs](https://cloud.google.com/workstations/docs/preconfigured-ides) that can be selected.  
            - The [base editor](https://cloud.google.com/workstations/docs/base-editor-overview) is based on [Code-OSS](https://github.com/microsoft/vscode), the open source project behind VSCode.
            - During workstation configuration the IDEs container can be switched to other available [preconfigured IDEs](https://cloud.google.com/workstations/docs/preconfigured-ides)
            - **R** - During configuration, one of the IDEs that can be picked is [Posit Workbench](https://cloud.google.com/workstations/docs/develop-code-using-posit-workbench-rstudio) which includes **RStudio Pro**. 
                - The configuration will require a license key from Posit
            - Customized environments are also possible with [custom containers](https://cloud.google.com/workstations/docs/customize-container-images), including using [preconfigurated base images](https://cloud.google.com/workstations/docs/preconfigured-base-images)
            - You can also use [local VS Code](https://cloud.google.com/workstations/docs/develop-code-using-local-vscode-editor) or local [JetBrains IDEs](https://cloud.google.com/workstations/docs/develop-code-using-local-jetbrains-ides) to connect to a Cloud Workstation for remote development.

---

## R Workflows


### Setup Vertex AI Workbench Instance For **R**

If the directions in the main [readme.md](../readme.md) were followed then this enviornment is Python based with Vertex AI Workbench Instances.  Some of the notebooks here will also be using R which requires adding R (very easy!).  If you are starting here then it is recommend to use [Vertex AI Workbench Instances](https://cloud.google.com/vertex-ai/docs/workbench/instances/introduction).  Here is how:
- Console > Vertex AI > Workbench > Instances - [direct link](https://console.cloud.google.com/vertex-ai/workbench/instances)
- Create a new instance - [instructions](https://cloud.google.com/vertex-ai/docs/workbench/instances/create)
- Once it is started, click the `Open JupyterLab` link.
- Add R: [Add A conda Environment](https://cloud.google.com/vertex-ai/docs/workbench/instances/add-environment)
    - Open A terminal window within JupyterLab: File > New > Terminal
    - Create environment: `conda create -n r`
    - Activate environment: `conda activate r`
    - Install R (with many common libraries): `conda install -c r r-essentials`
    - Install additional packages, like [bigrquery](https://bigrquery.r-dbi.org/)
        - run: `conda install -c conda-forge r-bigrquery`
        - Notice the prefix on the library name, `r-` that is added.  Read more about [R language packages for Anaconda](https://docs.anaconda.com/free/anaconda/reference/packages/r-language-pkg-docs/).
    - Deactivate environment: `conda deactivate`

To work with the workflows below, clone the repository to the enviornment:
- Clone this repository to the JupyterLab instance:
    - Either:
        - Go to the `Git` menu and choose `Clone a Repository`
        - Choose the Git icon on the left toolbar and click `Clone a Repository`
    - Provide the Clone URI of this repository: [https://github.com/statmike/vertex-ai-mlops.git](https://github.com/statmike/vertex-ai-mlops.git)
    - In the File Browser you will now have the folder "vertex-ai-mlops" that contains the files from this repository. Open the folder '08 - R'.


To start a new **R** notebook, do one of the following:
- File > New > Notebook
    - In the 'Select Kernel' popup select 'R (Local)' and click 'Select'
- File > New Launcher
    - Under 'Notebook' select 'R (Local)'
  
To start a new **R** command line session, do one of the following:
- File > New > Console
    - In the 'Select Kernel' popup select 'R (Local)' and click 'Select'
- File > New Launcher
    - Under 'Console' select 'R (Local)'

### R With BigQuery

- R - Working With BigQuery

### R Scripts As Jobs

- R - Vertex AI Custom Training Jobs
- R - Dataproc Serverless Spark-R Jobs
- R - Dataproc Spark-R Jobs

### R Serving With Vertex AI Prediction Endpoints

- R - Serving With Vertex AI Prediction Endpoints
- R - Serving With Cloud Run







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
