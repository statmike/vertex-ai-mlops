
# library import
library(bigrquery)
library(tidyverse)
library(data.table)

# inputs
args <- commandArgs(trailingOnly = TRUE)
project_id <- args[1]
region <- args[2]
experiment <- args[3]
series <- args[4]
bq_project <- args[5]
bq_dataset <- args[6]
bq_table <- args[7]
var_target <- args[8]
var_omit <- args[9]

# export from BigQuery to GCS
query <- "
EXPORT DATA
    OPTIONS (
        uri = 'gs://%sdata/%s/*.csv',
        format = 'CSV',
        overwrite = true,
        header = true,
        field_delimiter = ','
    )
AS (
    SELECT * EXCEPT(%s, splits)
    FROM `%s.%s.%s`
    WHERE splits = '%s'
)"
#cat(query)

get_data <- function(split){
    # populate export query
    path <- Sys.getenv('AIP_MODEL_DIR')
    path <- sub('gs://', '', path)
    
    split_query <- sprintf(query, path, split, var_omit, bq_project, bq_dataset, bq_table, split)
    cat(split_query)
    
    # run bq export
    export <- bq_perform_query(split_query, billing = bq_project)
    bq_job_wait(export)
    
    # make list of exports files
    files <- list.files(
        path = sprintf('/gcs/%sdata/%s', path, split),
        pattern = '*.csv',
        full.names = TRUE
    )
    
    # read bq export into dataframe from GCS using FUSE
    df <- 
        files %>%
        map_df(~fread(.))
    
    # delete exported copy in GCS
    sapply(files, unlink)
    
    # return the dataframe
    return(df)
}
train <- get_data('TRAIN')
test <- get_data('TEST')

# logistic regression model
model <- glm(
    Class ~ .,
    data = train,
    family = binomial)

# predictions for evaluation
preds <- predict(model, test, type = "response")

# evaluate
actual <- test[, get(var_target)]
names(actual) <- 'actual'
pred <- tibble(round(preds))
names(pred) <- 'pred'
results <- cbind(actual, pred)
cm <- table(results)

# save model to file
saveRDS(model, "model.rds")

# use Vertex AI Training Pre-Defined Environment Variables to Write to GCS
system2('gsutil', c('cp', 'model.rds', Sys.getenv('AIP_MODEL_DIR')))
