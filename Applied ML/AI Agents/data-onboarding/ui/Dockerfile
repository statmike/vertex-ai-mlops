FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ backend/
COPY frontend/ frontend/
COPY agent_voice/ agent_voice/

ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8080

CMD ["sh", "-c", "uv run uvicorn backend.app:app --host 0.0.0.0 --port ${PORT}"]
