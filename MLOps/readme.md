![tracker](https://us-central1-statmike-mlops-349915.cloudfunctions.net/tracking-pixel?path=statmike%2Fvertex-ai-mlops%2FMLOps&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# MLOps

Let's talk about MLOps!

---
## in progress - stay tuned

- more than ML
- authoring, testing, scaling
- controling - CI and CD - Hey this is just DevOps!
- Automation & Workflows
- Putting it all together with CT


Want more now?
- The best overview ever written: https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines
    - Even if you don't use TFX, this captures the whole goal!
- MLOps Overview: https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning
- MLOps on Vertex AI: https://cloud.google.com/vertex-ai/docs/start/introduction-mlops

---

## ML Code

This is where it all begins.  Hands find keyboard and start writing instructions to:
- find data source
- read data
- explore data
- prepare data
- process data into features
- build a training routine: language (R, Python) with a package or framework (XGBoost, TensorFlow, PyTorch, scikit-learn, ...)
- iterate, iterate, iterate, ...
- evaluate the model
- iterate, iterate, iterare, ...
- prepare model for deployment - batch, online, cloud, onprem, mobile, ....
- monitor shift and drift
- troubleshoot everything that goes wrong or does not make sense
- automate
- repeat
- a MILLION other things!

This starts with a user in a tool of choice.  An IDE for developing this code.  Sometimes its a controlled experience in a tool that authors code for the user (high level).  If you are reading this then it is likely an IDE where you are the author of the code like OSS-Code (VSCode), JupyterLab, Colab, PyCharm amongst the many choices.

---
## Pipelines

The workflow of ML code does many steps in sequence.  Some of the steps involve conditional logic like deploying the new model only when it is more accurate than the currently deployed model.  This is a pipeline.  Pipelines are essential for turning ML processes into MLOps.  MLOps goes the next mile with automation, monitoring, and governing the workflow.

There are frameworks for specifying these steps like [Kubeflow Pipelines (KFP)](https://www.kubeflow.org/docs/components/pipelines/v2/introduction/) and [TensorFlow Extended (TFX)](https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines).  [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction) is a orchestrator for both of these.
- The [history of Kubeflow](https://www.kubeflow.org/docs/started/introduction/#history) is creating a simplified way to running TensorFlow Extended jobs on Kubernetes.

### Components

The steps of the workflow, an ML task, are called components. Getting logic and code into components can consists of using prebuilt components or constructing custom components:
- KFP
    - Pre-Built:
        - [Google Cloud Pipeline Components](https://cloud.google.com/vertex-ai/docs/pipelines/gcpc-list)
            - [GitHub](https://github.com/kubeflow/pipelines/blob/master/components/google-cloud/README.md)
    - Custom:
        - [Lightweight Python Components](https://www.kubeflow.org/docs/components/pipelines/v2/components/lightweight-python-components/) - create a component from a Python function
        - [Containerized Python Components](https://www.kubeflow.org/docs/components/pipelines/v2/components/containerized-python-components/) - for complex dependencies
        - [Container Component](https://www.kubeflow.org/docs/components/pipelines/v2/components/container-components/) - a component from a container
- TFX
    - Pre-Built:
        - [TFX Standard Components](https://www.tensorflow.org/tfx/guide#tfx_standard_components)
        - [Community-developed components](https://www.tensorflow.org/tfx/addons)
    - Custom:
        - [Python function-based components](https://www.tensorflow.org/tfx/guide/custom_function_component) - create a component from a Python function
        - [Container-based components](https://www.tensorflow.org/tfx/guide/container_component) - a component from a contaienr
        - [Fully custom components](https://www.tensorflow.org/tfx/guide/custom_component) - reuse and extend standard components.

For an overview of components from custom to pre-built, check out this notebook:
- [Vertex AI Pipelines - Components](./Vertex%20AI%20Pipelines%20-%20Components.ipynb)

### Component IO

Component inputs and outputs can take two forms: parameters and artifacts.  

**Parameters** are Python objects like `str`, `int`, `float`, `bool`, `list`, `dict` objects that are defined as inputs to pipelines and components. Components can also return parameters for input into subsequent components. Paramters are excellent for changing the behavior of a pipeline/component through inputs rather than rewriting code.
- [KFP Parameters](https://www.kubeflow.org/docs/components/pipelines/v2/data-types/parameters/)
- [TFX Parameters](https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines#parameter)

**Artifacts** are multi-parameter objects that represent machine learning artifacts and have defined schemas and are stored as metadata with lineage.  The artifact schemas follow the [ML Metadata (MLMD)](https://github.com/google/ml-metadata) client library.  This helps with understanding and analyzing a pipeline.
- [KFP Artifacts](https://www.kubeflow.org/docs/components/pipelines/v2/data-types/artifacts/)
    - provided [artifact types](https://www.kubeflow.org/docs/components/pipelines/v2/data-types/artifacts/#artifact-types)
    - [Google Cloud Artifact Types](https://google-cloud-pipeline-components.readthedocs.io/en/google-cloud-pipeline-components-2.0.0/api/artifact_types.html)
- [TFX Artifacts](https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines#artifact)




### Scheduling Pipelines

Pipelines can be run on a schedule directly in Vertex AI without the need to setup a scheduler and trigger (like PubSub).  Here is an example of a pipeline run followed by a schedule that repeats the pipeline at a specified interval the number of iterations set as the maximum on the schedule:

- [Vertex AI Pipelines - Scheduling](./Vertex%20AI%20Pipelines%20-%20Scheduling.ipynb)

This can have many helpful applications, including:
- Running Batch predictions, evaluations, monitoring each day or week
- Retraining a model, do evaluations, and comparing the new model to the currently deployed model then conditionally updating the deployed model
- Check for new training records and commence with retraining if conditions are met - like records that increase a class by 10%, atleast 1000 new records, ....

### Triggering Pipelines



---

