import torch
import json
import logging

logger = logging.getLogger(__name__)

# Feature names in correct order (must match training data)
# This is used to convert BigQuery ML dict format to array format
FEATURE_NAMES = [
    'Time', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9',
    'V10', 'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 'V19',
    'V20', 'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28', 'Amount'
]

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

        Supports two input formats:
        1. Array format (from SDK/REST API): [[val1, val2, ...]]
        2. Dict format (from BigQuery ML): [{"Time": val1, "V1": val2, ...}]

        Args:
            data: List where each element is a request body (one per instance)

        Returns:
            Tensor ready for inference [batch_size, num_features]
        """
        instances = []

        for row in data:
            # Each row is one instance
            # It could be: raw list, bytes, string, or dict with 'body' key

            if isinstance(row, dict):
                # Try to extract the actual data
                instance = row.get("body") or row.get("data") or row
            else:
                instance = row

            # Decode if bytes
            if isinstance(instance, (bytes, bytearray)):
                instance = instance.decode("utf-8")

            # Parse JSON string
            if isinstance(instance, str):
                instance = json.loads(instance)

            # Now handle the instance based on its format
            if isinstance(instance, dict):
                # Dict format (from BigQuery ML) - convert to array using feature order
                try:
                    instance_array = [instance[feat] for feat in FEATURE_NAMES]
                    instances.append(instance_array)
                    logger.debug(f"Converted dict to array with {len(instance_array)} features")
                except KeyError as e:
                    logger.error(f"Missing feature in dict: {e}. Available keys: {list(instance.keys())}")
                    raise ValueError(f"Missing required feature: {e}")
            elif isinstance(instance, list):
                # Array format (from SDK/REST API) - use directly
                if all(isinstance(x, (int, float)) for x in instance):
                    if len(instance) != len(FEATURE_NAMES):
                        logger.warning(f"Expected {len(FEATURE_NAMES)} features, got {len(instance)}")
                    instances.append(instance)
                else:
                    # Nested array - flatten if needed
                    logger.warning(f"Unexpected nested structure: {type(instance)}")
                    instances.append(instance)
            else:
                logger.error(f"Unexpected instance type: {type(instance)}, value: {instance}")
                raise ValueError(f"Instance must be a list or dict, got {type(instance)}")

        # Convert to tensor [batch_size, 30]
        logger.info(f"Preprocessing {len(instances)} instances")
        tensor = torch.tensor(instances, dtype=torch.float32).to(self.device)
        logger.info(f"Input tensor shape: {tensor.shape}")
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
        # Determine batch size
        batch_size = None
        for key, value in inference_output.items():
            if torch.is_tensor(value):
                if value.dim() > 0:
                    batch_size = value.shape[0]
                    break

        if batch_size is None:
            batch_size = 1

        logger.info(f"Postprocessing {batch_size} predictions")

        # Build list of predictions (one dict per instance)
        result_dicts = []
        for i in range(batch_size):
            pred = {}
            for key, value in inference_output.items():
                if torch.is_tensor(value):
                    if value.dim() == 0:
                        # Scalar
                        pred[key] = value.item()
                    elif value.dim() == 1:
                        # 1D tensor - one value per instance
                        pred[key] = value[i].item()
                    else:
                        # 2D+ tensor - one row per instance
                        pred[key] = value[i].cpu().numpy().tolist()
                else:
                    pred[key] = value
            result_dicts.append(pred)

        return result_dicts

# Instantiate handler
_service = ModelHandler()

def handle(data, context):
    """TorchServe entry point"""
    try:
        if not _service.initialized:
            _service.initialize(context)

        if data is None:
            return None

        logger.info(f"Received {len(data)} request(s)")

        # Preprocess
        input_tensor = _service.preprocess(data)

        # Inference
        output = _service.inference(input_tensor)

        # Postprocess
        return _service.postprocess(output)

    except Exception as e:
        logger.error(f"Error in handle: {str(e)}", exc_info=True)
        raise
