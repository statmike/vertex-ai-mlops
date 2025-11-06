# Start from Google's PyTorch pre-built container for base dependencies
FROM us-docker.pkg.dev/vertex-ai/prediction/pytorch-cpu.1-13:latest

# Install FastAPI and dependencies
RUN pip install --no-cache-dir \
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
