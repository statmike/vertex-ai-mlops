![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FPyTorch%2Fserving&file=torchserve-gke.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/PyTorch/serving/torchserve-gke.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/torchserve-gke.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/torchserve-gke.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/torchserve-gke.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/torchserve-gke.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# TorchServe Deployment on Google Kubernetes Engine

Deploy TorchServe on Google Kubernetes Engine (GKE) for enterprise-scale, multi-model orchestration with advanced deployment strategies.

## When to Use GKE

**Best for**:
- **Multiple models**: Serve different models with independent scaling
- **Complex deployments**: Canary releases, blue/green deployments, A/B testing
- **High availability**: Multi-zone redundancy and self-healing
- **Enterprise scale**: Large-scale production workloads
- **Advanced orchestration**: Fine-grained control over infrastructure
- **Microservices**: Integration with existing Kubernetes ecosystem

**Choose GKE over**:
- **Cloud Run**: When you need GPU support, advanced orchestration, or multi-model serving
- **GCE**: When you need Kubernetes benefits (self-healing, rolling updates, declarative config)
- **Local**: When you need production-grade deployment with high availability

**Cost Comparison** (3 n1-standard-4 nodes):
- **GKE Cluster**: ~$438/month (3 nodes always on) + $73/month cluster management fee
- **GCE (3 VMs)**: ~$438/month (no cluster fee, manual orchestration)
- **Cloud Run (min=0)**: $0 idle, ~$0.20/hour when serving (significantly cheaper for intermittent traffic)

**Trade-offs**:
- GKE adds cluster management overhead but provides orchestration, self-healing, and rolling updates
- Best for workloads requiring 24/7 availability with multiple models or complex deployment strategies
- Use Spot VMs to reduce costs by up to 91%

---

## Prerequisites

Before starting, ensure you have:

1. **Model Archive**: Completed [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)
   - Model trained and `.mar` file created
   - Upload to GCS: `gs://{PROJECT_ID}/frameworks/pytorch-autoencoder/torchserve-gke/pytorch_autoencoder.mar`

2. **GCP Project**:
   - GKE API enabled
   - Appropriate IAM permissions for cluster creation
   - `kubectl` installed locally ([Install Guide](https://kubernetes.io/docs/tasks/tools/))

3. **Container Image**: Built from Cloud Run or GCE workflow
   - Can reuse Dockerfile from [torchserve-cloud-run.ipynb](./torchserve-cloud-run.ipynb)
   - Image pushed to Artifact Registry or GCR

4. **Dependencies**: Model handler requires `pyyaml` (included in container image)

---

## Architecture

```
Internet → Cloud Load Balancer → Ingress (optional)
                                     ↓
                            Kubernetes Service (LoadBalancer)
                                     ↓
                    ┌────────────────┴────────────────┐
                    ▼                ▼                ▼
            TorchServe Pod 1  TorchServe Pod 2  TorchServe Pod 3
                    ↓                ↓                ▼
                Persistent Volume (shared model storage)
                                     ↓
                            GCS (.mar file download)
```

**Key Design**:
- **Init Container**: Downloads model from GCS to shared PersistentVolume
- **ConfigMap**: Stores TorchServe configuration
- **Deployment**: Manages pod replicas with health checks
- **Service**: Exposes LoadBalancer for external access
- **HPA**: Auto-scales pods based on CPU/memory
- **Workload Identity**: GKE service account accesses GCS securely

---

## Quick Start

### 1. Set Variables

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export CLUSTER_NAME="pytorch-torchserve"
export IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/frameworks/pytorch-autoencoder-torchserve"
```

### 2. Create GKE Cluster

**Standard CPU Cluster** (recommended for testing):

```bash
gcloud container clusters create $CLUSTER_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --num-nodes=3 \
    --machine-type=n1-standard-4 \
    --disk-size=50GB \
    --disk-type=pd-standard \
    --enable-autoscaling \
    --min-nodes=2 \
    --max-nodes=10 \
    --enable-autorepair \
    --enable-autoupgrade \
    --scopes=https://www.googleapis.com/auth/cloud-platform
```

**GPU Cluster** (for accelerated inference):

```bash
gcloud container clusters create $CLUSTER_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --num-nodes=2 \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --disk-size=50GB \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5 \
    --scopes=https://www.googleapis.com/auth/cloud-platform

# Install NVIDIA GPU drivers
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

**Get Cluster Credentials**:

```bash
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Verify connection
kubectl get nodes
```

### 3. Build Container Image (if not done already)

If you haven't built the image from Cloud Run workflow:

```bash
# Build using Cloud Build
gcloud builds submit --tag $IMAGE_NAME

# Or build locally and push
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME
```

---

## Kubernetes Resource Setup

### 1. Create Namespace

```bash
kubectl create namespace torchserve
```

### 2. Create TorchServe Configuration

Create `torchserve-config.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: torchserve-config
  namespace: torchserve
data:
  config.properties: |
    inference_address=http://0.0.0.0:8080
    management_address=http://0.0.0.0:8081
    metrics_address=http://0.0.0.0:8082
    model_store=/mnt/models
    load_models=all
    disable_token_authorization=true
    number_of_netty_threads=8
    job_queue_size=100
    default_workers_per_model=2
```

**Key Settings**:
- `disable_token_authorization=true`: Allows unauthenticated requests (for public endpoints)
- `load_models=all`: Auto-loads all `.mar` files in model store
- `default_workers_per_model=2`: Initial worker count per model

Apply:
```bash
kubectl apply -f torchserve-config.yaml
```

### 3. Create Persistent Volume for Model Storage

Create `model-pv.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-store-pvc
  namespace: torchserve
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard-rwo
```

**Why PVC?** Shared storage allows init container to download model once, accessible by all pods.

Apply:
```bash
kubectl apply -f model-pv.yaml
```

### 4. Download Model from GCS

Create `model-downloader-job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: model-downloader
  namespace: torchserve
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: downloader
        image: google/cloud-sdk:slim
        command:
          - /bin/bash
          - -c
          - |
            echo "Downloading model from GCS..."
            gsutil cp gs://${PROJECT_ID}/frameworks/pytorch-autoencoder/torchserve-gke/pytorch_autoencoder.mar /mnt/models/
            echo "Model downloaded successfully"
            ls -lh /mnt/models/
        volumeMounts:
        - name: model-store
          mountPath: /mnt/models
      volumes:
      - name: model-store
        persistentVolumeClaim:
          claimName: model-store-pvc
```

Apply (with variable substitution):
```bash
envsubst < model-downloader-job.yaml | kubectl apply -f -

# Check job completion
kubectl get jobs -n torchserve
kubectl logs job/model-downloader -n torchserve
```

### 5. Deploy TorchServe Application

Create `torchserve-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: torchserve
  namespace: torchserve
  labels:
    app: torchserve
spec:
  replicas: 3
  selector:
    matchLabels:
      app: torchserve
  template:
    metadata:
      labels:
        app: torchserve
    spec:
      containers:
      - name: torchserve
        image: us-central1-docker.pkg.dev/${PROJECT_ID}/frameworks/pytorch-autoencoder-torchserve
        ports:
        - containerPort: 8080
          name: inference
          protocol: TCP
        - containerPort: 8081
          name: management
          protocol: TCP
        - containerPort: 8082
          name: metrics
          protocol: TCP
        env:
        - name: TS_CONFIG_FILE
          value: /mnt/config/config.properties
        volumeMounts:
        - name: model-store
          mountPath: /mnt/models
          readOnly: true
        - name: config
          mountPath: /mnt/config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /ping
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ping
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      volumes:
      - name: model-store
        persistentVolumeClaim:
          claimName: model-store-pvc
      - name: config
        configMap:
          name: torchserve-config
```

**Key Configuration**:
- **Replicas**: 3 for high availability
- **Health Checks**: Liveness (restart unhealthy pods) and Readiness (route traffic only when ready)
- **Resources**: 1-2 CPU, 2-4Gi memory per pod
- **Volumes**: Shared PVC for models, ConfigMap for TorchServe config

Apply:
```bash
envsubst < torchserve-deployment.yaml | kubectl apply -f -

# Watch deployment progress
kubectl get pods -n torchserve -w
```

### 6. Create Service (LoadBalancer)

Create `torchserve-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: torchserve
  namespace: torchserve
  labels:
    app: torchserve
spec:
  type: LoadBalancer
  selector:
    app: torchserve
  ports:
  - name: inference
    port: 8080
    targetPort: 8080
    protocol: TCP
  - name: management
    port: 8081
    targetPort: 8081
    protocol: TCP
  - name: metrics
    port: 8082
    targetPort: 8082
    protocol: TCP
```

Apply:
```bash
kubectl apply -f torchserve-service.yaml

# Get external IP (may take 1-2 minutes)
kubectl get service torchserve -n torchserve
```

### 7. Configure Auto-Scaling

Create `hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: torchserve-hpa
  namespace: torchserve
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: torchserve
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Scaling Behavior**:
- Scales up when CPU > 70% or memory > 80%
- Scales down when below thresholds for sustained period
- Min 2 replicas for availability, max 10 for cost control

Apply:
```bash
kubectl apply -f hpa.yaml
```

---

## Test Deployment

### Get Service Endpoint

```bash
export EXTERNAL_IP=$(kubectl get service torchserve -n torchserve -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "TorchServe Endpoints:"
echo "  Inference: http://$EXTERNAL_IP:8080"
echo "  Management: http://$EXTERNAL_IP:8081"
echo "  Metrics: http://$EXTERNAL_IP:8082"
```

### Make Test Prediction

```bash
# Create test data (raw JSON array, NOT {"instances": ...})
cat > test-data.json <<'EOF'
[92.35, -0.26, 0.13, 1.45, -0.89, 0.72, -0.34, 1.21, -0.56, 0.98,
 -0.12, 0.67, -0.43, 0.88, -0.21, 1.12, -0.67, 0.34, -0.91, 0.56,
 -0.23, 0.79, -0.45, 1.03, -0.78, 0.41, -0.15, 0.92, -0.63, 0.28]
EOF

# Make prediction
curl -X POST http://$EXTERNAL_IP:8080/predictions/pytorch_autoencoder \
    -H "Content-Type: application/json" \
    -d @test-data.json
```

**Expected Response**:
```json
{
  "denormalized_MAE": 2791.81,
  "denormalized_RMSE": 15284.22,
  "encoded": [0.0, 0.0, 0.34, 0.0],
  ...
}
```

**Note**: TorchServe expects raw JSON array, not Vertex AI format `{"instances": [...]}`

### Check Service Health

```bash
# Health check
curl http://$EXTERNAL_IP:8080/ping

# List models
curl http://$EXTERNAL_IP:8081/models

# Model details
curl http://$EXTERNAL_IP:8081/models/pytorch_autoencoder

# Metrics
curl http://$EXTERNAL_IP:8082/metrics
```

---

## Monitor and Manage

### View Cluster Resources

```bash
# Get pods
kubectl get pods -n torchserve

# Get pod details
kubectl describe pod <pod-name> -n torchserve

# View logs
kubectl logs -f <pod-name> -n torchserve

# Stream logs from all pods
kubectl logs -f -l app=torchserve -n torchserve --all-containers=true
```

### Check Auto-Scaling Status

```bash
# HPA status
kubectl get hpa -n torchserve

# Detailed HPA info
kubectl describe hpa torchserve-hpa -n torchserve

# Pod resource usage
kubectl top pods -n torchserve

# Node resource usage
kubectl top nodes
```

### Scale Manually

```bash
# Scale deployment
kubectl scale deployment torchserve --replicas=5 -n torchserve

# Verify
kubectl get pods -n torchserve
```

### Update Model

Deploy a new model version:

```bash
# Upload new .mar to GCS
gsutil cp new_pytorch_autoencoder.mar gs://${PROJECT_ID}/frameworks/pytorch-autoencoder/torchserve-gke/

# Delete downloader job
kubectl delete job model-downloader -n torchserve

# Re-run downloader with new model
envsubst < model-downloader-job.yaml | kubectl apply -f -

# Rolling restart to pick up new model
kubectl rollout restart deployment torchserve -n torchserve

# Watch rollout
kubectl rollout status deployment torchserve -n torchserve
```

---

## Advanced Configurations

### Canary Deployment

Deploy new model version to subset of pods:

Create `torchserve-deployment-v2.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: torchserve-v2
  namespace: torchserve
spec:
  replicas: 1  # Start with 1 replica (canary)
  selector:
    matchLabels:
      app: torchserve
      version: v2
  template:
    metadata:
      labels:
        app: torchserve
        version: v2
    spec:
      containers:
      - name: torchserve
        image: us-central1-docker.pkg.dev/${PROJECT_ID}/frameworks/pytorch-autoencoder-torchserve:v2
        # ... same config as v1
```

Update service to route traffic to both versions:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: torchserve
  namespace: torchserve
spec:
  type: LoadBalancer
  selector:
    app: torchserve  # Matches both v1 and v2 (no version label)
  ports:
  - name: inference
    port: 8080
    targetPort: 8080
```

**Traffic Distribution**: With 3 v1 pods and 1 v2 pod, ~25% traffic goes to v2. Gradually increase v2 replicas and decrease v1.

### Multi-Model Serving

Serve multiple models in same deployment:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: multi-model-downloader
  namespace: torchserve
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: downloader
        image: google/cloud-sdk:slim
        command:
          - /bin/bash
          - -c
          - |
            gsutil cp gs://${PROJECT_ID}/models/model1.mar /mnt/models/
            gsutil cp gs://${PROJECT_ID}/models/model2.mar /mnt/models/
            gsutil cp gs://${PROJECT_ID}/models/model3.mar /mnt/models/
        volumeMounts:
        - name: model-store
          mountPath: /mnt/models
      volumes:
      - name: model-store
        persistentVolumeClaim:
          claimName: model-store-pvc
```

TorchServe `load_models=all` will auto-load all `.mar` files.

### GPU Support

Add GPU resources to deployment:

```yaml
spec:
  template:
    spec:
      containers:
      - name: torchserve
        resources:
          limits:
            nvidia.com/gpu: 1
        # ... rest of config
      nodeSelector:
        cloud.google.com/gke-accelerator: nvidia-tesla-t4
```

**Note**: Requires GPU-enabled node pool created with `--accelerator` flag.

---

## Monitoring with Prometheus & Grafana

### Install Prometheus Stack

```bash
# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (includes Prometheus, Grafana, Alertmanager)
helm install prometheus prometheus-community/kube-prometheus-stack \
    -n monitoring \
    --create-namespace
```

### Configure TorchServe Metrics Collection

Create `torchserve-servicemonitor.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: torchserve-metrics
  namespace: torchserve
  labels:
    app: torchserve
spec:
  selector:
    matchLabels:
      app: torchserve
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

Apply:
```bash
kubectl apply -f torchserve-servicemonitor.yaml
```

### Access Grafana

```bash
# Port-forward Grafana service
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Access at http://localhost:3000
# Default credentials: admin / prom-operator
```

**Create Dashboard**: Import TorchServe metrics for request rates, latencies, queue sizes, worker counts.

---

## Cost Optimization

### 1. Use Spot VMs for Worker Nodes

Create node pool with Spot VMs (up to 91% discount):

```bash
gcloud container node-pools create spot-pool \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    --spot \
    --machine-type=n1-standard-4 \
    --num-nodes=2 \
    --enable-autoscaling \
    --min-nodes=0 \
    --max-nodes=10

# Taint spot nodes so only tolerant workloads run there
kubectl taint nodes -l cloud.google.com/gke-spot=true spot=true:NoSchedule
```

Update deployment to tolerate spot nodes:

```yaml
spec:
  template:
    spec:
      tolerations:
      - key: "spot"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      nodeSelector:
        cloud.google.com/gke-spot: "true"
```

**Spot VM Savings**: ~91% discount vs on-demand (n1-standard-4: $0.03/hr vs $0.19/hr)

**Trade-off**: Pods may be evicted with 30s notice. Ensure graceful shutdown and maintain min replicas on regular nodes.

### 2. Enable Node Auto-Provisioning

Automatically create/delete node pools based on demand:

```bash
gcloud container clusters update $CLUSTER_NAME \
    --enable-autoprovisioning \
    --region=$REGION \
    --min-cpu=4 \
    --max-cpu=64 \
    --min-memory=16 \
    --max-memory=256 \
    --autoprovisioning-scopes=https://www.googleapis.com/auth/cloud-platform
```

### 3. Right-Size Resource Requests

Monitor actual usage and adjust:

```bash
# View container resource usage
kubectl top pods -n torchserve --containers

# Adjust deployment requests/limits based on actual usage
# Aim for: requests = typical usage, limits = max expected
```

**Example Adjustment**:
```yaml
resources:
  requests:
    memory: "1.5Gi"  # Reduced from 2Gi if actual usage is ~1.2Gi
    cpu: "750m"      # Reduced from 1000m if actual usage is ~500m
  limits:
    memory: "3Gi"    # Keep headroom for spikes
    cpu: "1500m"
```

### 4. Use Committed Use Discounts

For predictable workloads, commit to 1 or 3 years:
- **1 year**: ~37% discount
- **3 years**: ~55% discount

Purchase via: Console > Compute Engine > Committed Use Discounts

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n torchserve

# Describe pod for events
kubectl describe pod <pod-name> -n torchserve

# Check logs
kubectl logs <pod-name> -n torchserve

# Common issues:
# 1. Image pull errors - verify IMAGE_NAME
# 2. PVC not bound - check PVC status
# 3. Resource limits - check node capacity
```

### Model Loading Failures

```bash
# Check init container logs (model downloader)
kubectl logs <pod-name> -n torchserve -c downloader

# Exec into pod to verify model file
kubectl exec -it <pod-name> -n torchserve -- /bin/bash
ls -lh /mnt/models/

# Verify .mar file integrity
cd /mnt/models
unzip -l pytorch_autoencoder.mar

# Check for pyyaml dependency (common issue)
python3 -c "import yaml; print('✅ pyyaml installed')"

# View TorchServe worker logs
kubectl logs <pod-name> -n torchserve | grep -i error
```

### High Latency

```bash
# Check pod resource usage
kubectl top pods -n torchserve

# Check HPA status
kubectl get hpa -n torchserve

# Check current workers per model
curl http://$EXTERNAL_IP:8081/models/pytorch_autoencoder | jq '.workers'

# Scale workers (via management API from within pod)
kubectl exec -it <pod-name> -n torchserve -- \
  curl -X PUT "http://localhost:8081/models/pytorch_autoencoder?min_worker=4&max_worker=8"

# Scale deployment
kubectl scale deployment torchserve --replicas=10 -n torchserve
```

### Worker Crashes

```bash
# Check worker logs for errors
kubectl logs <pod-name> -n torchserve | grep -i "worker\|error"

# Common causes:
# 1. Out of memory - increase pod memory limits
# 2. Missing dependencies - check pyyaml, etc.
# 3. Model incompatibility - verify PyTorch version

# Restart problematic pod
kubectl delete pod <pod-name> -n torchserve
```

### Service Not Accessible

```bash
# Check service status
kubectl get service torchserve -n torchserve

# Verify LoadBalancer IP assigned
kubectl describe service torchserve -n torchserve

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n torchserve -- \
  curl http://torchserve:8080/ping

# Check firewall rules (if using private cluster)
gcloud compute firewall-rules list --filter="name~torchserve"
```

---

## Production Hardening

### 1. Enable Network Policies

Restrict pod-to-pod communication:

Create `network-policy.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: torchserve-netpol
  namespace: torchserve
spec:
  podSelector:
    matchLabels:
      app: torchserve
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}  # Allow from same namespace
    ports:
    - port: 8080
      protocol: TCP
  egress:
  - to:
    - namespaceSelector: {}  # Allow to all namespaces
    ports:
    - port: 443  # HTTPS for GCS access
      protocol: TCP
```

Apply:
```bash
kubectl apply -f network-policy.yaml
```

### 2. Add Resource Quotas

Prevent resource exhaustion:

Create `resource-quota.yaml`:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: torchserve-quota
  namespace: torchserve
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "5"
    services.loadbalancers: "2"
```

Apply:
```bash
kubectl apply -f resource-quota.yaml
```

### 3. Enable Pod Security

Run containers as non-root:

```yaml
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: torchserve
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false  # TorchServe needs write access to /tmp
          capabilities:
            drop:
            - ALL
```

### 4. Configure HTTPS with Ingress

Replace LoadBalancer with Ingress for SSL termination:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: torchserve-ingress
  namespace: torchserve
  annotations:
    kubernetes.io/ingress.class: "gce"
    networking.gke.io/managed-certificates: "torchserve-cert"
spec:
  rules:
  - host: torchserve.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: torchserve
            port:
              number: 8080
```

**Requires**: Domain name, managed certificate, and changing Service type to ClusterIP.

---

## Cleanup

### Delete All Resources

```bash
# Delete namespace (removes all resources)
kubectl delete namespace torchserve

# Delete cluster
gcloud container clusters delete $CLUSTER_NAME --region=$REGION --quiet

# Delete container images (optional)
gcloud artifacts docker images delete $IMAGE_NAME --quiet
```

### Delete Individual Resources

```bash
# Delete deployment
kubectl delete deployment torchserve -n torchserve

# Delete service
kubectl delete service torchserve -n torchserve

# Delete HPA
kubectl delete hpa torchserve-hpa -n torchserve

# Delete PVC (also deletes data)
kubectl delete pvc model-store-pvc -n torchserve
```

---

## Next Steps

**Enhance Deployment**:
- Add Ingress for HTTPS and domain mapping
- Implement CI/CD with Cloud Build and Skaffold
- Add distributed tracing with Cloud Trace
- Configure multi-region clusters for geo-distribution

**Advanced Orchestration**:
- Implement Istio service mesh for traffic management
- Add Knative for serverless workloads on GKE
- Configure Anthos for hybrid/multi-cloud deployments

**Monitoring**:
- Create Grafana dashboards for TorchServe metrics
- Set up alerting for errors, latency, and resource usage
- Integrate with Cloud Logging for centralized logs

**Upgrade to Multi-Model**:
- Deploy multiple models with different resource requirements
- Implement model routing based on request headers
- Configure per-model auto-scaling policies

---

## Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Kubernetes Best Practices for Cost](https://cloud.google.com/architecture/best-practices-for-running-cost-effective-kubernetes-applications-on-gke)
- [TorchServe Kubernetes Examples](https://github.com/pytorch/serve/tree/master/kubernetes)
- [GKE Pricing Calculator](https://cloud.google.com/products/calculator)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
