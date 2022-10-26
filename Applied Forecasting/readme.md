# Applied Forecasting
This series of notebooks highlights the use of Vertex AI for forecasting workflows.  These use techniques in BigQuery ML (BQML), Vertex AI AutoML Forecasting, and custom methods like OSS Prophet.

This series will use bike Citibike rentals in New York city. The bike stations near central park will be selected and the daily number bike trips that orignate from these stations will be followed over time. This will be complicated as new stations are introduced over time and some stations only have the most recent few months, or just weeks of data.  The data are found in the BigQuery Public datasets at: `bigquery-public-data.new_york.citibike_trips`.

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
- [X] Describe the data source in the readme file
- [X] 01 Data review in BigQuery
    - [X] Move BigQuery client examples to Tips/BigQuery - Python Client
    - [X] format overview section like 03/05 and others (not using headers)
    - [X] parameterize SERIES and EXPERIMENT to replace DATANAME and NOTEBOOK
    - [X] reformat query to not use bq_runner, just simple bq.query(query)
    - [X] add input `viz_limit = 12` and use throughout to limit visuzlization (and pandas) number of time_series displayed
    - [X] parameterize time series variables like 8: TIME_COLULMN, TARGET_COLUMN, SERIES_COLUMN
    - [ ] add bokeh plot
- [IP] 02 BQML Univariate Forecasting
    - [X] format overview section like 03/05 and others (not using headers)
    - [X] parameterize SERIES and EXPERIMENT to replace DATANAME and NOTEBOOK
    - [X] reformat query to not use bq_runner, just simple bq.query(query)
    - [X] add input `viz_limit = 12` and use throughout to limit visuzlization (and pandas) number of time_series displayed
    - [X] parameterize time series variables like 8: TIME_COLULMN, TARGET_COLUMN, SERIES_COLUMN
    - [ ] add bokeh plot
- [IP] full update pass to bring this project up to standards of 05 and others:
    - [ ] formatting, links to console for review, setup (installs), gcs and bq naming follows SERIES, EXPERIMENT
    - [ ] parameterize examples with consideration for use cases where dataset may have too many time series to plot individually - subset of total with parameter and user specified series as a list
    - [ ] add Bokeh plot to each example
- [ ] Turn 8 into solution: register components to artifact registry and build pipelines dynamically












