# Sports API Service - Deployment Guide

Simple deployment guide for the Sports API service.

---

## Prerequisites

1. **API-SPORTS API Key**
   - Sign up at https://api-sports.io
   - Subscribe to NFL and/or NHL API
   - Copy your API key

2. **InfluxDB Instance**
   - Running InfluxDB 2.7+
   - Create database: `sports_data`
   - Generate authentication token

3. **Docker & Docker Compose**
   - Docker 24+
   - Docker Compose 2.20+

---

## Quick Start

### 1. Configure Environment

```bash
# Copy template
cp infrastructure/env.sports.template .env

# Edit with your API key
vi .env
# Set: API_SPORTS_KEY=your-actual-key-here
```

### 2. Start Service

```bash
# Development
docker-compose up sports-api

# Production
docker-compose -f docker-compose.prod.yml up -d sports-api
```

### 3. Verify Health

```bash
curl http://localhost:8015/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "sports-api",
  "components": {
    "nfl_client": "healthy",
    "nhl_client": "healthy",
    "cache": "healthy",
    "influxdb": "healthy"
  }
}
```

---

## Configuration

### Required Environment Variables

```bash
API_SPORTS_KEY=your-api-key-here
```

### Optional Configuration

```bash
# Service
SPORTS_API_PORT=8015
NFL_ENABLED=true
NHL_ENABLED=true

# Rate Limiting
API_SPORTS_REQUESTS_PER_SECOND=1
API_SPORTS_BURST_SIZE=5

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_BUCKET=sports_data
```

See `infrastructure/env.sports.template` for all options.

---

## Testing

### Unit Tests
```bash
cd services/sports-api
pytest --cov=src
```

Expected: 93/93 tests passing, 73%+ coverage

### Smoke Test
```bash
# Health check
curl http://localhost:8015/health

# NFL scores
curl http://localhost:8015/api/nfl/scores

# Stats
curl http://localhost:8015/api/sports/stats
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker logs ha-sports-api
```

**Common issues:**
- Missing API_SPORTS_KEY
- InfluxDB not running
- Port 8015 already in use

### API Errors

**Check API key:**
```bash
curl -H "x-rapidapi-key: YOUR_KEY" https://api-sports.io/nfl/scores
```

**Check quota:**
- Visit API-SPORTS dashboard
- Verify daily limit not exceeded

### InfluxDB Issues

**Verify connection:**
```bash
curl http://localhost:8086/health
```

**Check token:**
- Verify INFLUXDB_TOKEN is correct
- Verify database exists

---

## Production Deployment

### 1. Optimize Docker Image

Production Dockerfile already optimized:
- Multi-stage build
- Minimal base image (python:3.11-slim)
- Non-root user
- Health checks

### 2. Set Production Environment

```bash
API_SPORTS_KEY=production-key
LOG_LEVEL=INFO
INFLUXDB_URL=http://production-influx:8086
```

### 3. Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d sports-api
```

### 4. Verify

```bash
# Health
curl http://production-host:8015/health

# Logs
docker logs ha-sports-api --tail=100
```

---

## Monitoring

### Health Check
```bash
curl http://localhost:8015/health
```

### Service Stats
```bash
curl http://localhost:8015/api/sports/stats
```

Shows:
- Cache hit rate
- Rate limiter usage
- InfluxDB write statistics
- API client statistics

### Expected Metrics
- Cache hit rate: >60%
- Rate limit waits: <20%
- InfluxDB success rate: >95%

---

## Rollback

If issues occur:

```bash
# Stop service
docker-compose down sports-api

# Check logs
docker logs ha-sports-api

# Restart
docker-compose up -d sports-api
```

---

**Simple, straightforward deployment - production ready!** 🚀

