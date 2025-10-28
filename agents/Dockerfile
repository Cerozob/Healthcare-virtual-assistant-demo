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
COPY pyproject.toml README.md ./

# Generate ARM64-specific lock file and install dependencies
RUN uv lock && uv sync --frozen

# Copy agent source code
COPY . ./

# Ensure ARM64-compatible virtual environment
RUN rm -rf .venv && uv sync --frozen

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp

# Set proper permissions
RUN chmod -R 755 /app

# Verify Python installation and architecture
RUN uv run python -c "import platform; print(f'Architecture: {platform.machine()}'); print(f'Platform: {platform.platform()}')"

# Health check for AgentCore Runtime using uv run
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/ping')" || exit 1

# Expose port 8080 (required for AgentCore Runtime)
EXPOSE 8080

# Run the FastAPI application with uvicorn using uv run
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
