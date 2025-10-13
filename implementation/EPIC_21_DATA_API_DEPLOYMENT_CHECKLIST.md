# Epic 21 - Data API Deployment Checklist

**Created:** 2025-10-13  
**Status:** Ready for Deployment  
**Critical Issue:** Data API service exists but is NOT deployed

---

## 🚨 Critical Discovery

Epic 13 (Admin API Service Separation) created the `data-api` service to separate feature data from system monitoring, but **the service was never deployed**. 

**Impact:**
- Dashboard expects data-api to be running (port 8006)
- nginx routes configured for data-api
- All feature tabs try to connect to non-existent service
- Result: Connection errors, 502 Bad Gateway, features unavailable

---

## ✅ Pre-Deployment Checklist

### Verify Service Exists
```bash
# 1. Check service directory exists
ls -la services/data-api/

# Expected files:
# ├── Dockerfile
# ├── Dockerfile.dev
# ├── README.md
# ├── requirements.txt
# ├── requirements-prod.txt
# └── src/
#     ├── main.py
#     ├── events_endpoints.py
#     ├── devices_endpoints.py
#     ├── sports_endpoints.py
#     ├── alert_endpoints.py
#     ├── metrics_endpoints.py
#     ├── integration_endpoints.py
#     ├── websocket_endpoints.py
#     └── ha_automation_endpoints.py
```

### Verify Docker Configuration
```bash
# 2. Check docker-compose.yml includes data-api
grep -A 30 "data-api:" docker-compose.yml

# Should show:
# data-api:
#   build:
#     context: .
#     dockerfile: services/data-api/Dockerfile
#   container_name: ha-ingestor-data-api
#   ports:
#     - "8006:8006"
#   environment:
#     - DATA_API_PORT=8006
#   depends_on:
#     - influxdb
```

### Verify nginx Configuration
```bash
# 3. Check nginx routes data-api correctly
grep -A 10 "data-api" services/health-dashboard/nginx.conf

# Should show routes like:
# location /api/v1/events {
#     proxy_pass http://ha-ingestor-data-api:8006/api/v1/events;
# }
```

---

## 🚀 Deployment Steps

### Step 1: Build Container
```bash
# Build data-api service
docker-compose build data-api

# Expected output:
# [+] Building X.Xs (data-api)
# => [internal] load build definition from Dockerfile
# => => transferring dockerfile: XXB
# ...
# => exporting to image
# => => writing image sha256:...
```

**Verification:**
```bash
docker images | grep data-api
# Expected: ha-ingestor-data-api latest ... X hours ago XXX MB
```

### Step 2: Start Service
```bash
# Start data-api in detached mode
docker-compose up -d data-api

# Expected output:
# [+] Running 1/1
#  ✔ Container ha-ingestor-data-api  Started
```

**Verification:**
```bash
docker ps --filter "name=data-api"

# Expected output:
# CONTAINER ID   IMAGE                     STATUS         PORTS
# xxxxx          ha-ingestor-data-api:latest   Up X seconds   0.0.0.0:8006->8006/tcp
```

### Step 3: Check Service Logs
```bash
# View startup logs
docker logs ha-ingestor-data-api --tail 50

# Expected to see:
# INFO:     Started server process [1]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8006
```

**Look for any errors:**
- ❌ "Connection refused" to InfluxDB → Check InfluxDB running
- ❌ "Module not found" → Build error, check requirements.txt
- ❌ "Port already in use" → Port 8006 conflict

### Step 4: Test Health Endpoint
```bash
# Test from host
curl http://localhost:8006/health

# Expected response (200 OK):
{
  "status": "healthy",
  "service": "data-api",
  "version": "1.0.0",
  "timestamp": "2025-10-13T...",
  "uptime": "00:00:30",
  "influxdb": {
    "status": "connected",
    "url": "http://influxdb:8086"
  }
}
```

**If health check fails:**
```bash
# Check detailed logs
docker logs ha-ingestor-data-api

# Check InfluxDB connectivity
docker exec ha-ingestor-data-api curl http://influxdb:8086/health
```

### Step 5: Test All Endpoints
```bash
# Events endpoint
curl http://localhost:8006/api/v1/events?limit=1
# Expected: [] or [...events...]

# Devices endpoint
curl http://localhost:8006/api/devices?limit=1
# Expected: {"devices": [...], "count": X}

# Sports endpoint
curl http://localhost:8006/api/v1/sports/games/live
# Expected: {"games": [...]} or {"games": []}

# OpenAPI documentation
curl -I http://localhost:8006/docs
# Expected: HTTP/1.1 200 OK
```

### Step 6: Test nginx Routing
```bash
# From dashboard container
docker exec ha-ingestor-health-dashboard curl http://ha-ingestor-data-api:8006/health

# Expected: Same health response as Step 4
# If "Connection refused" → Check Docker network, service name
```

### Step 7: Test from Browser
```bash
# Open dashboard
open http://localhost:3000

# Open browser DevTools (F12) → Network tab
# Navigate to different tabs
# Look for requests to:
# - /api/v1/events → Should return 200 OK (not 502/503)
# - /api/devices → Should return 200 OK
# - /api/v1/sports → Should return 200 OK

# Check Console tab for errors:
# ❌ "Failed to fetch" → Service not reachable
# ❌ "ERR_CONNECTION_REFUSED" → Service not running
# ✅ No connection errors → Success!
```

---

## 🔍 Verification Checklist

After deployment, verify all criteria:

### Service Status
- [ ] `docker ps` shows `ha-ingestor-data-api` with status "Up"
- [ ] Service listening on port 8006
- [ ] No restart loops (check "Up X seconds" doesn't reset)
- [ ] Logs show "Application startup complete"

### API Endpoints
- [ ] `/health` returns 200 OK with InfluxDB connected
- [ ] `/api/v1/events` returns 200 OK
- [ ] `/api/devices` returns 200 OK
- [ ] `/api/v1/sports/games/live` returns 200 OK
- [ ] `/docs` returns OpenAPI documentation page

### InfluxDB Connectivity
- [ ] Health endpoint shows `influxdb.status: "connected"`
- [ ] No InfluxDB errors in service logs
- [ ] Can query events from InfluxDB

### Dashboard Integration
- [ ] Dashboard loads without errors
- [ ] Browser console shows no 502/503 errors
- [ ] Devices tab loads devices successfully
- [ ] Events tab shows events (or "No events" if none)
- [ ] No "Failed to fetch" errors in console

### nginx Routing
- [ ] Requests to `/api/v1/events` route to data-api
- [ ] Requests to `/api/devices` route to data-api
- [ ] Requests to `/api/v1/sports` route to data-api
- [ ] No 502 Bad Gateway errors

---

## 🐛 Troubleshooting

### Issue: Container Won't Start
```bash
# Check build logs
docker-compose build data-api --no-cache

# Check for Python errors
docker-compose up data-api  # (without -d to see logs)

# Common causes:
# - Missing dependencies in requirements.txt
# - Import errors in main.py
# - Port 8006 already in use
```

### Issue: Health Endpoint Returns 503
```bash
# Check InfluxDB is running
docker ps --filter "name=influxdb"

# Check InfluxDB health
curl http://localhost:8086/health

# Check environment variables
docker exec ha-ingestor-data-api env | grep INFLUX
```

### Issue: Dashboard Shows 502 Errors
```bash
# Check nginx can resolve service name
docker exec ha-ingestor-health-dashboard nslookup ha-ingestor-data-api

# Check nginx error logs
docker logs ha-ingestor-health-dashboard 2>&1 | grep error

# Restart nginx
docker-compose restart health-dashboard
```

### Issue: Port 8006 Already in Use
```bash
# Find what's using port 8006
netstat -ano | grep 8006  # Windows
lsof -i :8006            # Linux/Mac

# Options:
# 1. Stop conflicting service
# 2. Change DATA_API_PORT in docker-compose.yml
```

---

## 🎯 Success Criteria

All criteria MUST pass before proceeding to Story 21.1:

✅ **Service Running**
- data-api container shows "Up" status
- No restart loops or crashes

✅ **Endpoints Accessible**
- All 8 endpoint categories responding
- OpenAPI docs accessible

✅ **InfluxDB Connected**
- Health endpoint shows connected status
- No database errors in logs

✅ **Dashboard Integration**
- Dashboard loads without errors
- Browser console clean (no connection errors)
- Devices tab functional

✅ **Performance**
- Health check responds in <100ms
- Endpoints respond in <500ms
- No memory leaks over 10-minute test

---

## 📋 Post-Deployment Tasks

1. **Update Documentation**
   - [ ] Update deployment guides with data-api
   - [ ] Update troubleshooting guide
   - [ ] Update architecture diagrams

2. **Monitoring Setup**
   - [ ] Add data-api to monitoring dashboards
   - [ ] Configure alerts for service health
   - [ ] Set up log aggregation

3. **Testing**
   - [ ] Run integration tests
   - [ ] Run E2E tests (Playwright)
   - [ ] Performance testing

4. **Verification**
   - [ ] QA sign-off on deployment
   - [ ] User acceptance testing
   - [ ] Document any issues found

---

## 🔄 Rollback Procedure

If critical issues arise:

```bash
# 1. Stop data-api service
docker-compose stop data-api

# 2. Dashboard will show connection errors but remain functional
#    (Graceful degradation - admin-api still works)

# 3. Investigate logs
docker logs ha-ingestor-data-api > data-api-error.log

# 4. Fix issues and redeploy
docker-compose build data-api
docker-compose up -d data-api

# 5. Verify fix
curl http://localhost:8006/health
```

---

## 📞 Escalation

If deployment fails after troubleshooting:

1. Collect logs:
   ```bash
   docker logs ha-ingestor-data-api > data-api.log
   docker logs ha-ingestor-health-dashboard > dashboard.log
   docker logs ha-ingestor-influxdb > influxdb.log
   ```

2. Check system resources:
   ```bash
   docker stats --no-stream
   ```

3. Contact: Development Team Lead
4. Reference: Epic 21, Story 21.0

---

**Deployment Checklist Version:** 1.0  
**Last Updated:** 2025-10-13  
**Next Review:** After successful deployment

