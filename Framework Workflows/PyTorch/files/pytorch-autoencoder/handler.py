import torch
import json
import logging

logger = logging.getLogger(__name__)

# TorchServe handler following standard format
class ModelHandler:
    def __init__(self):
        self.model = None
        self.initialized = False

    def initialize(self, context):
        """Initialize model"""
        properties = context.system_properties
        model_dir = properties.get("model_dir")

        # Determine device
        if torch.cuda.is_available():
            self.device = torch.device("cuda:" + str(properties.get("gpu_id", 0)))
        else:
            self.device = torch.device("cpu")

        # Load TorchScript model
        model_path = f"{model_dir}/final_model_traced.pt"
        self.model = torch.jit.load(model_path, map_location=self.device)
        self.model.eval()

        self.initialized = True
        logger.info(f"Model loaded successfully on {self.device}")

    def preprocess(self, data):
        """
        Preprocess input data for inference.

        Args:
            data: List of input data, where each item is the request body

        Returns:
            Tensor ready for inference
        """
        # data is a list of request bodies
        instances = []

        for row in data:
            # row is the request body (could be dict with "body" key or direct data)
            if isinstance(row, dict):
                # Try to get body or data
                input_data = row.get("body") or row.get("data") or row
            else:
                input_data = row

            # If it's bytes, decode it
            if isinstance(input_data, (bytes, bytearray)):
                input_data = input_data.decode("utf-8")

            # If it's a string, parse JSON
            if isinstance(input_data, str):
                input_data = json.loads(input_data)

            # Extract instances array if present
            if isinstance(input_data, dict) and "instances" in input_data:
                instances.extend(input_data["instances"])
            elif isinstance(input_data, list):
                instances.extend(input_data)
            else:
                instances.append(input_data)

        # Convert to tensor
        tensor = torch.tensor(instances, dtype=torch.float32).to(self.device)
        return tensor

    def inference(self, data):
        """Run inference"""
        with torch.no_grad():
            output = self.model(data)
        return output

    def postprocess(self, inference_output):
        """
        Convert model output to JSON-serializable format.

        Returns:
            List of predictions (one dict per instance)
        """
        # The model returns a dict of tensors
        # We need to convert this to a list of dicts (one per instance)

        batch_size = None
        result_dicts = []

        # Determine batch size from first output
        for key, value in inference_output.items():
            if torch.is_tensor(value):
                if value.dim() > 0:
                    batch_size = value.shape[0]
                    break

        if batch_size is None:
            batch_size = 1

        # Build list of predictions (one dict per instance)
        for i in range(batch_size):
            pred = {}
            for key, value in inference_output.items():
                if torch.is_tensor(value):
                    # Extract value for this instance
                    if value.dim() == 0:
                        # Scalar
                        pred[key] = value.item()
                    elif value.dim() == 1:
                        # 1D tensor - this is for the batch
                        pred[key] = value[i].item()
                    else:
                        # 2D+ tensor - take the row for this instance
                        pred[key] = value[i].cpu().numpy().tolist()
                else:
                    pred[key] = value
            result_dicts.append(pred)

        return result_dicts

# Instantiate handler
_service = ModelHandler()

def handle(data, context):
    """TorchServe entry point"""
    if not _service.initialized:
        _service.initialize(context)

    if data is None:
        return None

    # Preprocess
    input_tensor = _service.preprocess(data)

    # Inference
    output = _service.inference(input_tensor)

    # Postprocess
    return _service.postprocess(output)
