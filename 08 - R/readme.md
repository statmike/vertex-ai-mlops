# 08 - Custom Models: R
This series of notebooks highlights the use of Vertex AI for machine learning workflows with [R](https://www.r-project.org/).

## Environment Setup
If the directions in the main [readme.md](../readme.md) were followed then this enviornment is Python based with TensorFlow installed.  The notebooks here will also be using R so an additional install is needed to remain in this enviornment.  Alternatively, you could choose a notebook install with R already installed.

To add R:
- Open a Terminal: File > New > Terminal
- use [conda] to add both [R](https://anaconda.org/conda-forge/r) and the [R kernel](https://anaconda.org/conda-forge/r-irkernel) for Jupyter
    - `conda install -c r r-irkernel`

## Notebooks:
- [08 - Vertex AI Custom Model - R - in Notebook](./08%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20in%20Notebook.ipynb)
- [08 - Vertex Ai Custom Model - R - Notebook to Script](08%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20Notebook%20to%20Script.ipynb)
- [08a - Vertex AI Custom Model - R - Training Pipeline With Custom Container](./08a%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20Training%20Pipeline%20With%20Custom%20Container.ipynb)


---
ToD0
- [ ] Custom Container Workflow with a Custom Job
- [ ] Link to Tips for BigQuery

---
Quick Notes
```

 R -e 'install.packages(c("randomForest"), repos = "https://cran.rstudio.com/")'
 R -e 'install.packages(c("lme4"), repos = "https://cran.rstudio.com/")'
 R -e 'install.packages(c("bigrquery"), repos = "https://cran.rstudio.com/")'
 R -e 'install.packages(c("DBI"), repos = "https://cran.rstudio.com/")'
 R -e 'install.packages(c("dplyr"), repos = "https://cran.rstudio.com/")'
 
 https://cloud.google.com/deep-learning-containers/docs/choosing-container
 OR
 gcloud container images list --repository="gcr.io/deeplearning-platform-release"
 
 FROM gcr.io/deeplearning-platform-release/r-cpu.4-1:latest
 
 ```