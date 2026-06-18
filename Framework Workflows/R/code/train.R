# R - Shared GLM Workflow
#
# The single workflow used across every runtime notebook in this series so the
# runtimes can be compared apples-to-apples:
#   read (TRAIN/TEST splits from BigQuery) -> fit GLM -> evaluate -> save model.rds
#
# Reads use the BigQuery Storage Read API (Arrow) via `bigrquerystorage` when it
# is installed - fast and parallel, no CSV export. See the data-access notebook:
#   "R - Reading BigQuery Iceberg Tables.ipynb"
#
# Invoked as a script with positional arguments:
#   Rscript train.R <bq_project> <bq_dataset> <bq_table> <var_target> <var_omit_csv>

# libraries ------------------------------------------------------------------
library(bigrquery)
suppressWarnings(suppressMessages({
    # enables the fast Arrow / Storage Read API download path when present
    has_storage <- requireNamespace("bigrquerystorage", quietly = TRUE)
}))

# inputs ---------------------------------------------------------------------
args <- commandArgs(trailingOnly = TRUE)
bq_project <- args[1]
bq_dataset <- args[2]
bq_table   <- args[3]
var_target <- args[4]
var_omit   <- args[5]   # comma-separated list of columns to exclude, e.g. "transaction_id,splits"

cat("Storage Read API available:", has_storage, "\n")

# data source ----------------------------------------------------------------
# Read one split (TRAIN/VALIDATE/TEST). Column projection (EXCEPT) and the row
# filter are pushed to BigQuery so only the needed bytes are read.
get_data <- function(s) {
    query <- sprintf('
        SELECT * EXCEPT(%s)
        FROM `%s.%s.%s`
        WHERE splits = "%s"
    ', var_omit, bq_project, bq_dataset, bq_table, s)

    table <- bq_project_query(bq_project, query)

    # bq_table_download auto-uses the Storage Read API (Arrow) when
    # bigrquerystorage is installed; falls back to REST otherwise.
    bq_table_download(table, n_max = Inf)
}

train <- get_data("TRAIN")
test  <- get_data("TEST")
cat("train rows:", nrow(train), " test rows:", nrow(test), "\n")

# train: logistic regression -------------------------------------------------
model_exp <- paste0(var_target, " ~ .")
model <- glm(
    as.formula(model_exp),
    data = train,
    family = binomial
)

# evaluate: confusion matrix on the test split -------------------------------
preds  <- predict(model, test, type = "response")
actual <- test[, var_target]
names(actual) <- "actual"
pred <- data.frame(pred = round(preds))
results <- cbind(actual, pred)
cm <- table(results)
cat("Confusion matrix (rows = actual, cols = predicted):\n")
print(cm)

# save model -----------------------------------------------------------------
# Vertex AI sets AIP_MODEL_DIR to a gs:// path and mounts the bucket via Cloud
# Storage FUSE at /gcs, so we can write the model straight there as a local file
# - no gcloud/gsutil CLI needed (the rocker/r-ver base image does not ship one).
# Falls back to the working directory for local/interactive runs.
model_dir <- Sys.getenv("AIP_MODEL_DIR")
if (nzchar(model_dir)) {
    dest_dir <- sub("/+$", "", sub("^gs://", "/gcs/", model_dir))  # trim trailing slash
    dir.create(dest_dir, recursive = TRUE, showWarnings = FALSE)
    dest <- file.path(dest_dir, "model.rds")
    saveRDS(model, dest)
    cat("Saved model to", dest, "(", model_dir, ")\n")
} else {
    saveRDS(model, "model.rds")
    cat("AIP_MODEL_DIR not set; model.rds saved to working directory.\n")
}

cat("Done. project:", bq_project, " dataset:", bq_dataset, " table:", bq_table, "\n")
