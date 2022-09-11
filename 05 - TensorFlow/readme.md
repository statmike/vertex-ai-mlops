# 05 - Custom Models: TensorFlow
This series of notebooks highlights the use of Vertex AI for machine learning workflows with [TensorFlow](https://www.tensorflow.org/). 

## Notebooks:
- 05 - Vertex AI Custom Model - TensorFlow - in Notebook.ipynb
- 05a - Vertex AI Custom Model - TensorFlow - Custom Job With Python File.ipynb
- 05b - Vertex AI Custom Model - TensorFlow - Custom Job With Python Source Distribution.ipynb
- 05c - Vertex AI Custom Model - TensorFlow - Custom Job With Custom Container.ipynb
- 05d - Vertex AI Custom Model - TensorFlow - Training Pipeline With Python file.ipynb
- 05e - Vertex AI Custom Model - TensorFlow - Training Pipeline With Python Source Distribution.ipynb
- 05f - Vertex AI Custom Model - TensorFlow - Training Pipeline With Custom Container.ipynb
- 05g - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Python file.ipynb
- 05h - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Python Source Distribution.ipynb
- 05i - Vertex AI Custom Model - TensorFlow - Hyperparameter Tuning Job With Custom Container.ipynb
- 05Tools - Distributed Training.ipynb'
- 05Tools - Experiments.ipynb'
- 05Tools - Explainability.ipynb'
- 05Tools - Interpretability with LIT.ipynb'
- 05Tools - Interpretability with WIT.ipynb'
- 05Tools - ML Metadata.ipynb'
- 05Tools - Monitoring.ipynb'
- 05Tools - Pipelines.ipynb'
- 05Tools - Prediction.ipynb'

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
- `05_train.py` is the script used for all:
    - Vertex AI Training > Custom Jobs
    - Vertex AI Training > Training Jobs
- `05_train_hp.py` is the script used for all:
    - Vertex AI Training > Hyperparameter Tuning Jobs
- Example `05a` through `05i` all:
    - Work as Experiments, each time the are run the log as an experiment run
    - Write TensorFlow callback to hosted TensorBoard
    - Can be run multiple times and each time will update the resulting model as a new version in the Vertex AI Model Registry.  The model name is unique to the notebook=experiment.


<p align="center" width="100%"><center><img src="../architectures/overview/training.png" width="50%"></center></p>
