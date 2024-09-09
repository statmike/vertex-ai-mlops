![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2Fresources&file=todo.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/resources/todo.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

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
- [ ] pattern: add run of single component
- [ ] management: add AR storage of sinngle component, recall, and direct run
- [ ] management: add python library for sharing components and pipelines
    - https://github.com/kubeflow/pipelines/blob/master/components/google-cloud/README.md

    
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
