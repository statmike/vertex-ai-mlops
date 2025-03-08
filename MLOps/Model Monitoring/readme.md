![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FModel+Monitoring&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Model%20Monitoring/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Model Monitoring
> You are here: `vertex-ai-mlops/MLOps/Model Monitoring/readme.md`

Understanding the ongoing performance of a model in production is important to maintain accuracy.  While evaluations can be run on new data, they rely on also knowing the ground truth of the new records which is often delayed.  To monitor models for potential impacts to peformance it is better to monitoring what the model learned from - features.  The distribution of feature can be compared between training and current for **skew** and between rolling time points for **drift**.  

Model monitoring tasks can be easily accessed in both BigQuery ML and Vertex AI:
- [BigQuery Model Monitoring](https://cloud.google.com/bigquery/docs/model-monitoring-overview)
    - Easily conduct monitoring task on any model with logged predictions in BigQuery, including Vertex AI Endpoints or even offline models with logs saved to BigQuery.
- [Introduction To Vertex AI Model Monitoring](https://cloud.google.com/vertex-ai/docs/model-monitoring/overview)
    - Monitoring for any Vertex AI model with visuals integrated directly in the console.
    
## BigQuery ML Model Monitoring

BigQuery ML model monitoring provides a powerful and efficient way to ensure the ongoing performance and accuracy of your machine learning models. By leveraging the techniques and tools covered in this notebook, you can gain valuable insights into your data, detect potential issues early on, and take corrective actions to maintain the effectiveness of your models over time.

These resources help get started with BQML based model monitoring:
- Blog Post: [Introducing new ML model monitoring capabilities in BigQuery](https://cloud.google.com/blog/products/data-analytics/monitor-ml-model-skew-and-drift-in-bigquery)
    - Introduction Notebook Workflow: [BQML Model Monitoring Introduction](./bqml-model-monitoring-introduction.ipynb)
    - Tutorial Notebook Workflow: [BQML Model Monitoring Tutorial](bqml-model-monitoring-tutorial.ipynb)
        - Includes:
            - Vertex AI Endpoint Monitoring Directly in BigQuery
            - Visualization for monitoring jobs and alerts
            - Automation with scheduled BigQuery Jobs
            - Email notifications for alerts

## BigQuery ML Model Monitoring - In Vertex AI

BigQuery ML models that are created with BigQuery [can be registered to the Vertex AI Model Registry](https://cloud.google.com/bigquery/docs/managing-models-vertex) by adding parameters to the `CREATE MODEL` statement.  This is the basis for also beign able to visualize and collect results of `ML.VALIDATE_DATA_SKEW` and `ML.VALIDATE_DATA_DRIFT` directly in Vertex AI Model Monitoring! More on this coming soon!

## Vertex AI Model Monitoring

Vertex AI has a [model registry](https://cloud.google.com/vertex-ai/docs/model-registry/introduction) the organize models.  Each model has versions and each version holds the links to the model files, evaluation information, list of batch prediction jobs, and deployed instances on Vertex AI Endpoints.  

Vertex AI Model Monitoring has two version currently.  [Version 1](https://cloud.google.com/vertex-ai/docs/model-monitoring/overview#v1) was/is specific to a deployed instance on Vertex AI Endpoints.  The newer [version 2](https://cloud.google.com/vertex-ai/docs/model-monitoring/overview#v2) is connected to a model version in the model registry - a prefered and more general approach to monitoring models.  Only version 2 is covered here and you can read more about both versions [in the documentation](https://cloud.google.com/vertex-ai/docs/model-monitoring/overview#versions).

Monitoring means comparing distribution between training and serving.  This include both numerical (float, int) and categorical (bool, string, category) data that is a feature, and output (prediction), or feature attribution (SHAP value).  Comparison is done using metrics:
- Categorical features and predictions:
    - L-Infinity
    - Jansen Shannon Divergence
- Numerical features and predictions:
    - Jensen Shannon Divergence
- Feature attributions:
    - SHAP Value

With Vertex AI Model Monitoring V2 the monitoring can use data from:
- BigQuery
    - Including time windows for tables that have a timestamp column in the table
- Cloud Storage for CSV and JSONL formats
- Vertex AI Batch Predictions Jobs
- Vertex AI Endpoint Logging
- Vertex AI Managed Dataset such as the input for AutoML

The Vertex AI Model Monitoring V2 is also continous in that jobs can be scheduled on a routine.

## Understanding Monitoring Metrics



---
TODO for Tutorial:
More automations:
- [ ] Dataform
- [ ] Workflows
- [ ] Cloud Composer
- [ ] Vertex AI Pipelines (KFP)
    
Questions/Choices:
- this has moved from tutorial to full workshop - ok? or think about splitting up into segments?
- removed transform only model - i did add a section showing how to monitor transformed features with ML.TRANSFORM
- removed history table for feature management - another notebook based workflow could focus on this data architecture with a focus in ongoing serving
---
