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

Understanding the ongoing performance of a model in production is important to maintain accuracy.  While evaluations can be run on new data, they rely on also knowing the ground truth of the new records which is often delayed.  To monitor models for potential impacts to peformance is better done by monitoring what the model learned from - features.  The distribution of feature can be compared between training and current for **skew** and between rolling time points for **drift**.  

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

## Vertex AI Model Monitoring

In progress




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
