![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FDev&file=04g+Notes+Holder.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Dev/04g%20Notes%20Holder.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
### Notes (in-progress and needs placement)

**Method References**

- [BigQuery ML ARIMA+](https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-create-time-series)
- [Vertex AI AutoML Forecasting](https://cloud.google.com/vertex-ai/docs/tabular-data/forecasting/overview)
    - [Python Client](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.AutoMLForecastingTrainingJob)
- [Prophet](https://facebook.github.io/prophet/docs/quick_start.html#python-api)

**source data for forecasting:**

- Required:
    - At a minimum these columns types are needed:
        - `time_column` - identifies the date/time of records
        - `target_column` - the metric being tracked over time that needs forecasting
        - `time_series_identifier_column` - the column that identifies the individual series of target values being tracked over time
            - examples: product, store, region, location, sku
- Optional and only used by some methods:
    - Some forecasting methods allow the inclusion of additional covariates like:
        - `unavailable_at_forecast_columns` - a list of columns whose value is know at forecast time
            - at a minimum this should be [`target_column`]
            - examples: weather, traffic, view, number in carts, price rank/ratio
        - `available_at_forecast_columns` - a list of columns whose value is not yet known at forecast time
            - at a minimum this should be [`time_column`]
            - examples: quantity available, holiday, promotion, discount, price
        - `time_series_attribute_columns` - a list of columns with fixed attributes of the `time_series_identifier_column` value
            - characteristics of the time series

**Forecasting Operational Paramerters:**

- `dataset` - the name of the dataset to use for forecasting
- `data_granularity_unit` - the time aggregation level is one of minute, hour, day, week, month, year
    - `data_granularity_count` - 1 unless `data_granularity_unit` is minute then can be 1, 5, 10, 15, or 30
- `forecast_horizon` - number of date/time units (`data_granularity_unit`) to forecast into the future (beyond the test split)
- `predefined_split_column_name` - column with predefined values of 'TRAIN', 'VALIDATE', 'TEST'
    - OR set split fracts (without either of these specified, AutoML Forecasting will choose and 80/10/10 split by default)
        - `training_fraction_split` - the proportion, (0,1) to allocate to training - the earliest rows
        - `validation_fraction_split` - the proportion, (0,1) to allocate to validation - dates/times between training and test - some methods only have training
        - `test_fraction_split` - the proportion, (0,1) to allocate to test - the latest rows
        - `timestamp_split_column_name` - column name with date/time to be used for creating the splits
     - more info on splits:
         - [Vertex AI AutoML Forecasting](https://cloud.google.com/vertex-ai/docs/tabular-data/forecasting/prepare-data#split)
         - [BigQuery ML (BQML) ARIMA+](https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-create-time-series)
             - This method does not use data splits as it fits ARIMA based models.  Use the 'TRAIN' and 'VALIDATE' splits set for other methods and then include the length of the 'TEST' data with the forecast horizon.
         - [Prophet](https://facebook.github.io/prophet/docs/quick_start.html#python-api)
             - This method does not use data splits.  Use the 'TRAIN' and 'VALIDATE' splits set for other methods and then include the length of the 'TEST' split with the forecast horizon.
    
**Method Specific Parameters:**

- Vertex AI AutoML Forecasting:
    - `context_window` - the number of `data_granularity_units` into the past used for a single point in time training or prediction
        - Vertex AI AutoML Forecasting default is 0 which represents a cold start
        - more information on [consideration for setting context window](https://cloud.google.com/vertex-ai/docs/datasets/bp-tabular#context-window)
    - `optimization_objective` - the objective function the model optimizes towards over the validation date
        - [methods](https://cloud.google.com/vertex-ai/docs/tabular-data/forecasting/train-automl-model#optimization_objectives_for_tabular_automl_forecast_models)
        - `quantiles` - a list of up to 5 quantile values in the range 0 to 1 for use when `optimzation_objective` = 'minimize-quantile-loss' 
            - using [0.5] is similar to `optimization_objective` = 'minimize-mae'
    - `weight_column` - by default all data is weighted equally but this parameter can list a column with weights (0-10000) to allow higher weights to have a larger impact on the model
    - Parameters Managed By The Code (or defaults):
        - `export_evaluated_data_items` - True/False to export 'TEST" split predictions to a BigQuery Table
        - `export_evaluated_data_items_bigquery_destination_uri` - Provide the URI for a BigQuery table in the form 'bq://<project_id>:<dataset_id>:<table>'
        - `export_evaluated_data_items_override_destination` - True/False to replace the table if it already exists
        - `validation_options` - indicator for how to proceed if validation fails with options 'fail-pipeline' (default) or 'ignore-validation'
        - `budget_milli_node_hours` - the time budget for creating the model in range 1000-72000 where 1000 is 1 hour
        - `model_display_name` - a string with the desired model display name by Vertex AI made up of 128 UTF-8 characters
        - `model_labels` - a dictionary of key:value pars for labels to use for the model in Vertex AI made up of as many as 64 characters (lowercase, numeric, _, -)
        - `sync` - True/False to execute synchnously
        - `create_request_timeout` - a timeout for the request provided in seconds
    - `additional_experiments` - can be used to specify hierarchical forecasting (time and/or group)
- BigQuery ML ARIMA+:
    - Parameters:
        - `time_series_timestamp_col` - column name that identifies the date/time of records
        - `time_series_data_col` -  column name that records the metric being tracked over time that needs forecasting
        - `time_series_id_col` - the column that identifies the individual series of target values being tracked over time 
        - `holiday_region` - 'US' sets the holiday region and i used for daily or weekly aggregation with series longer than a year
            - [possible values](https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-create-time-series#holiday_region)
    - Parameters Managed By The Code (or defaults):
        - `model_type` - set to 'ARIMA_PLUS' to enable forecasting method
        - `AUTO_ARIMA` - set to 'TRUE' to automatically determine the best (p,d,q) 
        - `auto_arima_max_order` - 5 (default) or set to one of (1,2,3,4,5)and determines the max value for p+q
        - `horizon` - set to include the length of the 'TEST' split and the specified horizon {forecast_test_length}+{forecast_horizon_length}
- Prophet:
    - Currently implemented parameters:
        - weekly_seasonality=True
        - yearly_seasonality=True
        - add_country_holidays(country_name='US')
    


    
TODO:
- [] redo with parameterized variables
    - [] update data architecture chart
- [] AutoML add covars
- [] AutoML add hierachical
- [] Prophet add covars
- [] Prophet add hierarchical ???
- [] expose all parameters
    - [] AutoML
    - [] BQML
    - [] Prophet
- [] Champion Ensemble
    - [] Vizier Weight methods to optimize MAPE
- [] Chart for splits with prediction Timeline infor for AutoML method
- [] Tuning
    - Vizier for AutoML parameters
    - Vizier for Prophet - see crossvalidation 
        - cross val: https://facebook.github.io/prophet/docs/diagnostics.html#cross-validation
        - tune parms: https://rdrr.io/cran/modeltime/man/prophet_params.html#:~:text=The%20main%20parameters%20for%20Prophet,%22%2C%20or%20%22logistic%22.&text=changepoint_range%20%3A%20The%20range%20affects%20how,the%20more%20flexible%20the%20trend.
    - Vizier for BQML???
    
