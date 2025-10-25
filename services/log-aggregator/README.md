# Log Aggregator Service

**Centralized Log Collection & Analysis for HomeIQ**

Lightweight log aggregation service that collects, parses, and analyzes logs from all Docker containers in the HomeIQ system.

---

## 📊 Overview

**Port:** 8015
**Technology:** Python 3.11, Docker API, FastAPI
**Container:** `homeiq-log-aggregator`
**Memory:** 128MB (minimal footprint)

### Purpose

Centralized logging for:
- Docker container log collection
- JSON log parsing
- Real-time log streaming
- Log search and filtering
- Error detection and alerting

---

## 🎯 Features

### Log Collection

**Docker Integration:**
- Automatic discovery of all HomeIQ containers
- Real-time log streaming via Docker API
- Container lifecycle monitoring
- Multi-container aggregation

**Log Parsing:**
- JSON log parsing (structured logs)
- Plain text log support
- Timestamp normalization
- Log level extraction

### Search & Filter

**Query Capabilities:**
- Search by service name
- Filter by log level (INFO, WARNING, ERROR)
- Time range filtering
- Keyword search
- Regex pattern matching

### Analysis

**Error Detection:**
- Automatic error log identification
- Exception tracking
- Critical error alerting
- Error rate monitoring

---

## 🔌 API Endpoints

### Log Retrieval

```bash
GET /logs
# Get recent logs from all services

Query Parameters:
- service: Filter by service name (e.g., websocket-ingestion)
- level: Filter by log level (INFO, WARNING, ERROR)
- since: Time range (e.g., 5m, 1h, 1d)
- limit: Maximum number of logs (default: 100)
- search: Keyword search

Example:
curl "http://localhost:8015/logs?service=data-api&level=ERROR&since=1h"

Response:
{
  "logs": [
    {
      "timestamp": "2025-10-25T14:30:00Z",
      "service": "data-api",
      "level": "ERROR",
      "message": "Failed to connect to InfluxDB",
      "container_id": "abc123"
    }
  ],
  "count": 1,
  "total_containers": 25
}
```

### Real-Time Streaming

```bash
GET /logs/stream
# WebSocket endpoint for real-time logs

Query Parameters:
- service: Filter by service
- level: Minimum log level

Example (JavaScript):
const ws = new WebSocket('ws://localhost:8015/logs/stream?level=ERROR');
ws.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

### Service Logs

```bash
GET /logs/service/{service_name}
# Get logs for specific service

Example:
curl http://localhost:8015/logs/service/websocket-ingestion?limit=50
```

### Error Summary

```bash
GET /errors/summary
# Get error statistics

Response:
{
  "total_errors": 42,
  "error_rate": 0.05,
  "services_with_errors": [
    {
      "service": "websocket-ingestion",
      "error_count": 25,
      "last_error_at": "2025-10-25T14:30:00Z"
    }
  ]
}
```

### Health

```bash
GET /health

Response:
{
  "status": "healthy",
  "containers_monitored": 25,
  "docker_connection": "connected",
  "log_buffer_size": 1000
}
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Service Configuration
LOG_AGGREGATOR_PORT=8015
LOG_LEVEL=INFO

# Docker Configuration
DOCKER_SOCKET=/var/run/docker.sock
DOCKER_API_VERSION=auto

# Log Processing
MAX_LOG_BUFFER=10000
LOG_RETENTION_HOURS=24
BATCH_SIZE=100

# Filtering
DEFAULT_LOG_LIMIT=100
MAX_LOG_LIMIT=1000
```

### Docker Compose

```yaml
log-aggregator:
  build: ./services/log-aggregator
  container_name: homeiq-log-aggregator
  ports:
    - "8015:8015"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
  mem_limit: 128m
```

---

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Start service
docker-compose up log-aggregator

# View logs being collected
curl http://localhost:8015/logs?limit=10
```

### Standalone Docker

```bash
# Build
docker build -t homeiq-log-aggregator \
  -f services/log-aggregator/Dockerfile .

# Run (requires Docker socket access)
docker run -p 8015:8015 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  homeiq-log-aggregator
```

### Local Development

```bash
cd services/log-aggregator

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

---

## 📊 Performance

### Resource Usage
- Memory: ~50-128MB (very lightweight)
- CPU: <1% (idle), ~5% (active logging)
- Startup: <5 seconds
- Log buffer: 10,000 entries (configurable)

### Throughput
- Log ingestion: 1000+ logs/second
- API response: <50ms (recent logs)
- Stream latency: <100ms

---

## 🏗️ Architecture

### Service Design

```
Log Aggregator (8015)
├── Docker Client
│   ├── Connect to Docker socket
│   ├── List all containers
│   └── Stream container logs
├── Log Parser
│   ├── JSON parsing
│   ├── Plain text parsing
│   ├── Timestamp extraction
│   └── Level detection
├── Log Buffer
│   ├── In-memory circular buffer
│   ├── Time-based retention
│   └── Overflow protection
└── API Layer
    ├── REST endpoints
    ├── WebSocket streaming
    └── Query filtering
```

### Log Flow

```
HomeIQ Containers (25+)
    ↓ stdout/stderr
Docker Engine
    ↓ Docker API
Log Aggregator
    ├─ Parse & Buffer
    ├─ Index by service
    └─ Expose via API
    ↓
Health Dashboard / CLI / Monitoring
```

---

## 🧪 Testing

### Manual Testing

```bash
# Get recent logs
curl http://localhost:8015/logs

# Get errors only
curl http://localhost:8015/logs?level=ERROR

# Get logs from specific service
curl http://localhost:8015/logs?service=websocket-ingestion

# Search for keyword
curl http://localhost:8015/logs?search=timeout

# Error summary
curl http://localhost:8015/errors/summary
```

### Test Log Streaming

```bash
# Using websocat (WebSocket client)
websocat ws://localhost:8015/logs/stream

# Using curl (HTTP/1.1 upgrade)
curl -N http://localhost:8015/logs/stream
```

---

## 🔍 Troubleshooting

### No Logs Appearing

**Check Docker socket access:**
```bash
# Verify socket is mounted
docker exec homeiq-log-aggregator ls -la /var/run/docker.sock

# Should show: srw-rw---- 1 root docker ...
```

**Check permissions:**
```bash
# Log aggregator user needs docker group access
# In Dockerfile:
RUN groupadd -g 999 docker && usermod -a -G docker appuser
```

### High Memory Usage

**Reduce buffer size:**
```bash
MAX_LOG_BUFFER=5000  # Reduce from 10000
LOG_RETENTION_HOURS=12  # Reduce from 24
```

### Slow Queries

**Add indexing:**
```python
# Index logs by service and timestamp
# Implement time-series bucketing
```

---

## 📚 Log Format Standards

### JSON Logs (Recommended)

```json
{
  "timestamp": "2025-10-25T14:30:00.123Z",
  "level": "INFO",
  "service": "websocket-ingestion",
  "message": "Connected to Home Assistant",
  "context": {
    "correlation_id": "abc-123",
    "operation": "websocket_connect"
  }
}
```

### Plain Text Logs

```
2025-10-25 14:30:00 INFO [websocket-ingestion] Connected to Home Assistant
```

---

## 📚 Related Documentation

- [Health Dashboard](../health-dashboard/README.md) - Log viewing UI
- [Docker Logging Drivers](https://docs.docker.com/config/containers/logging/)
- [Shared Logging Config](../../shared/logging_config.py)

---

## 🤝 Integration

### Used By
- Health Dashboard (log viewer)
- Admin API (error monitoring)
- Monitoring systems (Grafana, etc.)

### Monitors
- All 25 HomeIQ services
- Docker system containers
- Any container in same network

---

## 🔧 Advanced Features

### Custom Log Parsers

```python
# Add custom parser for specific service
class CustomLogParser:
    def parse(self, log_line: str) -> dict:
        # Custom parsing logic
        return {
            "timestamp": ...,
            "level": ...,
            "message": ...
        }
```

### Log Forwarding

```python
# Forward logs to external systems
# Syslog, Elasticsearch, CloudWatch, etc.
class LogForwarder:
    async def forward(self, log: dict):
        await self.send_to_external_system(log)
```

---

## 🔒 Security

### Docker Socket Access

**Important:** Docker socket access grants significant permissions

**Best Practices:**
- Mount socket as read-only (`:ro`)
- Run with minimal user permissions
- Restrict to logging API endpoints only
- No container start/stop capabilities

### Log Sanitization

```python
# Remove sensitive data from logs
SENSITIVE_PATTERNS = [
    r'password["\s:=]+[\w]+',
    r'token["\s:=]+[\w]+',
    r'api[_-]?key["\s:=]+[\w]+'
]
```

---

**Version:** 1.0.0
**Status:** ✅ Production Ready
**Last Updated:** October 25, 2025
**Memory Limit:** 128MB
