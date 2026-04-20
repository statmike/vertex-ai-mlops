#!/bin/bash
export PORT=$AIP_HTTP_PORT
# Single worker — each container loads a large model at startup.
# Vertex AI scales by adding replicas, not gunicorn workers.
export WEB_CONCURRENCY=1
