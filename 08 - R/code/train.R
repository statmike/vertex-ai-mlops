
# library import
library(bigrquery)
library(dplyr)

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

# data source
get_data <- function(s){
    query = sprintf('SELECT * EXCEPT(%s, splits) FROM `%s.%s.%s` WHERE splits = "%s"', var_omit, bq_project, bq_dataset, bq_table, s)
    table <- bq_project_query(bq_project, query)
    ds <- bq_table_download(table)
    return(ds)
}
train <- get_data("TRAIN")
test <- get_data("TEST")

# logistic regression model
model <- glm(
    Class ~ .,
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
