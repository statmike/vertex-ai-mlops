![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2F08+-+R&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/08%20-%20R/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /08 - R/readme.md

This series of notebooks highlights the use of Vertex AI for machine learning workflows that use [**R**](https://www.r-project.org/).

Contents:
- [R Development Environments](#R-Development-Environments)
- [R Workflows](#R-Workflows)
    - [Setup Vertex AI Workbench Instance For **R**](#Setup-Vertex-AI-Workbench-Instance-For-R)
    - [R Basics](#R-Basics)
    - [R Scripts As Jobs](#R-Scripts-As-Jobs)
    - [R Serving Predictions](#R-Serving-Predictions)

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

If the directions in the main [readme.md](../readme.md) were followed then this enviornment is Python based with Vertex AI Workbench Instances.  Some of the notebooks here will also be using R which requires adding R (very easy!).  

**Setup Workbench Instance**

If you are starting here then it is recommend to use [Vertex AI Workbench Instances](https://cloud.google.com/vertex-ai/docs/workbench/instances/introduction).  Here is how:
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

**Clone Content To Workbench Instance**

To work with the workflows below, clone the repository to the enviornment:
- Clone this repository to the JupyterLab instance:
    - Either:
        - Go to the `Git` menu and choose `Clone a Repository`
        - Choose the Git icon on the left toolbar and click `Clone a Repository`
    - Provide the Clone URI of this repository: [https://github.com/statmike/vertex-ai-mlops.git](https://github.com/statmike/vertex-ai-mlops.git)
    - In the File Browser you will now have the folder "vertex-ai-mlops" that contains the files from this repository. Open the folder '08 - R'.

**Use R In Workbench Instance**

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

### R Basics

These are notebook based workflows that use an **R** kernel.  

- [R - Working With BigQuery](./R%20-%20Working%20With%20BigQuery.ipynb)
- [R - Notebook Based Workflow](./R%20-%20Notebook%20Based%20Workflow.ipynb)

### R Scripts As Jobs

These workflows are driven from notebooks with Python kernels that launch remote jobs that run **R** code.  The **R** code is first collected in a script file and then submitted to run on Google Cloud.  This allows the specification of compute resources while also limiting cost to just the needed run time for jobs - scalable and cost efficient!  Addtionally, jobs can be scheduled and/or triggered easily making it possible to build MLOps workflows around R code.

> To have a complete **R** based workflow, the code in these workflows could be adapted to run in **R** with the [reticulate](https://cran.r-project.org/web/packages/reticulate/vignettes/calling_python.html) package.  This package provides an **R** interface to Python.

- [R - Vertex AI Custom Training Jobs](./R%20-%20Vertex%20AI%20Custom%20Training%20Jobs.ipynb)
- R - Vertex AI Custom Training Jobs On Persistant Resource
- [R - Dataproc Serverless Spark-R Jobs](./R%20-%20Dataproc%20Serverless%20Spark-R%20Jobs.ipynb)
- [R - Dataproc Cluster Spark-R Jobs](./R%20-%20Dataproc%20Cluster%20Spark-R%20Jobs.ipynb)

### R Serving Predictions

**NOTE: THIS SECTION IS STILL IN DEVELOPMENT**

Make an R model available to serve preditions when and where they are needed.  These workflows show how to make an R model serve predictions.  This is the core buidling block to turning an R model into an applications feature!

- R - Serving With Vertex AI Prediction Endpoints
- R - Serving With BigQuery ML (BQML)
- R - Serving With Cloud Run





