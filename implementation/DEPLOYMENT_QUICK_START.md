# Quick Start: Epic 22 & 23 Deployment

**⏱️ Total Time:** ~60 minutes  
**📋 Full Plan:** See [DEPLOYMENT_PLAN_EPIC_22_23.md](./DEPLOYMENT_PLAN_EPIC_22_23.md)

---

## 🚀 Rapid Deployment (30 minutes)

### Step 1: Pre-flight Checks (5 min)
```powershell
# Navigate to project
cd c:\cursor\homeiq

# Verify prerequisites
docker --version  # Need 24+
docker-compose --version

# Check environment variables
echo $env:HOME_ASSISTANT_URL
echo $env:HOME_ASSISTANT_TOKEN

# Create backup directory
mkdir -p backups/$(Get-Date -Format 'yyyy-MM-dd-HHmmss')
```

### Step 2: Deploy (10 min)
```powershell
# Stop existing services
docker-compose down

# Build new images
docker-compose build

# Start infrastructure
docker-compose up -d influxdb

# Wait for InfluxDB
Start-Sleep -Seconds 30

# Start all services
docker-compose up -d

# Wait for services to be healthy
Start-Sleep -Seconds 30
```

### Step 3: Run Migrations (5 min)
```powershell
# Run SQLite migrations
docker-compose exec data-api alembic upgrade head

# Verify tables created
docker-compose exec data-api sqlite3 /app/data/metadata.db ".tables"
# Should show: alembic_version, devices, entities
```

### Step 4: Verify Discovery (Automatic - 2 min)
```powershell
# Discovery runs AUTOMATICALLY when websocket-ingestion connects to HA
# Wait for discovery to complete (happens on connection)
Start-Sleep -Seconds 30

# Verify devices stored (should see 90+ real devices)
$devices = Invoke-WebRequest -Uri http://localhost:8006/api/devices | ConvertFrom-Json
Write-Host "Devices discovered: $($devices.count)"

# Should show: 90+ devices from your Home Assistant instance
# If 0: Check websocket-ingestion logs for connection issues
```

**Note**: Discovery is now **fully automatic** - no manual trigger needed!
- Runs on WebSocket connection to Home Assistant
- Stores directly to SQLite via data-api
- No sync scripts required

### Step 5: Quick Tests (5 min)
```powershell
# Test all APIs
curl http://localhost:8001/health  # websocket
curl http://localhost:8006/health  # data-api
curl http://localhost:8003/health  # admin-api

# Test devices endpoint (should be fast <10ms)
Measure-Command { curl "http://localhost:8006/api/devices" }

# Test events endpoint
curl "http://localhost:8006/api/events?limit=5"

# Open dashboard
Start-Process "http://localhost:3000"
```

---

## ✅ Success Indicators

**All Good If:**
- ✅ `docker-compose ps` shows all services "Up (healthy)"
- ✅ Device query responds in <10ms
- ✅ Events have `device_id`, `area_id`, `context_id` fields
- ✅ SQLite has devices: `SELECT COUNT(*) FROM devices;` > 0
- ✅ Dashboard loads at http://localhost:3000
- ✅ No errors in logs: `docker-compose logs --tail=100`

---

## ⚠️ Common Issues

### Issue: Migration Fails
```powershell
# Reset and retry
docker-compose exec data-api rm -f /app/data/metadata.db
docker-compose exec data-api alembic upgrade head
```

### Issue: No Devices in SQLite
```powershell
# Re-trigger discovery
curl -X POST http://localhost:8001/api/discover
Start-Sleep -Seconds 30
docker-compose exec data-api sqlite3 /app/data/metadata.db "SELECT COUNT(*) FROM devices;"
```

### Issue: WebSocket Not Connected
```powershell
# Check token and restart
echo $env:HOME_ASSISTANT_TOKEN
docker-compose restart websocket-ingestion
docker-compose logs --tail=50 websocket-ingestion
```

### Issue: High Memory/Errors
```powershell
# Full restart
docker-compose down
docker-compose up -d
docker stats --no-stream
```

---

## 🧪 Essential Tests (30 minutes)

### Test 1: Database Performance
```powershell
# Device query (should be <10ms - 10x faster!)
Measure-Command { curl "http://localhost:8006/api/devices" }

# Event query (baseline ~30-50ms)
Measure-Command { curl "http://localhost:8006/api/events?limit=100" }
```

### Test 2: Epic 23 Fields
```powershell
# Get recent event and check Epic 23 fields
curl "http://localhost:8006/api/events?limit=1" | ConvertFrom-Json | Select-Object -ExpandProperty events | Select-Object entity_id, device_id, area_id, context_id, duration_in_state_seconds, manufacturer, model | Format-List
```

**Expected fields:**
- `device_id` - Device ID (NEW)
- `area_id` - Area ID (NEW)
- `context_id` - Context tracking (NEW)
- `duration_in_state_seconds` - Duration (NEW)
- `manufacturer` - Manufacturer (NEW)
- `model` - Model (NEW)

### Test 3: Context Hierarchy
```powershell
# Find an event with context_id
$event = curl "http://localhost:8006/api/events?limit=50" | ConvertFrom-Json | Select-Object -ExpandProperty events | Where-Object { $_.context_id } | Select-Object -First 1

# Trace automation chain
curl "http://localhost:8006/api/v1/events/automation-trace/$($event.context_id)"
```

### Test 4: Device/Area Filtering
```powershell
# Filter by area (replace with your area_id)
curl "http://localhost:8006/api/events?area_id=living_room&limit=10"

# Filter by device (replace with your device_id)
curl "http://localhost:8006/api/events?device_id=abc123&limit=10"

# Exclude diagnostic entities
curl "http://localhost:8006/api/events?exclude_category=diagnostic&limit=10"
```

### Test 5: Real-time Event Flow
```
1. Go to Home Assistant UI
2. Toggle a light or sensor
3. Run: curl "http://localhost:8006/api/events?event_type=state_changed&limit=1"
4. Verify event appears within 1-2 seconds
```

### Test 6: Dashboard UI
```
1. Open http://localhost:3000
2. Click "Devices" tab → Should load fast (<1s)
3. Click "Events" tab → Should show real-time events
4. Check browser console (F12) → No errors
```

---

## 🎯 What Changed?

### Epic 22: SQLite Metadata Storage
- **NEW:** SQLite databases for devices, entities, webhooks
- **NEW:** Alembic migrations for schema management
- **FASTER:** 10x faster device/entity queries (<10ms vs ~50ms)
- **IMPROVED:** ACID transactions, concurrent-safe operations

### Epic 23: Enhanced Event Data Capture
- **NEW:** `context_id`, `context_parent_id` - trace automation chains
- **NEW:** `device_id`, `area_id` tags - spatial analytics
- **NEW:** `duration_in_state_seconds` - time-based analytics
- **NEW:** `entity_category` filtering - exclude diagnostics
- **NEW:** `manufacturer`, `model`, `sw_version` - device metadata
- **NEW:** `/api/v1/events/automation-trace/{context_id}` endpoint

---

## 🔄 Rollback (if needed)

```powershell
# Stop everything
docker-compose down

# Restore code
git reset --hard HEAD

# Remove SQLite volumes
docker volume rm homeiq_data_api_sqlite
docker volume rm homeiq_sports_data_sqlite

# Restart
docker-compose up -d
```

---

## 📞 Need Help?

**Check Full Plan:** [DEPLOYMENT_PLAN_EPIC_22_23.md](./DEPLOYMENT_PLAN_EPIC_22_23.md)

**View Logs:**
```powershell
# All services
docker-compose logs --tail=100

# Specific service
docker-compose logs --tail=50 websocket-ingestion
docker-compose logs --tail=50 data-api
```

**Check Service Status:**
```powershell
docker-compose ps
docker stats --no-stream
```

---

**Last Updated:** October 14, 2025  
**Deployment Version:** Epic 22 + 23

