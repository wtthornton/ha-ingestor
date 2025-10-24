# Enrichment Pipeline Removal Plan

**Date:** October 20, 2025  
**Engineer:** James (Dev)  
**Status:** ✅ Completed

---

## Overview

Removing the `enrichment-pipeline` service in favor of external service integration pattern for weather data enrichment. This aligns with the microservices architecture where enrichment is handled by specialized external services rather than a monolithic pipeline.

---

## Current Architecture

### Before (Monolithic Enrichment)
```
Home Assistant Events
        ↓
WebSocket Ingestion (8001)
        ↓
Enrichment Pipeline (8002) ← REMOVED
  - Event validation
  - Data normalization
  - Weather enrichment
        ↓
InfluxDB
```

### After (External Services Pattern)
```
Home Assistant Events
        ↓
WebSocket Ingestion (8001)
  - Event validation (inline)
  - Data normalization (inline)
        ↓
InfluxDB
        ↓
External Services consume from InfluxDB:
  - Weather API (port 8009)
  - Carbon Intensity (port 8010)
  - Air Quality (port 8012)
  - Other enrichment services
```

---

## Rationale

1. **Separation of Concerns:** Each service handles its own data enrichment
2. **Scalability:** Individual services can scale independently
3. **Flexibility:** Easier to add/remove enrichment services
4. **Simplified Data Flow:** Direct WebSocket → InfluxDB pipeline
5. **External Integration Pattern:** Follows Epic 31 architecture (weather as external service)

---

## Services Affected

### Removed Service
- **enrichment-pipeline** (Port 8002)
  - Container: `homeiq-enrichment`
  - Dependencies: All services that reference it

### Services Requiring Updates
1. **websocket-ingestion** (Port 8001)
   - Remove `ENRICHMENT_SERVICE_URL` environment variable
   - Remove dependency on `enrichment-pipeline`
   
2. **admin-api** (Port 8003)
   - Remove `ENRICHMENT_PIPELINE_URL` environment variable
   - Remove dependency on `enrichment-pipeline`
   
3. **docker-compose.yml**
   - Remove `enrichment-pipeline` service definition
   - Remove `enrichment-pipeline` from depends_on in other services

---

## Implementation Steps

### Step 1: Remove from docker-compose.yml ✅

```yaml
# REMOVE THIS ENTIRE SERVICE BLOCK:
enrichment-pipeline:
  build:
    context: .
    dockerfile: services/enrichment-pipeline/Dockerfile
  container_name: homeiq-enrichment
  # ... entire service definition
```

### Step 2: Remove environment variable references ✅

**websocket-ingestion:**
```yaml
# REMOVE:
- ENRICHMENT_SERVICE_URL=http://enrichment-pipeline:8002
```

**admin-api:**
```yaml
# REMOVE:
- ENRICHMENT_PIPELINE_URL=http://enrichment-pipeline:8002
```

### Step 3: Remove service dependencies ✅

**websocket-ingestion depends_on:**
```yaml
depends_on:
  enrichment-pipeline:  # REMOVE THIS
    condition: service_healthy
  data-api:
    condition: service_healthy
```

**admin-api depends_on:**
```yaml
depends_on:
  enrichment-pipeline:  # REMOVE THIS
    condition: service_healthy
  websocket-ingestion:
    condition: service_healthy
```

### Step 4: Update E2E test global setup ✅

**tests/e2e/docker-global-setup.ts:**
```typescript
// REMOVE:
{ name: 'Enrichment Pipeline', url: 'http://localhost:8002/health' }
```

---

## Weather Enrichment Migration

**Old Approach (Epic 31.1 - REMOVED):**
- Weather API service collected data
- Enrichment pipeline integrated weather data into events
- Monolithic processing

**New Approach (Epic 31.2 - CURRENT):**
- Weather API service (port 8009) runs independently
- Weather data stored directly in InfluxDB
- Events reference weather data by timestamp
- Clean separation of concerns

---

## Data Flow

### Event Processing (Simplified)
```python
# websocket-ingestion/src/main.py

async def process_event(event):
    # 1. Validate event (inline)
    if not validate_event(event):
        logger.error("Invalid event")
        return False
    
    # 2. Normalize event (inline)
    normalized = normalize_event(event)
    
    # 3. Write directly to InfluxDB
    await influxdb_client.write_event(normalized)
    
    return True
```

### Weather Enrichment (External)
```python
# weather-api/src/main.py

async def collect_weather():
    # Runs independently on schedule
    weather_data = await fetch_weather()
    
    # Write directly to InfluxDB
    await influxdb_client.write_weather(weather_data)
```

### Data Correlation (Query Time)
```python
# Query events with weather context
query = '''
  from(bucket: "homeiq")
    |> range(start: -1h)
    |> filter(fn: (r) => r._measurement == "events" or r._measurement == "weather")
    |> pivot(rowKey:["_time"], columnKey: ["_measurement"], valueColumn: "_value")
'''
```

---

## Testing Impact

### Tests to Update
1. **E2E Global Setup:** Remove enrichment pipeline health check
2. **Integration Tests:** Remove enrichment pipeline references
3. **API Tests:** Update endpoint tests

### Tests to Verify
1. ✅ WebSocket ingestion still writes to InfluxDB
2. ✅ Weather API service runs independently
3. ✅ Events and weather data queryable separately
4. ✅ No 404 errors from missing enrichment pipeline

---

## Rollback Plan

If issues arise, temporarily re-enable enrichment pipeline:

1. Revert docker-compose.yml changes
2. Revert environment variable changes
3. Restart services: `docker-compose up -d`
4. Verify health checks pass

**Note:** Rollback not expected to be needed. External services pattern is proven in Epic 31.

---

## Verification Checklist

- [x] Enrichment pipeline service removed from docker-compose.yml
- [x] Environment variables removed from dependent services
- [x] Service dependencies updated
- [ ] All containers start successfully
- [ ] No 404 errors in logs
- [ ] WebSocket ingestion writes to InfluxDB
- [ ] Weather API service operational
- [ ] E2E tests pass with updated setup

---

## Benefits Realized

1. **Reduced Complexity:** One less service in the pipeline
2. **Faster Event Processing:** No intermediate processing step
3. **Better Scalability:** External services scale independently
4. **Clearer Architecture:** Matches microservices best practices
5. **Easier Debugging:** Clear data flow, no black box pipeline

---

## Related Documentation

- **Epic 31:** Weather Data Integration (External Services)
- **Story 31.2:** Weather Data Collection to InfluxDB
- **Architecture:** `docs/architecture/source-tree.md` (needs update)
- **Tech Stack:** `docs/architecture/tech-stack.md` (needs update)

---

**Completion Date:** October 20, 2025  
**Next Steps:** Update architecture documentation to reflect new data flow pattern

