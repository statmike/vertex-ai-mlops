![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2F02+-+Vertex+AI+AutoML&dt=readme.md)

# 02 - Vertex AI AutoML
Accelerated ML with [Vertex AI AutoML](https://cloud.google.com/vertex-ai/docs/start/automl-model-types)

Vertex AI AutoML accelerate the workflow of creating an ML model by preprocessing the data and choosing model architectures for you, even testing multiple and creating ensembles to achieve a best model.  This is available for ML models on text, image, video, and tabular data.  

**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)
- [01 - BigQuery - Table Data Source.ipynb](../01%20-%20Data%20Sources/01%20-%20BigQuery%20-%20Table%20Data%20Source.ipynb)

## This series of notebooks will introduce Vertex AI AutoML with a focus on Tabular data Classification Methods.
- 02a - Vertex AI - AutoML in GCP Console (no code).ipynb
- 02b - Vertex AI - AutoML with clients (code).ipynb
- 02c - Vertex AI > Pipelines - AutoML with clients (code) in automated pipeline.ipynb

**Notes:**


**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)
- [01 - BigQuery - Table Data Source.ipynb](../01%20-%20Data%20Sources/01%20-%20BigQuery%20-%20Table%20Data%20Source.ipynb)

---
ToDo:
- [X] add prereq to readme
- [X] Update references to Service Account and check for permissions - reference the 00 notebooks new section for correct setup
- [IP] Add TabNet example
    - [IP] Include TabNet with Hyperparameter Tuning Example
    - [IP] Online and Batch Predictions
    - [IP] Explainability with feature masks
- [ ] Refinement+Update Pass
    - General
        - [ ] Update readme with hyperlinks
        - [ ] Update notebook naming
            - [ ] Update links in YouTube Video descriptions        
    - [ ] 02a
    - [ ] 02b
    - [ ] 02c    
- [ ] Add Multiple AutoML in parallel model example - see applied forecasting
- [ ] Add AutoML Workflow examples
- [ ] 02d - add fetching logs to see which models were tried to create the final model
- [ ] show how to interpret log of AutoML jobs: https://cloud.google.com/vertex-ai/docs/tabular-data/classification-regression/logging