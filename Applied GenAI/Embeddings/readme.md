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

Embeddings are condensed representations of data that retain the information from the data.  They are represented by a vector of numbers, usually floats, like `[0, 1, 0, 1]` or `[0.63475, 0.234, ..., 0.2646]`.  The are trained/learned representations for data like text, images, and tables. Based on the type of model that is used in training they can be very good at retraining latent information like semantic meaning in text, objects in images, and correlation in tables.  This series shows ways of creating embeddings through OSS models, API's and custom models.  

**TABLES**

There are applications where being able to condense a table can be helpful.  Like fewer features for model training.  One method of learning a condensed representation of a table is an autoencoder, which uses successive hidden layers of a neaural network that first condense (encode) and then expand (decode) while comparing the input to the output to create a loss function with a goal of recreating the input from the encoded representation.  The predicted encoding for a row can be used to create an embedding for rows that can then be used for clustering, row matching (think master data management), and more.

The notebook workflow in ["BQML Autoencoder As Table Embedding"](./BQML%20Autoencoder%20As%20Table%20Embedding.ipynb) shows how to create an embedding for a BigQuery table using BigQuery ML to train an autoencoder.  The result is also used in ["Feature Store - Embeddings"](../../MLOps/Feature%20Store/Feature%20Store%20-%20Embeddings.ipynb) to show vector matching and entity matching with Vertex AI Feature Store online serving.


---
TODO:
- what are embeddings overview with numpy
- embeddings API deep dive
- tools:
    - vertex vector search
    - bigquery ml
    - alloy db
    - scaan
    - llamaindex
    - others?
- projector 
- build your own with BQML autoencoder
- working with embeddings



A review of embedding in Vertex AI:
- Foundation models for text, and multi modal (text, image, text and image)
- OSS pre-trained: local, BQML, and Vertex AI Endpoints


A review of tools for Vector Matching:
- ScANN
- BigQuery with ML.DISTANCE
- CloudSQL and pgvector
- Vertex AI Vector Search (fomerly Matching Engine)

Topics:
- Brute force and approximate matching
- Indexes that update with insert/delete/updates
- Filtered searches
