# Multi-stage build for Data Retention Service
FROM python:3.11-alpine AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev linux-headers

# Copy requirements and install Python dependencies
COPY services/data-retention/requirements-prod.txt .
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# Production stage
FROM python:3.11-alpine AS production

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache curl

# Create non-root user first
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Copy Python dependencies from builder stage to user directory
COPY --from=builder /root/.local /home/appuser/.local

# Copy source code and shared modules
COPY services/data-retention/src/ ./src/
COPY shared/ ./shared/

# Set ownership of all files to appuser
RUN chown -R appuser:appgroup /app /home/appuser/.local

# Create log directory with proper permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appgroup /app/logs && \
    chmod -R 755 /app/logs

# Set environment variables
ENV PYTHONPATH=/app:/app/src
ENV PATH=/home/appuser/.local/bin:$PATH

# Create backups directory with proper permissions
RUN mkdir -p /backups && \
    chown -R appuser:appgroup /backups

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the service
CMD ["python", "-m", "src.main"]
