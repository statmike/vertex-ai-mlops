![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows&file=readme.md)
<!--- header table --->
<table align="left">
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bksy.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
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
- [BigQuery ML](./BQML/readme.md)
- [R](./R/readme.md)

Planning:
- LightGBM
- scikit-learn
- XGBoost
- PyTorch
- Pycaret
- statsmodels
- scipy
- stan
- PyMC
- JAX (direct)

