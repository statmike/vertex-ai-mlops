![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2F05+-+TensorFlow&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/05%20-%20TensorFlow/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /05 - TensorFlow/readme.md

This series of notebooks highlights the use of Vertex AI for machine learning workflows with [TensorFlow](https://www.tensorflow.org/).  The same simple model specification is used for all examples with the focus put on workflows for different ML workflows and operational tasks.  The goal is to provide a starting point that can be used with the model architecture you already have.

>**NOTE (UPDATE FOR AUGUST 2023):** The notebooks in the `05 - TensorFlow` series demonstrate training, serving and operations for TensorFlow models and take advantage of [Vertex AI TensorBoard](https://cloud.google.com/vertex-ai/docs/experiments/tensorboard-overview) to track training across experiments.  Running these notebooks will create a Vertex AI TensorBoard instance which previously (before August 2023) had a subscription cost but is now priced based on storage of which this notebook will create minimal size (<2MB). - [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing#tensorboard).

<p align="center" width="100%">
    <img src="../architectures/overview/training.png" width="45%">
    &nbsp; &nbsp; &nbsp; &nbsp;
    <img src="../architectures/overview/training2.png" width="45%">
</p>

**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)
- [01 - BigQuery - Table Data Source.ipynb](../01%20-%20Data%20Sources/01%20-%20BigQuery%20-%20Table%20Data%20Source.ipynb)

## Notebooks:
- Train A Model In A Notebook - with local resources:
    - [05 - Vertex AI Custom Model - TensorFlow - in Notebook.ipynb](./05%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20in%20Notebook.ipynb)
- Convert Notebook based Code Into Python Scripts:
    - [05 - Vertex AI Custom Model - TensorFlow - Notebook to Script.ipynb](./05%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Notebook%20to%20Script.ipynb)
    - Run the script as a [Vertex AI Custom Job](https://cloud.google.com/vertex-ai/docs/training/create-custom-job):
        - Script as Source: [05a - Vertex AI Custom Model - TensorFlow - Custom Job With Python File.ipynb](./05a%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Custom%20Job%20With%20Python%20File.ipynb)
        - Python Source Distribution as Source: [05b - Vertex AI Custom Model - TensorFlow - Custom Job With Python Source Distribution.ipynb](./05b%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Custom%20Job%20With%20Python%20Source%20Distribution.ipynb)
        - Custom Container as Source: [05c - Vertex AI Custom Model - TensorFlow - Custom Job With Custom Container.ipynb](./05c%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Custom%20Job%20With%20Custom%20Container.ipynb)
    - Run the script as a [Vertex AI Training Pipeline](https://cloud.google.com/vertex-ai/docs/training/create-training-pipeline), a Custom Job that also creates a Vertex AI Model Registry resource:
        - Script as Source: [05d - Vertex AI Custom Model - TensorFlow - Training Pipeline With Python file.ipynb](./05d%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Training%20Pipeline%20With%20Python%20file.ipynb)
        - Python Source Distribution as Source: [05e - Vertex AI Custom Model - TensorFlow - Training Pipeline With Python Source Distribution.ipynb](./05e%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Training%20Pipeline%20With%20Python%20Source%20Distribution.ipynb)
        - Custom Container as Source: [05f - Vertex AI Custom Model - TensorFlow - Training Pipeline With Custom Container.ipynb](./05f%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Training%20Pipeline%20With%20Custom%20Container.ipynb)
- Convert Notebook based Code Into Python Scripts For Hyperparameter Tuning:
    - [05 - Vertex AI Custom Model - TensorFlow - Notebook to Hyperparameter Tuning Script.ipynb](./05%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Notebook%20to%20Hyperparameter%20Tuning%20Script.ipynb)
    - Run the script as a [Vertex AI Hyperparameter Tuning Job](https://cloud.google.com/vertex-ai/docs/training/using-hyperparameter-tuning)
        - Script as Source: [05g - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Python file.ipynb](./05g%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Hyperparameter%20Tuning%20Job%20With%20Python%20file.ipynb)
        - Python Source Distribution as Source: [05h - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Python Source Distribution.ipynb](./05h%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Hyperparameter%20Tuning%20Job%20With%20Python%20Source%20Distribution.ipynb)
        - Custom Container as Source: [05i - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Custom Container.ipynb](./05i%20-%20Vertex%20AI%20Custom%20Model%20-%20TensorFlow%20-%20Hyperparameter%20Tuning%20Job%20With%20Custom%20Container.ipynb)
- Predictions From Models:
    - [05Tools - Prediction - Online](./05Tools%20-%20Prediction%20-%20Online.ipynb)
    - [05Tools - Prediction - NVIDIA Triton](./05Tools%20-%20Prediction%20-%20NVIDIA%20Triton.ipynb)
    - [05Tools - Prediction - Batch](./05Tools%20-%20Prediction%20-%20Batch.ipynb)
    - [05Tools - Prediction - Local](./05Tools%20-%20Prediction%20-%20Local.ipynb)
    - [05Tools - Prediction - Custom](./05Tools%20-%20Prediction%20-%20Custom.ipynb)
- Understanding and Explaining Models:
    - [05Tools - Explainability - Example-Based](./05Tools%20-%20Explainability%20-%20Example-Based.ipynb)
    - [05Tools - Explainability - Feature-Based](./05Tools%20-%20Explainability%20-%20Feature-Based.ipynb)
    - [05Tools - Interpretability with LIT](./05Tools%20-%20Interpretability%20with%20LIT.ipynb)
    - [05Tools - Interpretability with WIT](./05Tools%20-%20Interpretability%20with%20WIT.ipynb)
- Scaling and Tracking:
    - [05Tools - Distributed Training](./05Tools%20-%20Distributed%20Training.ipynb)
    - [05Tools - Experiments](./05Tools%20-%20Experiments.ipynb)
    - [05Tools - ML Metadata](./05Tools%20-%20ML%20Metadata.ipynb)
    - [05Tools - Monitoring](./05Tools%20-%20Monitoring.ipynb)
    - [05 Tools - Automation](./05Tools%20-%20Automation.ipynb)


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
- [`./code/train.py`](./code/train.py) is the script used for all:
    - Vertex AI Training > Custom Jobs: `05a`, `05b` and `05c` 
    - Vertex AI Training > Training Jobs: `05d`, `05e` and `05f`
- [`./code/hp_train.py`](./code/hp_train.py) is the script used for all:
    - Vertex AI Training > Hyperparameter Tuning Jobs: `05g`, `05h`, and `05i`
- Example `05a` through `05i` all:
    - Work as Experiments, each time they are run they log as an experiment run
    - Write TensorFlow callbacks to hosted TensorBoard
    - Can be run multiple times and each time will update the resulting model as a new version in the Vertex AI Model Registry.  The model name is unique to the notebook=experiment.




















