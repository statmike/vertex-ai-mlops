# SparkR - Distributed GLM Workflow
#
# The same fraud-detection GLM as code/train.R, but expressed in SparkR so it
# runs distributed on Dataproc Serverless. Reads BigQuery directly with the
# Spark BigQuery connector (bundled with Dataproc Serverless runtimes) - no
# CSV export, no driver-side download.
#
# Submitted with:
#   gcloud dataproc batches submit spark-r sparkr.R -- <project.dataset.table> <var_target>

library(SparkR)

# inputs ---------------------------------------------------------------------
args <- commandArgs(trailingOnly = TRUE)
bq_table   <- args[1]   # fully qualified: project.dataset.table (the _prepped table with splits)
var_target <- if (length(args) >= 2) args[2] else "Class"

sparkR.session(appName = "r-fraud-glm")

# read from BigQuery via the Spark BigQuery connector ------------------------
# The connector reads through the BigQuery Storage API (Arrow) in parallel
# across executors.
df <- read.df(source = "bigquery", table = bq_table)
cat("source rows:", count(df), "\n")

# split using the prepared `splits` column, then drop non-feature columns ----
drop_cols <- c("transaction_id", "splits")
features  <- setdiff(columns(df), drop_cols)

train <- drop(filter(df, df$splits == "TRAIN"), drop_cols)
test  <- drop(filter(df, df$splits == "TEST"),  drop_cols)
cat("train rows:", count(train), " test rows:", count(test), "\n")

# train: distributed logistic regression -------------------------------------
model_formula <- as.formula(paste0(var_target, " ~ ."))
model <- spark.glm(train, model_formula, family = "binomial")
print(summary(model))

# evaluate: confusion matrix on the test split -------------------------------
preds <- predict(model, test)
# spark.glm prediction column is `prediction` (a probability for binomial);
# round to a 0/1 label and cross-tabulate against the actual target.
preds <- withColumn(preds, "pred", cast(round(preds$prediction), "integer"))
cm <- collect(count(groupBy(preds, var_target, "pred")))
cat("Confusion matrix (actual x pred):\n")
print(cm)

sparkR.session.stop()
cat("Done. table:", bq_table, "\n")
