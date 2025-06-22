![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FKeras&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/Keras/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/Keras/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/Keras/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/Keras/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/Keras/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
</table><br/><br/>

---
# Keras
> You are here: `vertex-ai-mlops/Framework Workflows/Keras/readme.md`

[Keras](https://keras.io/) is an OSS library for Neural Networks with TensorFlow, PyTorch, and/or JAX!

**Workflows:**
- [Keras With JAX Overview](./Keras%20With%20JAX%20Overview.ipynb)
    - Setup Keras with a JAX backend
    - Specify and Train an Autoencoder
    - Set up a training data pipeline for Keras training
        - transform instances in the pipelines
    - Use Keras preprocessing layers
        - Incorporate preprocessing into the model for serving
    - Continue training models for fine-tuning
    - Extract the encoder as a separate model
    - Enhance the Autoencoder:
        - Stack preprocessing, the model, and postprocessing into a new model object
        - Add a named input layer
        - Create detailed post-processing with metrics, each features reconstruction, the encoded values, and present both normalized and denormalized values
    - Save models
        - In Keras format
        - In TensorFlow SavedModel Format
- [Keras With TensorFlow Overview](./Keras%20With%20TensorFlow%20Overview.ipynb)
    - Parallel workflow to the JAX example above but with a TensorFlow backend
    - This will create models without XLA which can be used in BigQuery and other serving environments:
        - See these models imported for serving directly in BigQuery in this workflow: [../../MLOps/Serving/Serve TensorFlow SavedModel Format With BigQuery](../../MLOps/Serving/Serve%20TensorFlow%20SavedModel%20Format%20With%20BigQuery.ipynb)
        
**Planning:**
- Keras With PyTorch Overview