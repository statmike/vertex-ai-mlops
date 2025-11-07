![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FPyTorch%2Fserving&file=serve-gce.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/PyTorch/serving/serve-gce.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/serve-gce.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/serve-gce.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/serve-gce.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/serve-gce.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# TorchServe Deployment on Google Compute Engine

This guide walks through deploying TorchServe on a Google Compute Engine (GCE) VM for long-running, dedicated serving workloads.

## When to Use GCE

**Best for**:
- Consistent 24/7 traffic patterns
- Need for dedicated resources
- Specific VM configurations or GPUs
- Cost-effective for steady loads
- Full control over the serving environment

**Choose GCE over**:
- **Cloud Run**: When you need always-on serving (no cold starts) or specific VM configurations
- **Local**: When you need production deployment with proper infrastructure
- **GKE**: When you don't need Kubernetes orchestration complexity

---

## Prerequisites

- Completed [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb) - Model trained and .mar file created
- .mar file uploaded to GCS at `gs://{PROJECT_ID}/frameworks/pytorch-autoencoder/model.mar`
- GCP project with Compute Engine API enabled

---

## Architecture

```
Internet → Load Balancer → GCE VM (TorchServe) → Predictions
                               ↓
                          GCS (.mar file)
```

---

## Step 1: Create VM Instance

### Basic VM (CPU-only)

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"
export VM_NAME="pytorch-torchserve"

gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=n1-standard-4 \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-standard \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=torchserve-server \
    --metadata=startup-script='#!/bin/bash
# Startup script will be added in Step 2
'
```

### VM with GPU (Optional)

For GPU-accelerated inference:

```bash
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=us-central1-a \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --image-family=pytorch-latest-gpu \
    --image-project=deeplearning-platform-release \
    --boot-disk-size=50GB \
    --maintenance-policy=TERMINATE \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=torchserve-server
```

---

## Step 2: Create Startup Script

Create `startup-script.sh`:

```bash
#!/bin/bash

# Update system
apt-get update
apt-get install -y python3-pip openjdk-11-jdk

# Install TorchServe
pip3 install torchserve torch-model-archiver torch-workflow-archiver

# Create directories
mkdir -p /opt/torchserve/model-store
mkdir -p /opt/torchserve/logs

# Download model from GCS
gsutil cp gs://${PROJECT_ID}/frameworks/pytorch-autoencoder/model.mar /opt/torchserve/model-store/

# Create TorchServe config
cat > /opt/torchserve/config.properties <<EOF
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
number_of_netty_threads=4
job_queue_size=100
model_store=/opt/torchserve/model-store
load_models=all
EOF

# Create systemd service
cat > /etc/systemd/system/torchserve.service <<EOF
[Unit]
Description=TorchServe
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/torchserve
ExecStart=/usr/local/bin/torchserve --start --ts-config /opt/torchserve/config.properties --ncs
ExecStop=/usr/local/bin/torchserve --stop
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
systemctl daemon-reload
systemctl enable torchserve
systemctl start torchserve

# Wait for TorchServe to start
sleep 30

# Register model
curl -X POST "http://localhost:8081/models?url=/opt/torchserve/model-store/model.mar&initial_workers=2&synchronous=true"
```

Upload and use the startup script:

```bash
# Upload script to VM
gcloud compute instances add-metadata $VM_NAME \
    --zone=$ZONE \
    --metadata-from-file startup-script=startup-script.sh

# Or SSH and run manually
gcloud compute ssh $VM_NAME --zone=$ZONE
sudo bash startup-script.sh
```

---

## Step 3: Configure Firewall

Allow traffic to TorchServe:

```bash
# Create firewall rule for inference endpoint
gcloud compute firewall-rules create allow-torchserve-inference \
    --project=$PROJECT_ID \
    --allow=tcp:8080 \
    --target-tags=torchserve-server \
    --description="Allow inference requests to TorchServe"

# (Optional) Create rule for management API
gcloud compute firewall-rules create allow-torchserve-management \
    --project=$PROJECT_ID \
    --allow=tcp:8081 \
    --source-ranges=YOUR_IP/32 \
    --target-tags=torchserve-server \
    --description="Allow management access to TorchServe"
```

---

## Step 4: Test Deployment

Get the VM's external IP:

```bash
export EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

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

## Step 5: Monitor and Manage

### Check Service Status

SSH into the VM:

```bash
gcloud compute ssh $VM_NAME --zone=$ZONE
```

Check TorchServe status:

```bash
# Check systemd service
sudo systemctl status torchserve

# View logs
sudo journalctl -u torchserve -f

# Check model status
curl http://localhost:8081/models
curl http://localhost:8081/models/pytorch_autoencoder

# View metrics
curl http://localhost:8082/metrics
```

### Scale Workers

```bash
# Scale up workers
curl -X PUT "http://localhost:8081/models/pytorch_autoencoder?min_worker=4&max_worker=8"

# Check worker status
curl http://localhost:8081/models/pytorch_autoencoder
```

### Update Model

```bash
# Download new .mar file
gsutil cp gs://${PROJECT_ID}/frameworks/pytorch-autoencoder/model.mar /opt/torchserve/model-store/model-v2.mar

# Unregister old model
curl -X DELETE http://localhost:8081/models/pytorch_autoencoder

# Register new model
curl -X POST "http://localhost:8081/models?url=/opt/torchserve/model-store/model-v2.mar&initial_workers=2&synchronous=true"
```

---

## Step 6: Add Load Balancer (Optional)

For production with multiple VMs:

```bash
# Create instance template from existing VM
gcloud compute instance-templates create torchserve-template \
    --source-instance=$VM_NAME \
    --source-instance-zone=$ZONE

# Create managed instance group
gcloud compute instance-groups managed create torchserve-mig \
    --base-instance-name=torchserve \
    --template=torchserve-template \
    --size=2 \
    --zone=$ZONE

# Create health check
gcloud compute health-checks create http torchserve-health \
    --port=8080 \
    --request-path=/ping

# Create backend service
gcloud compute backend-services create torchserve-backend \
    --protocol=HTTP \
    --health-checks=torchserve-health \
    --global

# Add instance group to backend
gcloud compute backend-services add-backend torchserve-backend \
    --instance-group=torchserve-mig \
    --instance-group-zone=$ZONE \
    --global

# Create URL map
gcloud compute url-maps create torchserve-lb \
    --default-service=torchserve-backend

# Create target proxy
gcloud compute target-http-proxies create torchserve-proxy \
    --url-map=torchserve-lb

# Create forwarding rule
gcloud compute forwarding-rules create torchserve-rule \
    --global \
    --target-http-proxy=torchserve-proxy \
    --ports=80
```

---

## Cost Optimization

### Right-size your VM

```bash
# Monitor resource usage
gcloud compute ssh $VM_NAME --zone=$ZONE --command="top -b -n 1"

# Resize if needed
gcloud compute instances set-machine-type $VM_NAME \
    --zone=$ZONE \
    --machine-type=n1-standard-2
```

### Use Committed Use Discounts

For predictable workloads, commit to 1 or 3 years for up to 57% discount.

### Use Preemptible VMs for Dev/Test

```bash
gcloud compute instances create $VM_NAME-dev \
    --preemptible \
    --machine-type=n1-standard-2 \
    # ... other flags
```

---

## Troubleshooting

### TorchServe won't start

```bash
# Check logs
sudo journalctl -u torchserve -n 50

# Verify Java installation
java -version

# Check ports
sudo netstat -tlnp | grep -E '8080|8081|8082'

# Manually start for debugging
sudo /usr/local/bin/torchserve --start --ts-config /opt/torchserve/config.properties --ncs --foreground
```

### Model loading fails

```bash
# Check model file
ls -lh /opt/torchserve/model-store/

# Test model extraction
torch-model-archiver --model-file /opt/torchserve/model-store/model.mar --export-path /tmp/test

# Check handler
unzip -l /opt/torchserve/model-store/model.mar
```

### High latency

```bash
# Increase workers
curl -X PUT "http://localhost:8081/models/pytorch_autoencoder?min_worker=4"

# Monitor metrics
curl http://localhost:8082/metrics | grep -E 'QueueTime|WorkerLoadTime|PredictionTime'

# Consider larger VM or GPU
```

---

## Cleanup

```bash
# Delete VM
gcloud compute instances delete $VM_NAME --zone=$ZONE

# Delete firewall rules
gcloud compute firewall-rules delete allow-torchserve-inference
gcloud compute firewall-rules delete allow-torchserve-management

# (If using load balancer) Delete all resources
gcloud compute forwarding-rules delete torchserve-rule --global
gcloud compute target-http-proxies delete torchserve-proxy
gcloud compute url-maps delete torchserve-lb
gcloud compute backend-services delete torchserve-backend --global
gcloud compute health-checks delete torchserve-health
gcloud compute instance-groups managed delete torchserve-mig --zone=$ZONE
gcloud compute instance-templates delete torchserve-template
```

---

## Next Steps

- **Scale horizontally**: Set up managed instance group with auto-scaling
- **Add monitoring**: Integrate with Cloud Monitoring and Logging
- **Secure access**: Add authentication and HTTPS
- **Upgrade to GKE**: For multi-model orchestration, see [serve-gke.md](./serve-gke.md)

---

## Resources

- [Compute Engine Documentation](https://cloud.google.com/compute/docs)
- [TorchServe Configuration](https://pytorch.org/serve/configuration.html)
- [GCE Pricing Calculator](https://cloud.google.com/products/calculator)
