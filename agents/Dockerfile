# Healthcare Assistant Agent - Dockerfile for AgentCore Runtime
# Optimized for ARM64 platform with Python 3.11 and Strands Agents

ARG BUILDPLATFORM=linux/arm64
ARG TARGETPLATFORM=linux/arm64

FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set working directory
WORKDIR /app

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv
RUN uv sync --frozen --no-cache --no-dev

# Copy agent source code
COPY . ./

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp

# Set proper permissions
RUN chmod -R 755 /app

# Install OpenTelemetry instrumentation for observability
RUN uv add opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation \
    opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-boto3sqs \
    opentelemetry-exporter-otlp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

# Expose port for AgentCore Runtime
EXPOSE 8080

# Set user for security (non-root)
RUN useradd -m -u 1000 agentuser && chown -R agentuser:agentuser /app
USER agentuser

# Run with OpenTelemetry instrumentation for observability
CMD ["opentelemetry-instrument", "uv", "run", "python", "main.py"]
