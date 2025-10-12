# Production Dockerfile for Sports API Service
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy shared libraries
COPY --from=shared /shared /shared 2>/dev/null || true

# Create non-root user
RUN useradd -m -u 1000 sportsapi && chown -R sportsapi:sportsapi /app
USER sportsapi

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8015

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import aiohttp; import asyncio; asyncio.run(aiohttp.ClientSession().get('http://localhost:8015/health').close())" || exit 1

# Run service
CMD ["python", "-m", "src.main"]

