import torch
import torch.nn as nn
import json
import logging

logger = logging.getLogger(__name__)

class AutoencoderHandler:
    def __init__(self):
        self.model = None
        self.device = None
        self.initialized = False

    def initialize(self, context):
        """Initialize model and device"""
        properties = context.system_properties
        self.device = torch.device(
            "cuda:" + str(properties.get("gpu_id"))
            if torch.cuda.is_available()
            else "cpu"
        )

        # Load model
        model_dir = properties.get("model_dir")
        model_path = f"{model_dir}/final_model.pt"

        # Note: This expects the model class to be available
        # In production, you would include the model definition in the .mar
        self.model = torch.jit.load(model_path, map_location=self.device)
        self.model.eval()

        self.initialized = True
        logger.info("Model initialized successfully")

    def preprocess(self, requests):
        """Convert HTTP request to tensor"""
        instances = []
        for request in requests:
            data = request.get("data") or request.get("body")
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8")

            # Parse JSON
            if isinstance(data, str):
                data = json.loads(data)

            # Extract instances
            if "instances" in data:
                instances.extend(data["instances"])
            else:
                instances.append(data)

        # Convert to tensor
        input_tensor = torch.tensor(instances, dtype=torch.float32, device=self.device)
        return input_tensor

    def inference(self, input_tensor):
        """Run model inference"""
        with torch.no_grad():
            output = self.model(input_tensor)
        return output

    def postprocess(self, inference_output):
        """Convert model output to JSON"""
        # Convert all tensor values to lists
        result = {}
        for key, value in inference_output.items():
            result[key] = value.cpu().numpy().tolist()

        return [result]

# TorchServe entry point
_service = AutoencoderHandler()

def handle(data, context):
    if not _service.initialized:
        _service.initialize(context)

    if data is None:
        return None

    input_tensor = _service.preprocess(data)
    output = _service.inference(input_tensor)
    return _service.postprocess(output)
