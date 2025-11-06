import os
import zipfile
import logging
from fastapi import FastAPI, Request
import torch
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global model variable
_model = None

@app.on_event("startup")
async def startup_event():
    """Load model at startup"""
    global _model

    try:
        logger.info("Starting model loading...")

        # Get storage URI from environment
        storage_uri = os.environ.get('AIP_STORAGE_URI')
        if not storage_uri:
            raise ValueError("AIP_STORAGE_URI environment variable not set")

        logger.info(f"Storage URI: {storage_uri}")

        # Download .mar file from GCS
        gcs = storage.Client()
        paths = storage_uri.replace('gs://', '').split('/')
        bucket = gcs.bucket(paths[0])
        mar_blob = bucket.blob('/'.join(paths[1:]) + '/model.mar')

        logger.info(f"Downloading model.mar from {mar_blob.name}...")
        mar_blob.download_to_filename('model.mar')
        logger.info("✅ Downloaded model.mar")

        # Extract .pt file from .mar
        logger.info("Extracting final_model_traced.pt from .mar...")
        with zipfile.ZipFile('model.mar', 'r') as zip_ref:
            zip_ref.extract('final_model_traced.pt')
        logger.info("✅ Extracted model file")

        # Load PyTorch model
        logger.info("Loading TorchScript model...")
        _model = torch.jit.load('final_model_traced.pt')
        _model.eval()
        logger.info("✅ Model loaded successfully and ready for predictions")

    except Exception as e:
        logger.error(f"❌ Failed to load model: {str(e)}")
        raise

# Health check endpoint - Vertex AI custom container format
@app.get("/v1/endpoints/{endpoint_id}/deployedModels/{deployed_model_id}", status_code=200)
def vertex_health(endpoint_id: str, deployed_model_id: str):
    """Health check endpoint for Vertex AI custom containers"""
    if _model is None:
        return {"status": "unhealthy", "reason": "model not loaded"}
    return {"status": "healthy"}

# Health check endpoint - Standard route (for compatibility)
@app.get(os.environ.get('AIP_HEALTH_ROUTE', '/health'), status_code=200)
def health():
    """Health check endpoint"""
    if _model is None:
        return {"status": "unhealthy", "reason": "model not loaded"}
    return {"status": "healthy"}

# Prediction endpoint - Vertex AI custom container format
@app.post("/v1/endpoints/{endpoint_id}/deployedModels/{deployed_model_id}:predict")
async def vertex_predict(endpoint_id: str, deployed_model_id: str, request: Request):
    """
    Prediction endpoint for Vertex AI custom containers.

    Vertex AI sends predictions to this path format, not the configured AIP_PREDICT_ROUTE.
    """
    return await predict_impl(request)

# Prediction endpoint - Standard route (for compatibility)
@app.post(os.environ.get('AIP_PREDICT_ROUTE', '/predict'))
async def predict(request: Request):
    """Prediction endpoint (standard route)"""
    return await predict_impl(request)

async def predict_impl(request: Request):
    """
    Core prediction implementation.

    Returns only anomaly scores and embeddings (2 fields)
    instead of all 13 model outputs, reducing response size by ~70%
    """
    global _model

    if _model is None:
        return {"error": "Model not loaded"}, 503

    try:
        body = await request.json()
        instances = torch.tensor(body["instances"], dtype=torch.float32)

        logger.info(f"Processing {len(instances)} instances")

        with torch.no_grad():
            full_output = _model(instances)

        # ✅ CUSTOM OUTPUT: Return only anomaly scores and embeddings
        # This reduces response size by ~70% compared to full output
        simplified = [
            {
                "anomaly_score": full_output["denormalized_MAE"][i].item(),
                "encoded": full_output["encoded"][i].tolist()
            }
            for i in range(len(instances))
        ]

        return {"predictions": simplified}

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return {"error": str(e)}, 500
