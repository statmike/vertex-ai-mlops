
FROM rocker/r-ver:4.4.1
RUN apt-get update && apt-get install -y --no-install-recommends     libcurl4-openssl-dev libssl-dev libsodium-dev && rm -rf /var/lib/apt/lists/*
RUN install2.r --error --skipinstalled plumber jsonlite
WORKDIR /app
COPY plumber.R serve.R /app/
# bake the model into the image (copied from GCS during the build)
COPY model.rds /model/model.rds
# trim fit-time data the GLM carries but point-prediction does not need
# (no-op if already trimmed at training time). predict(type="response") needs
# only coefficients, terms, family, and qr.
RUN Rscript -e 'm <- readRDS("/model/model.rds"); for (k in c("model","data","residuals","fitted.values","effects","linear.predictors","weights","prior.weights","y")) m[[k]] <- NULL; saveRDS(m, "/model/model.rds"); cat(sprintf("model.rds trimmed -> %.0f MB\n", file.size("/model/model.rds")/1e6))'
ENV MODEL_PATH=/model/model.rds
ENTRYPOINT ["Rscript", "/app/serve.R"]
