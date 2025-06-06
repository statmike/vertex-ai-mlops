![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FModel+Evaluation&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Model%20Evaluation/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Model Evaluation

> You are here: `vertex-ai-mlops/MLOps/Model Evaluation/readme.md`

Model evaluation is the critical process of rigorously comparing a model's predictions against the actual, known truth. These comparisons are quantified by **evaluation metrics**, which succinctly describe the model's performance over a given sample of data instances. Evaluations are indispensable throughout a model's lifecycle: they are tremendously helpful during **training iterations** to understand not only how well a current model version performs on the training data, but more importantly, how effectively it **generalizes** when exposed to unseen validation and test data. Beyond development, evaluations remain crucial during the **operational life of a deployed model**. Here, new data samples with confirmed outcomes are continuously used to verify that the model retains the accuracy observed during initial training, detect performance degradation, and maintain trust. Furthermore, it can be particularly insightful to evaluate models on data instances from various time periods, including historical data, to assess how consistently the model behaves across different temporal segments compared to newer data.

---

**Important Note on Model Evaluation vs. Model Monitoring:**

While model evaluations help us understand performance, particularly in a deployed setting, it's crucial to distinguish them from **model monitoring**. Noticing model degradation through evaluations, such as the observed accuracy on new, labeled data, is often a **lagging and delayed signal**. This is because evaluations typically require ground truth labels, which may only become available after some time.

**Model monitoring**, on the other hand, is a more proactive and real-time approach. It involves continuously tracking the statistical properties of a model's **feature inputs** and **predictions** for shifts from the training data distribution, and detecting **drift** over time. Monitoring tools aim to alert you to potential issues *before* or *as* performance degrades, allowing for earlier intervention.

For a deeper dive into proactive strategies, refer to the dedicated content on [Model Monitoring](../Model%20Monitoring/readme.md).

---

## Workflows: Model Evaluation by Task Type

**In each of the following workflow examples, you will observe a consistent pattern:**

1.  **Creating and Training a Model:** We'll start by defining and training a machine learning model specific to the task type.
2.  **Evaluating the Model:** Comprehensive evaluation will be performed using appropriate metrics for the given problem (e.g., binary classification, regression, etc.).
3.  **Registering the Model in Vertex AI Model Registry:** The trained model will then be registered as a new version within the Vertex AI Model Registry.
4.  **Custom Loading Evaluations to the Model in the Registry:** Finally, the collected evaluation metrics will be custom loaded and associated with the respective model version in the Vertex AI Model Registry, demonstrating how to centralize your model's performance data.
  
Additional concepts covered:
- Including explainations (feature attributions) with evaluations is also possible.  This is demonstrated in the Binary Classification example.
- Including metrics on data slices, like the individual class levels, is possible and included in the multi-class and multi-level classification examples.


---

This project provides practical examples and code snippets demonstrating how to collect and understand evaluation metrics for various machine learning task types, ultimately preparing these results for integration with the Vertex AI Model Registry. Click through the links below to explore each specific evaluation scenario:

* ### Binary Classification: Is it A or Not-A?
    Dive into the fundamental world of binary classification. This notebook covers key metrics like accuracy, precision, recall, F1-score, and ROC AUC, showcasing how to interpret them when your model predicts one of two outcomes.
    * [Explore Binary Classification Evaluation](model-evaluation-classification-binary.ipynb)
      * Prepare Data
      * Train a model with preprocessing pipeline
      * Save and upload the model to Vertex AI Model Registry
      * Create and upload custom evaluations to the model in Vertex AI Model Registry
        * Review and compare evaluations in the console and with the Vertex AI SDK
      * Create and upload model explanations (feature attributions) to the evaluation in the Vertex AI Model Registry.

* ### Multi-Class Classification: Distinguishing Between Many Categories
    Expand your understanding to scenarios where your model must categorize inputs into more than two distinct classes. Learn about metrics like macro/micro averages, weighted averages, and confusion matrices to gain a comprehensive view of performance across multiple categories.
    * [Explore Multi-Class Classification Evaluation](model-evaluation-classification-multi-class.ipynb)
      * Prepare Data
      * Train a model with preprocessing pipeline
      * Save and upload the model to Vertex AI Model Registry
      * Create and upload custom evaluations to the model in Vertex AI Model Registry
        * Review and compare evaluations in the console and with the Vertex AI SDK
      * Create and upload custom evaluations on model slices, each class level of the multi-class model, to the evaluations in Vertex AI Model Registry
        * Review the slice evaluations in the console and with the Vertex AI SDK

* ### Multi-Label Classification: When One Sample Has Many Answers
    Discover how to evaluate models that predict multiple independent labels for a single input. This notebook will guide you through relevant metrics like Hamming loss, Jaccard score, and per-label performance analysis, crucial for understanding models where an item can belong to several categories simultaneously.
    * [Explore Multi-label Classification Evaluation](model-evaluation-classification-multi-label.ipynb)
      * In Progress

* ### Regression: Predicting Continuous Values
    Shift focus to models that predict continuous numerical outputs. This section details essential regression metrics such as Mean Squared Error (MSE), Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and R-squared ($R^2$), providing insights into prediction accuracy and error magnitude.
    * Explore Regression Evaluation - future: model-evaluation-regression.ipynb

* ### Forecasting: Predicting Future Trends Over Time
    Delve into the specialized world of time-series forecasting. Learn how to evaluate models that predict future values, often using metrics that account for temporal dependencies, such as Mean Absolute Percentage Error (MAPE), Symmetric Mean Absolute Percentage Error (sMAPE), and various error measures over time horizons.
    * Explore Forecasting Evaluation - future: model-evaluation-forecasting.ipynb

---
## Considerations

These example workflows above create metrics locally and use the Vertex AI SDK to manually load these to the model in Vertex AI Model Registry.  There are more automated ways to accomplish this:
- Directly from the console with the Vertex AI Model Registry:
  - Uses a batch prediction job
  - [read more](https://cloud.google.com/vertex-ai/docs/evaluation/using-model-evaluation#create_an_evaluation)
-  Using pre-built pipeline components to create and load evaluation metrics:
   - Uses VertexAI Pipelines
   - [read more](https://cloud.google.com/vertex-ai/docs/pipelines/gcpc-list#modeleval_components)
