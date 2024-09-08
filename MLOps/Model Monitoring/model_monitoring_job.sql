DECLARE drift_anomalies ARRAY<STRING>;
DECLARE drift STRING;
DECLARE skew_anomalies ARRAY<STRING>;
DECLARE skew STRING;

# Monitor Drift
SET drift_anomalies = (
    SELECT ARRAY_AGG(input)
    FROM ML.VALIDATE_DATA_DRIFT(
        (
            SELECT * EXCEPT(instance_timestamp)
            FROM `statmike-mlops-349915.bqml_model_monitoring.serving_all`
            WHERE
                DATE(instance_timestamp) >= DATE_SUB(@run_date, INTERVAL 2 WEEK)
                AND
                DATE(instance_timestamp) < DATE_SUB(@run_date, INTERVAL 1 WEEK)
        ),
        (
            SELECT * EXCEPT(instance_timestamp)
            FROM `statmike-mlops-349915.bqml_model_monitoring.serving_all`
            WHERE DATE(instance_timestamp) >= DATE_SUB(@run_date, INTERVAL 1 WEEK)
        ),
        STRUCT(
            0.4 AS categorical_default_threshold,
            0.4 AS numerical_default_threshold
        )
    )
    WHERE is_anomaly = True
);
IF(ARRAY_LENGTH(drift_anomalies) > 0) THEN
    SET drift = CONCAT(
        "Found data drift (", ARRAY_TO_STRING(drift_anomalies, ", "), ")"
    );
    ELSE SET drift = 'No drift detected.';
END IF;

# Monitor Skew
SET skew_anomalies = (
    SELECT ARRAY_AGG(input)
    FROM ML.VALIDATE_DATA_SKEW(
        MODEL `statmike-mlops-349915.bqml_model_monitoring.classify_species_rf`,
        (
            SELECT * EXCEPT(instance_timestamp)
            FROM `statmike-mlops-349915.bqml_model_monitoring.serving_all`
            WHERE DATE(instance_timestamp) >= DATE_SUB(@run_date, INTERVAL 1 WEEK)
        )
    )
    WHERE is_anomaly = True
);
IF(ARRAY_LENGTH(skew_anomalies) > 0) THEN
    SET skew = CONCAT(
        "Found data skew (", ARRAY_TO_STRING(skew_anomalies, ", "), ")"
    );
    ELSE SET skew = 'No skew detected.';
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
                MODEL_REGISTRY = 'VERTEX_AI'
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
                "\nThe Model was retrained:",
                "\n\taccuracy of prior model: ", train_accuracy,
                "\n\trecent accuracy of prior model: ", recent_accuracy,
                "\n\taccuracy after retraining: ", retrain_accuracy,
                "\n\n"
            )
        );
    END;
    # ELSE ... supressed alerts on runs without anomalies detected
END IF;
