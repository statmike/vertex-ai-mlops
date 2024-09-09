![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FExperiment+Tracking&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Experiment%20Tracking/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Experiment Tracking
> You are here: `vertex-ai-mlops/MLOps/Experiment Tracking/readme.md`

The work of ML is inherantly iterative and experimental, involving trying different approaches and comparing results to make decisions towards future iteration.  A key part of moving from ad-hoc coding to fully operationalize ML training is tracking inputs, outputs, and other parameters.  Keeping track of information within experiments is the goal of [Vertex AI Experiments](https://cloud.google.com/vertex-ai/docs/experiments/intro-vertex-ai-experiments#experiments-experiment-runs). This hosted service lets you [log information](https://cloud.google.com/vertex-ai/docs/experiments/log-data) from each run, and even has [autologging](https://cloud.google.com/vertex-ai/docs/experiments/autolog-data) for common ML Frameworks.

The architecture of experiments is:
- The Vertex AI Experiments **Service** (setup by default)
    - An **Experiment**: Create, Delete
        - **Runs** of the Experiment: Start, End, Resume, Delete, Manage
            - Use Autologging for common frameworks (Keras, LightGBM, Pytorch Lightning, Scikit-learn, XGBoost, and more)
            - Directed logging for:
                - parameters (learning rate, epochs, ...)
                - metrics (accuracy, precision, ...)
                - classification metrics (confusion matrix, ROC curve data, ...)
                - time series metrics (metrics for each step(epoch) of training)

The logging is further enhanced with connectivity to other Vertex AI services:
- Integrated with Vertex AI TensorBoard instance for backing time series metrics
- Model Logging
    - Save, Track, Load Models
    - Select models to register to Vertex AI Model Registry
- Use Executions and Artifacts to assign stages to your workflow with input and output Artifacts
- Include Pipeline runs in experiments or experiment and have all pipeline parameters and Artifacts directly inferred
- Logging within Training Jobs
- Retrieve data for a run and compare data across runs using the Vertex AI SDK or the Vertex AI Console

<div id='workflow-8'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

Work with experiments and explore all of these features in the following notebook based workflow:
- [Vertex AI Experiments](./Vertex%20AI%20Experiments.ipynb)

</td></tr></table></div>