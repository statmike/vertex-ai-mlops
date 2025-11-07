FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-jdk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install TorchServe and dependencies
RUN pip install --no-cache-dir \
    torchserve \
    torch-model-archiver \
    torch-workflow-archiver \
    torch \
    torchvision \
    google-cloud-storage \
    pyyaml

# Create TorchServe directories
RUN mkdir -p /home/model-server/model-store /home/model-server/tmp

WORKDIR /home/model-server

# Create TorchServe configuration
RUN echo "inference_address=http://0.0.0.0:8080" > config.properties && \
    echo "management_address=http://0.0.0.0:8081" >> config.properties && \
    echo "metrics_address=http://0.0.0.0:8082" >> config.properties && \
    echo "model_store=/home/model-server/model-store" >> config.properties && \
    echo "load_models=all" >> config.properties && \
    echo "disable_token_authorization=true" >> config.properties

# Create startup script that downloads model from GCS and starts TorchServe
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Downloading model from GCS..."\n\
python -c "from google.cloud import storage; \\\n\
    client = storage.Client(project=\047statmike-mlops-349915\047); \\\n\
    bucket = client.bucket(\047statmike-mlops-349915\047); \\\n\
    blob = bucket.blob(\047frameworks/pytorch-autoencoder/torchserve-cloud-run/pytorch_autoencoder.mar\047); \\\n\
    blob.download_to_filename(\047/home/model-server/model-store/pytorch_autoencoder.mar\047)"\n\
echo "Model downloaded successfully"\n\
echo "Starting TorchServe..."\n\
torchserve --start --ts-config config.properties --models pytorch_autoencoder=pytorch_autoencoder.mar --foreground\n\
' > /home/model-server/start.sh && chmod +x /home/model-server/start.sh

EXPOSE 8080

CMD ["/home/model-server/start.sh"]
