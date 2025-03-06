![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FKeras&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/Keras/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Keras
> You are here: `vertex-ai-mlops/Framework Workflows/Keras/readme.md`

[Keras](https://keras.io/) is an OSS library for Neural Networks with TensorFlow, PyTorch, and/or JAX!

Workflows:
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
        