![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2F02+-+Vertex+AI+AutoML&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/02%20-%20Vertex%20AI%20AutoML/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /02 - Vertex AI AutoML/readme.md

This series of notebooks will introduce [Vertex AI AutoML](https://cloud.google.com/vertex-ai/docs/start/automl-model-types) with a focus on Tabular data Classification Methods.

Vertex AI AutoML accelerate the workflow of creating an ML model by preprocessing the data and choosing model architectures for you, even testing multiple and creating ensembles to achieve a best model.  This is available for ML models on text, image, video, and tabular data.  

**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)
- [01 - BigQuery - Table Data Source.ipynb](../01%20-%20Data%20Sources/01%20-%20BigQuery%20-%20Table%20Data%20Source.ipynb)

---
## AutoML Services

[AutoML](https://cloud.google.com/vertex-ai/docs/beginner/beginners-guide) is a service on Vertex AI that creates custom models from users data.  The data source for AutoML jobs is a [Vertex AI managed dataset](https://cloud.google.com/vertex-ai/docs/datasets/overview).  These managed datasets are links to actual data locations in GCS or BigQuery. The data is not imported so each training job that uses them will always grab a current version of the data source. When creating a dataset, the location selected needs to match the location of the linked data (like `us-central1` for example).  AutoML training jobs use these datasets as inputs.  The AutoML service availability by region should be reviewed to make sure it is available in the data location - [feature availability](https://cloud.google.com/vertex-ai/docs/general/locations#vertex-ai-regions).

When using [AutoML from BigQuery ML](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-automl) a Vertex AI managed dataset is not required.  Instead, the BigQuery locations should be checked for AutoML availability via [this table](https://cloud.google.com/bigquery/docs/locations#bqml-loc) of BigQuery ML resource locations.

---
## Notebooks: 
This list is in the suggest order of review for anyone getting an overview and learning about Vertex AI AutoML.  It is also ok to pick a particular notebook of interest and if there are dependencies on prior notebooks they will be listed in the **prerequisites** section at the top of the notebook.

>The notebooks are designed to be editable for trying with other data sources.  The same parameter names are used across the notebooks to also help when trying multiple methods on a custom data source.

- 02a - Vertex AI - AutoML in GCP Console (no code).ipynb
- 02b - Vertex AI - AutoML with clients (code).ipynb
- 02c - Vertex AI > Pipelines - AutoML with clients (code) in automated pipeline.ipynb
- [BQML AutoML](../02%20-%20Vertex%20AI%20AutoML/BQML%20AutoML.ipynb) Using AutoML directly from BigQuery ML

## Additional AutoML techniques are explored throughout this repository:
- AutoML Forecasting:
    - [Vertex AI AutoML Forecasting - GCP Console (no code)](../Applied%20Forecasting/Vertex%20AI%20AutoML%20Forecasting%20-%20GCP%20Console%20(no%20code).ipynb)
    - [Vertex AI AutoML Forecasting - Python client](../Applied%20Forecasting/Vertex%20AI%20AutoML%20Forecasting%20-%20Python%20client.ipynb)
    - [Vertex AI AutoML Forecasting - multiple simultaneously](../Applied%20Forecasting/Vertex%20AI%20AutoML%20Forecasting%20-%20multiple%20simultaneously.ipynb)  






