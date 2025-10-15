# Architecture Flaw: Device Storage Duplication

## Date: October 14, 2025

## The Problem You Identified ✅

**Current (Broken) Flow:**
```
Home Assistant
      ↓ WebSocket
Discovery Service (websocket-ingestion)
      ↓ Stores to
InfluxDB (devices measurement)
      ↓ ⚠️ MANUAL SYNC REQUIRED
SQLite (metadata.db)
      ↓ Served by
Data API (/api/devices)
```

**What Should Happen:**
```
Home Assistant
      ↓ WebSocket Discovery
Discovery Service
      ├─→ InfluxDB (historical snapshots for analytics)
      └─→ SQLite (current metadata) ✅ PRIMARY SOURCE
            ↓ Served by
         Data API (/api/devices)
```

## Root Cause Analysis

### Epic 22 Implementation Gap

**Epic 22** (SQLite Metadata Storage) introduced SQLite for devices/entities but:

1. ✅ **Created** SQLite database with Device/Entity models
2. ✅ **Updated** data-api to serve from SQLite
3. ❌ **Never Updated** discovery service to write to SQLite
4. ❌ **Never Automated** the InfluxDB → SQLite sync

**From Epic 22 docs:**
> "Migration script from InfluxDB tags to SQLite"

This was meant to be a **one-time migration**, not an ongoing sync process!

### Why This Happened

**Original Design (Pre-Epic 22):**
- Everything stored in InfluxDB
- Devices as tags on events
- Simple, single database

**Epic 22 Goal:**
- Split metadata (SQLite) from time-series (InfluxDB)
- Faster device queries (<10ms vs ~50ms)
- Better relational queries

**What Went Wrong:**
- Discovery service was never updated to write to SQLite
- It still writes to InfluxDB (old behavior)
- Manual sync script created but never automated
- Result: Two databases, no sync, stale data in SQLite

## The Correct Architecture

### Data Flow by Type

| Data Type | Storage | Rationale |
|-----------|---------|-----------|
| **Device Metadata** | SQLite (primary) | Current state, fast queries, joins |
| **Entity Metadata** | SQLite (primary) | Current state, fast queries, joins |
| **Device History** | InfluxDB (optional) | Track changes over time, analytics |
| **HA Events** | InfluxDB | Time-series data, state changes |
| **Sports Scores** | InfluxDB | Time-series data |
| **Webhooks** | SQLite | Metadata, transactions |

### Proposed Fix

**Option 1: Direct SQLite Write (RECOMMENDED)**

```python
# services/websocket-ingestion/src/discovery_service.py

class DiscoveryService:
    def __init__(self, influxdb_manager=None, data_api_url=None):
        self.influxdb_manager = influxdb_manager
        self.data_api_url = data_api_url  # NEW: data-api endpoint
    
    async def store_discovery_results(self, devices, entities, config_entries):
        # NEW: Write to SQLite via data-api HTTP endpoint
        await self._store_to_sqlite(devices, entities)
        
        # OPTIONAL: Also store snapshot to InfluxDB for historical tracking
        if self.influxdb_manager:
            await self._store_snapshot_to_influxdb(devices, entities)
    
    async def _store_to_sqlite(self, devices, entities):
        """Write directly to SQLite via data-api internal endpoint"""
        async with aiohttp.ClientSession() as session:
            # Bulk upsert devices
            await session.post(
                f"{self.data_api_url}/internal/devices/bulk_upsert",
                json={"devices": devices}
            )
            
            # Bulk upsert entities
            await session.post(
                f"{self.data_api_url}/internal/entities/bulk_upsert",
                json={"entities": entities}
            )
```

**Option 2: Shared Database Connection**

```python
# services/websocket-ingestion/src/discovery_service.py
# Add SQLite connection alongside InfluxDB

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from models import Device, Entity  # Shared models

class DiscoveryService:
    def __init__(self, influxdb_manager=None, sqlite_session_factory=None):
        self.influxdb_manager = influxdb_manager
        self.sqlite_session = sqlite_session_factory  # NEW
    
    async def store_discovery_results(self, devices, entities, config_entries):
        # Write to SQLite (primary)
        async with self.sqlite_session() as session:
            for device_data in devices:
                device = Device.from_ha_device(device_data)
                session.merge(device)  # Upsert
            await session.commit()
        
        # Optional: Snapshot to InfluxDB for history
        if self.influxdb_manager:
            await self._store_snapshot_to_influxdb(devices)
```

**Option 3: Message Queue (Over-engineered for now)**

```
Discovery Service → Redis/RabbitMQ → Data-API Worker → SQLite
```

## Recommended Solution

### Phase 1: Quick Fix (TODAY)

1. **Add internal bulk upsert endpoint to data-api:**
   ```python
   # services/data-api/src/devices_endpoints.py
   
   @router.post("/internal/devices/bulk_upsert")
   async def bulk_upsert_devices(
       devices: List[Dict[str, Any]],
       db: AsyncSession = Depends(get_db)
   ):
       """Internal endpoint for websocket-ingestion to update devices"""
       for device_data in devices:
           device = Device(
               device_id=device_data["device_id"],
               name=device_data.get("name"),
               manufacturer=device_data.get("manufacturer"),
               model=device_data.get("model"),
               # ... all fields
           )
           await db.merge(device)  # Upsert
       await db.commit()
       return {"status": "success", "count": len(devices)}
   ```

2. **Update discovery service to call data-api:**
   ```python
   # services/websocket-ingestion/src/discovery_service.py
   
   async def store_discovery_results(self, devices, entities, config_entries):
       # NEW: Post to data-api
       async with aiohttp.ClientSession() as session:
           await session.post(
               "http://ha-ingestor-data-api:8006/internal/devices/bulk_upsert",
               json=devices
           )
   ```

3. **Keep InfluxDB storage optional (for analytics):**
   ```python
   # Optional: Also store snapshot for historical tracking
   if self.influxdb_manager and STORE_DEVICE_HISTORY:
       await self._store_snapshot_to_influxdb(devices)
   ```

### Phase 2: Cleanup (Later)

1. **Remove sync scripts:**
   - Delete `sync_devices.py` (no longer needed)
   - Delete `populate_sqlite.py` (no longer needed)

2. **Add configuration flag:**
   ```env
   # Should we keep device history in InfluxDB?
   STORE_DEVICE_HISTORY_IN_INFLUXDB=false  # Default: false
   ```

3. **Migration path:**
   - Run discovery once to populate SQLite from HA
   - Optionally import historical data from InfluxDB (one-time)

## Benefits of the Fix

| Aspect | Before | After |
|--------|--------|-------|
| **Data Source** | InfluxDB → (manual) → SQLite | HA → SQLite (direct) ✅ |
| **Refresh** | Never (manual sync) | Real-time on discovery ✅ |
| **Complexity** | 2 DBs + sync script | 2 DBs, separate purposes ✅ |
| **Latency** | Stale data | Live data ✅ |
| **Dependencies** | websocket → influx → sync → sqlite → api | websocket → sqlite → api ✅ |

## Why InfluxDB Was Used Initially

Looking at the original code, discovery service was written before Epic 22:

1. **Initial Design:** Everything in InfluxDB (simple, one database)
2. **Epic 22 Added:** SQLite for faster metadata queries
3. **Gap:** Discovery service never updated to use SQLite
4. **Result:** Two databases, no sync automation

## Current State

### What Exists in Each Database

**InfluxDB `devices` measurement:**
- 94 real devices from Home Assistant ✅
- Last updated: When websocket connected
- Purpose: Was intended as primary storage
- Current role: Abandoned/orphaned data

**SQLite `devices` table:**
- 5 mock devices from populate script ❌
- Last updated: October 14, 2025 20:39:40 (static)
- Purpose: Serve via /api/devices
- Current role: Primary API source (but stale)

## Implementation Plan

### Step 1: Add Bulk Upsert Endpoint (30 min)
```python
# File: services/data-api/src/devices_endpoints.py
# Add internal bulk upsert for devices and entities
```

### Step 2: Update Discovery Service (1 hour)
```python
# File: services/websocket-ingestion/src/discovery_service.py
# Change store_discovery_results to call data-api
```

### Step 3: Test (30 min)
```bash
# Restart websocket-ingestion
docker restart ha-ingestor-websocket

# Watch logs - should see HTTP POST to data-api
docker logs -f ha-ingestor-websocket

# Check SQLite has 94 devices
curl http://localhost:8006/api/devices | jq '.count'
# Should return: 94
```

### Step 4: Optional InfluxDB History (future)
```python
# Only store device snapshots to InfluxDB if enabled
if os.getenv("TRACK_DEVICE_HISTORY", "false") == "true":
    await influxdb_manager.store_device_snapshot(devices)
```

## Summary

**You're 100% correct!** The architecture should be:

```
✅ HA → SQLite (devices/entities metadata)
✅ HA → InfluxDB (events, time-series data)
❌ HA → InfluxDB → SQLite (unnecessary hop, breaks data flow)
```

**The fix:**
- Discovery service writes directly to SQLite (via data-api endpoint)
- InfluxDB keeps historical event data only
- No sync scripts needed
- Real-time, always current data

**Estimated Time to Fix:** 2-3 hours
**Impact:** High - fixes stale data issue permanently
**Complexity:** Low - straightforward endpoint + HTTP call

## Files to Modify

1. **services/data-api/src/devices_endpoints.py** - Add bulk upsert endpoints
2. **services/websocket-ingestion/src/discovery_service.py** - Call data-api instead of InfluxDB
3. **services/websocket-ingestion/src/main.py** - Pass data-api URL to discovery service
4. **docker-compose.yml** - Add `DATA_API_URL` env var to websocket-ingestion

## Files to Deprecate (After Fix)

1. **sync_devices.py** - No longer needed
2. **populate_sqlite.py** - No longer needed
3. **simple_populate_sqlite.py** - No longer needed
4. **scripts/discover-and-store-devices.py** - Redundant with built-in discovery

