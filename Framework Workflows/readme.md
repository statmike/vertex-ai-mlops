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

Using the tools from [MLOps](../MLOps/readme.md) in workflows for specific frameworks.  These start with notebook based workflows showcasing the features of the framework.  For each framework the workflows will focus on a common task:
> Training a classification model on data that is stored in Google BigQuery

Information is shared between frameworks:
- Each framework focuses on the same source data in BigQuery
- The preparation and access to this data is the same across the frameworks - and shared in case you run examples from muliple frame works
- Vertex AI resources are shared between example across frameworks
    - Vertex AI Model Registry - models registered as different versions of the same model registry entry
    - Vertex AI Feature Store - The online store is shared across frameworks
    - Vertex AI One Prediction Endpoint - The endpoint used in example is the same, shared, and deleted at the end of examples

**Frameworks:**
- [CatBoost](./CatBoost/readme.md)
- [Keras](./Keras/readme.md)

In-Progress
- [Flax](./Flax/readme.md)
- [Vertex AI AutoML](./Vertex%20AI%20AutoML/readme.md)

Planning:
- LightGBM
- scikit-learn
- XGBoost
- R
- PyTorch
- Pycaret
- statsmodels
- scipy
- stan
- PyMC
- JAX (direct)

