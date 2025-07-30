# LumiLens FastAPI Backend - Production Dockerfile
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data chroma_db

# Create non-root user
RUN groupadd -r lumilens && useradd -r -g lumilens lumilens
RUN chown -R lumilens:lumilens /app
USER lumilens

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "run_server.py"]
