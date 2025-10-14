# Deployment Plan: Epic 22 & 23 Implementation

**Date:** October 14, 2025  
**Epics:** Epic 22 (SQLite Metadata Storage) + Epic 23 (Enhanced Event Data Capture)  
**Priority:** HIGH  
**Risk Level:** MEDIUM (database changes + data model changes)

---

## 📋 Executive Summary

### What's Being Deployed

**Epic 22: SQLite Metadata Storage**
- ✅ New SQLite databases for metadata storage (devices, entities, webhooks)
- ✅ Alembic migrations for schema management
- ✅ Hybrid database architecture (InfluxDB + SQLite)
- ✅ 10x faster device/entity queries (<10ms vs ~50ms)

**Epic 23: Enhanced Event Data Capture**
- ✅ Context hierarchy tracking (`context_id`, `context_parent_id`)
- ✅ Device and area linkage (`device_id`, `area_id` tags)
- ✅ Time-based analytics (`duration_in_state_seconds`)
- ✅ Entity classification filtering
- ✅ Device metadata enrichment

### Services Affected

| Service | Changes | Risk |
|---------|---------|------|
| **data-api** | SQLite integration, new endpoints | MEDIUM |
| **websocket-ingestion** | Enhanced event capture, discovery cache | MEDIUM |
| **enrichment-pipeline** | Updated data processing | LOW |
| **sports-data** | SQLite webhook storage | LOW |
| **health-dashboard** | (Future - UI not updated yet) | N/A |

---

## ⚠️ Pre-Deployment Checklist

### 1. Environment Verification

- [ ] **Verify Docker is running** (version 24+)
  ```powershell
  docker --version
  docker-compose --version
  ```

- [ ] **Check disk space** (need ~2GB free for databases)
  ```powershell
  Get-PSDrive C | Select-Object Used,Free
  ```

- [ ] **Verify Home Assistant connection**
  ```powershell
  $env:HOME_ASSISTANT_URL = "http://your-ha-instance:8123"
  $env:HOME_ASSISTANT_TOKEN = "your-token-here"
  # Test connection
  curl "$env:HOME_ASSISTANT_URL/api/" -H "Authorization: Bearer $env:HOME_ASSISTANT_TOKEN"
  ```

### 2. Configuration Review

- [ ] **Review environment files**
  - `infrastructure/.env.websocket` - WebSocket configuration
  - `infrastructure/.env.weather` - Weather API settings
  - `infrastructure/.env.influxdb` - InfluxDB settings
  - `infrastructure/env.production` - Production overrides

- [ ] **Verify critical environment variables**
  ```powershell
  # Check if set
  echo $env:HOME_ASSISTANT_URL
  echo $env:HOME_ASSISTANT_TOKEN
  echo $env:INFLUXDB_TOKEN
  ```

### 3. Backup Current State

- [ ] **Backup InfluxDB data** (if exists)
  ```powershell
  docker-compose exec influxdb influx backup /var/lib/influxdb2/backup
  docker cp ha-ingestor-influxdb:/var/lib/influxdb2/backup ./backups/influxdb-backup-$(Get-Date -Format 'yyyy-MM-dd-HHmmss')
  ```

- [ ] **Backup any existing SQLite databases** (if redeploying)
  ```powershell
  # Create backup directory
  mkdir -p backups/sqlite-$(Get-Date -Format 'yyyy-MM-dd-HHmmss')
  
  # Backup data-api database
  docker cp ha-ingestor-data-api:/app/data/metadata.db ./backups/sqlite-backup/
  
  # Backup sports-data webhooks
  docker cp ha-ingestor-sports-data:/app/data/webhooks.db ./backups/sqlite-backup/
  ```

- [ ] **Export current git state**
  ```powershell
  git status > backups/git-status-$(Get-Date -Format 'yyyy-MM-dd-HHmmss').txt
  git diff > backups/git-diff-$(Get-Date -Format 'yyyy-MM-dd-HHmmss').txt
  ```

### 4. Code Review

- [ ] **Review modified files** (from git status)
  ```powershell
  git diff README.md
  git diff docs/architecture/data-models.md
  git diff docs/architecture/database-schema.md
  git diff services/data-api/src/devices_endpoints.py
  git diff services/websocket-ingestion/src/event_processor.py
  git diff services/websocket-ingestion/src/discovery_service.py
  git diff services/enrichment-pipeline/src/influxdb_wrapper.py
  ```

- [ ] **Verify no debug code left in**
  ```powershell
  git grep -n "console.log\|print(\|TODO\|FIXME" services/
  ```

---

## 🚀 Deployment Steps

### Phase 1: Stop and Clean (5 minutes)

**1.1 Stop all running services**
```powershell
cd c:\cursor\ha-ingestor
docker-compose down
```

**1.2 Verify all containers stopped**
```powershell
docker ps -a | Select-String "ha-ingestor"
```

**1.3 Clean old images (optional - fresh start)**
```powershell
# Remove old service images
docker-compose down --rmi local

# Prune dangling images
docker image prune -f
```

### Phase 2: Database Setup (10 minutes)

**2.1 Start InfluxDB first**
```powershell
docker-compose up -d influxdb
```

**2.2 Wait for InfluxDB to be healthy**
```powershell
# Wait ~30 seconds
Start-Sleep -Seconds 30

# Verify health
docker-compose ps influxdb
curl http://localhost:8086/health
```

**2.3 Verify InfluxDB initialization**
```powershell
# Check if bucket was created
docker-compose exec influxdb influx bucket list
```

**Expected output:**
```
ID                      Name                    Retention       Shard group duration
abc123...              home_assistant_events   infinite        168h0m0s
```

**2.4 Create Docker volumes for SQLite databases**
```powershell
# These are automatically created, but verify they exist
docker volume ls | Select-String "ha-ingestor"
```

**Expected volumes:**
- `ha-ingestor_influxdb_data`
- `ha-ingestor_influxdb_config`
- `ha-ingestor_data_api_sqlite` (for data-api metadata)
- `ha-ingestor_sports_data_sqlite` (for webhooks)

### Phase 3: Build Services (10 minutes)

**3.1 Build all service images**
```powershell
docker-compose build
```

**3.2 Verify builds completed**
```powershell
docker images | Select-String "ha-ingestor"
```

**Expected images:**
- `ha-ingestor-websocket-ingestion`
- `ha-ingestor-enrichment-pipeline`
- `ha-ingestor-data-api`
- `ha-ingestor-admin-api`
- `ha-ingestor-data-retention`
- `ha-ingestor-sports-data`
- `ha-ingestor-health-dashboard`

### Phase 4: Run Database Migrations (5 minutes)

**4.1 Start data-api service temporarily (for migrations)**
```powershell
docker-compose up -d data-api
```

**4.2 Wait for service to be healthy**
```powershell
Start-Sleep -Seconds 10
docker-compose ps data-api
```

**4.3 Run Alembic migrations**
```powershell
# Run migrations to create SQLite tables
docker-compose exec data-api alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, add_devices_entities
```

**4.4 Verify database schema**
```powershell
# Check tables were created
docker-compose exec data-api sqlite3 /app/data/metadata.db ".tables"
```

**Expected tables:**
- `alembic_version`
- `devices`
- `entities`

**4.5 Verify database structure**
```powershell
docker-compose exec data-api sqlite3 /app/data/metadata.db ".schema devices"
docker-compose exec data-api sqlite3 /app/data/metadata.db ".schema entities"
```

### Phase 5: Start All Services (5 minutes)

**5.1 Start all services in correct order**
```powershell
# Start infrastructure services
docker-compose up -d influxdb

# Start backend services
docker-compose up -d websocket-ingestion enrichment-pipeline data-api admin-api data-retention

# Start sports services
docker-compose up -d sports-data

# Start frontend
docker-compose up -d health-dashboard
```

**5.2 Wait for all services to be healthy**
```powershell
Start-Sleep -Seconds 30
docker-compose ps
```

**Expected status:** All services should show "Up" and "(healthy)" status

**5.3 Check logs for startup errors**
```powershell
# Check each service
docker-compose logs --tail=50 websocket-ingestion
docker-compose logs --tail=50 enrichment-pipeline
docker-compose logs --tail=50 data-api
docker-compose logs --tail=50 admin-api
docker-compose logs --tail=50 sports-data
```

**Look for:**
- ✅ "Application startup complete"
- ✅ "SQLite database connected"
- ✅ "InfluxDB client initialized"
- ❌ Any ERROR or CRITICAL level messages

### Phase 6: Trigger Device Discovery (10 minutes)

**6.1 Verify WebSocket connection to Home Assistant**
```powershell
docker-compose logs --tail=100 websocket-ingestion | Select-String "connected\|authenticated"
```

**Expected:** Should see "WebSocket connected" and "Authentication successful"

**6.2 Trigger device discovery to populate SQLite**
```powershell
# Discovery runs automatically on startup, but can be triggered manually
curl -X POST http://localhost:8001/api/discover
```

**6.3 Wait for discovery to complete**
```powershell
# Monitor logs
docker-compose logs -f websocket-ingestion | Select-String "discovery\|device\|entity"
```

**Expected output:**
```
INFO: Discovered 42 devices
INFO: Discovered 156 entities
INFO: Discovery cache updated
INFO: SQLite metadata updated
```

**6.4 Verify devices were stored in SQLite**
```powershell
# Check device count
docker-compose exec data-api sqlite3 /app/data/metadata.db "SELECT COUNT(*) FROM devices;"

# Check entity count
docker-compose exec data-api sqlite3 /app/data/metadata.db "SELECT COUNT(*) FROM entities;"

# Sample some devices
docker-compose exec data-api sqlite3 /app/data/metadata.db "SELECT device_id, name, manufacturer, model FROM devices LIMIT 5;"
```

---

## 🧪 Testing & Verification

### Test Suite 1: Database Integration (10 minutes)

**Test 1.1: Verify InfluxDB connection**
```powershell
# Check health endpoint
curl http://localhost:8086/health

# Query recent events
curl "http://localhost:8006/api/events?limit=10"
```

**Expected:** Should return JSON with recent events

**Test 1.2: Verify SQLite databases exist**
```powershell
# data-api metadata database
docker-compose exec data-api ls -lh /app/data/metadata.db

# sports-data webhooks database
docker-compose exec sports-data ls -lh /app/data/webhooks.db
```

**Test 1.3: Query devices via API**
```powershell
# Get all devices
curl "http://localhost:8006/api/devices"

# Should return JSON with devices array
# Response time should be <20ms (much faster than before)
```

**Test 1.4: Query entities via API**
```powershell
# Get all entities
curl "http://localhost:8006/api/entities"

# Filter by domain
curl "http://localhost:8006/api/entities?domain=sensor"

# Filter by area
curl "http://localhost:8006/api/entities?area_id=living_room"
```

**Test 1.5: Verify database performance**
```powershell
# Time a device query (should be <10ms)
Measure-Command { curl "http://localhost:8006/api/devices" }

# Compare to InfluxDB event query (typically 30-50ms)
Measure-Command { curl "http://localhost:8006/api/events?limit=100" }
```

### Test Suite 2: Epic 23 Features (15 minutes)

**Test 2.1: Context hierarchy tracking**
```powershell
# Wait for some automation events to come through
Start-Sleep -Seconds 60

# Query events to find one with context_id
$events = curl "http://localhost:8006/api/events?limit=50" | ConvertFrom-Json
$contextId = $events.events[0].context_id

# Trace automation chain
curl "http://localhost:8006/api/v1/events/automation-trace/$contextId"
```

**Expected:** Should return chain of related events with parent relationships

**Test 2.2: Device and area linkage**
```powershell
# Get events from specific area (if you have areas defined)
curl "http://localhost:8006/api/events?area_id=living_room&limit=20"

# Get events from specific device
curl "http://localhost:8006/api/events?device_id=abc123&limit=20"
```

**Expected:** Should filter events by area/device

**Test 2.3: Time-based analytics**
```powershell
# Query state_changed events
curl "http://localhost:8006/api/events?event_type=state_changed&limit=10" | ConvertFrom-Json | Select-Object -First 1 | ConvertTo-Json -Depth 10
```

**Expected:** Events should include `duration_in_state_seconds` field

**Test 2.4: Entity classification**
```powershell
# Exclude diagnostic entities
curl "http://localhost:8006/api/events?exclude_category=diagnostic&limit=20"

# Show only diagnostic entities
curl "http://localhost:8006/api/events?entity_category=diagnostic&limit=20"
```

**Test 2.5: Device metadata enrichment**
```powershell
# Check that events include device metadata
curl "http://localhost:8006/api/events?limit=5" | ConvertFrom-Json | Select-Object -ExpandProperty events | Select-Object entity_id, manufacturer, model, sw_version
```

### Test Suite 3: Health & Monitoring (10 minutes)

**Test 3.1: Service health checks**
```powershell
# Check all service health
curl http://localhost:8001/health  # websocket-ingestion
curl http://localhost:8002/health  # enrichment-pipeline
curl http://localhost:8003/health  # admin-api
curl http://localhost:8006/health  # data-api
curl http://localhost:8005/health  # sports-data
```

**Expected:** All should return 200 OK with `{"status": "healthy"}`

**Test 3.2: Database health in health checks**
```powershell
# data-api health should include SQLite status
curl http://localhost:8006/health | ConvertFrom-Json
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-14T...",
  "databases": {
    "influxdb": "connected",
    "sqlite": "connected"
  }
}
```

**Test 3.3: WebSocket connection status**
```powershell
curl http://localhost:8001/health | ConvertFrom-Json
```

**Expected:**
```json
{
  "status": "healthy",
  "websocket": "connected",
  "home_assistant": "authenticated"
}
```

**Test 3.4: Check Docker container stats**
```powershell
docker stats --no-stream
```

**Expected:** Memory usage should be reasonable:
- InfluxDB: <512MB
- Each Python service: <128MB
- Frontend (nginx): <50MB

**Test 3.5: Monitor logs for errors**
```powershell
# Check for errors in last 100 lines
docker-compose logs --tail=100 | Select-String "ERROR\|CRITICAL\|FATAL"
```

**Expected:** No critical errors (warnings are OK)

### Test Suite 4: End-to-End Event Flow (15 minutes)

**Test 4.1: Trigger a real Home Assistant event**
```
1. Go to Home Assistant UI
2. Toggle a light or sensor
3. Wait 5 seconds
```

**Test 4.2: Verify event captured**
```powershell
# Query recent events
curl "http://localhost:8006/api/events?event_type=state_changed&limit=5"
```

**Expected:** Should see the triggered event within seconds

**Test 4.3: Verify event enrichment**
```powershell
# Get the most recent event and check fields
$event = curl "http://localhost:8006/api/events?limit=1" | ConvertFrom-Json | Select-Object -ExpandProperty events | Select-Object -First 1

# Check Epic 23 fields are present
$event | Select-Object entity_id, device_id, area_id, context_id, duration_in_state_seconds, manufacturer, model
```

**Expected fields:**
- `entity_id` - entity that changed
- `device_id` - device ID (new in Epic 23)
- `area_id` - area ID (new in Epic 23)
- `context_id` - context tracking (new in Epic 23)
- `duration_in_state_seconds` - time in previous state (new in Epic 23)
- `manufacturer` - device manufacturer (new in Epic 23)
- `model` - device model (new in Epic 23)

**Test 4.4: Verify event stored in InfluxDB**
```powershell
# Query InfluxDB directly
docker-compose exec influxdb influx query 'from(bucket: "home_assistant_events") |> range(start: -5m) |> limit(n: 1)'
```

**Test 4.5: Verify real-time event streaming**
```powershell
# Watch logs for real-time events
docker-compose logs -f websocket-ingestion | Select-String "state_changed"
```

### Test Suite 5: Dashboard UI (5 minutes)

**Test 5.1: Access health dashboard**
```
Open browser: http://localhost:3000
```

**Expected:** Dashboard should load without errors

**Test 5.2: Check Overview tab**
```
Click "Overview" tab
```

**Expected:** Should show system metrics and service status

**Test 5.3: Check Devices tab**
```
Click "Devices" tab
```

**Expected:** 
- Should load devices quickly (<1 second)
- Should show device count
- Should show entity counts per device
- Query should be much faster than before (using SQLite now)

**Test 5.4: Check Events tab**
```
Click "Events" tab
```

**Expected:** Should show real-time event stream with Epic 23 fields

**Test 5.5: Check browser console for errors**
```
F12 -> Console tab
```

**Expected:** No JavaScript errors (warnings OK)

---

## 🔧 Troubleshooting

### Issue 1: Alembic Migration Fails

**Symptoms:**
```
ERROR [alembic.runtime.migration] Can't locate revision identified by '001'
```

**Solution:**
```powershell
# Reset Alembic and re-run migrations
docker-compose exec data-api rm -f /app/data/metadata.db
docker-compose exec data-api alembic upgrade head
```

### Issue 2: SQLite Database Locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```powershell
# Restart data-api service
docker-compose restart data-api

# Verify WAL mode is enabled
docker-compose exec data-api sqlite3 /app/data/metadata.db "PRAGMA journal_mode;"
# Should return: wal
```

### Issue 3: No Devices in SQLite

**Symptoms:**
```
SELECT COUNT(*) FROM devices;
0
```

**Solution:**
```powershell
# Manually trigger discovery
curl -X POST http://localhost:8001/api/discover

# Wait 30 seconds
Start-Sleep -Seconds 30

# Check again
docker-compose exec data-api sqlite3 /app/data/metadata.db "SELECT COUNT(*) FROM devices;"
```

### Issue 4: WebSocket Connection Failed

**Symptoms:**
```
ERROR: WebSocket connection failed: Unauthorized
```

**Solution:**
```powershell
# Verify Home Assistant token is set
echo $env:HOME_ASSISTANT_TOKEN

# Verify token is valid
curl "$env:HOME_ASSISTANT_URL/api/" -H "Authorization: Bearer $env:HOME_ASSISTANT_TOKEN"

# Update environment file
notepad infrastructure\.env.websocket
# Set: HOME_ASSISTANT_TOKEN=your-valid-token

# Restart service
docker-compose restart websocket-ingestion
```

### Issue 5: Events Missing Epic 23 Fields

**Symptoms:**
Events don't have `device_id`, `area_id`, or `context_id`

**Solution:**
```powershell
# Check if discovery cache is populated
docker-compose logs websocket-ingestion | Select-String "discovery cache"

# If cache is empty, trigger discovery
curl -X POST http://localhost:8001/api/discover

# Restart websocket service to reload cache
docker-compose restart websocket-ingestion
```

### Issue 6: High Memory Usage

**Symptoms:**
InfluxDB or services using excessive memory

**Solution:**
```powershell
# Check memory limits in docker-compose.yml
docker-compose config | Select-String "memory"

# Restart with memory limits
docker-compose down
docker-compose up -d

# Monitor usage
docker stats --no-stream
```

### Issue 7: Dashboard Not Loading

**Symptoms:**
http://localhost:3000 shows error or blank page

**Solution:**
```powershell
# Check health-dashboard logs
docker-compose logs health-dashboard

# Rebuild and restart
docker-compose up -d --build health-dashboard

# Check nginx configuration
docker-compose exec health-dashboard cat /etc/nginx/nginx.conf
```

---

## 📊 Success Criteria

### Deployment Success Checklist

- [ ] All services show "Up (healthy)" status
- [ ] InfluxDB contains events (`SELECT COUNT(*) > 0`)
- [ ] SQLite contains devices and entities (`SELECT COUNT(*) > 0`)
- [ ] API queries return data (<50ms response time)
- [ ] Device/entity queries are fast (<10ms with SQLite)
- [ ] Epic 23 fields present in events (device_id, area_id, context_id, duration)
- [ ] Health dashboard loads and shows data
- [ ] WebSocket connection to Home Assistant is stable
- [ ] No ERROR or CRITICAL messages in logs
- [ ] Real-time event streaming works
- [ ] Database migrations completed successfully

### Performance Benchmarks

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Device query response time | <10ms | `Measure-Command { curl "http://localhost:8006/api/devices" }` |
| Event query response time | <50ms | `Measure-Command { curl "http://localhost:8006/api/events?limit=100" }` |
| WebSocket latency | <1s | Check event timestamps vs InfluxDB write time |
| Dashboard load time | <2s | Browser DevTools Network tab |
| Memory usage per service | <128MB | `docker stats` |

### Data Quality Checks

- [ ] Events have valid `entity_id`
- [ ] Events have `context_id` (Epic 23)
- [ ] State_changed events have `device_id` when applicable (Epic 23)
- [ ] State_changed events have `area_id` when applicable (Epic 23)
- [ ] State_changed events have `duration_in_state_seconds` (Epic 23)
- [ ] Devices in SQLite have manufacturer/model (Epic 23)
- [ ] Entities correctly linked to devices (foreign keys)

---

## 🔄 Rollback Plan

### When to Rollback

Rollback if:
- ❌ Services fail to start after 5 minutes
- ❌ Critical errors in logs preventing operation
- ❌ Database corruption detected
- ❌ Data loss detected
- ❌ WebSocket connection cannot be established

### Rollback Steps

**Step 1: Stop all services**
```powershell
docker-compose down
```

**Step 2: Restore previous git state**
```powershell
# Discard all changes
git reset --hard HEAD

# Or restore specific files
git checkout HEAD -- services/data-api/src/devices_endpoints.py
git checkout HEAD -- services/websocket-ingestion/src/event_processor.py
git checkout HEAD -- services/websocket-ingestion/src/discovery_service.py
```

**Step 3: Restore database backups**
```powershell
# Restore InfluxDB
docker volume rm ha-ingestor_influxdb_data
docker volume create ha-ingestor_influxdb_data
docker run --rm -v ha-ingestor_influxdb_data:/restore -v ./backups/influxdb-backup:/backup influxdb:2.7 influx restore /backup

# Remove SQLite databases (start fresh)
docker volume rm ha-ingestor_data_api_sqlite
docker volume rm ha-ingestor_sports_data_sqlite
```

**Step 4: Rebuild and restart**
```powershell
docker-compose build
docker-compose up -d
```

**Step 5: Verify rollback successful**
```powershell
docker-compose ps
docker-compose logs --tail=50
```

---

## 📝 Post-Deployment Tasks

### Immediate (Day 1)

- [ ] **Monitor logs for 1 hour**
  ```powershell
  docker-compose logs -f | Select-String "ERROR\|CRITICAL"
  ```

- [ ] **Verify data accumulation**
  ```powershell
  # Check event count increasing
  curl "http://localhost:8006/api/events/stats"
  ```

- [ ] **Document any issues encountered**
  - Create issue in GitHub/Jira
  - Update troubleshooting section

- [ ] **Notify team of successful deployment**
  - Send status update
  - Share dashboard URL

### Short-term (Week 1)

- [ ] **Performance monitoring**
  - Track query response times
  - Monitor memory usage trends
  - Check disk space growth

- [ ] **Data quality validation**
  - Verify Epic 23 fields are populated correctly
  - Check for missing device_id/area_id (expected for some entities)
  - Validate context hierarchy tracing

- [ ] **Update UI to use Epic 23 features**
  - Add device/area filters to Events tab
  - Add automation trace visualization
  - Add time-based analytics charts

- [ ] **User acceptance testing**
  - Test real-world use cases
  - Gather feedback from users
  - Document any feature requests

### Long-term (Month 1)

- [ ] **Optimize database queries**
  - Add indexes based on query patterns
  - Review slow query logs
  - Consider caching strategies

- [ ] **Archive old data**
  - Configure data retention policies
  - Test backup/restore procedures
  - Document data lifecycle

- [ ] **Scale testing**
  - Test with high event volumes
  - Stress test API endpoints
  - Load test dashboard

- [ ] **Documentation updates**
  - Update API documentation with Epic 23 endpoints
  - Update user guides
  - Create video tutorials

---

## 📚 Related Documentation

- [Epic 22 Completion Summary](./EPIC_22_COMPLETION_SUMMARY.md)
- [Epic 23 Complete](./EPIC_23_COMPLETE.md)
- [Architecture: Database Schema](../docs/architecture/database-schema.md)
- [Architecture: Data Models](../docs/architecture/data-models.md)
- [README](../README.md)

---

## ✅ Sign-Off

### Deployment Team

| Role | Name | Sign-Off | Date |
|------|------|----------|------|
| **Deployment Lead** | Rick | ☐ | |
| **Developer** | BMad Master (AI) | ✅ | 2025-10-14 |
| **QA Engineer** | | ☐ | |

### Deployment Checklist Complete

- [ ] Pre-deployment checklist complete
- [ ] All services deployed successfully
- [ ] All tests passing
- [ ] No critical errors in logs
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Team notified

---

**Deployment Plan Version:** 1.0  
**Last Updated:** October 14, 2025  
**Next Review:** Post-deployment (after testing complete)


