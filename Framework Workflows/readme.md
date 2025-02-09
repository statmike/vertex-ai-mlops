![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Framework Workflows
> You are here: `vertex-ai-mlops/Framework Workflows/readme.md`

Using the tools from [MLOps](../MLOps/readme.md) in workflows for specific frameworks.  The start with notebook based workflows showcasing the features of the framework.

For each framework the workflows will focus on a common task:
> Training a classification model on data that is stored in Google BigQuery

There are no prerequisites for these code workflows. Also, there is no dependencies between the frameworks workflows and they all start by creating the same source tables in BigQuery - or they leverage the already created source if other frameworks have already be run.  

Frameworks:
- [CatBoost](./CatBoost/readme.md)
- [Keras](./Keras/readme.md)
- [Flax](./Flax/readme.md)
- [Vertex AI AutoML](./Vertex%20AI%20AutoML/readme.md)
- LightGBM
- scikit-learn
- XGBoost
- R