
import json
import torch
import inspect
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from ts.torch_handler.base_handler import BaseHandler

class SentimentHandler(BaseHandler):
    def initialize(self, context):
        self.manifest = context.manifest
        model_dir = context.system_properties.get("model_dir")
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model.eval()
        self.id2label = self.model.config.id2label
        # Get the model's accepted forward() arguments so we can filter tokenizer output
        self.forward_params = set(inspect.signature(self.model.forward).parameters.keys())

    def preprocess(self, data):
        texts = []
        for row in data:
            body = row.get("body") or row.get("data")
            if isinstance(body, (bytes, bytearray)):
                body = body.decode("utf-8")
            if isinstance(body, str):
                body = json.loads(body)
            text = body.get("text", body.get("instances", [{}])[0].get("text", ""))
            texts.append(text)
        encoded = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
        # Only pass keys the model accepts (e.g. DistilBERT does not use token_type_ids)
        return {k: v for k, v in encoded.items() if k in self.forward_params}

    def inference(self, inputs):
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.logits

    def postprocess(self, outputs):
        probs = torch.nn.functional.softmax(outputs, dim=1)
        results = []
        for prob in probs:
            idx = prob.argmax().item()
            results.append({"label": self.id2label[idx], "score": prob[idx].item()})
        return results
