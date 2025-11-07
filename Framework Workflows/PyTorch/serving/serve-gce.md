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

Deploy TorchServe on Google Compute Engine VMs for long-running, dedicated serving workloads with full infrastructure control.

## When to Use GCE

**Best for**:
- **Consistent 24/7 traffic**: Predictable, steady workloads
- **Dedicated resources**: Need guaranteed compute/memory
- **Custom configurations**: Specific OS, GPU types, or system libraries
- **Cost-effective for steady loads**: Lower cost than Cloud Run for always-on workloads
- **Full control**: Root access, custom networking, persistent storage

**Choose GCE over**:
- **Cloud Run**: When you need always-on serving (no cold starts acceptable) or specific VM configurations
- **Local Development**: When you need production deployment with proper infrastructure and uptime
- **GKE**: When you don't need Kubernetes orchestration complexity (single model, straightforward scaling)

**Cost Comparison** (n1-standard-4):
- **GCE Always-On**: ~$146/month (24/7)
- **Cloud Run (min=0)**: $0 idle, ~$0.20/hour when serving
- **Cloud Run (min=1)**: ~$146/month + request charges

---

## Prerequisites

Before starting, ensure you have:

1. **Model Archive**: Completed [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)
   - Model trained and `.mar` file created
   - Upload to GCS: `gs://{PROJECT_ID}/frameworks/pytorch-autoencoder/torchserve-gce/pytorch_autoencoder.mar`

2. **GCP Project**:
   - Compute Engine API enabled
   - Appropriate IAM permissions for VM creation

3. **Dependencies**: Model handler requires `pyyaml` (included in setup script)

---

## Architecture

```
Internet → Cloud Load Balancer → Firewall
                                     ↓
                            GCE VM (TorchServe)
                                     ↓
                            Systemd Service
                                     ↓
                         GCS (.mar file download)
```

**Key Design**:
- VMs download model from GCS at startup
- Systemd manages TorchServe lifecycle
- Firewall rules control access
- Optional load balancer for multiple VMs

---

## Quick Start

### 1. Set Variables

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"
export VM_NAME="pytorch-torchserve"
export MAR_FILE="pytorch_autoencoder.mar"
```

### 2. Create VM

**CPU-only VM** (recommended for testing):

```bash
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=n1-standard-4 \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-standard \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=torchserve-server \
    --metadata=enable-oslogin=true
```

**GPU VM** (for accelerated inference):

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
    --tags=torchserve-server \
    --metadata=enable-oslogin=true

# GPU drivers pre-installed with pytorch-latest-gpu image
```

### 3. Configure Firewall

Allow traffic to TorchServe:

```bash
# Inference endpoint (public)
gcloud compute firewall-rules create allow-torchserve-inference \
    --project=$PROJECT_ID \
    --allow=tcp:8080 \
    --target-tags=torchserve-server \
    --description="Allow inference requests to TorchServe"

# Management API (restrict to your IP)
gcloud compute firewall-rules create allow-torchserve-management \
    --project=$PROJECT_ID \
    --allow=tcp:8081 \
    --source-ranges=$(curl -s ifconfig.me)/32 \
    --target-tags=torchserve-server \
    --description="Allow management access from my IP"
```

### 4. Install and Configure TorchServe

SSH into the VM:

```bash
gcloud compute ssh $VM_NAME --zone=$ZONE
```

Create and run the installation script:

```bash
cat > install-torchserve.sh <<'SCRIPT'
#!/bin/bash
set -e

echo "Installing TorchServe on GCE VM..."

# Update system and install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip default-jdk curl

# Install TorchServe and dependencies
sudo pip3 install --no-cache-dir \
    torchserve \
    torch-model-archiver \
    torch-workflow-archiver \
    torch \
    torchvision \
    pyyaml

# Create TorchServe directories
sudo mkdir -p /opt/torchserve/model-store /opt/torchserve/logs

# Download model from GCS
echo "Downloading model from GCS..."
PROJECT_ID=$(gcloud config get-value project)
gsutil cp gs://${PROJECT_ID}/frameworks/pytorch-autoencoder/torchserve-gce/pytorch_autoencoder.mar \
    /opt/torchserve/model-store/

# Create TorchServe configuration
sudo cat > /opt/torchserve/config.properties <<EOF
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
model_store=/opt/torchserve/model-store
load_models=all
disable_token_authorization=true
number_of_netty_threads=4
job_queue_size=100
EOF

# Create systemd service
sudo cat > /etc/systemd/system/torchserve.service <<EOF
[Unit]
Description=TorchServe ML Model Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/torchserve
ExecStart=/usr/local/bin/torchserve \\
    --start \\
    --ts-config /opt/torchserve/config.properties \\
    --models pytorch_autoencoder=pytorch_autoencoder.mar \\
    --ncs
ExecStop=/usr/local/bin/torchserve --stop
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl enable torchserve
sudo systemctl start torchserve

echo "✅ TorchServe installation complete!"
echo "   Check status: sudo systemctl status torchserve"
echo "   View logs: sudo journalctl -u torchserve -f"
SCRIPT

# Run the installation
chmod +x install-torchserve.sh
./install-torchserve.sh
```

### 5. Verify Installation

```bash
# Check service status
sudo systemctl status torchserve

# View logs
sudo journalctl -u torchserve -n 50

# Check loaded models
curl http://localhost:8081/models

# Health check
curl http://localhost:8080/ping
```

### 6. Test Predictions

Get VM external IP:

```bash
export EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "TorchServe URL: http://$EXTERNAL_IP:8080"
```

Make a test prediction:

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

---

## Management and Operations

### Monitor TorchServe

```bash
# SSH into VM
gcloud compute ssh $VM_NAME --zone=$ZONE

# Check systemd service
sudo systemctl status torchserve

# View real-time logs
sudo journalctl -u torchserve -f

# Check model status
curl http://localhost:8081/models/pytorch_autoencoder

# View metrics
curl http://localhost:8082/metrics
```

### Scale Workers

Adjust number of workers for throughput:

```bash
# Scale up workers (SSH into VM first)
curl -X PUT "http://localhost:8081/models/pytorch_autoencoder?min_worker=4&max_worker=8"

# Verify
curl http://localhost:8081/models/pytorch_autoencoder | jq '.workers'
```

### Update Model

Deploy a new model version:

```bash
# Upload new .mar to GCS
gsutil cp new_model.mar gs://${PROJECT_ID}/frameworks/pytorch-autoencoder/torchserve-gce/

# SSH into VM
gcloud compute ssh $VM_NAME --zone=$ZONE

# Download new model
gsutil cp gs://${PROJECT_ID}/frameworks/pytorch-autoencoder/torchserve-gce/new_model.mar \
    /opt/torchserve/model-store/

# Unregister old model
curl -X DELETE http://localhost:8081/models/pytorch_autoencoder

# Register new model
curl -X POST "http://localhost:8081/models?url=new_model.mar&initial_workers=2&model_name=pytorch_autoencoder"

# Or restart service to reload all models
sudo systemctl restart torchserve
```

---

## Production Hardening

### 1. Add Load Balancer (Multi-VM)

For high availability with multiple VMs:

```bash
# Create instance template from configured VM
gcloud compute instance-templates create torchserve-template \
    --source-instance=$VM_NAME \
    --source-instance-zone=$ZONE

# Create managed instance group
gcloud compute instance-groups managed create torchserve-mig \
    --base-instance-name=torchserve \
    --template=torchserve-template \
    --size=3 \
    --zone=$ZONE

# Create health check
gcloud compute health-checks create http torchserve-health \
    --port=8080 \
    --request-path=/ping \
    --check-interval=10s \
    --timeout=5s \
    --healthy-threshold=2 \
    --unhealthy-threshold=3

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

# Create URL map and forwarding rule
gcloud compute url-maps create torchserve-lb \
    --default-service=torchserve-backend

gcloud compute target-http-proxies create torchserve-proxy \
    --url-map=torchserve-lb

gcloud compute forwarding-rules create torchserve-rule \
    --global \
    --target-http-proxy=torchserve-proxy \
    --ports=80

# Get load balancer IP
gcloud compute forwarding-rules describe torchserve-rule --global
```

### 2. Enable Auto-Scaling

```bash
gcloud compute instance-groups managed set-autoscaling torchserve-mig \
    --zone=$ZONE \
    --min-num-replicas=2 \
    --max-num-replicas=10 \
    --target-cpu-utilization=0.7 \
    --cool-down-period=60
```

### 3. Add Cloud Monitoring

```bash
# Install monitoring agent (SSH into VM)
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# Configure custom TorchServe metrics
sudo cat > /etc/google-cloud-ops-agent/config.yaml <<EOF
metrics:
  receivers:
    torchserve:
      type: prometheus
      config:
        scrape_configs:
          - job_name: 'torchserve'
            scrape_interval: 30s
            static_configs:
              - targets: ['localhost:8082']
  service:
    pipelines:
      torchserve:
        receivers: [torchserve]
EOF

sudo systemctl restart google-cloud-ops-agent
```

---

## Cost Optimization

### Right-Size VM

Monitor actual usage:

```bash
# Check resource usage (SSH into VM)
top -b -n 1
free -h
df -h

# Resize VM if over/under-provisioned
gcloud compute instances stop $VM_NAME --zone=$ZONE
gcloud compute instances set-machine-type $VM_NAME \
    --zone=$ZONE \
    --machine-type=n1-standard-2
gcloud compute instances start $VM_NAME --zone=$ZONE
```

### Use Committed Use Discounts

For predictable workloads, commit to 1 or 3 years:
- **1 year**: ~37% discount
- **3 years**: ~55% discount

Purchase via: Console > Compute Engine > Committed Use Discounts

### Use Spot VMs (Dev/Test)

For non-production workloads:

```bash
gcloud compute instances create $VM_NAME-dev \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --machine-type=n1-standard-2 \
    --zone=$ZONE \
    # ... other flags same as above
```

**Spot VM Savings**: Up to 91% discount vs on-demand pricing

---

## Troubleshooting

### TorchServe Won't Start

```bash
# Check logs
sudo journalctl -u torchserve -n 100 --no-pager

# Common issues:
# 1. Java not installed
java -version  # Should show version

# 2. Ports already in use
sudo netstat -tlnp | grep -E '8080|8081|8082'

# 3. Missing dependencies
sudo pip3 list | grep -E 'torchserve|yaml'

# 4. Permission issues
ls -la /opt/torchserve/

# Manual start for debugging
sudo /usr/local/bin/torchserve --start \
    --ts-config /opt/torchserve/config.properties \
    --models pytorch_autoencoder=pytorch_autoencoder.mar \
    --ncs --foreground
```

### Model Loading Fails

```bash
# Check model file exists
ls -lh /opt/torchserve/model-store/

# Inspect .mar contents
unzip -l /opt/torchserve/model-store/pytorch_autoencoder.mar

# Check for yaml dependency (common issue)
python3 -c "import yaml; print('✅ pyyaml installed')"

# View model-specific logs
sudo journalctl -u torchserve | grep pytorch_autoencoder
```

### High Latency

```bash
# Check current workers
curl http://localhost:8081/models/pytorch_autoencoder | jq '.workers'

# Increase workers
curl -X PUT "http://localhost:8081/models/pytorch_autoencoder?min_worker=4&max_worker=8"

# Monitor metrics
curl http://localhost:8082/metrics | grep -E 'QueueTime|PredictionTime'

# Check CPU/memory
top -b -n 1 | head -20

# Consider:
# - Larger VM (more CPU/memory)
# - GPU VM for faster inference
# - Horizontal scaling with load balancer
```

### Worker Crashes

```bash
# Check worker logs
sudo journalctl -u torchserve | grep -i "error\|worker"

# Common causes:
# 1. Out of memory - increase VM memory
# 2. Missing dependencies - check handler imports
# 3. Model incompatibility - verify torch version
```

---

## Cleanup

### Delete Single VM

```bash
# Delete VM
gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet

# Delete firewall rules
gcloud compute firewall-rules delete allow-torchserve-inference --quiet
gcloud compute firewall-rules delete allow-torchserve-management --quiet
```

### Delete Load Balancer Setup

```bash
# Delete in reverse order of creation
gcloud compute forwarding-rules delete torchserve-rule --global --quiet
gcloud compute target-http-proxies delete torchserve-proxy --quiet
gcloud compute url-maps delete torchserve-lb --quiet
gcloud compute backend-services delete torchserve-backend --global --quiet
gcloud compute health-checks delete torchserve-health --quiet
gcloud compute instance-groups managed delete torchserve-mig --zone=$ZONE --quiet
gcloud compute instance-templates delete torchserve-template --quiet
```

---

## Next Steps

**Scale Up**:
- Set up managed instance group with auto-scaling
- Add Cloud Load Balancer for high availability
- Implement blue/green deployments

**Monitor**:
- Integrate with Cloud Monitoring dashboards
- Set up alerting for errors and latency
- Enable Cloud Logging for centralized logs

**Secure**:
- Add authentication (remove `disable_token_authorization`)
- Use Cloud Armor for DDoS protection
- Enable HTTPS with SSL certificates
- Use Internal Load Balancer for private access

**Upgrade to GKE**: For multi-model orchestration, see [serve-gke.md](./serve-gke.md)

---

## Resources

- [Compute Engine Documentation](https://cloud.google.com/compute/docs)
- [TorchServe Configuration](https://pytorch.org/serve/configuration.html)
- [TorchServe Management API](https://pytorch.org/serve/management_api.html)
- [GCE Pricing Calculator](https://cloud.google.com/products/calculator)
- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
