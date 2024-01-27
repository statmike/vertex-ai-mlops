# library import
library(bigrquery)
library(dplyr)

# inputs
args <- commandArgs(trailingOnly = TRUE)
bq_project <- args[1]
bq_dataset <- args[2]
bq_table <- args[3]
var_target <- args[4]
var_omit <- args[5]

# data source
get_data <- function(s){
    
    # query for table
    query <- sprintf('
        SELECT * EXCEPT(%s)
        FROM `%s.%s.%s`
        WHERE splits = "%s"
    ', var_omit, bq_project, bq_dataset, bq_table, s)
    
    # connect to table
    table <- bq_project_query(bq_project, query)
    
    # load table to dataframe
    return(bq_table_download(table, n_max = Inf))

}
train <- get_data("TRAIN")
test <- get_data("TEST")

# logistic regression model
model_exp = paste0(var_target, "~ .")

model <- glm(
    as.formula(model_exp),
    data = train,
    family = binomial)

# predictions for evaluation
preds <- predict(model, test, type = "response")

# evaluate
actual <- test[, var_target]
names(actual) <- 'actual'
pred <- tibble(round(preds))
names(pred) <- 'pred'
results <- cbind(actual, pred)
cm <- table(results)

# save model to file
saveRDS(model, "model.rds")

# get GCS fusemount location to save file to:
path <- sub('gs://', '/gcs/', Sys.getenv('AIP_MODEL_DIR'))
#system2('cp', c('model.rds', path))

# copy model file to GCS
system2('gsutil', c('cp', 'model.rds', Sys.getenv('AIP_MODEL_DIR')))
