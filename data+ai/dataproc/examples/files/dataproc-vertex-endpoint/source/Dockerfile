FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Vertex AI expects the container on port 8080 (serving_container_ports)
ENV PORT 8080

COPY serve.py /app/main.py
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt
