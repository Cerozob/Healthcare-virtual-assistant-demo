# Healthcare Assistant Agent - Dockerfile for AgentCore Runtime
# ARM64 platform required for AgentCore Runtime
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set working directory
WORKDIR /app

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies using uv (creates .venv)
RUN uv sync --frozen --no-cache

# Copy agent source code
COPY . ./

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp

# Set proper permissions
RUN chmod -R 755 /app

# Health check for AgentCore Runtime using Python
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/ping')" || exit 1

# Expose port 8080 (required for AgentCore Runtime)
EXPOSE 8080

# Run the FastAPI application with uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
