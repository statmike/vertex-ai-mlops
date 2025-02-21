# a simple passthrough of instance to predictions

# packages
import os
from fastapi import FastAPI, Request
import numpy as np

# clients
app = FastAPI()

# Define function for health route
@app.get(os.environ['AIP_HEALTH_ROUTE'], status_code=200)
def health():
    return {}

# Define function for prediction route
@app.post(os.environ['AIP_PREDICT_ROUTE'])
async def predict(request: Request):
    # await the request
    body = await request.json()
    
    # parse the request
    instances = body["instances"]
    
    # return the received inputs as the "predictions" - a simple pass through
    predictions = instances

    # this returns just the predicted probabilities:
    return {"predictions": predictions}
