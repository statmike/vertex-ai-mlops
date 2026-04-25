FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Vertex AI probes AIP_HTTP_PORT (default 8080); tiangolo image binds to PORT
ENV PORT 8080
# Single worker — batch prediction only needs one, and faster startup
ENV WEB_CONCURRENCY 1

COPY ./app /app
COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt
