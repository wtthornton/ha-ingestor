# Technical Stack

## Application Framework
- **Python 3.12+** with async-first architecture

## Database System
- **InfluxDB 2.7+** for time-series data storage
- **PostgreSQL 17+** (optional) for relational metadata if needed

## JavaScript Framework
- **N/A** (Python backend service only)

## Import Strategy
- **N/A** (Python backend service only)

## CSS Framework
- **N/A** (Python backend service only)

## UI Component Library
- **N/A** (Python backend service only)

## Fonts Provider
- **N/A** (Python backend service only)

## Icon Library
- **N/A** (Python backend service only)

## Application Hosting
- **DigitalOcean Kubernetes (DOKS)** for containerized deployment
- **Docker** for containerization

## Database Hosting
- **InfluxDB Cloud** or **Self-hosted on DOKS** with DO Volumes
- **PostgreSQL** (if needed) via DO Managed Postgres

## Asset Hosting
- **N/A** (Python backend service only)

## Deployment Solution
- **Terraform + Helm** for infrastructure as code
- **GitHub Actions** for CI/CD pipelines
- **Docker Compose** for local development

## Code Repository URL
- **GitHub** repository for source code and collaboration

## Additional Technical Components

### Messaging & Protocols
- **Eclipse Mosquitto 2.x** (MQTT broker integration)
- **Home Assistant WebSocket API** for event bus integration
- **Target Instance:** http://192.168.1.86:8123/ (local network)

### Python Dependencies
- **FastAPI 0.115+** for HTTP endpoints (health checks, metrics)
- **paho-mqtt** for MQTT client functionality
- **websockets** for WebSocket client
- **influxdb-client** for InfluxDB operations
- **pydantic** for data validation and settings
- **structlog** for structured logging
- **prometheus-client** for metrics collection
- **tenacity** for retry logic

### Development Tools
- **Poetry** for dependency management
- **pytest** for testing framework
- **ruff** for linting and formatting
- **mypy** for type checking
- **pre-commit** for code quality hooks

### Observability
- **OpenTelemetry** for telemetry collection
- **Prometheus** for metrics storage
- **Grafana** for dashboards and visualization
- **Loki** for log aggregation
