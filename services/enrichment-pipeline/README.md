# Enrichment Pipeline Service

> **⚠️ DEPRECATED - October 2025 (Epic 31)**
>
> This service has been deprecated as part of Epic 31 architectural improvements. The code remains for reference but is **not deployed in production**.
>
> - **Status:** ❌ Not Active (deprecated in Epic 31)
> - **Reason:** Simplified architecture - direct writes to InfluxDB
> - **Replacement:** Inline normalization in websocket-ingestion service
> - **Migration:** Epic 31 - Direct InfluxDB writes
> - **Old Port:** 8002 (not in use)
> - **Deprecated:** October 2025

---

## 📋 Historical Purpose

The Enrichment Pipeline was a FastAPI service that provided:
- Event data validation
- Data normalization to standard format
- InfluxDB Line Protocol conversion
- Quality metrics and monitoring
- Batch write optimization

---

## 🔄 Epic 31 Migration

### Old Architecture (Pre-Epic 31)

```
Home Assistant
    ↓ WebSocket
websocket-ingestion (8001)
    ↓ HTTP POST /events
enrichment-pipeline (8002)
    ├─ Validate events
    ├─ Normalize data
    ├─ Generate Line Protocol
    └─ Write to InfluxDB (8086)
```

### New Architecture (Epic 31)

```
Home Assistant
    ↓ WebSocket
websocket-ingestion (8001)
    ├─ Validate events (inline)
    ├─ Normalize data (inline)
    ├─ Device/area lookups (Epic 23.2)
    ├─ Duration calculation (Epic 23.3)
    └─ DIRECT InfluxDB writes
```

---

## 💡 Why Was It Deprecated?

### Reasons for Removal

1. **Simplified Architecture**
   - Removed unnecessary service hop
   - Reduced system complexity
   - Fewer points of failure

2. **Performance Improvements**
   - Eliminated HTTP POST overhead
   - Reduced latency (2-hop → 1-hop)
   - Direct batch writes to InfluxDB

3. **Maintenance Reduction**
   - One less service to maintain
   - Simplified deployment
   - Reduced Docker resource usage

4. **Inline Processing**
   - Validation moved to websocket-ingestion
   - Normalization happens in-place
   - Batch processing maintained

### Performance Impact

**Before Epic 31:**
- Event flow: HA → WS (8001) → Enrichment (8002) → InfluxDB
- Total latency: ~50-100ms per event
- Two services to monitor

**After Epic 31:**
- Event flow: HA → WS (8001) → InfluxDB
- Total latency: ~20-30ms per event
- One less service to monitor

---

## 🔧 Migration Guide

### For Developers

If you have code that references the enrichment-pipeline:

**Old Code:**
```python
# DON'T DO THIS - Deprecated pattern
async with aiohttp.ClientSession() as session:
    async with session.post(
        "http://enrichment-pipeline:8002/events",
        json=event_data
    ) as response:
        result = await response.json()
```

**New Code (Epic 31):**
```python
# DO THIS - Direct InfluxDB write
from influxdb_client import Point

point = Point("state_changed") \
    .tag("entity_id", event["entity_id"]) \
    .tag("domain", event["domain"]) \
    .field("state", event["new_state"]) \
    .time(event["timestamp"])

await influx_write_api.write(point)
```

### For Configuration

**Old docker-compose.yml:**
```yaml
enrichment-pipeline:
  build: ./services/enrichment-pipeline
  ports:
    - "8002:8002"
  # REMOVE THIS SERVICE
```

**New docker-compose.yml:**
```yaml
# No enrichment-pipeline service needed
# websocket-ingestion handles everything
websocket-ingestion:
  build: ./services/websocket-ingestion
  ports:
    - "8001:8001"
  environment:
    - INFLUXDB_URL=http://influxdb:8086  # Direct write
```

---

## 📚 Historical Documentation

For historical reference, the enrichment-pipeline provided:

### Endpoints (Deprecated)
- `POST /events` - Process events from websocket-ingestion
- `POST /process-event` - Process single event
- `POST /process-events` - Batch event processing
- `GET /health` - Service health status
- `GET /status` - Service statistics

### Features (Now in websocket-ingestion)
- Event validation ✅ Moved to websocket-ingestion
- Data normalization ✅ Moved to websocket-ingestion
- InfluxDB writes ✅ Direct writes from websocket-ingestion
- Quality metrics ✅ Maintained in websocket-ingestion
- Batch processing ✅ Improved in websocket-ingestion

---

## 📖 Code Reference

The enrichment-pipeline code is preserved in the repository for:
- Historical reference
- Understanding Epic 31 changes
- Code reuse (validation logic, normalization functions)
- Educational purposes

**Location:** `services/enrichment-pipeline/`

**Key Files:**
- `src/main.py` - FastAPI application (deprecated)
- `src/data_validator.py` - Validation logic (moved to websocket-ingestion)
- `src/data_normalizer.py` - Normalization (moved to websocket-ingestion)

---

## 🔍 If You See References to This Service

### In Documentation
- Update to reference websocket-ingestion direct writes
- Remove HTTP POST to enrichment-pipeline
- Update architecture diagrams

### In Code
- Replace with direct InfluxDB writes
- Use inline validation
- Follow Epic 31 patterns

### In Configuration
- Remove enrichment-pipeline from docker-compose.yml
- Update environment variables
- Remove port 8002 mappings

---

## 📚 Related Documentation

- [Epic 31 Documentation](../../docs/architecture/epic-31-architecture.md)
- [WebSocket Ingestion Service](../websocket-ingestion/README.md) - Replacement service
- [.cursor/rules/epic-31-architecture.mdc](../../.cursor/rules/epic-31-architecture.mdc) - Current architecture
- [SERVICES_OVERVIEW.md](../../docs/SERVICES_OVERVIEW.md) - Current service list

---

## ✅ Verification

To verify enrichment-pipeline is not running:

```bash
# Check docker-compose.yml
grep -A 5 "enrichment-pipeline:" docker-compose.yml
# Should be commented out or missing

# Check running containers
docker ps | grep enrichment
# Should return nothing

# Check port 8002
curl http://localhost:8002/health
# Should return connection refused
```

---

**Original Version:** 1.0.0
**Deprecated:** October 2025 (Epic 31)
**Status:** ❌ Not Active
**Replacement:** Direct InfluxDB writes from websocket-ingestion
**Last Active:** October 2025
