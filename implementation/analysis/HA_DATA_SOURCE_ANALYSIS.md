# Home Assistant Data Source Analysis - SQLite vs InfluxDB

## Date: October 14, 2025

## Question
Is the device data in SQLite real or mocked? How does it get refreshed?

## Current Situation: MOCK DATA ⚠️

### The Data You're Seeing is Mocked

The 5 devices showing in the API are **hardcoded mock data** from `simple_populate_sqlite.py`:

```python
devices_data = [
    {"device_id": "a0d7b954...", "name": "Sun", "manufacturer": "Home Assistant", "model": "Sun"},
    {"device_id": "b1e8c965...", "name": "Moon", "manufacturer": "Home Assistant", "model": "Moon"},
    {"device_id": "c2f9d076...", "name": "Person", "manufacturer": "Home Assistant", "model": "Person"},
    {"device_id": "d3a0e187...", "name": "Zone", "manufacturer": "Home Assistant", "model": "Zone"},
    {"device_id": "e4b1f298...", "name": "Weather", "manufacturer": "OpenWeatherMap", "model": "Weather"}
]
```

**Evidence:**
1. Device IDs match exactly: `a0d7b954f1b8c9e2f3a4b5c6d7e8f9a0` for Sun ✅
2. All timestamps identical: `2025-10-14T20:39:40.961413+00:00` ✅  
3. All devices have `entity_count: 0` (hardcoded in script) ✅
4. Only 5 devices (script only populates 5) ✅

## How the System SHOULD Work (Architecture)

### 1. Real Device Discovery Flow

```
Home Assistant WebSocket
         ↓
websocket-ingestion service
         ↓ (discovery_service.py)
Queries HA Device Registry
         ↓
Stores in InfluxDB
         ↓ (sync process)
Copies to SQLite (data-api)
         ↓
Exposed via /api/devices
```

### 2. Components Involved

#### A. Discovery Service (`services/websocket-ingestion/src/discovery_service.py`)
- **Purpose:** Queries Home Assistant registries via WebSocket
- **Methods:**
  - `discover_devices()` - Gets all devices from HA
  - `discover_entities()` - Gets all entities from HA  
  - `discover_config_entries()` - Gets all integrations from HA
  - `discover_all()` - Runs all discovery and stores to InfluxDB

#### B. When Discovery Runs
**Location:** `services/websocket-ingestion/src/connection_manager.py:319`

```python
async def _on_connect(self):
    # ... after authentication ...
    logger.info("🔍 Starting device and entity discovery...")
    await self.discovery_service.discover_all(self.client.websocket)
```

**Trigger:** When WebSocket connects to Home Assistant
**Frequency:** On initial connection + after reconnects
**Storage:** Writes to InfluxDB measurement `devices`

#### C. SQLite Sync Gap ⚠️
**PROBLEM:** There is NO automated sync from InfluxDB → SQLite!

The sync scripts exist but are **manual only:**
1. `sync_devices.py` - Reads from InfluxDB, generates populate script
2. `populate_sqlite.py` - Manually run inside data-api container
3. `simple_populate_sqlite.py` - Mock data (currently being used)

## Current Status

### What IS Working ✅
1. **WebSocket connection** - Connected to Home Assistant
2. **Event streaming** - Receiving state_changed events
3. **InfluxDB storage** - Events stored in InfluxDB
4. **Discovery service** - Code exists and works

### What is NOT Working ❌
1. **Device discovery not running** - No logs showing discovery
2. **No InfluxDB → SQLite sync** - Manual process only
3. **Using mock data** - SQLite populated with hardcoded values
4. **No periodic refresh** - Discovery only on connect, no scheduler

## Why Are You Seeing Mock Data?

Someone ran `simple_populate_sqlite.py` to test the SQLite database:

```bash
# This was run at some point (probably October 14, 2025 at 20:39:40 UTC):
python simple_populate_sqlite.py
# or
docker exec homeiq-data-api python /app/simple_populate_sqlite.py
```

This populated the database with 5 test devices to verify the API works.

## How to Get Real Data

### Option 1: Manual Discovery and Sync (Quick Test)

```bash
# Step 1: Trigger discovery (run discovery script)
python scripts/discover-and-store-devices.py

# Step 2: Check InfluxDB has devices
docker exec homeiq-influxdb influx query \
  -o homeassistant \
  'from(bucket:"home_assistant_events") |> range(start:-1h) |> filter(fn:(r) => r._measurement == "devices")'

# Step 3: Sync from InfluxDB to SQLite
python sync_devices.py
# This creates populate_sqlite.py

# Step 4: Run populate script in data-api container
docker cp populate_sqlite.py homeiq-data-api:/app/
docker exec homeiq-data-api python /app/populate_sqlite.py
```

### Option 2: Verify WebSocket Discovery is Running

```bash
# Check if websocket is connected and running discovery
docker logs homeiq-websocket | grep -i "discovery\|devices"

# If discovery isn't running, restart websocket service
docker restart homeiq-websocket

# Watch logs for discovery
docker logs -f homeiq-websocket
# Look for: "DISCOVERING DEVICES", "Discovered X devices", "Stored X devices in InfluxDB"
```

### Option 3: Implement Automated Sync (Long-term Fix)

**Need to add:**

1. **Periodic Discovery Refresh** (websocket-ingestion)
   - Add scheduler to run discovery every N hours
   - Update devices/entities periodically

2. **Automated InfluxDB → SQLite Sync** (data-api)
   - Background task in data-api
   - Reads from InfluxDB every N minutes
   - Updates SQLite with latest devices/entities

3. **Real-time Updates** (websocket-ingestion → data-api)
   - Subscribe to device_registry_updated events
   - Forward updates to data-api via HTTP
   - data-api updates SQLite immediately

## Recommended Solution

### Immediate (Use Discovery Script)

```bash
# 1. Run discovery to populate InfluxDB
cd scripts
python discover-and-store-devices.py

# 2. Then sync to SQLite
cd ..
python sync_devices.py
docker cp populate_sqlite.py homeiq-data-api:/app/
docker exec homeiq-data-api python /app/populate_sqlite.py

# 3. Refresh browser - should see real devices
```

### Long-term (Add to data-api startup)

Add to `services/data-api/src/main.py` startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for startup/shutdown"""
    # Initialize database
    await init_db()
    
    # NEW: Sync devices from InfluxDB on startup
    await sync_devices_from_influxdb()
    
    # Start background tasks
    asyncio.create_task(periodic_device_sync())  # Every 5 minutes
    
    yield
    # Cleanup
```

## Summary

| Aspect | Current Status | Desired Status |
|--------|---------------|----------------|
| **Device Data Source** | Mock (hardcoded 5 devices) | Real (from Home Assistant) |
| **Last Update** | Oct 14, 20:39:40 UTC (static) | Live/periodic |
| **Discovery Running** | Unknown (check logs) | On connect + periodic |
| **InfluxDB Storage** | Unknown (need to check) | Active |
| **SQLite Sync** | Manual only | Automated |
| **Refresh Frequency** | Never (static mock data) | Should be: Every 5-15 min |

## Next Steps

1. ✅ **Verify discovery is running:** Check websocket logs
2. ⚠️ **Check InfluxDB:** See if real devices are stored
3. ❌ **Run sync:** Get real data from InfluxDB → SQLite
4. 🔧 **Implement automation:** Add periodic sync to data-api

## Files Referenced

- `simple_populate_sqlite.py` - Mock data script (currently in use)
- `populate_sqlite.py` - Real data script (generated by sync_devices.py)
- `sync_devices.py` - InfluxDB → SQLite sync script
- `scripts/discover-and-store-devices.py` - Manual discovery script
- `services/websocket-ingestion/src/discovery_service.py` - Discovery implementation
- `services/websocket-ingestion/src/connection_manager.py:319` - Where discovery is triggered
- `services/data-api/src/devices_endpoints.py` - API that serves device data

