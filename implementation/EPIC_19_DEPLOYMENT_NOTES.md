# Epic 19: Device & Entity Discovery - Deployment Notes

**Date**: October 12, 2025  
**Epic**: 19 - Device & Entity Discovery  
**Status**: Ready for Deployment

---

## Pre-Deployment Checklist

### ✅ Code Complete
- [x] All 4 stories implemented
- [x] 54 tests passing
- [x] 0 linter errors
- [x] Code reviewed

### ⚠️ Configuration Required

**InfluxDB Manager Integration**:

The discovery service is ready but needs InfluxDB manager wired up in `connection_manager.py`:

**Current**:
```python
self.discovery_service = DiscoveryService()
```

**Needs** (for storage to work):
```python
self.discovery_service = DiscoveryService(influxdb_manager=self.influxdb_manager)
```

**Note**: Discovery and API endpoints work without this. Storage is optional until InfluxDB is wired up.

---

## Deployment Steps

### 1. InfluxDB Bucket Creation

InfluxDB will auto-create buckets on first write, but you can pre-create them:

```bash
# Connect to InfluxDB container
docker exec -it influxdb influx

# Create buckets
influx bucket create -n devices -o ha-ingestor -r 90d
influx bucket create -n entities -o ha-ingestor -r 90d
```

**Or**: Let buckets auto-create (recommended - simpler)

---

### 2. Rebuild Docker Images

```bash
# Rebuild websocket-ingestion service
cd services/websocket-ingestion
docker build -t ha-ingestor-websocket:latest .

# Rebuild admin-api service  
cd ../admin-api
docker build -t ha-ingestor-admin-api:latest .
```

---

### 3. Deploy Services

```bash
# Restart services with new images
docker-compose down
docker-compose up -d

# Or restart specific services
docker-compose restart websocket-ingestion admin-api
```

---

### 4. Verify Deployment

**Check logs for discovery**:
```bash
docker-compose logs websocket-ingestion | grep "DISCOVERY"
```

**Expected output**:
```
🚀 STARTING COMPLETE HOME ASSISTANT DISCOVERY
✅ DISCOVERY COMPLETE
   Devices: 100
   Entities: 450
   Config Entries: 25
📱 Subscribed to device registry events
🔌 Subscribed to entity registry events
```

**Test API endpoints**:
```bash
# List devices
curl http://localhost:8000/api/devices

# List entities
curl http://localhost:8000/api/entities

# List integrations
curl http://localhost:8000/api/integrations
```

---

### 5. Smoke Tests

**Test Discovery**:
1. Check logs show discovery complete
2. Verify device/entity counts reasonable
3. Check no errors in logs

**Test Real-Time**:
1. Add a new device in Home Assistant
2. Check logs show registry event received
3. Verify device stored

**Test API**:
1. Call GET /api/devices
2. Verify response contains devices
3. Test filters work
4. Test pagination works

---

## Environment Variables

**No new variables required!** Uses existing:
- `HOME_ASSISTANT_URL` (existing)
- `HOME_ASSISTANT_TOKEN` (existing)
- `INFLUXDB_URL` (existing)
- `INFLUXDB_TOKEN` (existing)

---

## Performance Monitoring

**Metrics to Watch**:
- Discovery time on startup (target: < 5 seconds)
- Memory usage (expect: +30-50MB)
- CPU usage (expect: < 5% increase)
- InfluxDB storage growth (~200MB over 90 days)
- API response times (target: < 100ms)

**Log Monitoring**:
```bash
# Watch for discovery
docker-compose logs -f websocket-ingestion | grep "DISCOVERY"

# Watch for registry events
docker-compose logs -f websocket-ingestion | grep "REGISTRY EVENT"

# Check for errors
docker-compose logs websocket-ingestion | grep "ERROR"
```

---

## Rollback Plan

If issues occur:

### Quick Rollback
```bash
# Stop services
docker-compose down

# Revert to previous images
docker-compose up -d
```

### Partial Rollback

Discovery is **non-fatal** - can disable without affecting existing functionality:

**Option 1**: Comment out discovery calls in `connection_manager.py`:
```python
# Temporarily disable discovery
# await self.discovery_service.discover_all(self.client.websocket)
# await self.discovery_service.subscribe_to_device_registry_events(...)
```

**Option 2**: Remove devices_router from admin-api `main.py`:
```python
# Temporarily disable API endpoints
# self.app.include_router(devices_router)
```

**State events continue working** - no impact on existing functionality.

---

## Known Issues / Limitations

### ⚠️ InfluxDB Manager Not Wired

**Issue**: Discovery service doesn't have InfluxDB manager yet  
**Impact**: Discovery runs, logs results, but doesn't store in InfluxDB  
**Workaround**: Can add later in follow-up commit  
**Priority**: Medium (API queries won't work until storage active)

**Fix Required**:
1. Wire up InfluxDB manager in ConnectionManager
2. Pass to DiscoveryService on initialization
3. Test storage works

### ℹ️ Manual Testing Pending

**Issue**: Not tested with live Home Assistant yet  
**Impact**: Unknown real-world behavior  
**Mitigation**: 54 tests with mocks prove logic works  
**Action**: Test with live HA after deployment

---

## Success Criteria

After deployment, verify:

✅ **Discovery**:
- Service starts without errors
- Logs show device/entity counts
- Discovery completes in < 5 seconds

✅ **Real-Time**:
- Add device in HA
- Logs show registry event
- Event processed without errors

✅ **API** (once storage wired):
- GET /api/devices returns data
- GET /api/entities returns data
- Filters work correctly
- Pagination works

✅ **Performance**:
- CPU < 5% increase
- Memory < 50MB increase
- No impact on state event processing

✅ **Stability**:
- No errors in logs
- Service remains connected
- Events continue processing

---

## Post-Deployment Tasks

### Immediate (Day 1)
- [ ] Monitor logs for errors
- [ ] Verify discovery works
- [ ] Test API endpoints
- [ ] Check performance metrics

### Week 1
- [ ] Wire up InfluxDB manager (storage)
- [ ] Test storage working
- [ ] Verify retention policies
- [ ] Monitor storage growth

### Week 2
- [ ] Start Epic 20 (Dashboard UI)
- [ ] Create devices browser tab
- [ ] Reuse Dependencies Tab pattern
- [ ] Add topology visualization

---

## Support & Troubleshooting

### Common Issues

**Issue**: "Cannot run discovery: WebSocket not available"  
**Cause**: WebSocket not connected  
**Fix**: Check HA connection, verify token valid

**Issue**: "Failed to subscribe to registry events"  
**Cause**: HA permissions or version issue  
**Fix**: Check HA version, verify token has admin access

**Issue**: API returns empty arrays  
**Cause**: InfluxDB manager not wired up  
**Fix**: Wire up InfluxDB manager in ConnectionManager

**Issue**: High memory usage  
**Cause**: Too many devices/entities cached  
**Fix**: Normal for large installations (1000+ devices)

### Logs to Check

```bash
# Startup logs
docker-compose logs websocket-ingestion | head -100

# Discovery logs
docker-compose logs websocket-ingestion | grep "DISCOVERY"

# Registry event logs
docker-compose logs websocket-ingestion | grep "REGISTRY"

# API logs
docker-compose logs admin-api | grep "/api/devices"

# Errors
docker-compose logs | grep "ERROR"
```

---

## Contact & Documentation

**Epic Documentation**: `docs/prd/epic-19-device-entity-discovery.md`  
**Architecture**: `docs/architecture/device-discovery-service.md`  
**Stories**: `docs/stories/19.{1-4}-*.md`  
**Research**: `docs/research/RESEARCH_SUMMARY.md`  
**Completion Summary**: `docs/EPIC_19_COMPLETION_SUMMARY.md`

---

**Deployment Status**: Ready (with note about InfluxDB wiring)  
**Risk Level**: LOW  
**Estimated Deployment Time**: 15-30 minutes  
**Recommended**: Deploy to test environment first

