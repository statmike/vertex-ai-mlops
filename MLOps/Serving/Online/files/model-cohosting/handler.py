import json
import inspect
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from ts.torch_handler.base_handler import BaseHandler


class SentimentHandler(BaseHandler):

    def initialize(self, context):
        properties = context.system_properties
        model_dir = properties.get("model_dir", ".")

        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model.eval()
        self.id2label = self.model.config.id2label

        # Cache the set of parameter names the model's forward() accepts.
        # DistilBERT doesn't take token_type_ids; BERT does — this lets the
        # same handler work for both without hard-coding model differences.
        self._model_params = set(
            inspect.signature(self.model.forward).parameters.keys()
        )

    def handle(self, data, context):
        """Override handle directly to bypass the request envelope.

        Vertex AI sends instances as dicts with a "body" key containing the
        JSON-serialized prediction payload ({"instances": [...]}).  TorchServe
        may also pass raw strings or bytes depending on the call path.  This
        method handles all variants.
        """
        texts = []
        for row in data:
            # Extract the raw body from whichever wrapper TorchServe uses
            if isinstance(row, dict):
                body = row.get("body") or row.get("data") or ""
            elif isinstance(row, (bytes, bytearray)):
                body = row.decode("utf-8")
            else:
                body = row

            if isinstance(body, (bytes, bytearray)):
                body = body.decode("utf-8")

            # The body may be a JSON string — e.g. '{"instances": ["text"]}'
            if isinstance(body, str):
                try:
                    parsed = json.loads(body)
                    if isinstance(parsed, dict) and "instances" in parsed:
                        texts.extend([str(t) for t in parsed["instances"]])
                        continue
                    elif isinstance(parsed, list):
                        texts.extend([str(t) for t in parsed])
                        continue
                    elif isinstance(parsed, str):
                        body = parsed
                except (json.JSONDecodeError, ValueError):
                    pass

            texts.append(str(body))

        if not texts:
            return []

        tokenized = self.tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True, max_length=128,
        )

        # Only pass keys the model's forward() actually accepts
        # (e.g. DistilBERT doesn't take token_type_ids, BERT does)
        inputs = {k: v for k, v in tokenized.items() if k in self._model_params}

        with torch.no_grad():
            outputs = self.model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=1)

        results = []
        for prob in probs:
            idx = prob.argmax().item()
            results.append({
                "label": self.id2label[idx],
                "score": round(prob[idx].item(), 6),
            })
        return results
