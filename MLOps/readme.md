![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps&file=readme.md)
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

Before we get started, check these resources out:
- The best overview ever written (#opinion): https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines
    - Even if you don't use TFX, this captures the whole goal!
- MLOps Overview: https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning
- MLOps on Vertex AI: https://cloud.google.com/vertex-ai/docs/start/introduction-mlops

**TL;DR**

This is a series of notebook based workflows that teach all the ways to use pipelinnes and experiment withing Vertex AI. The suggested order and description/reason is:

|Notebook Workflow|Description|
|---|---|
|[Vertex AI Pipelines - Introduction](./Vertex%20AI%20Pipelines%20-%20Introduction.ipynb)|Introduction to pipelines with the console and Vertex AI SDK|
|[Vertex AI Pipelines - Components](./Vertex%20AI%20Pipelines%20-%20Components.ipynb)|An introduction to all the ways to create pipeline components from your code|
|[Vertex AI Pipelines - IO](./Vertex%20AI%20Pipelines%20-%20IO.ipynb)|An overview of all the type of inputs and outputs for pipeline components|
|[Vertex AI Pipelines - Control](./Vertex%20AI%20Pipelines%20-%20Control.ipynb)|An overview of controlling the flow of exectution for pipelines|
|[Vertex AI Pipelines - Secret Manager](./Vertex%20AI%20Pipelines%20-%20Secret%20Manager.ipynb)|How to pass sensitive information to pipelines and components|
|[Vertex AI Pipelines - Scheduling](./Vertex%20AI%20Pipelines%20-%20Scheduling.ipynb)|How to schedule pipeline execution|
|[Vertex AI Pipelines - Management](./Vertex%20AI%20Pipelines%20-%20Management.ipynb)|Managing, Reusing, and Storing pipelines and components|
|[Vertex AI Experiments](./Vertex%20AI%20Experiments.ipynb)|Understanding and using Vertex AI Experiments|

To discover these notebooks as part of an introduction to MLOps read on below!

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

This starts with a user in a tool of choice.  An IDE for developing this code.  Sometimes it's a controlled experience in a tool that authors code for the user (high level).  If you are reading this then it is likely an IDE where you are the author of the code like OSS-Code (VSCode), JupyterLab, Colab, PyCharm amongst the many choices.

---
## Pipelines

The workflow of ML code does many steps in sequence.  Some of the steps involve conditional logic like deploying the new model only when it is more accurate than the currently deployed model.  This is a pipeline.  Pipelines are essential for turning ML processes into MLOps.  MLOps goes the next mile with automation, monitoring, and governing the workflow.

There are frameworks for specifying these steps like [Kubeflow Pipelines (KFP)](https://www.kubeflow.org/docs/components/pipelines/v2/introduction/) and [TensorFlow Extended (TFX)](https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines).  [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction) is a managed service that can execute both of these.
- The [history of Kubeflow](https://www.kubeflow.org/docs/started/introduction/#history) is creating a simplified way to running TensorFlow Extended jobs on Kubernetes.

Get a quick start with pipelines by reviewing this workflow for an example using both the Vertex AI Console and SDK.
- [Vertex AI Pipelines - Introduction](./Vertex%20AI%20Pipelines%20-%20Introduction.ipynb)
    - **Build** a simple pipeline with IO parameters and artifacts as well as conditional execution
    - **Review** all parts (runs, tasks, parameters, artifacts, metadata) with the Vertex AI Console
    - **Retrieve** all parts (runs, tasks, parameters, artifacts, metadata) with the Vertex AI SDK

---
### Components

The steps of the workflow, an ML task, are run with components. Getting logic and code into components can consists of using prebuilt components or constructing custom components:
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
    - **Pre-Built Components:** Easy access to many GCP services
    - **Lightweight Python Components:** Build a component from a Python function
    - **Containerized Python Components:** Build an entire Python enviornment as a component
    - **Container Components:** Any container as a component
    - **Importer Components:** Quickly import artifacts

**Compute Resources** For Components:

Running pipleines on Vertex AI Pipelines runs each component as a Vertex AI Training `CustomJob`.  This defaults to a vm based on `e2-standard-4` (4 core CPU, 16GB memory).  This can be modified at the task level of pipelines to choose different computing resources, including GPUs.  For example:

```Python
@kfp.dsl.pipeline()
def pipeline():
    task = component().set_cpu_limit(C).set_memory_limit(M).add_node_selector_constraint(A).set_accelerator_limit(G).
```
Where the inputs are defining [machine configuration for the step](https://cloud.google.com/vertex-ai/docs/pipelines/machine-types):
- C = a string representing the number of CPUs (up to 96).
- M = a string represent the memory limit.  An integer follwed by K, M, or G (up to 624GB).
- A = a string representing the desired GPU  or TPU type
- G = an integer representing the multiple of A desired.


---
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

See all the types of parameters and artifacts in action with the following notebook based workflow:
- [Vertex AI Pipelines - IO](./Vertex%20AI%20Pipelines%20-%20IO.ipynb)
    - **parameters:** input, multi-input, output, multi-output
    - **artifacts:** input, output, Vertex AI ML Metadata Lineage

**Secure Parameters:** Passing credentials for an API or service can expose them.  If these credentials are hardcoded then they can be discovered from the source code and are harder to update.  A great solution is using [Secret Manager](https://cloud.google.com/secret-manager/docs/create-secret-quickstart#secretmanager-quickstart-console) to host credentials and then pass the name of the credential as a parameter.  The only modification needed to a component is to use a Python client to retrieve the credentials at run time.  Check out how easy this is to implement with the following notebook based example workflow:
- [Vertex AI Pipelines - Secret Manager](./Vertex%20AI%20Pipelines%20-%20Secret%20Manager.ipynb)
    - **Setup** Secret Manager and use the console and Python Client to store secrets
    - **Retrieve** secrets using the Python Client
    - An **example** pipeline that retrieves credentails from Secret Manager
---
### Control Flow For Pipelines

As the task of an ML pipeline run they form a graph.  The outputs of upstream components become the inputs of downstram components.  Both TFX and KFP automatically use these connection to create a DAG of execution.  When logic needs to be specified in the pipeline flow of execution the use of control structures is necessary.  

The following notebook shows many examples of implement controls in KFP while running on Vertex AI Pipelines:
- [Vertex AI Pipelines - Control](./Vertex%20AI%20Pipelines%20-%20Control.ipynb)
    - **Ordering**: DAG and Explicit ordering
    - **Conditional Execution**: if, elif (else if), and else
        - **Collecting**: Conditional results
    - **Looping**: And Parallelism
        - **Collecting**: Looped Results
    - **Exit Handling:** with and without task failures
    - **Error Handling** continue execution even after task failures

---
### Scheduling Pipelines

Pipelines can be run on a schedule directly in Vertex AI without the need to setup a scheduler and trigger (like PubSub).  Here is an example of a pipeline run followed by a schedule that repeats the pipeline at a specified interval the number of iterations set as the maximum on the schedule:

- [Vertex AI Pipelines - Scheduling](./Vertex%20AI%20Pipelines%20-%20Scheduling.ipynb)
    - **Create**
    - **Retrieve**
    - **Manage**

This can have many helpful applications, including:
- Running Batch predictions, evaluations, monitoring each day or week
- Retraining a model, do evaluations, and comparing the new model to the currently deployed model then conditionally updating the deployed model
- Check for new training records and commence with retraining if conditions are met - like records that increase a class by 10%, atleast 1000 new records, ....

---
### Managing Pipelines: Storing And Reusing Pipelines & Components

As seen above, pipelines are made up of steps which are executions of components.  These components are made up of code, container, and instructions (inputs and outputs).  

**Components:**

For each type of component, `kfp` compiles the component into YAML as part of the pipeline.  You can also directly compile individual components.  This makes the YAML for a component a source that can be managed.  And using this in additional pipelines is made possible with `kfp.components.load_component_from_*()` which has version for files, urls, text (strings).

**Pipelines:**

Pipelines are compiled into YAML files that include component specifications.  Managine these pipelines files as artifacts is made easy with the combination of:
- Kubeflow Pipelines SDK and the included [`kfp.registry.RegistryClient`](https://kubeflow-pipelines.readthedocs.io/en/latest/source/registry.html)
- Google Cloud [Artifact Registry](https://cloud.google.com/artifact-registry/docs/overview) with native format for [Kubeflow pipeline templates](https://cloud.google.com/artifact-registry/docs/kfp)
- [Integration with Vertex AI](https://cloud.google.com/vertex-ai/docs/pipelines/create-pipeline-template#kubeflow-pipelines-sdk-client) for creating, uploading and using pipeline templates

Work directly with these concepts in the following notebook based workflow:
- [Vertex AI Pipelines - Management](./Vertex%20AI%20Pipelines%20-%20Management.ipynb)

---
## Experiments
Describe.

Workflow:
- [Vertex AI Experiments](./Vertex%20AI%20Experiments.ipynb)

---
### Topics In Progress

- [ ] Triggering Pipelines
- [ ] Graphic for code > container > component > pipeline with entrypoints
- [ ] docstring for components and pipelines
- [ ] caching with Vertex AI Pipelines
- [ ] local execution for testing
- [ ] Link to surrounding topics
    - [feature architectures](../Feature%20Store/Feature%20Focused%20Data%20Architecture.ipynb)
    - [feature store](../Feature%20Store/readme.md)
    - [model monitoring](../Model%20Monitoring/readme.md)
