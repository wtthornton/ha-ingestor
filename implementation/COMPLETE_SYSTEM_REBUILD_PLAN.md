# Complete System Rebuild Plan
**Generated:** October 14, 2025  
**Purpose:** Full review and clean rebuild of HA-Ingestor Docker system  
**Reviewed By:** BMAD Master

---

## Executive Summary

✅ **Overall Status:** System is ready for complete rebuild with minor issues to address  
✅ **Docker Configs:** Well-structured with multi-stage builds and security best practices  
✅ **Service Configuration:** Comprehensive with proper health checks  
⚠️ **Issues Found:** 7 issues identified (1 critical, 3 warnings, 3 minor)  
✅ **Recommendation:** Proceed with rebuild after addressing critical issue

---

## 📋 Review Findings

### 1. Docker Compose Configuration Review

#### Main `docker-compose.yml` ✅
**Status:** Production-ready  
**Services:** 13 microservices  
**Strengths:**
- ✅ Comprehensive service definitions
- ✅ Health checks on all services
- ✅ Resource limits defined
- ✅ Logging configured
- ✅ Proper dependency management
- ✅ SQLite volume for metadata persistence
- ✅ Archived sports-api with clear documentation

**Issues:**
- ⚠️ **WARNING:** Missing data-api service dependency on admin-api (line 186 references websocket-ingestion but not data-api)
- ⚠️ **WARNING:** No .dockerignore in root directory (only in service directories)
- ℹ️ **MINOR:** Port mapping inconsistency - admin-api maps 8003:8004 instead of 8004:8004

#### Production `docker-compose.prod.yml` ⚠️
**Status:** Needs updates  
**Issues:**
- ❌ **CRITICAL:** Missing several services present in main compose file:
  - data-api (port 8006) - **Critical for device/entity browsing**
  - log-aggregator (port 8015)
  - sports-data (port 8005)
  - carbon-intensity (port 8010)
  - electricity-pricing (port 8011)
  - air-quality (port 8012)
  - calendar (port 8013)
  - smart-meter (port 8014)
- ⚠️ Different build contexts (prod uses service-specific, main uses root)
- ⚠️ Enhanced security features (read-only, security_opt) not in main file
- ℹ️ More detailed resource limits in prod vs. main

#### Development `docker-compose.dev.yml` ✅
**Status:** Good for development  
**Strengths:**
- ✅ Volume mounts for hot-reload
- ✅ HA simulator included
- ✅ Debug logging enabled
- ✅ Proper service dependencies

---

### 2. Dockerfile Review

#### ✅ **Excellent Examples:**

**`services/websocket-ingestion/Dockerfile`**
- ✅ Multi-stage build (builder + production)
- ✅ Non-root user (appuser:1001)
- ✅ Alpine-based for minimal size
- ✅ Proper health check
- ✅ Layer caching optimization
- ✅ Python 3.12 (latest stable)

**`services/data-api/Dockerfile`**
- ✅ Multi-stage build
- ✅ Minimal runtime dependencies
- ✅ Health check included
- ✅ Python 3.11 (stable)

**`services/health-dashboard/Dockerfile`**
- ✅ Three-stage build (deps → builder → production)
- ✅ Nginx-based production stage
- ✅ Non-root user configuration
- ✅ Cache mount for npm install
- ✅ Node 18 LTS

#### ⚠️ **Issues Found:**
- ℹ️ **MINOR:** No USER directive in data-api Dockerfile (runs as root)
- ℹ️ **MINOR:** Inconsistent Python versions (3.11 vs 3.12) across services

---

### 3. Service Configuration Review

#### All Services Have:
- ✅ Health check endpoints at `/health`
- ✅ Proper environment variable configuration
- ✅ Logging configured
- ✅ CORS settings (where applicable)
- ✅ Structured FastAPI/Flask applications

#### Service Dependencies (Validated):
```
InfluxDB (base)
  ↓
enrichment-pipeline → data-api
  ↓                      ↓
websocket-ingestion → admin-api → health-dashboard
  ↓
data-retention
  ↓
external services (carbon, electricity, air-quality, etc.)
```

**Issue:** Admin-api depends on websocket-ingestion but not data-api (lines 185-188 in docker-compose.yml)

---

### 4. Dependencies Review

#### Python Services ✅
**`services/data-api/requirements.txt`:**
- ✅ FastAPI 0.104.1 (production-ready)
- ✅ Pydantic 2.4.2 (modern validation)
- ✅ SQLAlchemy 2.0.25 (latest async support)
- ✅ InfluxDB clients (both v2 and v3)
- ✅ Proper test dependencies included

**Pattern:** All Python services follow similar dependency structure

#### Node.js Dashboard ✅
**`services/health-dashboard/package.json`:**
- ✅ React 18.2.0
- ✅ TypeScript 5.2.2
- ✅ Vite 5.0.8 (modern build tool)
- ✅ Vitest for testing
- ✅ Playwright for E2E tests
- ✅ Chart.js & Recharts for visualizations
- ✅ TailwindCSS for styling

---

### 5. Environment Configuration Review

#### Main `.env` Template (`infrastructure/env.example`) ✅
**Coverage:** Comprehensive  
**Sections:**
- ✅ Home Assistant configuration
- ✅ Nabu Casa fallback
- ✅ InfluxDB configuration
- ✅ Weather API configuration
- ✅ External services (carbon, electricity, air quality, etc.)
- ✅ WebSocket retry configuration
- ✅ Authentication configuration
- ✅ Data retention configuration
- ✅ Service ports
- ✅ Timezone configuration

**Issues:**
- ℹ️ **MINOR:** Some default values use placeholders (e.g., "your_token_here")
- ✅ Good: Includes helpful comments for each section

#### Service-Specific Templates ✅
- ✅ `.env.influxdb.template` - InfluxDB-specific settings
- ✅ `.env.websocket.template` - WebSocket-specific settings
- ✅ `.env.weather.template` - Weather API settings
- ✅ `.env.sports.template` - Sports API settings

---

### 6. Deployment Scripts Review

#### `scripts/deploy.sh` ✅
**Status:** Production-ready  
**Features:**
- ✅ Prerequisites checking
- ✅ Configuration validation
- ✅ Directory setup
- ✅ Image pulling and building
- ✅ Service deployment with graceful shutdown
- ✅ Health check validation
- ✅ Post-deployment testing
- ✅ Multiple command support (deploy, validate, status, logs, stop, restart)

**Strengths:**
- ✅ Colored output for readability
- ✅ Proper error handling
- ✅ Validates required environment variables
- ✅ Waits for services to be healthy
- ✅ Tests service connectivity

---

### 7. Network Configuration Review ✅

#### Main Compose Network:
```yaml
networks:
  homeiq-network:
    driver: bridge
```

#### Production Compose Network:
```yaml
networks:
  homeiq-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.bridge.name: homeiq-br
      com.docker.network.bridge.enable_icc: "true"
      com.docker.network.bridge.enable_ip_masquerade: "true"
```

**Assessment:**
- ✅ Proper bridge network configuration
- ✅ Production network has explicit subnet
- ✅ All services on same network for inter-service communication
- ✅ No exposed ports to external networks (only localhost)

---

### 8. Volume Configuration Review ✅

#### Main Compose Volumes:
```yaml
volumes:
  influxdb_data:         # InfluxDB time-series data
  influxdb_config:       # InfluxDB configuration
  data_retention_backups: # Backup storage
  ha_ingestor_logs:      # Shared logs
  sqlite-data:           # SQLite metadata database
```

#### Production Compose Volumes (Enhanced):
```yaml
volumes:
  influxdb_data:         # + influxdb_logs
  websocket_logs:
  enrichment_logs:
  weather_logs:
  admin_logs:
  data_retention_backups:
  data_retention_logs:
  dashboard_logs:
```

**Assessment:**
- ✅ Proper data persistence for InfluxDB
- ✅ SQLite database properly persisted
- ✅ Backup volumes configured
- ✅ Production has granular log volumes
- ⚠️ Main compose uses single shared log volume vs. per-service in prod

---

### 9. Security Review

#### Strengths ✅
- ✅ Non-root users in most Dockerfiles
- ✅ Multi-stage builds minimize attack surface
- ✅ Read-only filesystems in production compose
- ✅ Security options (no-new-privileges) in production
- ✅ Resource limits prevent DoS
- ✅ Environment variables for secrets (not hardcoded)
- ✅ Proper .dockerignore files exclude sensitive data
- ✅ CORS configured (not wildcard in production)

#### Concerns ⚠️
- ⚠️ data-api Dockerfile runs as root (no USER directive)
- ⚠️ Main compose has `ENABLE_AUTH=false` default
- ℹ️ Default passwords in env.example (expected, needs user override)
- ℹ️ Wildcard CORS in main compose (`CORS_ORIGINS=*`)

---

### 10. .dockerignore Review ✅

**Found in:**
- ✅ `services/websocket-ingestion/.dockerignore`
- ✅ `services/admin-api/.dockerignore`
- ✅ `services/enrichment-pipeline/.dockerignore`
- ✅ `services/data-retention/.dockerignore`
- ✅ `services/weather-api/.dockerignore`
- ✅ `services/health-dashboard/.dockerignore`

**Content Review:**
- ✅ Excludes `__pycache__`, `*.pyc`, `*.pyo`
- ✅ Excludes `.git/`, `.gitignore`
- ✅ Excludes documentation (`docs/`, `implementation/`, `*.md`)
- ✅ Excludes test artifacts
- ✅ Excludes environment files (`.env`, `.venv`)
- ✅ Excludes logs

**Missing:**
- ⚠️ No root-level `.dockerignore` for context builds

---

## 🔥 Critical Issues to Address Before Rebuild

### 1. ❌ **CRITICAL: Missing data-api in production compose**
**File:** `docker-compose.prod.yml`  
**Impact:** Production deployment will fail - dashboard cannot access device/entity data  
**Fix Required:** Add data-api service definition to docker-compose.prod.yml

### 2. ⚠️ **WARNING: Incomplete service dependencies**
**File:** `docker-compose.yml` (line 186)  
**Impact:** Race condition on startup - admin-api may start before data-api is ready  
**Fix Required:** Add data-api to admin-api dependencies

### 3. ⚠️ **WARNING: Missing services in production**
**File:** `docker-compose.prod.yml`  
**Impact:** Feature loss in production (sports, external data services, log aggregation)  
**Fix Required:** Add all services from main compose to prod compose

---

## 🚀 Complete Rebuild Procedure

### Phase 1: Pre-Rebuild Preparation

#### Step 1.1: Backup Current State
```bash
# Create backup directory
mkdir -p ~/homeiq-backup-$(date +%Y%m%d)
cd ~/homeiq-backup-$(date +%Y%m%d)

# Backup InfluxDB data
docker exec homeiq-influxdb influx backup /tmp/backup
docker cp homeiq-influxdb:/tmp/backup ./influxdb-backup

# Backup SQLite database
docker cp homeiq-data-api:/app/data/metadata.db ./metadata.db.backup

# Backup environment files
cp ~/homeiq/.env ./env.backup
cp ~/homeiq/infrastructure/.env.* ./

# Backup current docker-compose.yml
cp ~/homeiq/docker-compose.yml ./docker-compose.yml.backup

# Export current images list
docker images | grep homeiq > docker-images-list.txt

# Export current volumes list
docker volume ls | grep homeiq > docker-volumes-list.txt

# Export container list and status
docker ps -a | grep homeiq > docker-containers-status.txt
```

#### Step 1.2: Document Current State
```bash
# Get service health status
curl http://localhost:8003/api/v1/health > health-status.json

# Get InfluxDB buckets
curl http://localhost:8086/api/v2/buckets \
  -H "Authorization: Token ${INFLUXDB_TOKEN}" > influxdb-buckets.json

# Check disk usage
du -sh ~/homeiq/* > disk-usage.txt
```

#### Step 1.3: Fix Critical Issues

**Fix 1: Update docker-compose.prod.yml**
```bash
cd ~/homeiq

# Backup production compose
cp docker-compose.prod.yml docker-compose.prod.yml.backup

# Option A: Use main compose as template for production
# (Recommended - main compose is more complete)
cp docker-compose.yml docker-compose.prod.yml

# Then add production-specific enhancements:
# - Enhanced resource limits
# - Security options (read-only, no-new-privileges)
# - Detailed logging configuration
# - Specific network subnet
```

**Fix 2: Update service dependencies**
```bash
# Edit docker-compose.yml
# Find admin-api service (around line 182)
# Update depends_on section to include data-api:

# FROM:
depends_on:
  influxdb:
    condition: service_healthy
  websocket-ingestion:
    condition: service_healthy
  enrichment-pipeline:
    condition: service_healthy

# TO:
depends_on:
  influxdb:
    condition: service_healthy
  websocket-ingestion:
    condition: service_healthy
  enrichment-pipeline:
    condition: service_healthy
  data-api:
    condition: service_healthy
```

**Fix 3: Add root .dockerignore**
```bash
cat > .dockerignore << 'EOF'
# Git
.git/
.gitignore
.gitattributes

# Documentation
docs/
implementation/
*.md
!README.md

# Tests
tests/
test-results/
test-reports/

# Environment
.env*
!.env.example
infrastructure/env.production

# Build artifacts
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log
ha_events.log

# Temporary
tmp/
temp/
*.tmp

# Backups
*backup*/
*.backup
*.bak

# Database files
*.db
*.sqlite
*.sqlite3

# Docker
**/Dockerfile*.backup
docker-compose*.backup
EOF
```

---

### Phase 2: Complete System Teardown

#### Step 2.1: Stop All Services
```bash
cd ~/homeiq

# Stop all services gracefully (30-second timeout)
docker-compose down --timeout 30

# Verify all containers stopped
docker ps | grep homeiq
# Should show no results

# Check for stuck containers
docker ps -a | grep homeiq
```

#### Step 2.2: Remove All Containers
```bash
# Force remove any remaining containers
docker ps -a --filter "name=homeiq" -q | xargs -r docker rm -f

# Verify removal
docker ps -a | grep homeiq
# Should show no results
```

#### Step 2.3: Remove All Images
```bash
# List all homeiq images
docker images | grep homeiq

# Remove all homeiq images (force)
docker images --filter=reference='*homeiq*' -q | xargs -r docker rmi -f

# Remove unused/dangling images
docker image prune -f

# Verify removal
docker images | grep homeiq
# Should show no results
```

#### Step 2.4: Handle Volumes (IMPORTANT!)

**Option A: Preserve data (RECOMMENDED)**
```bash
# Keep volumes for data persistence
# Volumes to preserve:
# - influxdb_data (time-series data)
# - influxdb_config (InfluxDB configuration)
# - sqlite-data (device/entity metadata)
# - data_retention_backups (backup data)

# List volumes
docker volume ls | grep homeiq

# Do NOT remove volumes if you want to keep data
```

**Option B: Complete clean slate (DESTRUCTIVE)**
```bash
# ⚠️ WARNING: This deletes ALL data!
# Only use if you want to start completely fresh

# Remove all homeiq volumes
docker volume ls --filter name=homeiq -q | xargs -r docker volume rm

# Verify removal
docker volume ls | grep homeiq
# Should show no results
```

**Option C: Selective removal**
```bash
# Remove only log volumes, keep data volumes
docker volume rm homeiq_ha_ingestor_logs
docker volume rm homeiq_websocket_logs
docker volume rm homeiq_enrichment_logs
# etc...

# Keep these volumes:
# - homeiq_influxdb_data
# - homeiq_influxdb_config
# - homeiq_sqlite-data
# - homeiq_data_retention_backups
```

#### Step 2.5: Remove Networks
```bash
# Remove homeiq network
docker network rm homeiq-network

# Remove any dev networks
docker network rm homeiq-network-dev

# Clean up unused networks
docker network prune -f

# Verify removal
docker network ls | grep homeiq
# Should show no results
```

#### Step 2.6: Clean Build Cache
```bash
# Remove Docker build cache
docker builder prune -a -f

# This frees up disk space and ensures fresh builds
```

#### Step 2.7: Final Verification
```bash
# Verify everything is removed
echo "=== CONTAINERS ==="
docker ps -a | grep homeiq

echo "=== IMAGES ==="
docker images | grep homeiq

echo "=== VOLUMES ==="
docker volume ls | grep homeiq

echo "=== NETWORKS ==="
docker network ls | grep homeiq

# All should show no results (except volumes if preserving data)
```

---

### Phase 3: System Rebuild

#### Step 3.1: Prepare Environment
```bash
cd ~/homeiq

# Ensure we're on the latest code
git status
# Commit or stash any local changes if needed

# Verify environment files exist
ls -la .env infrastructure/.env.*

# If missing, copy from templates
if [ ! -f .env ]; then
    cp infrastructure/env.example .env
    echo "⚠️  Edit .env with your configuration!"
fi
```

#### Step 3.2: Validate Configuration
```bash
# Run configuration validation
./scripts/deploy.sh validate

# If validation fails, fix issues before proceeding
```

#### Step 3.3: Build Images
```bash
# Build all images from scratch (no cache)
docker-compose build --no-cache --parallel

# This will take 10-20 minutes depending on your system

# Monitor build progress
# Each service will show build output
```

#### Step 3.4: Verify Build Success
```bash
# List newly built images
docker images | grep homeiq

# Expected images:
# - homeiq-websocket
# - homeiq-enrichment
# - homeiq-admin
# - homeiq-data-api
# - homeiq-data-retention
# - homeiq-dashboard
# - homeiq-sports-data
# - homeiq-log-aggregator
# - homeiq-carbon-intensity
# - homeiq-electricity-pricing
# - homeiq-air-quality
# - homeiq-calendar
# - homeiq-smart-meter

# Plus external images:
# - influxdb:2.7
```

---

### Phase 4: Service Deployment

#### Step 4.1: Start Core Services
```bash
# Start in detached mode
docker-compose up -d

# Services will start in dependency order:
# 1. influxdb
# 2. enrichment-pipeline, data-api
# 3. websocket-ingestion
# 4. admin-api
# 5. health-dashboard
# 6. data-retention
# 7. external services
```

#### Step 4.2: Monitor Startup
```bash
# Watch logs in real-time
docker-compose logs -f

# Or watch specific service
docker-compose logs -f influxdb

# In another terminal, check status
watch -n 2 'docker-compose ps'

# Wait for all services to show "healthy"
# This may take 2-5 minutes
```

#### Step 4.3: Verify Health Checks
```bash
# Check all services are healthy
docker-compose ps

# Expected output:
# All services should show "Up (healthy)"

# If any service shows "starting" wait longer
# If any service shows "unhealthy" check logs:
docker-compose logs <service-name>
```

---

### Phase 5: Post-Deployment Validation

#### Step 5.1: Test Service Endpoints
```bash
# Test InfluxDB
curl -v http://localhost:8086/health
# Expected: 200 OK

# Test WebSocket Ingestion
curl -v http://localhost:8001/health
# Expected: 200 OK, JSON response

# Test Enrichment Pipeline
curl -v http://localhost:8002/health
# Expected: 200 OK

# Test Admin API
curl -v http://localhost:8003/api/v1/health
# Expected: 200 OK, comprehensive health data

# Test Data API
curl -v http://localhost:8006/health
# Expected: 200 OK

# Test Data Retention
curl -v http://localhost:8080/health
# Expected: 200 OK

# Test Sports Data
curl -v http://localhost:8005/health
# Expected: 200 OK

# Test Log Aggregator
curl -v http://localhost:8015/health
# Expected: 200 OK

# Test Dashboard
curl -v http://localhost:3000
# Expected: 200 OK, HTML response
```

#### Step 5.2: Test Dashboard Access
```bash
# Open dashboard in browser
# Linux:
xdg-open http://localhost:3000

# macOS:
open http://localhost:3000

# Windows:
start http://localhost:3000

# Verify:
# - Dashboard loads without errors
# - All tabs are accessible
# - Service status shows green
# - No console errors (F12 developer tools)
```

#### Step 5.3: Test Home Assistant Connection
```bash
# Check websocket service logs
docker-compose logs websocket-ingestion | tail -50

# Look for:
# ✅ "Connected to Home Assistant"
# ✅ "Subscribed to state_changed events"
# ✅ "Received event" (if HA is active)

# If connection fails:
# - Check HOME_ASSISTANT_URL in .env
# - Check HOME_ASSISTANT_TOKEN is valid
# - Check HA is accessible: curl ${HOME_ASSISTANT_URL}
```

#### Step 5.4: Verify Database Connectivity

**InfluxDB:**
```bash
# Check InfluxDB buckets
docker exec homeiq-influxdb influx bucket list

# Expected: home_assistant_events bucket exists

# Check if data is being written (wait 1 minute for events)
docker exec homeiq-influxdb influx query \
  'from(bucket:"home_assistant_events") |> range(start: -1m) |> limit(n:10)'
```

**SQLite:**
```bash
# Check SQLite database
docker exec homeiq-data-api ls -lh /app/data/metadata.db

# Should show database file with size > 0

# Check devices table
docker exec homeiq-data-api sqlite3 /app/data/metadata.db \
  "SELECT COUNT(*) FROM devices;"

# Should show device count (might be 0 on fresh install)
```

#### Step 5.5: Test API Endpoints

**Device API:**
```bash
# Get all devices
curl http://localhost:8006/api/devices | jq

# Get device details
curl http://localhost:8006/api/devices/<device_id> | jq
```

**Events API:**
```bash
# Get recent events
curl "http://localhost:8006/api/events?limit=10" | jq
```

**Sports API:**
```bash
# Get NFL games
curl http://localhost:8005/api/nfl/games | jq

# Get NHL games
curl http://localhost:8005/api/nhl/games | jq
```

#### Step 5.6: Run Automated Tests
```bash
# Run service connectivity tests
./scripts/test-services.sh

# Run API key validation
python tests/test_api_keys.py

# Run system integration test
python tests/test_system_integration.py

# All tests should pass
```

---

### Phase 6: Data Restoration (If Needed)

#### Step 6.1: Restore InfluxDB Data
```bash
# If you backed up InfluxDB in Phase 1
cd ~/homeiq-backup-$(date +%Y%m%d)

# Copy backup into container
docker cp ./influxdb-backup homeiq-influxdb:/tmp/backup

# Restore from backup
docker exec homeiq-influxdb influx restore /tmp/backup

# Verify restoration
docker exec homeiq-influxdb influx bucket list
```

#### Step 6.2: Restore SQLite Data
```bash
# If you backed up SQLite in Phase 1
cd ~/homeiq-backup-$(date +%Y%m%d)

# Stop data-api service
docker-compose stop data-api

# Restore database
docker cp ./metadata.db.backup homeiq-data-api:/app/data/metadata.db

# Fix permissions
docker exec homeiq-data-api chown appuser:appgroup /app/data/metadata.db

# Restart service
docker-compose start data-api

# Wait for healthy
docker-compose ps data-api
```

---

### Phase 7: Production Hardening (Optional)

#### Step 7.1: Enable Authentication
```bash
# Edit .env
nano .env

# Set:
ENABLE_AUTH=true
JWT_SECRET_KEY=<generate-random-key>
ADMIN_PASSWORD=<strong-password>

# Restart services
docker-compose restart admin-api
```

#### Step 7.2: Configure CORS
```bash
# Edit .env
nano .env

# Set specific origins instead of wildcard:
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Restart services
docker-compose restart admin-api data-api
```

#### Step 7.3: Set Up SSL/TLS (If Exposing Externally)
```bash
# Use reverse proxy (nginx, Caddy, Traefik)
# Configure SSL certificates (Let's Encrypt)
# Update CORS and environment URLs

# Example nginx config:
# server {
#     listen 443 ssl;
#     server_name yourdomain.com;
#     
#     ssl_certificate /path/to/cert.pem;
#     ssl_certificate_key /path/to/key.pem;
#     
#     location / {
#         proxy_pass http://localhost:3000;
#     }
# }
```

#### Step 7.4: Configure Backups
```bash
# Set up automated backups
crontab -e

# Add backup job (daily at 2 AM):
0 2 * * * /home/user/homeiq/scripts/backup-influxdb.sh

# Add SQLite backup:
0 2 * * * docker cp homeiq-data-api:/app/data/metadata.db \
          /backup/metadata-$(date +\%Y\%m\%d).db
```

---

## 📊 Validation Checklist

After completing the rebuild, verify the following:

### Infrastructure Checks
- [ ] All containers running: `docker-compose ps`
- [ ] All services healthy: All show "Up (healthy)" status
- [ ] Networks created: `docker network ls | grep homeiq`
- [ ] Volumes mounted: `docker volume ls | grep homeiq`
- [ ] No error logs: `docker-compose logs --tail=100`

### Service Health Checks
- [ ] InfluxDB: `curl http://localhost:8086/health` → 200 OK
- [ ] WebSocket: `curl http://localhost:8001/health` → 200 OK
- [ ] Enrichment: `curl http://localhost:8002/health` → 200 OK
- [ ] Admin API: `curl http://localhost:8003/api/v1/health` → 200 OK
- [ ] Data API: `curl http://localhost:8006/health` → 200 OK
- [ ] Data Retention: `curl http://localhost:8080/health` → 200 OK
- [ ] Sports Data: `curl http://localhost:8005/health` → 200 OK
- [ ] Log Aggregator: `curl http://localhost:8015/health` → 200 OK
- [ ] Dashboard: `curl http://localhost:3000` → 200 OK

### Functional Checks
- [ ] Dashboard loads in browser
- [ ] All dashboard tabs accessible (12 tabs total)
- [ ] Home Assistant connection established (check websocket logs)
- [ ] InfluxDB receiving data (check bucket)
- [ ] SQLite devices populated (check data-api)
- [ ] Sports data loading (check sports-data endpoint)
- [ ] No console errors in browser (F12 developer tools)
- [ ] Service logs show no errors

### Integration Checks
- [ ] HA WebSocket connected: `docker-compose logs websocket-ingestion | grep "Connected"`
- [ ] Events flowing: `curl "http://localhost:8006/api/events?limit=1" | jq`
- [ ] Devices discovered: `curl http://localhost:8006/api/devices | jq`
- [ ] Weather enrichment working (if configured)
- [ ] Sports data available: `curl http://localhost:8005/api/nfl/games | jq`

### Performance Checks
- [ ] Dashboard loads in <3 seconds
- [ ] API responses <100ms for health endpoints
- [ ] No memory leaks (monitor with `docker stats`)
- [ ] CPU usage reasonable (<50% average)
- [ ] Disk usage acceptable (`df -h`)

### Security Checks
- [ ] No exposed secrets in logs
- [ ] Environment variables properly set
- [ ] Services running with proper permissions
- [ ] No unnecessary ports exposed
- [ ] Authentication enabled (if configured)
- [ ] CORS properly configured

---

## 🚨 Troubleshooting Guide

### Issue: Services Not Starting

**Symptoms:**
- Container exits immediately
- Status shows "Restarting"
- Health check fails

**Diagnosis:**
```bash
# Check logs
docker-compose logs <service-name>

# Check container status
docker-compose ps

# Inspect container
docker inspect homeiq-<service-name>
```

**Common Causes:**
1. **Missing environment variable**
   - Check `.env` file has all required variables
   - Compare with `infrastructure/env.example`

2. **Port conflict**
   - Check if port already in use: `netstat -tulpn | grep <port>`
   - Change port in `docker-compose.yml` or stop conflicting service

3. **Volume permission issue**
   - Check volume permissions: `docker exec <container> ls -la /path`
   - Fix with: `docker exec <container> chown -R appuser:appgroup /path`

4. **Dependency not ready**
   - Wait longer for dependencies to start
   - Check dependency service logs

---

### Issue: Home Assistant Connection Failed

**Symptoms:**
- WebSocket service logs show connection errors
- "401 Unauthorized" or "Connection refused"
- No events in dashboard

**Diagnosis:**
```bash
# Check websocket logs
docker-compose logs websocket-ingestion | grep -i error

# Test HA connectivity
curl -v ${HOME_ASSISTANT_URL}

# Test token validity
curl -H "Authorization: Bearer ${HOME_ASSISTANT_TOKEN}" \
     ${HOME_ASSISTANT_URL}/api/
```

**Solutions:**
1. **Invalid token**
   - Generate new Long-Lived Access Token in HA
   - Update `HOME_ASSISTANT_TOKEN` in `.env`
   - Restart: `docker-compose restart websocket-ingestion`

2. **Wrong URL**
   - Check `HOME_ASSISTANT_URL` in `.env`
   - Ensure URL is accessible from Docker network
   - Use `http://host.docker.internal:8123` if HA on same machine

3. **Network issue**
   - Check firewall rules
   - Verify HA is running: `curl ${HOME_ASSISTANT_URL}`
   - Check Docker DNS: `docker-compose exec websocket-ingestion ping homeassistant.local`

---

### Issue: Dashboard Shows 502 Error

**Symptoms:**
- Dashboard loads but API calls fail
- Console shows 502 Bad Gateway
- Nginx errors in logs

**Diagnosis:**
```bash
# Check dashboard logs
docker-compose logs health-dashboard

# Check admin-api logs
docker-compose logs admin-api

# Test admin-api directly
curl http://localhost:8003/api/v1/health
```

**Solutions:**
1. **Admin API not running**
   - Check status: `docker-compose ps admin-api`
   - Start if stopped: `docker-compose up -d admin-api`

2. **Nginx proxy configuration**
   - Check `services/health-dashboard/nginx.conf`
   - Verify proxy_pass URL matches admin-api container name
   - Restart dashboard: `docker-compose restart health-dashboard`

3. **Network issue**
   - Check services on same network: `docker network inspect homeiq-network`
   - Verify admin-api hostname resolves: 
     `docker-compose exec health-dashboard ping admin-api`

---

### Issue: InfluxDB Not Receiving Data

**Symptoms:**
- InfluxDB healthy but no data
- Events dashboard empty
- Queries return no results

**Diagnosis:**
```bash
# Check InfluxDB logs
docker-compose logs influxdb | grep -i error

# Check websocket logs
docker-compose logs websocket-ingestion | grep -i influx

# Check enrichment logs
docker-compose logs enrichment-pipeline | grep -i influx

# Verify bucket exists
docker exec homeiq-influxdb influx bucket list

# Check for recent data
docker exec homeiq-influxdb influx query \
  'from(bucket:"home_assistant_events") |> range(start: -1h) |> limit(n:1)'
```

**Solutions:**
1. **Wrong bucket name**
   - Check `INFLUXDB_BUCKET` in `.env`
   - Verify bucket exists: `docker exec homeiq-influxdb influx bucket list`
   - Create if missing: 
     `docker exec homeiq-influxdb influx bucket create -n home_assistant_events -o homeiq`

2. **Invalid token**
   - Check `INFLUXDB_TOKEN` in `.env`
   - Verify token works: 
     `curl -H "Authorization: Token ${INFLUXDB_TOKEN}" http://localhost:8086/api/v2/buckets`
   - Generate new token if needed

3. **No events from HA**
   - Check Home Assistant connection (see above)
   - Verify events are being received: `docker-compose logs websocket-ingestion | grep "Received event"`
   - Trigger a test event in HA (toggle a light)

---

### Issue: High Memory Usage

**Symptoms:**
- Docker stats shows high memory
- System becoming slow
- Out of memory errors

**Diagnosis:**
```bash
# Check memory usage
docker stats --no-stream

# Check specific service
docker stats homeiq-influxdb --no-stream

# Check container logs for OOM
docker-compose logs | grep -i "out of memory"
```

**Solutions:**
1. **InfluxDB using too much memory**
   - Reduce cache size in `influxdb.conf`
   - Increase retention policies to archive old data
   - Run data retention cleanup: 
     `curl -X POST http://localhost:8080/api/retention/cleanup`

2. **Services not respecting resource limits**
   - Check resource limits in `docker-compose.yml`
   - Adjust limits based on available memory
   - Restart with new limits: `docker-compose up -d --force-recreate`

3. **Memory leak**
   - Restart leaking service: `docker-compose restart <service>`
   - Check for updates/patches
   - Report issue with logs

---

### Issue: Slow Dashboard Performance

**Symptoms:**
- Dashboard takes long to load
- UI feels sluggish
- API calls slow

**Diagnosis:**
```bash
# Check API response times
time curl http://localhost:8003/api/v1/health

# Check database queries
docker-compose logs data-api | grep -i "slow query"

# Check resource usage
docker stats --no-stream
```

**Solutions:**
1. **Too much data**
   - Reduce query ranges in dashboard
   - Implement pagination
   - Run data archival: 
     `curl -X POST http://localhost:8080/api/retention/archive`

2. **Database performance**
   - Check SQLite index status
   - Rebuild indexes if needed
   - Consider vacuuming database

3. **Network latency**
   - Check if services on different networks
   - Use service names instead of IPs
   - Optimize API calls (reduce polling frequency)

---

## 📈 Performance Optimization

### After Successful Rebuild

1. **Monitor Resource Usage**
   ```bash
   # Watch resources continuously
   watch -n 2 'docker stats --no-stream'
   
   # Log resource usage
   docker stats --no-stream >> ~/homeiq-stats.log
   ```

2. **Optimize InfluxDB**
   ```bash
   # Set up retention policies
   docker exec homeiq-influxdb influx task create \
     --name "retention-policy" \
     --every 24h \
     --script "from(bucket:\"home_assistant_events\") |> range(start: -30d) |> drop()"
   
   # Enable downsampling for old data
   # (reduces storage and improves query performance)
   ```

3. **Optimize SQLite**
   ```bash
   # Run VACUUM periodically
   docker exec homeiq-data-api sqlite3 /app/data/metadata.db "VACUUM;"
   
   # Rebuild indexes
   docker exec homeiq-data-api sqlite3 /app/data/metadata.db "REINDEX;"
   ```

4. **Set Up Monitoring**
   ```bash
   # Install Grafana for monitoring (optional)
   # Create dashboards for:
   # - Service health
   # - API response times
   # - Database performance
   # - Resource usage
   ```

---

## 📝 Post-Rebuild Checklist

- [ ] All services running and healthy
- [ ] Home Assistant connected and receiving events
- [ ] Dashboard accessible and functional
- [ ] All API endpoints responding
- [ ] Data flowing to InfluxDB
- [ ] SQLite database populated
- [ ] Sports data loading (if configured)
- [ ] External services working (if configured)
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Documentation updated
- [ ] Team notified of rebuild

---

## 🎯 Success Criteria

✅ **Rebuild is successful when:**
1. All 13+ services running with "healthy" status
2. Dashboard loads in browser without errors
3. Home Assistant connection established
4. Events flowing to InfluxDB
5. Devices populated in SQLite
6. All API endpoints responding <100ms
7. No error messages in logs
8. Memory usage <70% of allocated
9. CPU usage stable <50% average
10. All validation checks passing

---

## 📚 Additional Resources

- **Deployment Guide:** `docs/DEPLOYMENT_GUIDE.md`
- **Docker Structure:** `docs/DOCKER_STRUCTURE_GUIDE.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING_GUIDE.md`
- **API Documentation:** `docs/API_DOCUMENTATION.md`
- **Architecture:** `docs/architecture/`

---

## 💡 Tips for Future Maintenance

1. **Regular Backups**
   - Schedule automated backups daily
   - Test restore procedure monthly
   - Keep backups for 30 days

2. **Version Control**
   - Tag working configurations
   - Document changes in git commits
   - Keep docker-compose.yml.backup copies

3. **Monitoring**
   - Set up alerts for service failures
   - Monitor disk usage
   - Track API performance metrics

4. **Updates**
   - Update services one at a time
   - Test in development first
   - Have rollback plan ready

5. **Documentation**
   - Keep this document updated
   - Document custom configurations
   - Share knowledge with team

---

**Document Version:** 1.0  
**Last Updated:** October 14, 2025  
**Maintained By:** BMAD Master  
**Review Schedule:** Quarterly or after major changes

