![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FExperiment+Tracking&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Experiment%20Tracking/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Experiment%20Tracking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Experiment%20Tracking/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Experiment%20Tracking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Experiment%20Tracking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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