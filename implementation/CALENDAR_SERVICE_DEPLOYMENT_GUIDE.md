# Calendar Service Deployment Guide - Home Assistant Integration

**Date:** October 16, 2025  
**Version:** 2.0.0 (Home Assistant Integration)  
**Status:** Ready for Deployment

---

## Prerequisites

### 1. Home Assistant Setup
- [ ] Home Assistant instance running and accessible
- [ ] Calendar integration configured in HA (Google, iCloud, CalDAV, etc.)
- [ ] Calendar entity ID noted (e.g., `calendar.primary`)

### 2. Create Long-Lived Access Token
- [ ] In HA: Click Profile (bottom left)
- [ ] Navigate to: Security → Long-Lived Access Tokens
- [ ] Click "Create Token"
- [ ] Name: "Calendar Service"
- [ ] **Copy token** (you won't see it again!)

### 3. Environment Configuration
- [ ] Home Assistant URL known (e.g., `http://homeassistant.local:8123`)
- [ ] Long-lived token copied
- [ ] Calendar entity IDs identified

---

## Deployment Steps

### Step 1: Update Environment Variables

Edit your `.env` file or set environment variables:

```bash
# Required - Home Assistant Connection
HOME_ASSISTANT_URL=http://homeassistant.local:8123
HOME_ASSISTANT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Required - Calendar Configuration  
CALENDAR_ENTITIES=calendar.primary

# Optional - Fetch Interval (seconds, default: 900 = 15 min)
CALENDAR_FETCH_INTERVAL=900

# Required - InfluxDB (usually already configured)
INFLUXDB_TOKEN=your_influxdb_token
```

**Multiple Calendars Example:**
```bash
CALENDAR_ENTITIES=calendar.google,calendar.icloud,calendar.work
```

### Step 2: Stop Existing Calendar Service

```bash
docker-compose stop calendar
```

### Step 3: Rebuild Calendar Service

Rebuild the service to pick up new dependencies:

```bash
docker-compose build calendar
```

### Step 4: Start Calendar Service

```bash
docker-compose up -d calendar
```

### Step 5: Verify Deployment

Check logs for successful startup:

```bash
docker-compose logs -f calendar
```

**Expected Log Messages:**
```
✅ Initializing Calendar Service (Home Assistant Integration)...
✅ Connected to Home Assistant: API running.
✅ Found N calendar(s) in Home Assistant: ['calendar.primary', ...]
✅ Calendar Service initialized successfully
✅ Starting continuous occupancy prediction (every 900s)
✅ Fetched X events from N calendar(s)
✅ Occupancy prediction: Home=false, WFH=false, Events=X, Confidence=0.70
✅ Occupancy prediction written to InfluxDB
```

### Step 6: Test Health Endpoint

```bash
curl http://localhost:8013/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "calendar-service",
  "integration_type": "home_assistant",
  "uptime_seconds": 120,
  "ha_connected": true,
  "calendar_count": 1,
  "last_successful_fetch": "2025-10-16T14:30:00",
  "total_fetches": 2,
  "failed_fetches": 0,
  "success_rate": 1.0
}
```

**Key Indicators:**
- ✅ `"status": "healthy"`
- ✅ `"ha_connected": true`
- ✅ `"calendar_count"` > 0
- ✅ `"success_rate": 1.0`

### Step 7: Verify InfluxDB Data

Query InfluxDB to confirm data is being written:

```bash
curl -H "Authorization: Token ${INFLUXDB_TOKEN}" \
     "http://localhost:8086/api/v2/query?org=ha-ingestor" \
     --data-urlencode 'query=from(bucket:"events") |> range(start:-1h) |> filter(fn:(r) => r._measurement == "occupancy_prediction") |> limit(n:5)'
```

Or use InfluxDB UI: http://localhost:8086

---

## Verification Checklist

### Service Health
- [ ] Container is running: `docker ps | grep calendar`
- [ ] No error logs: `docker-compose logs calendar | grep ERROR`
- [ ] Health endpoint returns 200: `curl -I http://localhost:8013/health`
- [ ] `ha_connected: true` in health response
- [ ] `calendar_count` matches configured calendars

### Data Flow
- [ ] Events fetched from HA: Check logs for "Fetched X events"
- [ ] Occupancy predictions generated: Check logs for "Occupancy prediction"
- [ ] Data written to InfluxDB: Check logs for "written to InfluxDB"
- [ ] InfluxDB shows `occupancy_prediction` measurement
- [ ] Latest data is recent (< 15 minutes old)

### Calendar Integration
- [ ] Service discovers configured calendars
- [ ] Events from all calendars are combined
- [ ] WFH/home patterns detected correctly
- [ ] Confidence scores are reasonable (0.5-0.95)

### Performance
- [ ] Event fetch time < 2 seconds (check logs)
- [ ] Memory usage < 150MB: `docker stats ha-ingestor-calendar`
- [ ] CPU usage < 5% average
- [ ] No memory leaks over 1 hour

---

## Troubleshooting

### Issue 1: Service Won't Start

**Symptoms:**
- Container exits immediately
- Error: "HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN required"

**Solution:**
```bash
# Verify environment variables are set
docker-compose config | grep HOME_ASSISTANT

# If missing, add to .env file:
echo "HOME_ASSISTANT_URL=http://homeassistant.local:8123" >> .env
echo "HOME_ASSISTANT_TOKEN=your_token" >> .env

# Restart
docker-compose up -d calendar
```

### Issue 2: Cannot Connect to Home Assistant

**Symptoms:**
- Error: "Failed to connect to Home Assistant"
- `ha_connected: false` in health check

**Solution:**
```bash
# Test HA connectivity from within container
docker exec -it ha-ingestor-calendar curl -H "Authorization: Bearer ${HOME_ASSISTANT_TOKEN}" http://homeassistant.local:8123/api/

# If connection fails, verify:
# 1. HA is running
docker ps | grep homeassistant

# 2. URL is correct (try with IP instead of hostname)
HOME_ASSISTANT_URL=http://192.168.1.100:8123

# 3. Token is valid
# Re-create token in HA if needed

# 4. Network connectivity
# Ensure both containers are on same network or HA is accessible
```

### Issue 3: No Events Found

**Symptoms:**
- Logs show "Found 0 calendar(s)" or "Fetched 0 events"
- Health check shows `calendar_count: 0`

**Solution:**
```bash
# List available calendars in HA
curl -H "Authorization: Bearer ${HOME_ASSISTANT_TOKEN}" \
     http://homeassistant.local:8123/api/states | \
     jq '.[] | select(.entity_id | startswith("calendar."))'

# Update CALENDAR_ENTITIES with correct entity IDs
# Use the entity_id values from above (e.g., calendar.google)

# Restart service
docker-compose restart calendar
```

### Issue 4: WFH Detection Not Working

**Symptoms:**
- Events fetched but `wfh_today: false` when should be true
- Confidence scores are low

**Solution:**
Check event summaries match detection patterns:

**Supported Patterns:**
- Summary: "WFH", "Work From Home", "Home Office", "Remote Work"
- Location: "Home", "House", "Residence", "Apartment"

**Example Good Events:**
```
✅ "WFH Day" → Detected as WFH
✅ "Working From Home" → Detected as WFH  
✅ Meeting (Location: "Home Office") → Detected as home
```

**Example Not Detected:**
```
❌ "Remote" → Not in pattern list
❌ "At house" → Lowercase, but pattern matches case-insensitive, should work
```

If your events use different terminology, you can customize patterns by editing `services/calendar-service/src/event_parser.py`.

### Issue 5: High Memory Usage

**Symptoms:**
- Memory usage > 200MB
- Container OOM (Out of Memory) kills

**Solution:**
```bash
# Check current memory usage
docker stats ha-ingestor-calendar

# If consistently high:
# 1. Reduce fetch interval (less frequent = less memory)
CALENDAR_FETCH_INTERVAL=1800  # 30 minutes instead of 15

# 2. Reduce number of calendars if possible
CALENDAR_ENTITIES=calendar.primary  # Instead of multiple

# 3. Increase memory limit in docker-compose.yml
# Edit docker-compose.yml:
    deploy:
      resources:
        limits:
          memory: 256M  # Increase from 128M

# Restart
docker-compose up -d calendar
```

### Issue 6: InfluxDB Write Errors

**Symptoms:**
- Error: "Error writing to InfluxDB"
- Health check shows high `failed_fetches`

**Solution:**
```bash
# Test InfluxDB connection
curl http://localhost:8086/health

# Verify InfluxDB token
echo $INFLUXDB_TOKEN

# Check InfluxDB logs
docker-compose logs influxdb

# If bucket doesn't exist, create it:
# Access InfluxDB UI: http://localhost:8086
# Create bucket named "events" (or match INFLUXDB_BUCKET value)

# Restart calendar service
docker-compose restart calendar
```

---

## Rollback Plan

If deployment fails and you need to revert to Google Calendar integration:

### 1. Stop New Service
```bash
docker-compose stop calendar
```

### 2. Restore Old Environment Variables
```bash
# Re-add to .env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_secret
GOOGLE_REFRESH_TOKEN=your_token

# Remove HA variables
# Comment out or remove:
# HOME_ASSISTANT_URL=...
# HOME_ASSISTANT_TOKEN=...
# CALENDAR_ENTITIES=...
```

### 3. Restore Old Requirements
```bash
# Edit services/calendar-service/requirements.txt
# Add back:
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.110.0
```

### 4. Restore Old docker-compose.yml
```bash
# Revert environment section in docker-compose.yml
# Replace HA variables with Google variables
```

### 5. Rebuild and Restart
```bash
docker-compose build calendar
docker-compose up -d calendar
```

---

## Post-Deployment Tasks

### Monitor for 24 Hours

After deployment, monitor service for first 24 hours:

**Every 4 Hours:**
- [ ] Check health endpoint: `curl http://localhost:8013/health`
- [ ] Verify `success_rate` remains > 0.95
- [ ] Check logs for errors: `docker-compose logs calendar | grep ERROR`

**Daily:**
- [ ] Verify InfluxDB data is current
- [ ] Check memory usage trends
- [ ] Review prediction accuracy

### Performance Baseline

Establish performance baseline:

```bash
# CPU and Memory
docker stats ha-ingestor-calendar --no-stream

# Response Time
time curl http://localhost:8013/health

# Log Analysis
docker-compose logs calendar | grep "Fetched.*events" | tail -20
```

**Expected Baselines:**
- Memory: 20-30MB idle, 40-50MB during fetch
- CPU: <1% idle, <5% during fetch
- Health response: <100ms
- Event fetch: <2s

### Update Monitoring

If using monitoring tools, update:
- [ ] Update service name in Grafana dashboards
- [ ] Update alert rules for new metrics
- [ ] Add `calendar_count` to monitoring
- [ ] Update documentation for support team

---

## Success Criteria

Deployment is successful when ALL criteria are met:

### Functional
- [x] Service starts without errors
- [x] Connects to Home Assistant
- [x] Discovers configured calendars
- [x] Fetches events successfully
- [x] Generates occupancy predictions
- [x] Writes data to InfluxDB
- [x] Health check returns healthy

### Performance
- [x] Event fetch < 2 seconds
- [x] Memory usage < 150MB
- [x] CPU usage < 5% average
- [x] No errors in logs
- [x] Success rate > 95%

### Data Quality
- [x] Events fetched match HA calendar
- [x] WFH detection works correctly
- [x] Confidence scores are reasonable
- [x] InfluxDB data is accurate
- [x] Timestamps are correct

---

## Support

### Logs Location
```bash
# Real-time logs
docker-compose logs -f calendar

# Last 100 lines
docker-compose logs --tail=100 calendar

# Errors only
docker-compose logs calendar | grep ERROR
```

### Health Check
```bash
# Quick health check
curl http://localhost:8013/health | jq

# Detailed with timestamp
curl -s http://localhost:8013/health | jq '. + {check_time: now|todate}'
```

### Contact
- **Documentation:** `services/calendar-service/README.md`
- **Implementation Details:** `implementation/CALENDAR_SERVICE_PHASE_*_COMPLETE.md`
- **Environment Template:** `infrastructure/env.calendar.template`

---

**Deployment Guide Version:** 1.0  
**Last Updated:** October 16, 2025  
**Compatible With:** Calendar Service 2.0.0+

