![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FBQML&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/BQML/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# BigQuery ML (BQML)
> You are here: `vertex-ai-mlops/Framework Workflows/BQML/readme.md`

This series of notebooks will introduce [BigQuery ML (BQML)](https://cloud.google.com/bigquery/docs/bqml-introduction).

**BigQuery ML (BQML) Overview**

[BigQuery ML](https://cloud.google.com/bigquery/docs/bqml-introduction) allows you to use `SQL` to constuct an ML workflow.  This is a great leap in productivity and flexibility when the data source is [BigQuery](https://cloud.google.com/bigquery/docs/introduction) and users are already familiar with `SQL`. Using just `SQL`, [multiple techniques](https://cloud.google.com/bigquery/docs/bqml-introduction#model_selection_guide) can be used for model training and even include [hyperparameter tuning](https://cloud.google.com/bigquery/docs/hp-tuning-overview).  It includes serverless [training, evaluation, and inference](https://cloud.google.com/bigquery/docs/e2e-journey) techniques for supervised, unsupervised, time series methods, even recommendation engines.  [Predictions](https://cloud.google.com/bigquery/docs/inference-overview) can be served directly in BigQuery which also include explainability measures. Predictive models can be [exported to their native framework](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-export-model) for portability, or even directly [registered to Vertex AI model registry](https://cloud.google.com/bigquery/docs/create_vertex) for online predictions on Vertex AI Endpoints.  You can [import models into BigQuery ML](https://cloud.google.com/bigquery/docs/inference-overview#inference_using_imported_models) from many common frameworks, or [connect to remotely hosted models](https://cloud.google.com/bigquery/docs/inference-overview#inference_using_remote_models) on Vertex AI Endpoints. You can even directly use many [pre-trained models](https://cloud.google.com/bigquery/docs/inference-overview#pretrained-models) in Vertex AI Like Cloud Vision API, Cloud Natural Language API, Cloud Translate API, and Generative AI with Vertex AI hosted LLMs.

A great starting point for seeing the scope of available methods is the [user journey for models](https://cloud.google.com/bigquery/docs/e2e-journey).  

**BigFrames**

A new way to interact with BigQuery and BigQuery ML is [BigQuery DataFrames](https://cloud.google.com/python/docs/reference/bigframes/latest).  A new Pythonic DataFrame with modules for BigQuery (`bigframes.pandas`) that is pandas-compatible and BigQuery ML (`bigframes.ml`) that is scikit-learn like.

**Workflows:**

This repository also has a series of notebook based workflows for many BigQuery ML methods that can be reviewed here: [../../03 - BigQuery ML (BQML)](../../03%20-%20BigQuery%20ML%20(BQML)/readme.md).  These workflows will be reviewed, updated, and migrated to this folder.

**Related Workflows:**
- `vertex-ai-mlops/MLOps/Serving/`
    - Import TensorFlow SavedModel format model directly into BigQuery and get serverless predictions with SQL
        - [Serve TensorFlow SavedModel Format With BigQuery](../../MLOps/Serving/Serve%20TensorFlow%20SavedModel%20Format%20With%20BigQuery.ipynb) 
   
