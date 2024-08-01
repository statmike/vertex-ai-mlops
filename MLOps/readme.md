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

How are you going to manage data, features, training, models, deployment, monitoring, and all the connectivity between these?  How will your approach be impacted if the number of models increases 10x, 100x, or more?

Let's talk about MLOps!

---

## Table of Contents

- [MLOps](#mlops)
    - [ML Code: More Than A Model](#ml-code-more-than-a-model)
    - [Model Fleets: MLOps for Scale](#model-fleets-mlops-for-scale)
    - [Content Overview](#content-overview)
    - [MLOps Resources & References](#mlops-resources--references)
- [Pipelines](#pipelines)
    - [Introduction](#introduction)
    - [Components](#components)
    - [Component IO](#component-io)
    - [Control Flow For Pipelines](#control-flow-for-pipelines)
    - [Scheduling Pipelines](#scheduling-pipelines)
    - [Notifications From Pipelines](#notifications-from-pipelines)
    - [Managing Pipelines: Storing And Reusing Pipelines & Components](#managing-pipelines-storing-and-reusing-pipelines--components)
- [Experiments](#experiments)
- [Putting It All Together](#putting-it-all-together)
- [Content Development Progress](#content-development-progress)

---

## ML Code: More Than A Model

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
- prepare model for deployment - batch, online, cloud, onprem, mobile, ...
- deploy, test, rolloout
- monitor shift and drift
- troubleshoot everything that goes wrong or does not make sense
- automate
- repeat
- scale
- a MILLION other things!

In other words, "ML Code" is much more than just ML code.  As depicted by the blocks in this diagram which are also sized to emphasize the effort of different parts of the full ML ecosystem:


<p align="center">
  <img src="../architectures/notebooks/mlops/readme/hidden-technical-debt-in-machine-learning-platforms.png" alt="Hidden Technical Debt In Machine Learning Platforms" width="80%">
</p>
<p align="center">
  <a href="https://proceedings.neurips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf">
    Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J., & Dennison, D. (2015). Hidden Technical Debt in Machine Learning Systems.expand_more
  </a>
</p>

The first takeaway is that this is more than just a model.  At the core, a model is the product of data, an architecture, and hyperparameters.  The system around this makes up the complete training pipeline. Putting the model into use expands the pipeline to deployment and monitoring. But Why invest in the extra steps of pipelines?  Even for a single model the benefits of automation, monitoring, and governing the workflow are great.  The speed of deployment and opportunity for continous training are also great. But ML maturity leads to more models, more versions, and more everything!

## Model Fleets: MLOps for Scale

As the workflow goes from one model to many models the practice of MLOps prevents also needing to scale the effort to support an maintain an ML environment.  Some common example of this scaling along with the benefits of MLOps are:

|Example|Description|MLOps Implication|
|---|---|---|
|Retraining|The periodic retraining of a model with new or expanded data to maintain performance.|Needs pipelines for automation, versioning, monitoring, and governening.|
|Multiple Datasets|Training the same architecture and hyperparameters on different datasets (regions, customer segments, etc.) as specialized models.|Need efficient data management, model deployment, and monitoring across environments.|
|Hyperparameter Tuning|Experimenting with hyperparameter configurations to optimize model performance (e.g., grid search, random search, Bayesian optimization).|Need to track experiment parameters, automation, scaling of training compute, compare model versions.|
|Multiple Architectures|Training a variety of model architectures (e.g., decision treees, neural networks, regression) on the same data and event combining predictions into stacked or ensemble models.|Needs efficient training, seleection, and deployment strategies to leverage the different architectures and model types.|
|Feature Engineering|Transforming and creating new features from raw data to improve model performance.|Needs for feature store to centrally manage data, track transformations, and ensure consistency across models and between traininng and serving.|
|Transfer Learning|Leveraging a trained model to accelerate training and improve performance on a new task.|Managing models and adapting to new taskswith seemless integration in to workflows.|
|Serving Strategies|Deploying models to serve preditions in different ways: batch, online, hybrid.|Requires a flexible infrastructure, model versioning, monitoring and seamless scaling, reliability, and responsiveness.|
|Model Optimization|Reducing model size and computational complexity through quantization, pruning, and distillation.|Involves evaluatinng trade-iffs between model performance and resource constraints, automation, and evaluation.|
|Model Proliferation|The growth of new models for new and various tasks, driven by business needs, technology advancements, and data availability.|Increases demand for scalable infrastructure, efficient model management, and robust governance to handle growing complexity of deployment and maintenance.|
|Continous Monitoring|Understanding each features distribution over time to get an early signal of change from the training data and/or over time as a precursor to model performance drops.|Need for robust automation for detection and notifications and ultimately automated retraining and subsequent deployment so that models adapt to real-world changes.|
|Explainability|The ability to interpret why a model makes specific predictions.|Incorporation of explainability techniques into model development and deployment broadly to identify and mitigate bias and error.|
|Addressing Bias|Identify and address biases in traininng data and training algorithms that lead to unfair predictions.|The need for automating auditing of training data for biases, implementing fairness metrics during evaluation, and implementing mitigation techniques (reweighing, adversarial debiasing, etc.) during training and deployment.|
|Security|Protect models and data from unauthorized access, and malicious attacks.|The need for a controled operating environment with encryption, access control, access logging, vulnerability scanning, anomaly detection, and code scanningn and upgrading to address security vulnerabilities.|
|Cost Optimization|Managed the computation, thus financial resources required to train, deploy, and maintain ML models.|Monitor resource utlization for over-provisioned compute and bottlenecks.  Optimize serving architectues for speed with cohosting and auto-scalinng techniques.|

Whew!! Is that enough?  The value of practicing MLOps is clear.  The core to this a bringing the entire workflow together into **pipelines** - the _'ops'_ in **MLOps**.  

---
## Content Overview

<div align="center">
<table style='text-align:center;vertical-align:middle;' cellpadding="1" cellspacing="0">
    <tr>
        <th colspan="12">Development</th>
    </tr>
    <tr>
        <th colspan="2">Vertex AI<br>SDK</th>
        <th colspan="2">Google<br>Colab</th>
        <th colspan="2">Vertex AI<br>Enterprise<br>Colab</th>
        <th colspan="2">Vertex AI<br>Workbench<br>Instances</th>
        <th colspan="2">Google<br>Cloud<br>Workstations</th>
        <th colspan="2">VSCode</th>
    </tr>
    <tr>
        <th colspan="12">Lifecycle</th>
    </tr>
    <tr>
          <th colspan="3">Features</th>
          <th colspan="3">Training</th>
          <th colspan="3">Serving</th>
          <th colspan="3">Monitoring</th>
    </tr>
    <tr>
        <th colspan="12">Manage</th>
    </tr>
    <tr>
        <th colspan="4">Model Registry</th>
        <th colspan="4">Experiments</th>
        <th colspan="4">ML Metadata</th>
    </tr>
    <tr>
        <th colspan="12">Orchestrate</th>
    </tr>
    <tr>
        <th colspan="12"><a href="#pipelines">Pipelines</a></th>
    </tr>
</table>
</div>

---
## MLOps Resources & References

Resources on MLOps:
- The best overview ever written (#opinion): https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines
   - Even if you don't use TFX, this captures the whole goal!
- Google Cloud + Vertex AI Content:
   - MLOps Overview: https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning
   - MLOps on Vertex AI: https://cloud.google.com/vertex-ai/docs/start/introduction-mlops
- Foundational Papers In This Area:
   - 2014: [Machine Learning: The High Interest Credit Card of Technical Debt](https://research.google/pubs/machine-learning-the-high-interest-credit-card-of-technical-debt/)
   - 2015: [Hidden Technical Debt in Machine Learning Systems](https://proceedings.neurips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf)

---
# Pipelines

The workflow of ML code does many steps in sequence.  Some of the steps involve conditional logic like deploying the new model only when it is more accurate than the currently deployed model.  This is a pipeline.  Pipelines are essential for turning ML processes into MLOps.  MLOps goes the next mile with automation, monitoring, and governing the workflow.

There are frameworks for specifying these steps like [Kubeflow Pipelines (KFP)](https://www.kubeflow.org/docs/components/pipelines/v2/introduction/) and [TensorFlow Extended (TFX)](https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines).  [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction) is a managed service that can execute both of these.
- The [history of Kubeflow](https://www.kubeflow.org/docs/started/introduction/#history) is creating a simplified way to running TensorFlow Extended jobs on Kubernetes.

**TL;DR**

This is a series of notebook based workflows that teach all the ways to use pipelines and experiments within Vertex AI. The suggested order and description/reason is:

|Link To Section|Notebook Workflow|Description|
|---|---|---|
|[Link To Section](#workflow-1)|[Vertex AI Pipelines - Introduction](./Vertex%20AI%20Pipelines%20-%20Introduction.ipynb)|Introduction to pipelines with the console and Vertex AI SDK|
|[Link To Section](#workflow-2)|[Vertex AI Pipelines - Components](./Vertex%20AI%20Pipelines%20-%20Components.ipynb)|An introduction to all the ways to create pipeline components from your code|
|[Link To Section](#workflow-3)|[Vertex AI Pipelines - IO](./Vertex%20AI%20Pipelines%20-%20IO.ipynb)|An overview of all the type of inputs and outputs for pipeline components|
|[Link To Section](#workflow-4)|[Vertex AI Pipelines - Control](./Vertex%20AI%20Pipelines%20-%20Control.ipynb)|An overview of controlling the flow of exectution for pipelines|
|[Link To Section](#workflow-5)|[Vertex AI Pipelines - Secret Manager](./Vertex%20AI%20Pipelines%20-%20Secret%20Manager.ipynb)|How to pass sensitive information to pipelines and components|
|[Link To Section](#workflow-6)|[Vertex AI Pipelines - Scheduling](./Vertex%20AI%20Pipelines%20-%20Scheduling.ipynb)|How to schedule pipeline execution|
|[Link To Section](#workflow-9)|[Vertex AI Pipelines - Notifications](./Vertex%20AI%20Pipelines%20-%20Notifications.ipynb)|How to send email notification of pipeline status.|
|[Link To Section](#workflow-7)|[Vertex AI Pipelines - Management](./Vertex%20AI%20Pipelines%20-%20Management.ipynb)|Managing, Reusing, and Storing pipelines and components|
|[Link To Section](#workflow-8)|[Vertex AI Experiments](./Vertex%20AI%20Experiments.ipynb)|Understanding and using Vertex AI Experiments|

To discover these notebooks as part of an introduction to MLOps read on below!

## Introduction

Pipelines are constructed of:
1. Create **Components** From Code
2. Construct **Pipelines** Where steps, or **Tasks**, are made from components
3. **Run** Pipelines on Vertex AI Pipelines
4. Review pipelines runs and **tasks results**
5. Review task **Execution**: Each task runs as a Vertex AI Training Custom Job

An overview:

<p align="center">
    <img src="../architectures/notebooks/mlops/readme/pipelines-overview-1-code_components.png" width="75%">
<p>
<p align="center">
    <img src="../architectures/notebooks/mlops/readme/pipelines-overview-2-components_pipeline.png" width="75%">
<p>
<p align="center">
    <img src="../architectures/notebooks/mlops/readme/pipelines-overview-3-pipeline_run.png" width="75%">
<p>
<p align="center">
    <img src="../architectures/notebooks/mlops/readme/pipelines-overview-4-pipeline_task_review.png" width="75%">
<p>
<p align="center">
    <img src="../architectures/notebooks/mlops/readme/pipelines-overview-5-pipeline_task_job.png" width="75%">
<p>

<div id='workflow-1'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

Get a quick start with pipelines by reviewing this workflow for an example using both the Vertex AI Console and SDK.
- [Vertex AI Pipelines - Introduction](./Vertex%20AI%20Pipelines%20-%20Introduction.ipynb)
    - **Build** a simple pipeline with IO parameters and artifacts as well as conditional execution
    - **Review** all parts (runs, tasks, parameters, artifacts, metadata) with the Vertex AI Console
    - **Retrieve** all parts (runs, tasks, parameters, artifacts, metadata) with the Vertex AI SDK

</td></tr></table></div>

---
## Components

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

<div id='workflow-2'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

For an overview of components from custom to pre-built, check out this notebook:
- [Vertex AI Pipelines - Components](./Vertex%20AI%20Pipelines%20-%20Components.ipynb)
    - **Pre-Built Components:** Easy access to many GCP services
    - **Lightweight Python Components:** Build a component from a Python function
    - **Containerized Python Components:** Build an entire Python enviornment as a component
    - **Container Components:** Any container as a component
    - **Importer Components:** Quickly import artifacts

</td></tr></table></div>

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
## Component IO

Getting information into code and results out is the IO part of components.  These inputs and outputs are particularly important in MLOps as they are the artifacts that define an ML system: datasets, models, metrics, and more.  Pipelines tools like TFX and KFP go a step further and automatically track the inputs and outpus and even provide lineage information for them.  Component inputs and outputs can take two forms: parameters and artifacts.  

**Parameters** are Python objects like `str`, `int`, `float`, `bool`, `list`, `dict` objects that are defined as inputs to pipelines and components. Components can also return parameters for input into subsequent components. Paramters are excellent for changing the behavior of a pipeline/component through inputs rather than rewriting code.
- [KFP Parameters](https://www.kubeflow.org/docs/components/pipelines/v2/data-types/parameters/)
- [TFX Parameters](https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines#parameter)

**Artifacts** are multi-parameter objects that represent machine learning artifacts and have defined schemas and are stored as metadata with lineage.  The artifact schemas follow the [ML Metadata (MLMD)](https://github.com/google/ml-metadata) client library.  This helps with understanding and analyzing a pipeline.
- [KFP Artifacts](https://www.kubeflow.org/docs/components/pipelines/v2/data-types/artifacts/)
    - provided [artifact types](https://www.kubeflow.org/docs/components/pipelines/v2/data-types/artifacts/#artifact-types)
    - [Google Cloud Artifact Types](https://google-cloud-pipeline-components.readthedocs.io/en/google-cloud-pipeline-components-2.0.0/api/artifact_types.html)
- [TFX Artifacts](https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines#artifact)

<div id='workflow-3'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

See all the types of parameters and artifacts in action with the following notebook based workflow:
- [Vertex AI Pipelines - IO](./Vertex%20AI%20Pipelines%20-%20IO.ipynb)
    - **parameters:** input, multi-input, output, multi-output
    - **artifacts:** input, output, Vertex AI ML Metadata Lineage

</td></tr></table></div>

**Secure Parameters:** Passing credentials for an API or service can expose them.  If these credentials are hardcoded then they can be discovered from the source code and are harder to update.  A great solution is using [Secret Manager](https://cloud.google.com/secret-manager/docs/create-secret-quickstart#secretmanager-quickstart-console) to host credentials and then pass the name of the credential as a parameter.  The only modification needed to a component is to use a Python client to retrieve the credentials at run time.  

<div id='workflow-5'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

Check out how easy secret manager isis to implement with the following notebook based example workflow:
- [Vertex AI Pipelines - Secret Manager](./Vertex%20AI%20Pipelines%20-%20Secret%20Manager.ipynb)
    - **Setup** Secret Manager and use the console and Python Client to store secrets
    - **Retrieve** secrets using the Python Client
    - **example** pipeline that retrieves credentials from Secret Manager

</td></tr></table></div>

---
## Control Flow For Pipelines

As the task of an ML pipeline run they form a graph.  The outputs of upstream components become the inputs of downstram components.  Both TFX and KFP automatically use these connection to create a DAG of execution.  When logic needs to be specified in the pipeline flow of execution the use of control structures is necessary.  

<div id='workflow-4'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

The following notebook shows many examples of implement controls in KFP while running on Vertex AI Pipelines:
- [Vertex AI Pipelines - Control](./Vertex%20AI%20Pipelines%20-%20Control.ipynb)
    - **Ordering**: DAG and Explicit ordering
    - **Conditional Execution**: if, elif (else if), and else
        - **Collecting**: Conditional results
    - **Looping**: And Parallelism
        - **Collecting**: Looped Results
    - **Exit Handling:** with and without task failures
    - **Error Handling** continue execution even after task failures

</td></tr></table></div>

---
## Scheduling Pipelines

Pipelines can be run on a schedule directly in Vertex AI without the need to setup a scheduler and trigger (like PubSub).  

<div id='workflow-6'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

Here is an example of a pipeline run followed by a schedule that repeats the pipeline at a specified interval the number of iterations set as the maximum on the schedule:

- [Vertex AI Pipelines - Scheduling](./Vertex%20AI%20Pipelines%20-%20Scheduling.ipynb)
    - **Create**
    - **Retrieve**
    - **Manage**

</td></tr></table></div>

This can have many helpful applications, including:
- Running Batch predictions, evaluations, monitoring each day or week
- Retraining a model, do evaluations, and comparing the new model to the currently deployed model then conditionally updating the deployed model
- Check for new training records and commence with retraining if conditions are met - like records that increase a class by 10%, atleast 1000 new records, ....

---
## Notifications From Pipelines

As the number of pipelines grow and the use of schedulinng and triggering is implemented it becomes necessary to know which pipelines need to be reviewed.  Getting notificaitons about the completion of pipeliens is a good first step.  Then, being able to control notificaitons to only be sent on failure or particular failures becomes important.

<div id='workflow-9'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

This notebook workflow covers pre-built components for email notification and building a custom notification system for send emails (or tasks) conditional on the pipelines status.

- [Vertex AI Pipelines - Notifications](./Vertex%20AI%20Pipelines%20-%20Notifications.ipynb)
    - Pre-Built Component to send emails on pipelines completion
    - Overview of retrieving pipeline runs final status information
    - Building a custom component to send emails conditional on the pipelines final status.

</td></tr></table></div>

---
## Managing Pipelines: Storing And Reusing Pipelines & Components

As seen above, pipelines are made up of steps which are executions of components.  These components are made up of code, container, and instructions (inputs and outputs).  

**Components:**

For each type of component, `kfp` compiles the component into YAML as part of the pipeline.  You can also directly compile individual components.  This makes the YAML for a component a source that can be managed.  And using this in additional pipelines is made possible with `kfp.components.load_component_from_*()` which has version for files, urls, text (strings).

**Pipelines:**

Pipelines are compiled into YAML files that include component specifications.  Managine these pipelines files as artifacts is made easy with the combination of:
- Kubeflow Pipelines SDK and the included [`kfp.registry.RegistryClient`](https://kubeflow-pipelines.readthedocs.io/en/latest/source/registry.html)
- Google Cloud [Artifact Registry](https://cloud.google.com/artifact-registry/docs/overview) with native format for [Kubeflow pipeline templates](https://cloud.google.com/artifact-registry/docs/kfp)
- [Integration with Vertex AI](https://cloud.google.com/vertex-ai/docs/pipelines/create-pipeline-template#kubeflow-pipelines-sdk-client) for creating, uploading and using pipeline templates

<div id='workflow-7'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

Work directly with these concepts in the following notebook based workflow:
- [Vertex AI Pipelines - Management](./Vertex%20AI%20Pipelines%20-%20Management.ipynb)

</td></tr></table></div>

---
## Pipeline Patterns - Puttinng Concepts Together Into Common Workflows

A series of notebook based workflows that show how to put all the concepts from the material above into common workflows:

- [Vertex AI Pipelines - Pattern - Modular and Reusable](./Vertex%20AI%20Pipelines%20-%20Pattern%20-%20Modular%20and%20Reusable.ipynb)
    - Example 1: Store a pipeline in artifact registry and directly run it on Vertex AI Pipelines without a local download.
    - Example 2: Store and retrieve components for reusability: as files (at url, file directory, or text string) and as artifact in artifact registry
    - Example 3: Store pipelines in artifact registry and retrieve (download, and import) to use as components in new pipelines

---
# Experiments
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

<div id='workflow-7'><table style='text-align:left;vertical-align:middle;background-color: #4285F4' width="100%" cellpadding="1" cellspacing="0"><tr><td markdown="block">

**Notebook Workflow:**

Work with experiments and explore all of these features in the following notebook based workflow:
- [Vertex AI Experiments](./Vertex%20AI%20Experiments.ipynb)

</td></tr></table></div>

---
# Putting It All Together

<p align="center">
    <img src="../architectures/notebooks/mlops/readme/kfp.png" width="75%">
<p>


---
# Content Development Progress
This readme is desigend to become the outline for a workshop on MLOps. It will also connect to surrounding content on feature stores, model monitoring, and developement tools for ML.

The following is an active todo list for content:

In Progress:
- [X] Fix HTML and MD artifacts to display in console
- [X] Test kfp artifacts with > 2 tags
- [X] Create Graphics for readme: ML process
- [ ] Create Graphic for experiments
- [Finish writeup] Notifications workflow: Vertex provided components, and custom (conditional notifications)
- [ ] Consolidate task configurations: see pipeline basis language in kfp docs
- [ ] Rerun all
    - [ ] Screenshots embedded in notebooks only displaying in IDEs, not GitHub or Colab
    - [ ] kfp artifacts update to pythonic approach throughout
- [ ] Finish Experiment workflow, include training jobs
- [X] Create Graphics for readme: pipelines overview
- [ ] Create Graphics for readme: Training Jobs
- [X] add readme section for patterns
- [X] pattern: reusable and modular
    
Reorganize this page:
- [ ] Make pipelines a linked topic in a subfolder
- [ ] move feature store into a subfolder
- [ ] move model monitoring into a subfolder
- [ ] create a training subfolder
- [ ] create a deployment subfolder
- [ ] create a subfolder for development tools
- [ ] reconfigure this page to be overall MLOps and link to the subfolders by topic

Upcoming:
- [ ] Training Job brought into this content - 6 methods, stand-alone, and from pipelines
- [ ] cache tasks, local testing, Vertex specific
- [ ] Vertex ML Metadata overview
- [ ] Governance overview (pull from all workflows in complete story)
- [ ] Create a series of "Patterns"
    - [ ] Straight Line: data > train > model > deploy > test
    - [ ] many data > many train > many model > cohost deploy > test
    - [ ] custom batch: in component, with endpoint, with triton
    - [ ] CT example
    - [ ] MM example
- [ ] Importer component with Metadata lookup example
- [ ] Triggering Pipelines - beyond scheduling
- [X] Graphic for code > container > component > pipeline with entrypoints
- [ ] docstring for components and pipelines
- [ ] Link to surrounding topics
    - IDEs: Colab, Colab Enterprise, Vertex AI Workbench, Google Cloud Workstations, VSCode, VSCode+Workstations
    - [feature architectures](../Feature%20Store/Feature%20Focused%20Data%20Architecture.ipynb)
    - [feature store](../Feature%20Store/readme.md)
    - [model monitoring](../Model%20Monitoring/readme.md)
