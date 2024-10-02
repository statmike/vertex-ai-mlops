![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FCatBoost&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/CatBoost/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# CatBoost

[CatBoost](https://catboost.ai/) is an OSS library for gradient boosted decision trees.

- [CatBoost In Notebook](./CatBoost%20In%20Notebook.ipynb)
- [CatBoost Custom Prediction With FastAPI](./CatBoost%20Custom%20Prediction%20With%20FastAPI.ipynb)
    - Build A custom container with Cloud Build and store it in Artifact Registry
    - Multiple version of formatting the output for prediction on the same container
    - Use the same containner to serve predictions three ways:
        - Test the container locally with Docker
        - Register the model (with container) in Vertex Model Registry and deploy To a Vertex AI Prediction Endpoint
        - Deploy the container and serve predictions with Cloud Run

---
todo:
- Pipeline For model train + deploy + test
