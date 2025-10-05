FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/websocket-ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/websocket-ingestion/src/ ./src/
COPY shared/ ./shared/

# Set Python path to include src and shared directories
ENV PYTHONPATH=/app:/app/src

# Create log directory and non-root user
RUN mkdir -p /var/log/ha-ingestor && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /var/log/ha-ingestor
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["python", "-m", "main"]
