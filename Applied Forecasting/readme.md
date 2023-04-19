![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FApplied+Forecasting&dt=readme.md)

# /Applied Forecasting/readme.md

**Series Introduction: Applied Forecasting**

This series explores forecasting with Vertex AI, BigQuery ML, and additional open source frameworks.  Forecasting consist of following a measurement over time and exploring trends, the impact of seasonality (years, months, days, etc), holidays, and special events with the hope of using these insights to forecast into the near future.  Some method also incoporate observable measurements that impact demand to understand the relationships and make forecasting more accurate.

**Data Source: Citibike rentals in New York City**

This series will use Citibike rentals in New York city.  The bike stations near central park will be selected and the daily number bike trips that orignate from these stations will be followed over time.  This will illustrate some common forecasting issues due to new stations being introduced over time and some stations only have the most recent few months, or just weeks of data.  The data are found in the BigQuery Public datasets at: `bigquery-public-data.new_york.citibike_trips`.

<table style='text-align:center;vertical-align:middle' width="75%" cellpadding="1" cellspacing="0">
    <tr>
        <th colspan='2'>Citibike Stations</th>
    </tr>
    <tr>
        <td>
            <a href="https://www.google.com/maps/search/central+park+citibike+stations/@40.7794305,-73.9733652,14z" target="_blank">
                <img src="../architectures/notebooks/applied/forecasting/citibike_central_park.png" width="100%">
                <h4 align="center">Central Park Stations</h4>
            </a>
        </td>
        <td>
            <img src="../architectures/notebooks/applied/forecasting/citibike_central_park_s_6_ave.jpg" width="75%">
            <h4 align="center">Central Park S & 6th Avenue</h4>
        </td>
    </tr>
</table>

**Prerequisites**
- Environment Setup with: [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)

## Notebooks:
This list is in the suggested order of review for anyone getting an overview and learning about forecasting approaches throughout GCP.  It is also ok to pick a particular notebook of interest and if there are dependencies on prior notebooks they will be listed in the **prerequisites** section at the top of the notebook.  

>The notebooks are designed to be editable for trying with other data sources.  The same parameter names are used across the notebooks to also help when trying multiple methods on a custom data source.

- Data Source:
    - 1 - [BigQuery Time Series Forecasting Data Review and Preparation](./BigQuery%20Time%20Series%20Forecasting%20Data%20Review%20and%20Preparation.ipynb)
- BigQuery ML:
    - 2 - [BQML Univariate Forecasting with ARIMA+](./BQML%20Univariate%20Forecasting%20with%20ARIMA+.ipynb)
    - 3 - [BQML Multivariate Forecasting with ARIMA+ XREG](./BQML%20Multivariate%20Forecasting%20with%20ARIMA+%20XREG.ipynb)
    - 4 - [BQML Regression Based Forecasting](./BQML%20Regression%20Based%20Forecasting.ipynb)
- Vertex AI AutoML:
    - 5 - [Vertex AI AutoML Forecasting - GCP Console (no code)](./Vertex%20AI%20AutoML%20Forecasting%20-%20GCP%20Console%20(no%20code).ipynb)
    - 6 - [Vertex AI AutoML Forecasting - Python client](./Vertex%20AI%20AutoML%20Forecasting%20-%20Python%20client.ipynb)
    - 7 - [Vertex AI AutoML Forecasting - multiple simultaneously](./Vertex%20AI%20AutoML%20Forecasting%20-%20multiple%20simultaneously.ipynb)
- Vertex AI Other:
    - 8 - [Vertex AI Seq2Seq+ Forecasting - Python client](./Vertex%20AI%20Seq2Seq+%20Forecasting%20-%20Python%20client.ipynb)
    - 9 - [Vertex AI Temporal Fusion Transformer Forecasting - Python client](./Vertex%20AI%20Temporal%20Fusion%20Transformer%20Forecasting%20-%20Python%20client.ipynb)
- Vertex AI Custom Models:
    - 10 - [Vertex AI Custom Model - Prophet - In Notebook](./Vertex%20AI%20Custom%20Model%20-%20Prophet%20-%20In%20Notebook.ipynb)
    - 11 - [Vertex AI Custom Model - Prophet - Custom Job With Custom Container](./Vertex%20AI%20Custom%20Model%20-%20Prophet%20-%20Custom%20Job%20With%20Custom%20Container.ipynb)
- Vertex AI Pipelines:
    - 12 - [Vertex AI Pipelines - BQML ARIMA+](./Vertex%20AI%20Pipelines%20-%20BQML%20ARIMA+.ipynb)
    - 13 - [Vertex AI Pipelines - Prophet](./Vertex%20AI%20Pipelines%20-%20Prophet.ipynb)
    - 14 - [Vertex AI Pipelines - Forecasting Tournament with Kubeflow Pipelines (KFP)](./Vertex%20AI%20Pipelines%20-%20Forecasting%20Tournament%20with%20Kubeflow%20Pipelines%20(KFP).ipynb)
    - **Forecasting Pipelines** For more detailed starting points using Pipelines for forecasting I highly recommend [this repository](https://github.com/tottenjordan/vertex-forecas-repo) from coworker Jordan Totten!



**Notes**


---
ToDo:
- [ ] full update for 10
- [ ] full update for 11
- [ ] 13 waiting on fix to complete update
- [ ] full update for 14
    - [ ] Turn into solution: register components to artifact registry and build pipelines dynamically
    - [ ] add 3 ARIMA_PLUS_XREG - wait for GA and time_series_id parameter
    - [ ] add 4
    - [ ] add 8
    - [ ] add 9
- Additions to make
    - 3 update after preview -> GA
        - add comparison to 2: make it optional
    - more methods in the custom models section?
        - XGBoost like 4
        - sktime
        - StatsForecast with Fugue
        - GluonTS
        - Darts
- Issues To Investigate:
    - 11 complete when bug is fixed
    - 12 and 13 - Clean up link to bucket, staging bucket for GCS. Understand what goes where.
    - 1,2,3,4 Consider printing all BQ query's out so they can be copy/pasted to console. 
    - 4 address horizon predictions and related challenges
    - 5 through 9 - Batch predictions - carry down known covariates into horizon
    - 5 through 9 - explanations?
    - 5 through 9 - get evaluations from Model Registry
    - 10 and 11 - add evaluations to model registry (see 05 series)
- thoughts:
    - Price optimization example like: https://cloud.google.com/blog/products/ai-machine-learning/price-optimization-using-vertex-ai-forecast
---











