# Multi-stage Docker build for AI Automation Service
# Using Debian-slim instead of Alpine for pre-built numpy/scikit-learn wheels
# (Alpine requires building from source which is complex and time-consuming)

FROM python:3.11-slim AS builder

WORKDIR /app

# Copy requirements from service directory
COPY services/ai-automation-service/requirements.txt .

# Install Python dependencies (pre-built wheels available for Debian)
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Final stage
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code from service directory
COPY services/ai-automation-service/src/ ./src/
COPY services/ai-automation-service/alembic/ ./alembic/
COPY services/ai-automation-service/alembic.ini ./
COPY services/ai-automation-service/tests/ ./tests/

# Copy shared logging (for imports)
COPY shared/ ./shared/

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Create data directory
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8018/health || exit 1

# Expose port
EXPOSE 8018

# Run migrations and start service
CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn src.main:app --host 0.0.0.0 --port 8018"]

