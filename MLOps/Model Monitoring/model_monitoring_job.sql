DECLARE drift_anomalies ARRAY<STRUCT<input STRING, visualization_link STRING>>;
DECLARE drift STRING;
DECLARE skew_anomalies ARRAY<STRUCT<input STRING, visualization_link STRING>>;
DECLARE skew STRING;

# Monitor Drift:
SET drift_anomalies = (
    SELECT ARRAY_AGG(STRUCT(input, visualization_link))
    FROM ML.VALIDATE_DATA_DRIFT(
        (# base
            SELECT * EXCEPT(instance_timestamp)
            FROM `statmike-mlops-349915.bqml_model_monitoring.serving_all`
            WHERE
                DATE(instance_timestamp) >= DATE_SUB(@run_date, INTERVAL 2 WEEK)
                AND
                DATE(instance_timestamp) < DATE_SUB(@run_date, INTERVAL 1 WEEK)
        ),
        (# compare
            SELECT * EXCEPT(instance_timestamp)
            FROM `statmike-mlops-349915.bqml_model_monitoring.serving_all`
            WHERE DATE(instance_timestamp) >= DATE_SUB(@run_date, INTERVAL 1 WEEK)
        ),
        STRUCT(
            0.4 AS categorical_default_threshold,
            0.4 AS numerical_default_threshold
        )
        , MODEL `statmike-mlops-349915.bqml_model_monitoring.classify_species_logistic`
    )
    WHERE is_anomaly = True
);
IF(ARRAY_LENGTH(drift_anomalies) > 0) THEN
    SET drift = CONCAT(
        "\n\tDrift: detected in the following features",
        (
            SELECT STRING_AGG(
                CONCAT(
                    '\n\t\t',
                    da.input,
                    ': ',
                    da.visualization_link
                )
            )
            FROM UNNEST(drift_anomalies) as da
        )
    );
    ELSE SET drift = '\n\tDrift: not detected.';
END IF;

# Monitor Skew
SET skew_anomalies = (
    SELECT ARRAY_AGG(STRUCT(input, visualization_link))
    FROM ML.VALIDATE_DATA_SKEW(
        # base
        MODEL `statmike-mlops-349915.bqml_model_monitoring.classify_species_rf`,
        (# compare
            SELECT * EXCEPT(instance_timestamp)
            FROM `statmike-mlops-349915.bqml_model_monitoring.serving_all`
            WHERE DATE(instance_timestamp) >= DATE_SUB(@run_date, INTERVAL 1 WEEK)
        )
        ,STRUCT(TRUE AS enable_visualization_link)
    )
    WHERE is_anomaly = True
);
IF(ARRAY_LENGTH(skew_anomalies) > 0) THEN
    SET skew = CONCAT(
        "\n\tSkew: detected in the following features",
        (
            SELECT STRING_AGG(
                CONCAT(
                    '\n\t\t',
                    sa.input,
                    ': ',
                    sa.visualization_link
                )
            )
            FROM UNNEST(skew_anomalies) as sa
        )
    );
    ELSE SET skew = '\n\tSkew: not detected.';
END IF;

# Prepare Alert
IF(ARRAY_LENGTH(drift_anomalies) > 0 OR ARRAY_LENGTH(skew_anomalies) > 0) THEN
    BEGIN
        DECLARE train_accuracy FLOAT64;
        DECLARE recent_accuracy FLOAT64;
        DECLARE retrain_accuracy FLOAT64;

        # get current models evaluation metrics: accuracy
        SET train_accuracy = (
            SELECT accuracy
            FROM ML.EVALUATE (
                MODEL `statmike-mlops-349915.bqml_model_monitoring.classify_species_rf`
            )
        );

        # get current models recent evaluation metrics: accuracy
        SET recent_accuracy = (
            SELECT accuracy
            FROM ML.EVALUATE (
                MODEL `statmike-mlops-349915.bqml_model_monitoring.classify_species_rf`,
                (
                    SELECT *
                    FROM `statmike-mlops-349915.bqml_model_monitoring.serving`
                    WHERE DATE(instance_timestamp) >= DATE_SUB(@run_date, INTERVAL 1 WEEK) 
                )
            )
        );

        # retrain the model
        CREATE OR REPLACE MODEL `statmike-mlops-349915.bqml_model_monitoring.classify_species_rf`
            TRANSFORM(
                ML.ROBUST_SCALER(body_mass_g) OVER() AS body_mass_g,
                ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
                ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
                ML.QUANTILE_BUCKETIZE(flipper_length_mm, 3) OVER() AS flipper_length_mm,
                ML.IMPUTER(sex, 'most_frequent') OVER() AS sex,
                ML.IMPUTER(island, 'most_frequent') OVER() AS island,
                species
            )
            OPTIONS(
                MODEL_TYPE = 'RANDOM_FOREST_CLASSIFIER',
                INPUT_LABEL_COLS = ['species'],

                # data specifics
                DATA_SPLIT_METHOD = 'AUTO_SPLIT',

                # model specifics
                AUTO_CLASS_WEIGHTS = FALSE,
                NUM_PARALLEL_TREE= 150,
                TREE_METHOD = 'HIST',
                SUBSAMPLE = 0.85,
                COLSAMPLE_BYTREE = 0.9,
                ENABLE_GLOBAL_EXPLAIN = TRUE,

                # register model in Vertex AI For Online Serving
                MODEL_REGISTRY = 'VERTEX_AI',
                VERTEX_AI_MODEL_ID = 'classify_species_rf'
            )
        AS
            SELECT species, island, culmen_length_mm, culmen_depth_mm, sex, flipper_length_mm, body_mass_g
            FROM `statmike-mlops-349915.bqml_model_monitoring.training_split`
            WHERE splits = 'TRAIN'
            UNION ALL
            SELECT species, island, culmen_length_mm, culmen_depth_mm, sex, flipper_length_mm, body_mass_g
            FROM `statmike-mlops-349915.bqml_model_monitoring.serving`
            WHERE DATE(instance_timestamp) < @run_date
        ;

        # get retrained models evaluation metrics: accuracy
        SET retrain_accuracy = (
            SELECT accuracy
            FROM ML.EVALUATE (
                MODEL `statmike-mlops-349915.bqml_model_monitoring.classify_species_rf`
            )
        );

        SELECT ERROR(
            CONCAT(
                "\n\nMonitoring Report for ", @run_date, ":",
                "\n\t", drift,
                "\n\t", skew,
                "\n\nThe Model was retrained:",
                "\n\taccuracy of prior model: ", train_accuracy,
                "\n\trecent accuracy of prior model: ", recent_accuracy,
                "\n\taccuracy after retraining: ", retrain_accuracy,
                "\n\n"
            )
        );
    END;
    # ELSE ... supressed alerts on runs without anomalies detected
END IF;
