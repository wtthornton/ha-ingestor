# Weather API Service

Standalone weather data integration service for Home Assistant analytics.

**Epic 31:** Weather API Service Migration  
**Port:** 8009  
**Pattern:** External API service (follows sports-data template)

## Overview

This service provides weather data through a REST API, replacing the previous event enrichment pattern. Weather data is fetched from OpenWeatherMap, cached for efficiency, and stored in InfluxDB for historical queries.

## Architecture

```
weather-api:8009 → OpenWeatherMap API
                 ↓
            Cache (15-min TTL)
                 ↓
            InfluxDB (weather_data)
                 ↓
          Dashboard queries
```

## API Endpoints

### Core Endpoints
- `GET /` - Service information
- `GET /health` - Health check with component status
- `GET /metrics` - Prometheus-compatible metrics

### Weather Endpoints (Story 31.3)
- `GET /current-weather` - Current weather conditions
- `GET /forecast` - 24-hour weather forecast
- `GET /historical` - Historical weather queries
- `GET /cache/stats` - Cache performance statistics

## Environment Variables

```bash
# OpenWeatherMap API
WEATHER_API_KEY=your_api_key_here
WEATHER_LOCATION=Las Vegas

# Cache Configuration
CACHE_TTL_SECONDS=900  # 15 minutes
FETCH_INTERVAL_SECONDS=300  # 5 minutes

# Service Configuration
SERVICE_PORT=8009

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your_token
INFLUXDB_ORG=home_assistant
INFLUXDB_BUCKET=weather_data
```

## Development

```bash
# Run in development mode with hot-reload
docker-compose -f docker-compose.dev.yml up weather-api

# Run tests
cd services/weather-api
pytest tests/

# Access API documentation
http://localhost:8009/docs
```

## Docker

```bash
# Build production image
docker build -f services/weather-api/Dockerfile -t weather-api:latest .

# Run standalone
docker run -p 8009:8009 --env-file infrastructure/env.weather weather-api:latest
```

## Implementation Status

- ✅ **Story 31.1:** Service Foundation (FastAPI, Docker, health checks)
- ⏳ **Story 31.2:** Data Collection & InfluxDB Persistence
- ⏳ **Story 31.3:** API Endpoints & Query Support
- ⏳ **Story 31.4:** Event Pipeline Decoupling
- ⏳ **Story 31.5:** Dashboard Integration

## References

- Epic Document: `docs/prd/epic-31-weather-api-service-migration.md`
- Story 31.1: `docs/stories/31.1-weather-api-service-foundation.md`
- Research Analysis: `implementation/analysis/WEATHER_ARCHITECTURE_ANALYSIS.md`

