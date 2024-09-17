![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FEmbeddings&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Embeddings/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Embeddings
> You are here: `vertex-ai-mlops/Applied GenAI/Embeddings/readme.md`

Embeddings are condensed representations of data that retain the information from the data.  They are represented by a vector of numbers, usually floats, like `[0, 1, 0, 1]` or `[0.63475, 0.234, ..., 0.2646]`.  They are a trained/learned representation for data like text, images, and tables and served as preditions form these models. Based on the type of model that is used in training they can be very good at retaining latent information like semantic meaning in text, objects in images, and correlation in tables.  This series shows ways of getting predicted embeddings and example uses of embeddings.  

## Vertex AI Text Embeddings API

Get to know the [Vertex AI Text Embeddings API](https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings) through example including how to scale request and make batch request for many embeddings predictions.  
- [Vertex AI Text Embeddings API](./Vertex%20AI%20Text%20Embeddings%20API.ipynb)

## Multimodal Embeddings of Text, Images, Video, and Combinations

Expand from predicted embedding of text (above) to images and video as well as text.  This include combinations where the embeddings are from the same semantic space so the embeddings can be use together for searching images, text, and video.
- [Vertex AI Multimodal Embeddings](./Vertex%20AI%20Multimodal%20Embeddings.ipynb)

## The Math of Similarity

A key use case for embeddings it representing semantic meaning of content, like chunks of text from a document.  Retrieving context for a prompt to an LLM can include using the predicted embedding of the prompt to find matching chunks of text using distance measures like dot product, Euclidean distance, and cosine similarity.  In the following notebook work the math of these methods is explored and visualized to provide intuition for which distance measure should be used for retrieval:
- [The Math of Similarity](./The%20Math%20of%20Similarity.ipynb)

## Embedding Tablular Data - Autoencoders

There are applications where being able to condense a table can be helpful.  Like fewer features for model training.  One method of learning a condensed representation of a table is an autoencoder, which uses successive hidden layers of a neural network that first condenses (encodes) and then expands (decodes) while comparing the input to the output to create a loss function with a goal of recreating the input from the encoded representation.  The predicted encoding for a row can be used to create an embedding for rows. This embedding can then be used for clustering, row matching (think master data management), and more.

The notebook workflow in ["BQML Autoencoder As Table Embedding"](./BQML%20Autoencoder%20As%20Table%20Embedding.ipynb) shows how to create an embedding for a BigQuery table using BigQuery ML to train an autoencoder.  The result is also used in ["Feature Store - Embeddings"](../../MLOps/Feature%20Store/Feature%20Store%20-%20Embeddings.ipynb) to show vector matching and entity matching with Vertex AI Feature Store online serving.

## Deeper Examples

These deeper example illustrate use case for embeddings:
- [Vertex AI GenAI Embeddings](./Vertex%20AI%20GenAI%20Embeddings.ipynb)
    - Work with embeddings for text, images, and combination to visualize embeddings spaces using the [TensorBoard](https://www.tensorflow.org/tensorboard) built-in [Embedding Projector](https://www.tensorflow.org/tensorboard/tensorboard_projector_plugin#saving_data_for_tensorboard)
- [Vertex AI GenAI Embeddings - As Feature For Hierarchical Classification](Vertex%20AI%20GenAI%20Embeddings%20-%20As%20Features%20For%20Hierarchical%20Classification.ipynb)
    - Categorize content from a store catalog using embeddings of text and images by using the embeddings of producting information to train a classifer.  The catalog includes a hierarchy of products an the workflow examines using the classifier to identify mis-classified items and predict the best placement for new items.

