![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FPyTorch%2Fserving&file=serve-gke.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/PyTorch/serving/serve-gke.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/serve-gke.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/serve-gke.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/serve-gke.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/serve-gke.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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

This guide walks through deploying TorchServe on Google Kubernetes Engine (GKE) for enterprise-scale, multi-model orchestration.

## When to Use GKE

**Best for**:
- Multiple models to serve
- Complex deployment strategies (canary, blue/green)
- High availability requirements
- Enterprise-scale infrastructure
- Need for orchestration and auto-scaling
- Microservices architecture

**Choose GKE over**:
- **Cloud Run**: When you need advanced orchestration, multiple models, or GPU support
- **GCE**: When you need Kubernetes benefits (self-healing, rolling updates, declarative config)
- **Local**: When you need production-grade deployment

---

## Prerequisites

- Completed [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb) - Model trained and .mar file created
- .mar file uploaded to GCS at `gs://{PROJECT_ID}/frameworks/pytorch-autoencoder/model.mar`
- GCP project with GKE API enabled
- `kubectl` installed locally
- Container image built (can use Dockerfile from Cloud Run notebook)

---

## Architecture

```
Internet → Load Balancer → Ingress
                             ↓
                    Kubernetes Service
                             ↓
                    TorchServe Pods (3 replicas)
                             ↓
                    Persistent Volume (model storage)
                             ↓
                    GCS (.mar file)
```

---

## Step 1: Create GKE Cluster

### Standard Cluster

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export CLUSTER_NAME="pytorch-torchserve"

gcloud container clusters create $CLUSTER_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --num-nodes=3 \
    --machine-type=n1-standard-4 \
    --disk-size=50 \
    --enable-autoscaling \
    --min-nodes=2 \
    --max-nodes=10 \
    --enable-autorepair \
    --enable-autoupgrade \
    --scopes=https://www.googleapis.com/auth/cloud-platform
```

### Cluster with GPU Support (Optional)

```bash
gcloud container clusters create $CLUSTER_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --num-nodes=2 \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --disk-size=50 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5 \
    --scopes=https://www.googleapis.com/auth/cloud-platform

# Install NVIDIA GPU drivers
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

### Get Cluster Credentials

```bash
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION
```

---

## Step 2: Build and Push Container Image

If you haven't already built the image:

```bash
export IMAGE_NAME="gcr.io/${PROJECT_ID}/pytorch-torchserve:latest"

# Build using Cloud Build
gcloud builds submit --tag $IMAGE_NAME

# Or build locally and push
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME
```

---

## Step 3: Create Kubernetes Resources

### Create Namespace

```bash
kubectl create namespace torchserve
```

### Create ConfigMap for TorchServe Config

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
    number_of_netty_threads=8
    job_queue_size=100
    model_store=/mnt/models
    load_models=all
    default_workers_per_model=2
```

Apply:
```bash
kubectl apply -f torchserve-config.yaml
```

### Create Persistent Volume for Models

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

Apply:
```bash
kubectl apply -f model-pv.yaml
```

### Create Init Container Job to Download Model

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
            gsutil cp gs://${PROJECT_ID}/frameworks/pytorch-autoencoder/model.mar /mnt/models/
        volumeMounts:
        - name: model-store
          mountPath: /mnt/models
      volumes:
      - name: model-store
        persistentVolumeClaim:
          claimName: model-store-pvc
```

Apply:
```bash
envsubst < model-downloader-job.yaml | kubectl apply -f -
```

### Create TorchServe Deployment

Create `torchserve-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: torchserve
  namespace: torchserve
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
        image: gcr.io/${PROJECT_ID}/pytorch-torchserve:latest
        ports:
        - containerPort: 8080
          name: inference
        - containerPort: 8081
          name: management
        - containerPort: 8082
          name: metrics
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
        readinessProbe:
          httpGet:
            path: /ping
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
      volumes:
      - name: model-store
        persistentVolumeClaim:
          claimName: model-store-pvc
      - name: config
        configMap:
          name: torchserve-config
```

Apply:
```bash
envsubst < torchserve-deployment.yaml | kubectl apply -f -
```

### Create Service

Create `torchserve-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: torchserve
  namespace: torchserve
spec:
  type: LoadBalancer
  selector:
    app: torchserve
  ports:
  - name: inference
    port: 8080
    targetPort: 8080
  - name: management
    port: 8081
    targetPort: 8081
  - name: metrics
    port: 8082
    targetPort: 8082
```

Apply:
```bash
kubectl apply -f torchserve-service.yaml
```

---

## Step 4: Configure Horizontal Pod Autoscaling

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

Apply:
```bash
kubectl apply -f hpa.yaml
```

---

## Step 5: Test Deployment

Get the service external IP:

```bash
kubectl get service torchserve -n torchserve

export EXTERNAL_IP=$(kubectl get service torchserve -n torchserve -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "TorchServe URL: http://$EXTERNAL_IP:8080"
```

Test prediction:

```bash
# Create test data
cat > test-data.json <<EOF
{
  "instances": [
    [92.35, -0.26, 0.13, 1.45, -0.89, 0.72, -0.34, 1.21, -0.56, 0.98,
     -0.12, 0.67, -0.43, 0.88, -0.21, 1.12, -0.67, 0.34, -0.91, 0.56,
     -0.23, 0.79, -0.45, 1.03, -0.78, 0.41, -0.15, 0.92, -0.63, 0.28]
  ]
}
EOF

# Make prediction
curl -X POST http://$EXTERNAL_IP:8080/predictions/pytorch_autoencoder \
    -H "Content-Type: application/json" \
    -d @test-data.json
```

---

## Step 6: Monitor and Manage

### View Pods

```bash
kubectl get pods -n torchserve
kubectl logs -f <pod-name> -n torchserve
```

### Check Model Status

```bash
curl http://$EXTERNAL_IP:8081/models
curl http://$EXTERNAL_IP:8081/models/pytorch_autoencoder
```

### View Metrics

```bash
# Metrics endpoint
curl http://$EXTERNAL_IP:8082/metrics

# Kubernetes metrics
kubectl top pods -n torchserve
kubectl top nodes
```

### Scale Manually

```bash
# Scale deployment
kubectl scale deployment torchserve --replicas=5 -n torchserve

# Check HPA status
kubectl get hpa -n torchserve
kubectl describe hpa torchserve-hpa -n torchserve
```

---

## Advanced Configurations

### Canary Deployment

Create a second deployment for the new version:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: torchserve-v2
  namespace: torchserve
spec:
  replicas: 1  # Start with 1 replica
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
      # ... same as torchserve deployment but with new image
```

Update service to include both versions:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: torchserve
  namespace: torchserve
spec:
  type: LoadBalancer
  selector:
    app: torchserve  # Matches both v1 and v2
  ports:
  - name: inference
    port: 8080
    targetPort: 8080
```

Gradually shift traffic by adjusting replica counts.

### Multi-Model Serving

Deploy multiple models:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: torchserve-multi
  namespace: torchserve
spec:
  replicas: 3
  template:
    spec:
      initContainers:
      - name: download-models
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
      containers:
      - name: torchserve
        # ... rest of container spec
```

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
      nodeSelector:
        cloud.google.com/gke-accelerator: nvidia-tesla-t4
```

---

## Monitoring with Prometheus & Grafana

### Install Prometheus

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### Create ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: torchserve-metrics
  namespace: torchserve
spec:
  selector:
    matchLabels:
      app: torchserve
  endpoints:
  - port: metrics
    interval: 30s
```

### Access Grafana

```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# Access at http://localhost:3000
# Default credentials: admin/prom-operator
```

---

## Cost Optimization

### Use Node Auto-provisioning

```bash
gcloud container clusters update $CLUSTER_NAME \
    --enable-autoprovisioning \
    --min-cpu=4 \
    --max-cpu=64 \
    --min-memory=16 \
    --max-memory=256
```

### Use Spot VMs

Add node pool with spot VMs:

```bash
gcloud container node-pools create spot-pool \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    --spot \
    --machine-type=n1-standard-4 \
    --num-nodes=2 \
    --enable-autoscaling \
    --min-nodes=0 \
    --max-nodes=5
```

### Optimize Resource Requests

Monitor actual usage and adjust:

```bash
kubectl top pods -n torchserve --containers
# Adjust requests/limits in deployment
```

---

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n torchserve
kubectl logs <pod-name> -n torchserve
```

### Model loading issues

```bash
# Check init container logs
kubectl logs <pod-name> -n torchserve -c downloader

# Exec into pod
kubectl exec -it <pod-name> -n torchserve -- /bin/bash
ls -lh /mnt/models/
```

### High latency

```bash
# Check pod resources
kubectl top pods -n torchserve

# Scale up
kubectl scale deployment torchserve --replicas=10 -n torchserve

# Check HPA
kubectl describe hpa torchserve-hpa -n torchserve
```

---

## Cleanup

```bash
# Delete namespace (removes all resources)
kubectl delete namespace torchserve

# Delete cluster
gcloud container clusters delete $CLUSTER_NAME --region=$REGION
```

---

## Production Hardening

### Enable Network Policies

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
  ingress:
  - from:
    - podSelector: {}
    ports:
    - port: 8080
```

### Add Resource Quotas

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
```

### Enable Pod Security

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: torchserve
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: torchserve
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
```

---

## Next Steps

- **Add Ingress**: Configure HTTPS and domain mapping
- **Implement CI/CD**: Automate model updates with Cloud Build
- **Add Observability**: Integrate logging, tracing, and monitoring
- **Multi-region**: Deploy to multiple clusters for geo-distribution

---

## Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Kubernetes Best Practices](https://cloud.google.com/architecture/best-practices-for-running-cost-effective-kubernetes-applications-on-gke)
- [TorchServe Kubernetes](https://github.com/pytorch/serve/tree/master/kubernetes)
- [GKE Pricing](https://cloud.google.com/kubernetes-engine/pricing)
