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
- [08 - Vertex Ai Custom Model - R - Notebook to Script](08%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20Notebook%20to%20Script.ipynb)
    - uses a Python kernel to construct the model script and test by running it locally (requires R)
- [08f - Vertex AI Custom Model - R - Training Pipeline With Custom Container](./08f%20-%20Vertex%20AI%20Custom%20Model%20-%20R%20-%20Training%20Pipeline%20With%20Custom%20Container.ipynb)
    - uses a Python kernel to create a Vertex AI Training job to run the R script and deploy for online and batch serving of predictions


---
ToDo
- [ ] finish writeup for 08f
- [ ] 08Tools predictions online
- [ ] 08Tools predictions batch
- [ ] 08c Custom Container Workflow with a Custom Job
- [ ] 08i Custom Conatiner Workflow with Hyperparameter tuning job (l2, or elastic net)
- [ ] Link to Tips for BigQuery with R
