# Fix Devices API - Detailed Task List

## Problem Summary

The Devices API returns 0 devices because there's a **bucket/measurement mismatch**:
- **Discovery Service writes to**: Separate buckets (`devices`, `entities`) 
- **Data API reads from**: `home_assistant_events` bucket with measurements (`devices`, `entities`, `config_entries`)

## Root Cause Analysis

1. ✅ **WebSocket Ingestion** - Properly discovers devices/entities on connection
2. ✅ **Discovery Service** - Successfully queries HA registries  
3. ❌ **Storage Layer** - Writes to WRONG buckets (`devices`/`entities` instead of `home_assistant_events`)
4. ❌ **Data API Queries** - Looks in `home_assistant_events` bucket but data isn't there

---

## Task List for Approval

### **Phase 1: Verify Current State** (Investigation - 15 min)

#### Task 1.1: Check InfluxDB Buckets
- [ ] Connect to InfluxDB and list all buckets
- [ ] Verify if `devices` and `entities` buckets exist
- [ ] Check if `home_assistant_events` bucket exists
- [ ] See if any data was written to wrong buckets

**Command:**
```bash
docker exec -it ha-ingestor-influxdb influx bucket list
```

#### Task 1.2: Check WebSocket Ingestion Logs
- [ ] Review logs to confirm discovery ran successfully
- [ ] Verify device/entity counts from discovery
- [ ] Check for storage success/failure messages
- [ ] Look for InfluxDB write errors

**Command:**
```bash
docker logs ha-ingestor-websocket --tail 200 | grep -E "(DISCOVERY|device|entity|InfluxDB)"
```

#### Task 1.3: Query InfluxDB Directly
- [ ] Query `home_assistant_events` bucket for devices measurement
- [ ] Query `devices` bucket (if exists) to see where data actually went
- [ ] Confirm data structure matches expected schema

**Command:**
```bash
# Check home_assistant_events bucket
docker exec -it ha-ingestor-influxdb influx query 'from(bucket:"home_assistant_events") |> range(start:-7d) |> filter(fn: (r) => r._measurement == "devices") |> limit(n:1)'

# Check devices bucket if it exists
docker exec -it ha-ingestor-influxdb influx query 'from(bucket:"devices") |> range(start:-7d) |> limit(n:1)'
```

---

### **Phase 2: Fix Storage Layer** (Code Changes - 30 min)

#### Task 2.1: Update Discovery Service Storage
**File:** `services/websocket-ingestion/src/discovery_service.py`

- [ ] **Line 363**: Change `bucket="devices"` to `bucket="home_assistant_events"`
- [ ] **Line 372**: Change `bucket="entities"` to `bucket="home_assistant_events"`
- [ ] Add measurement names to ensure correct measurement (`devices`, `entities`)

**Expected Change:**
```python
# OLD:
success = await self.influxdb_manager.batch_write_devices(device_points, bucket="devices")

# NEW:
success = await self.influxdb_manager.batch_write_devices(device_points, bucket="home_assistant_events")
```

#### Task 2.2: Update Individual Device/Entity Writes
**File:** `services/websocket-ingestion/src/discovery_service.py`

- [ ] **Line 488**: Change `bucket="devices"` to `bucket="home_assistant_events"` (device registry events)
- [ ] **Line 528**: Change `bucket="entities"` to `bucket="home_assistant_events"` (entity registry events)

#### Task 2.3: Verify Device/Entity Model to_influx_point() Methods
**File:** `services/websocket-ingestion/src/models.py`

- [ ] Check `Device.to_influx_point()` - ensure measurement name is "devices"
- [ ] Check `Entity.to_influx_point()` - ensure measurement name is "entities"  
- [ ] Check `ConfigEntry.to_influx_point()` - ensure measurement name is "config_entries"

**Expected Structure:**
```python
def to_influx_point(self):
    return {
        "measurement": "devices",  # Must match data-api query
        "tags": {...},
        "fields": {...},
        "time": ...
    }
```

---

### **Phase 3: Fix Config Entries Storage** (Code Changes - 15 min)

#### Task 3.1: Add Config Entries Storage to Discovery
**File:** `services/websocket-ingestion/src/discovery_service.py`

Currently, config entries are discovered but **NOT stored**. Need to add:

- [ ] **After line 375**: Add config entries batch write
```python
# Batch write config entries
if config_entries:
    entry_points = [ce.to_influx_point() for ce in config_entries]
    success = await self.influxdb_manager.batch_write_config_entries(entry_points, bucket="home_assistant_events")
    if success:
        logger.info(f"✅ Stored {len(config_entries)} config entries in InfluxDB")
    else:
        logger.error(f"❌ Failed to store config entries")
```

#### Task 3.2: Add batch_write_config_entries Method
**File:** `services/websocket-ingestion/src/influxdb_wrapper.py`

- [ ] Add new method similar to `batch_write_devices` and `batch_write_entities`
- [ ] Write to `home_assistant_events` bucket with measurement `config_entries`

---

### **Phase 4: Rebuild and Test** (Deployment - 20 min)

#### Task 4.1: Rebuild WebSocket Ingestion Service
- [ ] Build updated Docker image
```bash
docker-compose build websocket-ingestion
```

#### Task 4.2: Restart Service with Clean Start
- [ ] Stop websocket-ingestion
- [ ] Remove container
- [ ] Start fresh (will trigger discovery on reconnect)
```bash
docker-compose stop websocket-ingestion
docker-compose rm -f websocket-ingestion
docker-compose up -d websocket-ingestion
```

#### Task 4.3: Monitor Discovery Process
- [ ] Watch logs for discovery completion
- [ ] Verify device/entity counts
- [ ] Check storage success messages
```bash
docker logs -f ha-ingestor-websocket
```

#### Task 4.4: Verify Data in InfluxDB
- [ ] Query `home_assistant_events` bucket for devices
- [ ] Query for entities
- [ ] Query for config_entries
- [ ] Confirm data is present

```bash
docker exec -it ha-ingestor-influxdb influx query 'from(bucket:"home_assistant_events") |> range(start:-1h) |> filter(fn: (r) => r._measurement == "devices") |> count()'
```

---

### **Phase 5: Test Data API** (Verification - 10 min)

#### Task 5.1: Test Devices Endpoint
- [ ] Call `/api/devices` endpoint
- [ ] Verify device count > 0
- [ ] Check device data structure

```bash
curl http://localhost:8006/api/devices?limit=5 | jq
```

#### Task 5.2: Test Entities Endpoint
- [ ] Call `/api/entities` endpoint
- [ ] Verify entity count > 0
- [ ] Check entity data structure

```bash
curl http://localhost:8006/api/entities?limit=5 | jq
```

#### Task 5.3: Test Integrations Endpoint
- [ ] Call `/api/integrations` endpoint
- [ ] Verify integration count > 0
- [ ] Check integration data structure

```bash
curl http://localhost:8006/api/integrations?limit=5 | jq
```

---

### **Phase 6: Verify Dashboard UI** (Final Check - 5 min)

#### Task 6.1: Check Overview Tab
- [ ] Open http://localhost:3000
- [ ] Go to Overview Tab
- [ ] Scroll to "🏠 Home Assistant Integration" section
- [ ] Verify device/entity/integration counts are > 0
- [ ] Verify HA Devices API Status shows "Connected - X devices discovered"

#### Task 6.2: Check Devices Tab
- [ ] Click Devices Tab
- [ ] Verify device grid shows actual devices
- [ ] Test search and filters
- [ ] Click on a device to see entities

#### Task 6.3: Run Playwright Test
- [ ] Run verification test
```bash
npx playwright test simple-dashboard-check.spec.js
```

---

## Optional: Clean Up Old Buckets (Post-Fix)

#### Task 7.1: Remove Unused Buckets (Optional)
If `devices` and `entities` buckets were created and have old/wrong data:

- [ ] Backup any useful data (if needed)
- [ ] Delete old buckets
```bash
docker exec -it ha-ingestor-influxdb influx bucket delete --name devices
docker exec -it ha-ingestor-influxdb influx bucket delete --name entities
```

---

## Estimated Time

| Phase | Time | Complexity |
|-------|------|------------|
| Phase 1: Investigation | 15 min | Easy |
| Phase 2: Fix Storage | 30 min | Medium |
| Phase 3: Add Config Storage | 15 min | Medium |
| Phase 4: Rebuild & Test | 20 min | Easy |
| Phase 5: API Testing | 10 min | Easy |
| Phase 6: UI Verification | 5 min | Easy |
| **Total** | **~95 min** | **Medium** |

---

## Risk Assessment

**Low Risk** ✅
- Changes are isolated to storage layer
- No API contract changes
- No schema changes
- Easy rollback (just revert bucket names)

**Worst Case:**
- Discovery needs to run again (automatic on reconnect)
- Old data in wrong buckets (can be cleaned up later)

---

## Success Criteria

1. ✅ Devices API returns > 0 devices
2. ✅ Entities API returns > 0 entities
3. ✅ Integrations API returns > 0 integrations
4. ✅ Overview Tab shows device counts
5. ✅ Devices Tab shows device grid
6. ✅ HA Devices API Status indicator shows "Connected - X devices discovered"

---

## Questions Before Starting?

1. Do you want me to proceed with all phases automatically?
2. Should I pause after investigation (Phase 1) to show you findings?
3. Do you want to keep the old `devices`/`entities` buckets or delete them?

**Approve this plan and I'll execute it step-by-step!** 🚀

