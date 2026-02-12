![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FPyTorch%2Fserving&file=advanced-topics.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/PyTorch/serving/advanced-topics.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/advanced-topics.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/advanced-topics.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/advanced-topics.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/advanced-topics.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Advanced Serving Topics: Scaling, GPUs, and Optimization

This document provides advanced guidance on scaling, performance tuning, and optimizing the serving patterns demonstrated in this repository.

## Table of Contents
1. [Scale Testing Existing Workflows](#1-scale-testing-existing-workflows)
    - [Vertex AI Endpoint Scale Testing](#vertex-ai-endpoint-scale-testing)
    - [Dataflow Streaming (Local Model) Scale Testing](#dataflow-streaming-local-model-scale-testing)
    - [Dataflow Streaming (Vertex Endpoint) Combined System Testing](#dataflow-streaming-vertex-endpoint-combined-system-testing)
2. [General Scaling Advice](#2-general-scaling-advice)
    - [Vertex AI Endpoints](#vertex-ai-endpoints)
    - [Dataflow Pipelines](#dataflow-pipelines)
3. [Using GPUs for Inference](#3-using-gpus-for-inference)
    - [When to Use GPUs](#when-to-use-gpus)
    - [Prerequisites for Dataflow GPUs](#prerequisites-for-dataflow-gpus)
    - [How to Add GPUs](#how-to-add-gpus)
    - [Configuring the Container Image for Dataflow](#configuring-the-container-image-for-dataflow)
    - [Optimizing GPU Resource Usage in Dataflow](#optimizing-gpu-resource-usage-in-dataflow)
    - [GPU-Specific Scale Testing](#gpu-specific-scale-testing)
4. [Alternative: NVIDIA Triton Inference Server](#4-alternative-nvidia-triton-inference-server)

---

## 1. Scale Testing Existing Workflows

This repository includes dedicated notebooks for performance testing the Vertex AI Endpoint and Dataflow streaming pipelines. These notebooks provide a scientific approach to understanding capacity, identifying bottlenecks, and optimizing configurations.

### Vertex AI Endpoint Scale Testing
- **Notebook**: [`scale-tests-vertex-ai-endpoints.ipynb`](./scale-tests-vertex-ai-endpoints.ipynb)
- **Utilities**: [`scale_testing_utils.py`](./scale_testing_utils.py)

This notebook systematically tests a deployed Vertex AI Endpoint to analyze its performance across two key dimensions: **batch size** and **request rate**. It helps answer critical questions like:
- What is the optimal batch size for maximum throughput?
- At what request rate (RPS) does latency start to degrade?
- When does the endpoint's autoscaling trigger?
- What is the cold-start latency vs. warm-start latency?

The accompanying `scale_testing_utils.py` script provides the core infrastructure for running asynchronous load tests and collecting performance metrics from Cloud Monitoring.

### Dataflow Streaming (Local Model) Scale Testing
- **Notebook**: [`scale-tests-dataflow-streaming-runinference.ipynb`](./scale-tests-dataflow-streaming-runinference.ipynb)
- **Utilities**: [`scale_testing_dataflow_utils.py`](./scale_testing_dataflow_utils.py)

This notebook focuses on the performance of a Dataflow pipeline that runs inference with a model loaded directly onto the workers (in-process). It helps you understand:
- The maximum message rate the pipeline can handle before backlog accumulates.
- The end-to-end latency from message publish to result.
- How Dataflow worker autoscaling behaves under different load patterns (sustained, burst, ramp).
- The optimal machine type and worker configuration for your model.

The `scale_testing_dataflow_utils.py` script contains utilities for generating Pub/Sub load and collecting latency and Dataflow-specific metrics.

### Dataflow Streaming (Vertex Endpoint) Combined System Testing
- **Notebook**: [`scale-tests-dataflow-streaming-vertex.ipynb`](./scale-tests-dataflow-streaming-vertex.ipynb)
- **Utilities**: [`scale_testing_combined_utils.py`](./scale_testing_combined_utils.py)

This is the most advanced test, analyzing the performance of the **entire system** where a Dataflow pipeline calls a Vertex AI Endpoint. It's designed to identify which component is the bottleneck. Key analysis includes:
- **Bottleneck Identification**: Is the system limited by Dataflow worker capacity or by the endpoint's prediction throughput?
- **Dual Autoscaling Analysis**: Correlates Dataflow worker scaling with endpoint replica scaling to observe how the two systems interact.
- **Worker-to-Replica Ratio**: Helps determine the optimal balance between the number of Dataflow workers and endpoint replicas for cost-effectiveness.
- **Unified Recommendations**: Provides configuration guidance for both services together.

The `scale_testing_combined_utils.py` script contains specialized functions to collect and correlate metrics from both Dataflow and Vertex AI simultaneously.

---

## 2. General Scaling Advice

### Vertex AI Endpoints

#### Machine Types
- **Current Configuration Reference**: In the provided notebooks, the default machine type for Vertex AI Endpoints is typically `n1-standard-4` (4 vCPUs, 15 GB memory).
- **When to Change**: Change the machine type if you observe CPU saturation (consistently > 60-70%) on your current type, or if your model requires more memory than available.
- **Why**:
    - **CPU-Bound Models**: If your model is computationally heavy but has a small memory footprint, moving from an `n1-standard` series to a compute-optimized `c2-standard` series can increase throughput.
    - **Memory-Bound Models**: If your model is large, a high-memory machine type (`n1-highmem`) can prevent out-of-memory errors.
    - **GPU Acceleration**: If inference is slow, adding a GPU is the most effective way to boost performance (see section 3).

#### Replicas (min/max)
- **Current Configuration Reference**: The notebooks typically configure Vertex AI Endpoints with `min_replicas=1` and `max_replicas=4`.

##### Standard Scaling (`min_replicas >= 1`)
- **`min_replicas`**: Setting this to `1` or higher ensures that at least one replica is always running, which is crucial for production systems that cannot tolerate cold-start latency. A higher minimum can pre-warm capacity for expected baseline traffic, ensuring low latency even before autoscaling kicks in.
- **`max_replicas`**: This setting acts as a cost-control mechanism. It defines the upper limit of how many replicas the service can scale up to. The scale tests will help you determine how many replicas are needed to handle your peak traffic within your budget.

##### Scale to Zero (`min_replicas = 0`) (Preview)
Vertex AI offers a preview feature that allows you to set `min_replicas=0`, enabling deployments to scale down to zero replicas when idle, thus incurring no cost.

- **Use Case**: Ideal for development environments or workloads with long, predictable idle periods (e.g., applications only used during business hours).
- **Behavior**: When the first request hits a scaled-down endpoint, the service returns a `429` error with the message `Model is not yet ready for inference...`. This response is the trigger for the system to scale up. Your client application **must** implement a retry mechanism (e.g., exponential backoff) to handle this initial `429` and resend the request after a short delay.
- **Configuration**:
    - `initial_replica_count`: The number of replicas to launch when scaling up from zero (defaults to 1).
    - `idle_scaledown_period`: Duration of inactivity before scaling down to zero (default: 1 hour, min: 5 minutes).
- **Limitations**: Be aware of the preview limitations, which include a requirement for a single model per endpoint and automatic undeployment after 30 days of inactivity.

#### Scaling Triggers
By default, Vertex AI scales nodes based on CPU utilization, targeting 60%. However, this is not always the best metric for every workload. You can and should configure scaling based on the metric that best represents your model's bottleneck.

- **Default Trigger**: Vertex AI scales up when the average CPU utilization across all replicas exceeds **60%** for a sustained period. It scales down when utilization is consistently low.
- **Why Adjust**: You can set the CPU utilization target to any value between 0-100% to fine-tune autoscaling behavior.
    - **Lowering the Threshold (e.g., 50%)**: Triggers scaling earlier, which can help handle sudden traffic spikes more gracefully but may increase costs.
    - **Raising the Threshold (e.g., 75%)**: Delays scaling, which saves money but risks higher latency or dropped requests if traffic increases quickly. This is suitable for workloads that can tolerate longer wait times.
- **How to Adjust**: The CPU utilization target is a deployment-time configuration setting.
- **Alternative Metrics**:
    - **GPU Utilization** (`aiplatform.googleapis.com/prediction/online/accelerator/duty_cycle`): Use this if your model is GPU-bound. High GPU usage will trigger scaling even if CPU usage is low. The default target is also 60%.
    - **Request Count** (`aiplatform.googleapis.com/prediction/online/request_count`): Ideal for I/O-bound models or when throughput is measured in requests per second (RPS), not CPU load. You define a target number of requests per minute per replica.
    - **Pub/Sub Queue Size** (`pubsub.googleapis.com/subscription/num_undelivered_messages`) (Preview): Allows an endpoint to scale based on the number of messages in a Pub/Sub subscription, creating a pull-based architecture. This is disabled by default.

- **Why Adjust**: If your model spends most of its time waiting for I/O, its CPU utilization may be very low, and the default trigger may never scale the model up. In this scenario, configuring scaling based on `request_count` would be more appropriate.

#### Managing Resource Usage and Scaling Behavior

##### Container Workers and Threading
Properly utilizing the resources of the underlying machine is critical for autoscaling to work correctly. A common mistake is to run a single-threaded inference server on a multi-core machine.

- **The Problem**: If your Python server (e.g., FastAPI, Flask) runs with a single worker process, it can only use one CPU core. Even under heavy load, the replica's average CPU utilization will never exceed `1/N` where `N` is the number of cores. For an `n1-standard-4` machine, this means CPU usage will not go above ~25%, which is below the default 60% threshold, and **autoscaling will never be triggered**.
- **Recommendation**: Configure your container's entrypoint to launch multiple worker processes. A good starting point is **one worker per CPU core**. If you observe low CPU utilization under load, increase the number of workers. If latency degrades, you may be introducing contention, so try reducing the number of workers or moving to a smaller machine type.

##### Understanding Scaling Lag
The autoscaling process is not instantaneous. Understanding how it works helps set realistic performance expectations.

- **Scaling Formula**: Vertex AI adjusts the number of replicas based on the formula: `target_replicas = Ceil(current_replicas * (current_utilization / target_utilization))`.
- **Evaluation Window**: This calculation happens in a 15-second cycle, but it uses the **highest** target value from the previous **5-minute window**. This behavior favors scaling up aggressively to meet spikes but scaling down more conservatively.
- **Inherent Lag**: Even after a scale-up is triggered, there is a delay before the new replica is ready to serve traffic. This lag comes from:
    1. Time to provision the new VM.
    2. Time to download the container image.
    3. Time to load the model from storage into memory.
- **Practical Advice**: If the natural scaling lag is too slow for your application's traffic patterns, you should set `min_replicas` to a value high enough to handle the expected baseline load without relying on an immediate scale-up.

---

### Dataflow Pipelines

Dataflow Horizontal Autoscaling automatically chooses the number of worker instances for a job, scaling based on CPU utilization and the pipeline's estimated parallelism.

#### Machine Types
- **Current Configuration Reference**: The notebooks use `n1-standard-4` (4 vCPUs, 15 GB memory) as the default worker machine type.
- **When to Change**:
    - **Local Model Inference**: If workers run out of memory loading the model, or if the CPU is a bottleneck.
    - **Endpoint-Based Inference**: Usually not necessary, as the worker's main job is I/O (calling the endpoint). A smaller machine type might even be more cost-effective.

#### Worker Autoscaling Range
- **Configuration Parameters**:
    - `--num_workers`: Sets the *initial* number of workers when the job starts.
    - `--min_num_workers`: The minimum number of workers the job can scale down to. In streaming, setting this to `> 1` ensures high availability and pre-warms capacity, similar to `min_replicas` in Vertex AI.
    - `--max_num_workers`: The maximum number of workers, which acts as a critical cost-control lever. The notebooks typically default to `20`.
- **Updating a Running Job**: For streaming jobs that use Streaming Engine, you can update the `min-num-workers` and `max-num-workers` for a running job without stopping it by using the `gcloud dataflow jobs update-options` command.

#### Autoscaling Modes and Tuning

##### Batch Autoscaling
- **Behavior**: Enabled by default for all batch jobs. Dataflow estimates the total work and adjusts the number of workers dynamically. The scaling is *sublinear*, meaning a job with twice the work will have fewer than twice the workers.
- **Limitations**: Scaling can be limited by un-splittable work, such as reading from compressed files.

##### Streaming Autoscaling
- **Default Behavior**: For jobs using **Streaming Engine** (the default for new pipelines), Horizontal Autoscaling is enabled by default. For older jobs *not* using Streaming Engine, you must specify `--autoscaling_algorithm=THROUGHPUT_BASED`.
- **Tuning with Worker Utilization Hint**: You can guide the autoscaler by specifying a target CPU utilization.
    - **How**: `--dataflow_service_options=worker_utilization_hint=TARGET` (where TARGET is 0.1-0.9).
    - **Why**: The default target is `0.8` (80%). Setting a *lower* value (e.g., `0.6`) makes the pipeline scale up more aggressively, which can lower latency at the expense of higher cost. A *higher* value saves resources but may increase latency during traffic spikes.
- **Tuning for I/O or GPU-Bound Workloads**: If your workers are not CPU-bound (e.g., waiting on network calls to a Vertex Endpoint or performing GPU work), the CPU utilization hint is less effective. In this case, you can use a **parallelism hint**.
    - **How**: Attach `.with_resource_hints(max_active_bundles_per_worker=TARGET)` to a transform in your pipeline code.
    - **Why**: This switches the autoscaler to a mode that scales based on the number of parallel processing keys, which is a better signal for these types of workloads.

##### General Heuristics
The autoscaler aims to keep backlog time below 15 seconds. If backlog grows beyond this, it will attempt to scale up. It scales down when backlog is low and CPU utilization is below the target hint.

---

## 3. Using GPUs for Inference

#### When to Use GPUs
Use GPUs when your model's inference latency is a bottleneck and the model's operations can be significantly accelerated by parallel processing. This is common for:
- Large deep learning models (e.g., Transformers, large CNNs).
- Workloads involving large batch sizes.
- Models with custom CUDA kernels.

For the small autoencoder in this project, a GPU is likely not cost-effective, but the principles apply to larger models.

#### Prerequisites for Dataflow GPUs
To use GPUs with a Dataflow job, the following prerequisites must be met:
- **Runner v2**: You must use Dataflow Runner v2.
- **GPU Drivers**: Drivers must be installed on the worker VMs. This is done by the service, not by you.
- **Container Libraries**: Your custom container image must have the necessary NVIDIA libraries, such as the CUDA Toolkit.
- **Boot Disk**: Increase the worker boot disk size to at least 50 GB, as GPU containers can be large.

#### How to Add GPUs
- **Vertex AI Endpoints**:
    1. Specify an `accelerator_type` (e.g., `NVIDIA_TESLA_T4`, `NVIDIA_A100`) and `accelerator_count` when deploying the model.
    2. Choose a machine type that is compatible with the selected GPU.
- **Dataflow**:
    1. **Specify the GPU type and count** using the `worker_accelerator` service option. You must also include a token to instruct Dataflow to install the drivers.
        - Example: `--dataflow_service_options=worker_accelerator=type:nvidia-l4;count:1;install-nvidia-driver`
    2. **Supported Types** include `nvidia-l4`, `nvidia-tesla-a100`, `nvidia-a100-80gb`, `nvidia-tesla-t4`, `nvidia-tesla-p4`, `nvidia-tesla-v100`, `nvidia-tesla-p100`, and `nvidia-h100-80gb`.

#### Configuring the Container Image for Dataflow
Your custom container image is responsible for providing the software your code needs to use the GPU (e.g., CUDA Toolkit, cuDNN), but **not** the NVIDIA driver itself.

- **Best Practice**: Start from a pre-configured base image provided by NVIDIA or a framework like TensorFlow. These images already have the necessary libraries.
- **Important**: Do not install NVIDIA drivers inside your Docker container. They are installed on the host VM by Dataflow and can conflict with any drivers in your container.

#### Optimizing GPU Resource Usage in Dataflow
By default, Dataflow runs one SDK process per vCPU core, and all processes on a worker share the same GPU(s). This can lead to memory contention.

- **NVIDIA Multi-Process Service (MPS)**: For workloads with low individual GPU resource usage, enabling MPS can improve efficiency and throughput by allowing multiple processes to share the GPU more effectively.
- **Limit Worker Processes**: If a single inference process can consume most of the GPU memory (e.g., by loading a large model), you can force the worker to run only a single process, regardless of vCPU count. 
    - **How**: Set the pipeline option `--experiments=no_use_multiple_sdk_containers`.

#### GPU-Specific Scale Testing
When testing GPU-enabled services, it's important to monitor GPU-specific metrics in addition to CPU and memory.
- **NVIDIA Data Center GPU Manager (DCGM)**: For deep insights on GCE or GKE, you can run DCGM in your container or on the host VM to collect detailed metrics like:
    - `GPU Utilization`: Percentage of time the GPU was active.
    - `GPU Memory Used`: How much of the GPU's VRAM is allocated.
    - `PCIe Throughput`: Data transfer rate between the CPU and GPU, which can be a hidden bottleneck.
- **Cloud Monitoring**: Provides standard GPU utilization and memory metrics for Vertex AI and Dataflow.

---

## 4. Alternative: NVIDIA Triton Inference Server

While this project uses a pre-built PyTorch/TorchServe container and a custom FastAPI container, a powerful third option for Vertex AI Endpoints is the **NVIDIA Triton Inference Server**.

**What it is**: A high-performance inference server optimized for NVIDIA GPUs. It can be used as a custom container on Vertex AI.

**Advantages for our PyTorch Model**:
- **Dynamic Batching**: Triton can automatically batch incoming requests on the fly. If multiple individual requests arrive close together, Triton combines them into a single larger batch before running inference, significantly improving GPU utilization and overall throughput.
- **Multi-Framework Support**: A single Triton server can host models from PyTorch, TensorFlow, ONNX, and other frameworks simultaneously.
- **Performance**: Generally offers lower latency and higher throughput than TorchServe or a basic FastAPI server, especially under high load, due to its C++ core and advanced scheduling features.
- **Concurrent Model Execution**: Can run multiple copies of the same model or different models on a single GPU to maximize utilization.

**When to Choose Triton**:
- When you need the absolute best performance for a GPU-based deployment.
- When serving multiple models from different frameworks.
- When your request pattern is sporadic, and you can benefit from dynamic batching.
