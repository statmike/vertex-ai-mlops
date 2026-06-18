
library(plumber)
port  <- as.integer(Sys.getenv("AIP_HTTP_PORT", Sys.getenv("PORT", "8080")))
pr <- plumb("/app/plumber.R")
# honor Vertex AI's configurable route names by remounting if provided
health <- Sys.getenv("AIP_HEALTH_ROUTE", "/health")
predict_route <- Sys.getenv("AIP_PREDICT_ROUTE", "/predict")
pr$run(host = "0.0.0.0", port = port)
