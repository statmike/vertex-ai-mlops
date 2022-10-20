# Tips
A collection of tips for scaling jobs, generalizing jobs for flexibility, and developing ML training jobs that are portable.  Think of this as DevOps for ML training jobs.  The tips will show how to do multiple tasks in parallel within your code, pass parameters to jobs from the command line and input files, package training code, build custom containers with training code, and deploy training code on Vertex AI Training to take advantage of scalable managed infrastructure at the job level.

## Using This Repository
- Each notebook that has a parameter defined as `BUCKET = PROJECT_ID` can be customized:
    - change this to `BUCKET = PROJECT_ID + 'suffix'` if you already have a GCS bucket with the same name as the project.  

## Notes
- [`aiplatform` Python Client](./aiplatform_notes.md)
    - All about the Vertex AI Python Client: versions (`aiplatform_v1` and `aiplatform_v1beta`) and layers (`aiplatform` and `aiplatform.gapic`).  Includes the deeper details and examples of using each.

## Python: Notebooks on Skills For ML Training Jobs and Tasks
- [Python Multiprocessing](./Python%20Multiprocessing.ipynb)
    - tips for executing multiple tasks at the same time
- [Python Job Parameters](./Python%20Job%20Parameters.ipynb)
    - tips for passing values to programs from the command line (argparse, docopt, click) or with files (JSON, YAML, pickle)
- [Python Client for GCS](./Python%20Client%20for%20GCS.ipynb)
    - tips for interacting with GCS storage from Python, Vertex AI
- [Python Packages](./Python%20Packages.ipynb)
    - prepare ML training code with a file (modules), folders, packages, distributions (source distribution and built distribution) and storing in custom repositories with Artifact Registry
- [Python Custom Containers](./Python%20Custom%20Containers.ipynb)
    - tips for building derivative containers with Cloud Build and Artifact Registry
- [Python Training](./Python%20Training.ipynb)
    - move training code out of a notebook and into Vertex AI Training Custom Jobs
    - This demonstrates many workflows for directly using the code formats created in [Python Packages](./Python%20Packages.ipynb) and for the custom container workflows created in [Python Custom Containers](./Python%20Custom%20Containers.ipynb)

## BigQuery: Notebooks on BigQuery Topics
- [BQML | Slots for ML_EXTERNAL Jobs](https://gist.github.com/statmike/c3175a9cc138588c55bfbcef2a9e81b1)
- [BQ Tools | Divide A Query - Async](https://gist.github.com/statmike/d93bfc3dc68ed119a0d2b74303c1ad7a)
- [BQ Explained | Columns](https://gist.github.com/statmike/c72ae34045adfe84b33143ee8e403d22)
- [BQ Tools | UDF](https://gist.github.com/statmike/e36c7abfcab834d74f860c850cac1837)
- [BQ Explained | Tables](https://gist.github.com/statmike/627567e509d57970cc1927c5ba03d0d0)
- [Information Schema Example](https://gist.github.com/statmike/8f1fc48700bd57026c68cd0f3fcc4b64)
- [BQ Tools | Logging Sink](https://gist.github.com/statmike/79d91989c4caa76957b523db30bb1a81)
- [BQ Tools | CMEK and Cross-Region Move](https://gist.github.com/statmike/6a8dedb32c50829a5d2a4763dfab7754)
- [BQ TOOL | LOCF Time Series](https://gist.github.com/statmike/ad1bc97a95bc50ab076a9e8b1b234506)

## Additional Tips
- Tips for working with the Python Client for BigQuery can be found here:
    - [03 - Introduction to BigQuery ML (BQML)](../03%20-%20BigQuery%20ML%20(BQML)/03%20-%20Introduction%20to%20BigQuery%20ML%20(BQML).ipynb)
    
## Notebooks on Skills For BigQuery
- New series will go here (see todo)


---
ToDo:
- split this folder with subfolders
 - Python, BigQuery, KFP, ...
     - KFP Layers: components, tasks, artifacts, pipelines, IO
     - BQ Layers: project, dataset, table, rows, columns, cells + access, operations, ...
- [IP] BigQuery Tips:
    - [ ] BigQuery - Python Clients
    - [ ] BigQuery - R
    - [ ] BigQuery - Data Types
    - [ ] BigQuery - Tables
    - [ ] BigQuery - UDF
    - [ ] BigQuery - Remote Functions
- [ ] Add Git workflow tip - how to clone with PAT
- [DEV] add KFP tip, include [component authoring](https://www.kubeflow.org/docs/components/pipelines/v2/author-a-pipeline/components/#author-a-component)