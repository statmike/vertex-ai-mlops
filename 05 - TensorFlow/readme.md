# 05 - Custom Models: TensorFlow
This series of notebooks highlights the use of Vertex AI for machine learning workflows with [TensorFlow](https://www.tensorflow.org/).  The same simple model specification is used for all examples with the focus put on workflows for different ML workflows and operational tasks.  The goal is to provide a starting point that can be used with the model architecture you already have.

>**NOTE:** The notebooks in the `05 - TensorFlow` series demonstrate training, serving and operations for TensorFlow models and take advantage of [Vertex AI TensorBoard](https://cloud.google.com/vertex-ai/docs/experiments/tensorboard-overview) to track training across experiments.  Running these notebooks will create a Vertex AI TensorBoard instance which has a user-based montly pricing that is different than other services that charge by usage.  This cost is $300 per user - [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing#tensorboard).

<p align="center" width="100%">
    <img src="../architectures/overview/training.png" width="45%">
    &nbsp; &nbsp; &nbsp; &nbsp;
    <img src="../architectures/overview/training2.png" width="45%">
</p>

**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)
- [01 - BigQuery - Table Data Source.ipynb](../01%20-%20Data%20Sources/01%20-%20BigQuery%20-%20Table%20Data%20Source.ipynb)

## Notebooks:
- [05 - Vertex AI Custom Model - TensorFlow - in Notebook.ipynb](./05%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20in%20Notebook.ipynb)
- [05 - Vertex AI Custom Model - TensorFlow - Notebook to Script.ipynb](./05%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Notebook%20to%20Script.ipynb)
- [05 - Vertex AI Custom Model - TensorFlow - Notebook to Hyperparameter Tuning Script.ipynb](./05%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Notebook%20to%20Hyperparameter%20Tuning%20Script.ipynb)
- [05a - Vertex AI Custom Model - TensorFlow - Custom Job With Python File.ipynb](./05a%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Custom%20Job%20With%20Python%20File.ipynb)
- [05b - Vertex AI Custom Model - TensorFlow - Custom Job With Python Source Distribution.ipynb](./05b%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Custom%20Job%20With%20Python%20Source%20Distribution.ipynb)
- [05c - Vertex AI Custom Model - TensorFlow - Custom Job With Custom Container.ipynb](./05c%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Custom%20Job%20With%20Custom%20Container.ipynb)
- [05d - Vertex AI Custom Model - TensorFlow - Training Pipeline With Python file.ipynb](./05d%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Training%20Pipeline%20With%20Python%20file.ipynb)
- [05e - Vertex AI Custom Model - TensorFlow - Training Pipeline With Python Source Distribution.ipynb](./05e%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Training%20Pipeline%20With%20Python%20Source%20Distribution.ipynb)
- [05f - Vertex AI Custom Model - TensorFlow - Training Pipeline With Custom Container.ipynb](./05f%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Training%20Pipeline%20With%20Custom%20Container.ipynb)
- [05g - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Python file.ipynb](./05g%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Hyperparameter%20Tuning%20Job%20With%20Python%20file.ipynb)
- [05h - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Python Source Distribution.ipynb](./05h%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Hyperparameter%20Tuning%20Job%20With%20Python%20Source%20Distribution.ipynb)
- [05i - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Custom Container.ipynb](./05i%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Hyperparameter%20Tuning%20Job%20With%20Custom%20Container.ipynb)
- [05Tools - Distributed Training.ipynb](./05Tools%20-%20Distributed%20Training.ipynb)
- [05Tools - Experiments.ipynb](./05Tools%20-%20Experiments.ipynb)
- [05Tools - Explainability - Example-Based.ipynb](./05Tools%20-%20Explainability%20-%20Example-Based.ipynb)
- [05Tools - Explainability - Feature-Based.ipynb](./05Tools%20-%20Explainability%20-%20Feature-Based.ipynb)
- [05Tools - Interpretability with LIT.ipynb](./05Tools%20-%20Interpretability%20with%20LIT.ipynb)
- [05Tools - Interpretability with WIT.ipynb](./05Tools%20-%20Interpretability%20with%20WIT.ipynb)
- [05Tools - ML Metadata.ipynb](./05Tools%20-%20ML%20Metadata.ipynb)
- [05Tools - Monitoring.ipynb](./05Tools%20-%20Monitoring.ipynb)
- [05Tools - Pipelines.ipynb](./05Tools%20-%20Pipelines.ipynb)
- [05Tools - Prediction - Online.ipynb](./05Tools%20-%20Prediction%20-%20Online.ipynb)
- [05Tools - Prediction - Batch.ipynb](./05Tools%20-%20Prediction%20-%20Batch.ipynb)
- [05Tools - Prediction - Local.ipynb](./05Tools%20-%20Prediction%20-%20Local.ipynb)
- [05Tools - Prediction - Custom.ipynb](./05Tools%20-%20Prediction%20-%20Custom.ipynb)

**Notes:**
- Vertex AI Training > Custom Jobs run ML training code in a serverless environment:
    - This is featured in notebooks `05a`, `05b` and `05c`
- Vertex AI Training > Training Jobs run ML training code and register the resulting model in Vertex AI Model Registry:
    - This is featured in notebooks `05d`, `05e` and `05f`
- Vertex AI Training > Hyperparameter Tuning Jobs run ML training code and focus in on the best values for hyperparamters:
    - This is featured in notebooks `05g`, `05h`, and `05i`
- Each type of job can be specified with:
    - a single Python script: featured in notebooks `05a`, `05d`, and `05g`
    - a Python source distribution: featured in notebooks `05b`, `05e`, and `05h`
    - a custom container: featured in notebooks `05c`, `05f`, and `05i`
- [`./codetrain.py`](./code/train.py) is the script used for all:
    - Vertex AI Training > Custom Jobs: `05a`, `05b` and `05c` 
    - Vertex AI Training > Training Jobs: `05d`, `05e` and `05f`
- [`./code/hp_train.py`](./code/hp_train.py) is the script used for all:
    - Vertex AI Training > Hyperparameter Tuning Jobs: `05g`, `05h`, and `05i`
- Example `05a` through `05i` all:
    - Work as Experiments, each time they are run they log as an experiment run
    - Write TensorFlow callbacks to hosted TensorBoard
    - Can be run multiple times and each time will update the resulting model as a new version in the Vertex AI Model Registry.  The model name is unique to the notebook=experiment.

---

ToDo:
- [X] add prereq to readme
- [X] Update references to Service Account and check for permissions - reference the 00 notebooks new section for correct setup
- [X] fix references to data in GCS in the Tools - Predictions notebook (and others = search): bucket/series/experiment
- [X] 05 script creation notebooks
    - [X] add narrative
    - [X] add section for testing code
- [X] update/rework/modify a-i (done=abcdefghi)
- [X] modify tools notebook to match a-i update
- [X] split explainability into two notebooks
    - [ ] add example-based to explainability
- [X] split predictions: online, batch, local, custom
    - [X] fix local and cloud run notebooks - tensorflow/serving container issue
    - [X] add BQ input/output example for Batch Predictions
    - [ ] add deployment pools example
    - [ ] add CPR example used in batch and online - link to/from the batch prediction notebook
    - [ ] cloud functions example - with keras serving
    - [ ] BigQuery Remote Function: with cloud functions and cloud run
        - Vertex AI Endpoint, Cloud Run Endpoint, Cloud Function  (with Keras)
- [IP] Pipeline for Hyperparameter Tuning with Vizier example - multiple metrics
- [IP] trigger services: cloud function, cloud schedule, pub/sub
- [ ] distributed training examples: GPU and multi worker
    - [good codelab](https://codelabs.developers.google.com/vertex_multiworker_training#7)
- [X] complete monitoring migration from 06a to here
    - [ ] add batch job monitoring
    - [ ] feature attribution monitoring - requires .explain instead of .predict?
- [ ] ML Metadata - add throughout
- [ ] pipeline - make a tournament that uses experiments to pick a winner and deploy to endpoint
- [ ] Model Evaluation - where to add into workflows or standalone?
- [ ] incorporate example of using console to launch training job (custom container)
- [ ] for next cleaning path
    - update docker repository to be the one named for the project_id without -docker
    - add link to console for repo
    - see the flow in 08f for the artifact registry
    - a-i shorten the model = trainingJob.run - see 08f and the 03 series





















