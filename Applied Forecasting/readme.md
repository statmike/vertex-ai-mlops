# Applied Forecasting
This series of notebooks highlights the use of Vertex AI for forecasting workflows.  These use techniques in BigQuery ML (BQML), Vertex AI AutoML Forecasting, and custom methods like OSS Prophet.

**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)

## Notebooks:
- [1 - BigQuery Time Series Forecasting Data Review and Preparation](./1%20-%20BigQuery%20Time%20Series%20Forecasting%20Data%20Review%20and%20Preparation.ipynb)
- [2 - BQML Univariate Forecasting with ARIMA+](./2%20-%20BQML%20Univariate%20Forecasting%20with%20ARIMA+.ipynb)
- [3 - Vertex AI AutoML Forecasting - GCP Console (no code)](./3%20-%20Vertex%20AI%20AutoML%20Forecasting%20-%20GCP%20Console%20(no%20code).ipynb)
- [4 - Vertex AI AutoML Forecasting - Python client](./4%20-%20Vertex%20AI%20AutoML%20Forecasting%20-%20Python%20client.ipynb)
- [5 - Vertex AI AutoML Forecasting - multiple scenarios](./5%20-%20Vertex%20AI%20AutoML%20Forecasting%20-%20multiple%20scenarios.ipynb)
- [6 - Vertex AI Custom Model - Forecasting with Prophet - In Notebook](./6%20-%20Vertex%20AI%20Custom%20Model%20-%20Forecasting%20with%20Prophet%20-%20In%20Notebook.ipynb)
- [7 - Vertex AI Custom Model - Forecasting with Prophet - Custom Job With Custom Container](./7%20-%20Vertex%20AI%20Custom%20Model%20-%20Forecasting%20with%20Prophet%20-%20Custom%20Job%20With%20Custom%20Container.ipynb)
- [8 - Vertex AI Pipelines - Forecasting Tournament - BQML + AutoML + Prophet](./8%20-%20Vertex%20AI%20Pipelines%20-%20Forecasting%20Tournament%20-%20BQML%20+%20AutoML%20+%20Prophet.ipynb)

**Notes**

---
ToDo:
- [X] add prereq to readme
- [X] Update references to Service Account and check for permissions - reference the 00 notebooks new section for correct setup
- [IP] Describe the data source in the readme file
- [IP] full update pass to bring this project up to standards of 05 and others:
    - formatting, links to console for review, setup (installs), gcs and bq naming follows SERIES, EXPERIMENT
    - parameterize examples with consideration for use cases where dataset may have too many time series to plot individually - subset of total with parameter and user specified series as a list
    - add Bokeh plot to each example
    - [ ] 1
    - [ ] 2
    - [ ] 3
    - [ ] 4
    - [ ] 5
    - [ ] 6
    - [ ] 7
    - [ ] 8
- [ ] Turn 8 into solution: register components to artifact registry and build pipelines dynamically












