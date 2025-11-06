# Use official Python runtime as base image
FROM python:3.11-slim

# Install Python dependencies
RUN pip install --no-cache-dir \
    torch==2.0.1 --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    google-cloud-storage

# Copy application code
COPY ./app /app

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 8080

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
