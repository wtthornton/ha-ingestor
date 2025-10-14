# Deployment Architecture

### Deployment Strategy

**Frontend Deployment:**
- **Platform:** Docker container with nginx (Alpine-based)
- **Build Command:** `npm run build` (multi-stage build)
- **Output Directory:** `dist/`
- **CDN/Edge:** Local nginx serving static files
- **Image Size:** ~80MB (optimized from ~300MB)

**Backend Deployment:**
- **Platform:** Docker containers orchestrated by Docker Compose
- **Build Command:** Docker multi-stage builds with Alpine Linux
- **Deployment Method:** Docker Compose with health checks and restart policies
- **Security:** Non-root users, read-only filesystems, security options
- **Optimization:** 71% size reduction with Alpine-based images

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      influxdb:
        image: influxdb:2.7
        ports:
          - 8086:8086

    steps:
    - uses: actions/checkout@v4
    - name: Run tests
      run: |
        docker-compose -f docker-compose.yml build
        docker-compose -f docker-compose.yml up -d
        sleep 30
        docker-compose -f docker-compose.yml run --rm test-integration
        docker-compose -f docker-compose.yml down
```

### Environments

| Environment | Frontend URL | Backend URL | Purpose | Docker Compose File |
|-------------|--------------|-------------|---------|-------------------|
| Development | http://localhost:3000 | http://localhost:8000 | Local development | docker-compose.dev.yml |
| Production | http://localhost:3000 | http://localhost:8003 | Live environment | docker-compose.prod.yml |

### Docker Image Optimizations

| Service | Before | After | Reduction |
|---------|--------|-------|-----------|
| WebSocket Ingestion | ~200MB | ~60MB | 70% |
| Admin API | ~180MB | ~50MB | 72% |
| Enrichment Pipeline | ~220MB | ~70MB | 68% |
| Weather API | ~150MB | ~40MB | 73% |
| Data Retention | ~200MB | ~60MB | 70% |
| Health Dashboard | ~300MB | ~80MB | 73% |
| **Total** | **~1.25GB** | **~360MB** | **71%** |

### Security Enhancements
- **Non-root users:** All services run as uid=1001, gid=1001
- **Read-only filesystems:** Where applicable for enhanced security
- **Security options:** `no-new-privileges:true` for all services
- **Tmpfs mounts:** For temporary files and caches
- **Multi-stage builds:** Eliminate build tools from production images

### Persistent Storage (Epic 22)

**Docker Volumes:**
```yaml
volumes:
  influxdb_data:         # InfluxDB time-series data
  influxdb_config:       # InfluxDB configuration
  sqlite-data:           # SQLite metadata databases (Epic 22)
  data_retention_backups:# Retention service backups
  ha_ingestor_logs:      # Centralized logs
```

**Hybrid Database Architecture:**
- **InfluxDB** (`influxdb_data` volume):
  - Home Assistant events (time-series)
  - Sports scores and game data
  - Weather enrichment data
  - System metrics
  
- **SQLite** (`sqlite-data` volume):
  - `metadata.db` (data-api) - Devices and entities registry
  - `webhooks.db` (sports-data) - Webhook subscriptions
  - WAL mode enabled for concurrent access
  - File-based backups (simple `cp` command)

**Backup Strategy:**
```bash
# InfluxDB backup
docker exec ha-ingestor-data-api influx backup /backup/

# SQLite backup (simple file copy - safe with WAL mode)
docker cp ha-ingestor-data-api:/app/data/metadata.db ./backups/sqlite/
docker cp ha-ingestor-sports-data:/app/data/webhooks.db ./backups/sqlite/
```

