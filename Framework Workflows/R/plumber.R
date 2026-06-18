
library(plumber)
library(jsonlite)

# load model at startup (baked into the image or fetched to /model/model.rds)
model <- readRDS(Sys.getenv("MODEL_PATH", "/model/model.rds"))

#* @get /health
function() { list(status = "ok") }

#* @post /predict
function(req, res) {
    # Disable response gzip. httpuv compresses when the caller sends
    # 'Accept-Encoding: gzip' (the Vertex AI SDK's raw_predict does), and Vertex's
    # proxy then double-wraps it ('content-encoding: gzip, gzip') so the client
    # cannot decode the body. Forcing identity returns plain JSON.
    res$setHeader("Content-Encoding", "identity")

    # Parse the body from the raw bytes ourselves so it does NOT depend on the
    # request Content-Type (Vertex may forward without 'application/json', which
    # would leave plumber's auto-parsed req$body empty -> "object 'V1' not found").
    raw <- req$postBody
    if (is.null(raw) || !nzchar(raw)) raw <- rawToChar(req$bodyRaw)
    body <- jsonlite::fromJSON(raw, simplifyDataFrame = TRUE)

    # one row per instance; columns = features. Handle both shapes jsonlite can
    # produce (a data.frame, or a list of per-instance named lists).
    instances <- body$instances
    newdata <- if (is.data.frame(instances)) instances else do.call(rbind.data.frame, instances)

    out <- tryCatch(
        as.numeric(predict(model, newdata, type = "response")),
        error = function(e) {
            res$status <- 400
            list(error = conditionMessage(e), received_columns = names(newdata))
        }
    )
    if (is.list(out)) return(out)
    list(predictions = unname(out))
}
