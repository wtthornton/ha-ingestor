# Admin API Service

## Overview

The Admin API Service is a FastAPI-based REST API that provides comprehensive administration, monitoring, and configuration management for the HA Ingestor system.

**Port:** 8003  
**Technology:** Python 3.11, FastAPI, Pydantic  
**Container:** `homeiq-admin-api`

## Features

### System Monitoring
- Health check endpoints for all services
- Real-time system metrics and statistics
- Performance monitoring and analytics
- Service status tracking

### Integration Management ✨ NEW
- Configuration management for external services
- Read/write service configuration (.env files)
- Secure credential management with masked values
- Support for Home Assistant, Weather API, and InfluxDB configurations

### Service Control ✨ NEW
- Service status monitoring
- Service listing and health checks
- Restart capabilities (requires Docker socket access)

### Data Management
- InfluxDB query interface
- Data export capabilities
- Historical data analysis

### Alert Management ✨ NEW
- Real-time alert monitoring and management
- Automatic cleanup of stale alerts (timeout alerts older than 1 hour)
- Alert acknowledgment and resolution
- Critical alert filtering and prioritization

## API Endpoints

### Health & Monitoring

#### `GET /health`
Get service health status
```bash
curl http://localhost:8003/health
```

#### `GET /api/v1/health`
Get comprehensive system health
```json
{
  "status": "healthy",
  "services": {
    "influxdb": "healthy",
    "websocket": "healthy",
    "enrichment": "healthy"
  },
  "timestamp": "2025-10-11T12:00:00Z"
}
```

### Integration Management ✨ NEW

#### `GET /api/v1/integrations`
List all available service integrations
```bash
curl http://localhost:8003/api/v1/integrations
```

Response:
```json
{
  "integrations": [
    {
      "id": "websocket",
      "name": "Home Assistant WebSocket",
      "description": "Home Assistant connection configuration",
      "configured": true
    },
    {
      "id": "weather",
      "name": "Weather API",
      "description": "Weather data integration",
      "configured": true
    },
    {
      "id": "influxdb",
      "name": "InfluxDB",
      "description": "Time-series database configuration",
      "configured": true
    }
  ]
}
```

#### `GET /api/v1/integrations/{service}/config`
Get configuration for a specific service
```bash
curl http://localhost:8003/api/v1/integrations/websocket/config
```

Response:
```json
{
  "service": "websocket",
  "config": {
    "HA_URL": "ws://homeassistant.local:8123/api/websocket",
    "HA_TOKEN": "••••••••",
    "HA_VERIFY_SSL": "true",
    "HA_RECONNECT_DELAY": "5"
  },
  "masked_fields": ["HA_TOKEN"]
}
```

#### `PUT /api/v1/integrations/{service}/config`
Update service configuration
```bash
curl -X PUT http://localhost:8003/api/v1/integrations/websocket/config \
  -H "Content-Type: application/json" \
  -d '{
    "HA_URL": "ws://homeassistant.local:8123/api/websocket",
    "HA_TOKEN": "new-token-here",
    "HA_VERIFY_SSL": "true"
  }'
```

### Service Control ✨ NEW

#### `GET /api/v1/services`
List all services with status
```bash
curl http://localhost:8003/api/v1/services
```

Response:
```json
{
  "services": [
    {
      "name": "websocket-ingestion",
      "status": "running",
      "health": "healthy",
      "uptime": "2h 34m"
    },
    {
      "name": "enrichment-pipeline",
      "status": "running",
      "health": "healthy",
      "uptime": "2h 34m"
    }
  ]
}
```

#### `POST /api/v1/services/{service}/restart`
Restart a service (requires Docker socket access)
```bash
curl -X POST http://localhost:8003/api/v1/services/websocket-ingestion/restart
```

### Alert Management ✨ NEW

#### `GET /api/v1/alerts/active`
Get all active alerts with automatic cleanup of stale alerts
```bash
curl http://localhost:8003/api/v1/alerts/active
```

**Features:**
- Automatically resolves timeout alerts older than 1 hour
- Filters by severity (optional): `?severity=critical`
- Returns only currently relevant alerts

**Response:**
```json
{
  "value": [
    {
      "id": "service_unhealthy_1234567890",
      "name": "service_unhealthy",
      "severity": "critical",
      "status": "active",
      "message": "Service health is critical: critical",
      "service": "admin-api",
      "metric": "health_status",
      "current_value": null,
      "threshold_value": null,
      "created_at": "2025-10-18T21:19:58.537970Z",
      "resolved_at": null,
      "acknowledged_at": null,
      "metadata": {
        "dependency": "WebSocket Ingestion",
        "response_time_ms": 2000.0,
        "message": "Timeout after 2.0s"
      }
    }
  ],
  "Count": 1
}
```

#### `POST /api/v1/alerts/{alert_id}/acknowledge`
Acknowledge an alert
```bash
curl -X POST http://localhost:8003/api/v1/alerts/service_unhealthy_1234567890/acknowledge
```

#### `POST /api/v1/alerts/{alert_id}/resolve`
Resolve an alert
```bash
curl -X POST http://localhost:8003/api/v1/alerts/service_unhealthy_1234567890/resolve
```

## Configuration

### Environment Variables

```bash
# API Configuration
API_PORT=8003
API_HOST=0.0.0.0

# InfluxDB Connection
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=homeiq
INFLUXDB_BUCKET=home_assistant_events

# Configuration Management
CONFIG_DIR=/app/infrastructure
CONFIG_FILE_PERMISSIONS=0600

# Logging
LOG_LEVEL=INFO
```

### Configuration Files

The service reads/writes configuration from:
- `infrastructure/.env.websocket` - Home Assistant configuration
- `infrastructure/.env.weather` - Weather API configuration
- `infrastructure/.env.influxdb` - InfluxDB configuration

## Architecture

### Components

```
admin-api/
├── src/
│   ├── main.py                    # Main application
│   ├── simple_main.py             # Simplified entry point
│   ├── config_manager.py          # Configuration file I/O ✨ NEW
│   ├── service_controller.py      # Service management ✨ NEW
│   ├── integration_endpoints.py   # Integration API ✨ NEW
│   ├── health_handler.py          # Health checks
│   └── influxdb_client.py         # InfluxDB interface
├── tests/                         # Unit tests
├── Dockerfile                     # Container definition
└── requirements.txt               # Python dependencies
```

### Design Patterns

- **FastAPI Router Pattern** - Modular endpoint organization
- **Dependency Injection** - Configuration and client management
- **Repository Pattern** - Data access abstraction
- **Configuration Management** - Simple .env file strategy

## Development

### Local Setup

```bash
# Navigate to service directory
cd services/admin-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python -m uvicorn src.main:app --reload --port 8003
```

### Running with Docker

```bash
# Build container
docker-compose build admin-api

# Start service
docker-compose up admin-api

# View logs
docker-compose logs -f admin-api
```

### API Documentation

When running, interactive API documentation is available at:
- **Swagger UI:** http://localhost:8003/docs
- **ReDoc:** http://localhost:8003/redoc

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src --cov-report=html tests/

# Run specific test file
pytest tests/test_health_handler.py
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8003/health

# Test integrations list
curl http://localhost:8003/api/v1/integrations

# Test configuration read
curl http://localhost:8003/api/v1/integrations/websocket/config
```

## Security

### Authentication
- API key authentication (optional)
- Token-based authentication support
- CORS configuration for frontend access

### Configuration Security
- Sensitive values are masked in API responses
- Configuration files set to 600 permissions
- No secrets logged or exposed in error messages

### Best Practices
- Use environment variables for secrets
- Enable HTTPS in production
- Implement rate limiting for public endpoints
- Regular security audits

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker-compose logs admin-api
```

**Common issues:**
- InfluxDB not accessible
- Configuration files missing
- Port 8003 already in use

### Configuration Not Saving

**Check permissions:**
```bash
ls -la infrastructure/.env.*
```

**Should show:** `-rw-------` (600 permissions)

### Service Restart Failing

**Limitation:** Service restart requires Docker socket access

**Workaround:** Use command line
```bash
docker-compose restart websocket-ingestion
```

**Future:** Mount Docker socket or use Docker SDK

## Performance

- **Response Time:** <50ms for health checks
- **Throughput:** 1000+ requests/minute
- **Memory:** ~100MB baseline
- **CPU:** Minimal (<5% during normal operation)

## Dependencies

### Core
- `fastapi>=0.104.0` - Web framework
- `uvicorn>=0.24.0` - ASGI server
- `pydantic>=2.0.0` - Data validation
- `python-dotenv>=1.0.0` - Environment management

### Integration
- `influxdb-client>=1.36.0` - InfluxDB connection
- `aiohttp>=3.9.0` - Async HTTP client

### Development
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support

## Contributing

1. Follow Python PEP 8 style guidelines
2. Add tests for new functionality
3. Update API documentation
4. Use type hints for all functions
5. Document all endpoints with docstrings

## Related Documentation

- [API Documentation](../../docs/API_DOCUMENTATION.md)
- [Architecture Guide](../../docs/architecture.md)
- [Configuration Management](../../docs/QUICK_START_INTEGRATION_MANAGEMENT.md)
- [Deployment Guide](../../docs/DEPLOYMENT_GUIDE.md)

## Support

- **Issues:** File on GitHub
- **Documentation:** Check `/docs`
- **API Docs:** http://localhost:8003/docs

---

**Last Updated:** October 11, 2025  
**Version:** 2.0  
**Status:** Production Ready ✅

