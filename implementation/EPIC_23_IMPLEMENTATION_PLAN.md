# Epic 23: Enhanced Event Data Capture - Implementation Plan

**Status:** 📋 **READY TO START**  
**Priority:** ⭐ **HIGH**  
**Estimated Duration:** 5-7 days  
**Epic Document:** [docs/prd/epic-23-enhanced-event-data-capture.md](../docs/prd/epic-23-enhanced-event-data-capture.md)

---

## Quick Reference: What We're Adding

### New Fields Summary

| Field | Type | Size | Location | Purpose |
|-------|------|------|----------|---------|
| `context_parent_id` | Field | 32B | InfluxDB | Automation causality tracing |
| `device_id` | Tag | 32B | InfluxDB | Device-level aggregation |
| `area_id` | Tag | 20B | InfluxDB | Spatial/room analysis |
| `duration_in_state` | Field | 8B | InfluxDB | Time-based behavioral patterns |
| `entity_category` | Tag | 15B | InfluxDB | Entity filtering (diagnostic/config) |
| `manufacturer` | Field | 30B | InfluxDB | Device reliability analysis |
| `model` | Field | 40B | InfluxDB | Model-specific issue tracking |
| `sw_version` | Field | 15B | InfluxDB | Version correlation |

**Total:** ~192 bytes/event (~18% storage increase)

---

## Implementation Order

### ✅ Story 23.1: Context Hierarchy Tracking (Day 1)
**Priority:** HIGH ⭐ **START HERE**

**Files to Modify:**
```
services/websocket-ingestion/src/event_processor.py
  - Extract context.parent_id from event
  - Add to processed event structure

services/enrichment-pipeline/src/influxdb_wrapper.py
  - Add context_parent_id field to InfluxDB point
  - Line ~217: Add after context_id field

services/data-api/src/events_endpoints.py
  - Add /api/v1/events/automation-trace/{context_id} endpoint
  - Query InfluxDB for events with matching context_parent_id
```

**Test Plan:**
- Unit test: Extract context with/without parent_id
- Integration test: Query automation chain by context_id
- Validation: ~50% of events should have parent_id (automation-triggered)

**Acceptance Criteria:**
- [ ] context_parent_id stored in InfluxDB (field)
- [ ] Events without parent store null/empty
- [ ] API endpoint returns automation chain
- [ ] No performance degradation (<50ms p95)

---

### ✅ Story 23.2: Device and Area Linkage (Days 2-3)
**Priority:** HIGH ⭐

**Files to Modify:**
```
services/websocket-ingestion/src/discovery_service.py
  - Maintain entity_id → device_id mapping cache
  - Maintain device_id/entity_id → area_id mapping
  - Subscribe to device/entity registry updates

services/websocket-ingestion/src/event_processor.py
  - Lookup device_id from entity_id using discovery_service
  - Lookup area_id from device_id or entity_id
  - Add to processed event structure

services/enrichment-pipeline/src/influxdb_wrapper.py
  - Add device_id tag (indexed for queries)
  - Add area_id tag (indexed for queries)
  - Lines ~152-156: Add after device_class tag

services/data-api/src/events_endpoints.py
  - Add query parameters: ?device_id=xxx&area_id=yyy
  - Update InfluxDB queries to filter by new tags
```

**Test Plan:**
- Unit test: Device/area lookup from registry cache
- Performance test: Lookup time <1ms per event
- Integration test: Query events by device_id, area_id
- Validation: >95% of events have device_id (where applicable)

**Acceptance Criteria:**
- [ ] device_id tag stored for entities with devices
- [ ] area_id tag stored for entities/devices with areas
- [ ] Registry cache updates on registry_updated events
- [ ] API supports filtering by device_id and area_id
- [ ] Lookup adds <5ms to event processing

---

### ✅ Story 23.3: Time-Based Analytics (Day 4)
**Priority:** HIGH ⭐

**Files to Modify:**
```
services/websocket-ingestion/src/event_processor.py
  - Calculate duration: new_state.last_changed - old_state.last_changed
  - Handle edge cases: no old_state, timezone differences
  - Add duration_in_state field to processed event

services/enrichment-pipeline/src/influxdb_wrapper.py
  - Add duration_in_state_seconds field
  - Line ~196: Add after old_state field
  - Validate: 0 <= duration <= 604800 (7 days in seconds)

services/data-api/src/events_endpoints.py
  - Add duration aggregation endpoint
  - /api/v1/events/duration-stats?entity_id=xxx&period=1h
```

**Test Plan:**
- Unit test: Duration calculation edge cases
  - No old_state → null or 0
  - Same timezone → correct duration
  - Different timezones → normalized correctly
  - Duration > 7 days → log warning but store
- Integration test: Query duration statistics
- Validation: 100% of state_changed events with old_state have duration

**Acceptance Criteria:**
- [ ] duration_in_state_seconds calculated for all events with old_state
- [ ] First state changes (no old_state) store null
- [ ] Timezone differences handled correctly
- [ ] API provides duration aggregation (avg, max, percentiles)
- [ ] Duration validation logs warnings for outliers (>7 days)

---

### ✅ Story 23.4: Entity Classification (Day 5, AM)
**Priority:** MEDIUM

**Files to Modify:**
```
services/websocket-ingestion/src/event_processor.py
  - Extract entity_category from entity_metadata
  - Add to processed event structure

services/enrichment-pipeline/src/influxdb_wrapper.py
  - Add entity_category tag
  - Line ~155: Add after entity_category from entity_metadata

services/data-api/src/events_endpoints.py
  - Add query parameter: ?exclude_category=diagnostic
  - Update InfluxDB query to filter by entity_category

services/health-dashboard/src/components/tabs/EventsTab.tsx
  - Add checkboxes: "Show diagnostic entities", "Show config entities"
  - Default: exclude diagnostic entities
```

**Test Plan:**
- Unit test: Entity category extraction
- Integration test: Filter events by category
- Validation: Dashboard displays correct entity counts

**Acceptance Criteria:**
- [ ] entity_category tag stored for entities with category
- [ ] Entities without category store empty/null
- [ ] API supports ?exclude_category parameter
- [ ] Dashboard checkboxes filter events correctly
- [ ] Default view excludes diagnostic entities

---

### ✅ Story 23.5: Device Metadata Enrichment (Day 5, PM)
**Priority:** LOW (but user requested)

**Files to Modify:**
```
services/websocket-ingestion/src/discovery_service.py
  - Cache device metadata: manufacturer, model, sw_version
  - Lookup by device_id

services/websocket-ingestion/src/event_processor.py
  - Lookup device metadata from discovery_service
  - Add manufacturer, model, sw_version to processed event

services/enrichment-pipeline/src/influxdb_wrapper.py
  - Add manufacturer, model, sw_version fields
  - Only store if device_id present (avoid nulls)

services/data-api/src/devices_endpoints.py (new or extend)
  - Add /api/v1/devices/reliability endpoint
  - Aggregate failure rates by manufacturer/model

services/health-dashboard/src/components/tabs/DevicesTab.tsx
  - Add "Device Reliability" section
  - Show failure rates by manufacturer
```

**Test Plan:**
- Unit test: Device metadata lookup from cache
- Performance test: Metadata lookup adds <1ms
- Integration test: Reliability endpoint aggregation
- Validation: Metadata populated only for events with device_id

**Acceptance Criteria:**
- [ ] manufacturer, model, sw_version stored for events with device_id
- [ ] Metadata from device registry cache (no per-event API calls)
- [ ] Dashboard shows device reliability metrics
- [ ] API endpoint provides manufacturer/model breakdown
- [ ] Fields only stored when device_id present

---

## Storage Impact Calculation

```python
# Current event size: ~500 bytes
# New fields: ~192 bytes
# New event size: ~692 bytes (+38%)

# For 50,000 events/day:
daily_storage = 50000 * 692  # ~35 MB/day
annual_storage = daily_storage * 365  # ~12.8 GB/year (raw)

# With tiered retention (downsampling):
# - Hot (7 days): 7 * 35 MB = 245 MB
# - Warm (30 days, 5-min downsample): ~100 MB
# - Cold (365 days, 1-hour downsample): ~500 MB
# Total: ~850 MB/year (vs ~600 MB/year before)
# Increase: ~250 MB/year (+42% with retention tiers)
```

---

## Key Implementation Notes

### Context Parent ID (Story 23.1)
```python
# services/websocket-ingestion/src/event_processor.py
context = event_data.get("context", {})
if context.get("parent_id"):
    extracted["context_parent_id"] = context["parent_id"]
else:
    extracted["context_parent_id"] = None

# services/enrichment-pipeline/src/influxdb_wrapper.py
context_parent_id = event_data.get("context_parent_id")
if context_parent_id:
    point.field("context_parent_id", context_parent_id)
```

### Device and Area Linkage (Story 23.2)
```python
# services/websocket-ingestion/src/discovery_service.py
class DiscoveryService:
    def __init__(self):
        self.entity_to_device = {}  # entity_id → device_id
        self.device_to_area = {}    # device_id → area_id
        self.entity_to_area = {}    # entity_id → area_id (direct)
    
    def get_device_id(self, entity_id: str) -> Optional[str]:
        return self.entity_to_device.get(entity_id)
    
    def get_area_id(self, entity_id: str, device_id: str = None) -> Optional[str]:
        # Check entity-level area first
        if entity_id in self.entity_to_area:
            return self.entity_to_area[entity_id]
        # Fallback to device-level area
        if device_id and device_id in self.device_to_area:
            return self.device_to_area[device_id]
        return None

# services/websocket-ingestion/src/event_processor.py
entity_id = extracted.get("entity_id")
device_id = self.discovery_service.get_device_id(entity_id)
area_id = self.discovery_service.get_area_id(entity_id, device_id)

if device_id:
    extracted["device_id"] = device_id
if area_id:
    extracted["area_id"] = area_id
```

### Duration Calculation (Story 23.3)
```python
# services/websocket-ingestion/src/event_processor.py
from datetime import datetime

old_state = event_data.get("old_state", {})
new_state = event_data.get("new_state", {})

if old_state and "last_changed" in old_state and "last_changed" in new_state:
    try:
        old_time = datetime.fromisoformat(old_state["last_changed"].replace("Z", "+00:00"))
        new_time = datetime.fromisoformat(new_state["last_changed"].replace("Z", "+00:00"))
        duration = (new_time - old_time).total_seconds()
        
        # Validate duration (warn if >7 days or negative)
        if duration < 0:
            logger.warning(f"Negative duration calculated: {duration}s for {entity_id}")
            duration = 0
        elif duration > 604800:  # 7 days
            logger.warning(f"Very long duration: {duration}s for {entity_id}")
        
        extracted["duration_in_state"] = duration
    except Exception as e:
        logger.error(f"Error calculating duration: {e}")
        extracted["duration_in_state"] = None
else:
    extracted["duration_in_state"] = None
```

---

## Testing Checklist

### Unit Tests
- [ ] Context extraction with/without parent_id
- [ ] Device/area lookup from registry cache
- [ ] Duration calculation edge cases
- [ ] Entity category normalization
- [ ] Device metadata lookup

### Integration Tests
- [ ] End-to-end event flow with all new fields
- [ ] Registry cache update on device_registry_updated
- [ ] InfluxDB write with new fields
- [ ] Query filtering by new tags
- [ ] API endpoints return correct data

### Performance Tests
- [ ] Event processing throughput >1000 events/sec
- [ ] Registry lookup latency <1ms per lookup
- [ ] Storage growth rate within predictions (±10%)
- [ ] Query performance with new tags

### Validation Tests
- [ ] Data completeness: % of events with each new field
- [ ] Data accuracy: Cross-check device_id against HA API
- [ ] Duration reasonableness: Detect outliers
- [ ] No InfluxDB schema conflicts

---

## Monitoring & Alerts

### Metrics to Track
```python
# Add to metrics_collector.py
- events_with_parent_id_percentage
- events_with_device_id_percentage
- events_with_area_id_percentage
- events_with_duration_percentage
- average_duration_by_entity
- device_registry_cache_hits
- device_registry_cache_misses
- storage_bytes_per_event
```

### Alerts to Configure
- Storage growth exceeds 20% of predictions
- Event processing latency >100ms (p95)
- Registry lookup failures >1%
- Duration outliers (>7 days) >0.1%
- Missing expected fields >5%

---

## Rollback Plan

If issues arise during deployment:

1. **Rollback WebSocket Service** - Revert event_processor.py changes
2. **Disable New Fields** - Set environment flag `ENABLE_ENHANCED_FIELDS=false`
3. **Monitor InfluxDB** - New fields won't break existing queries (optional fields)
4. **Dashboard Compatibility** - New visualizations degrade gracefully (hide if no data)

**No schema migration needed** - InfluxDB handles new fields automatically, so rollback is safe.

---

## Post-Implementation Validation

### Data Quality Checks (Day 7)
```bash
# Check field coverage
curl http://localhost:8003/api/v1/events/field-coverage

# Expected results:
# - context_parent_id: ~50% (automation-triggered events)
# - device_id: >95% (entities with devices)
# - area_id: ~80% (entities/devices with areas)
# - duration_in_state: 100% (events with old_state)
# - entity_category: ~15% (diagnostic/config entities)
# - manufacturer/model/sw_version: >95% (events with device_id)
```

### Performance Validation
```bash
# Run performance tests
./tests/performance/test_event_throughput.sh

# Target: >1000 events/sec with all new fields
```

### Storage Validation
```bash
# Check storage growth
influx query 'from(bucket:"home_assistant_events") |> range(start: -7d) |> count()'

# Compare to predictions (should be within ±10%)
```

---

## Success Criteria

- ✅ All 7 new fields captured and stored
- ✅ Storage overhead <20% increase (~200 bytes/event)
- ✅ Event processing <50ms (95th percentile)
- ✅ Data completeness >95% for applicable fields
- ✅ API endpoints functional with filtering
- ✅ Dashboard displays new analytics
- ✅ All tests passing
- ✅ Production deployment successful
- ✅ Documentation complete

---

**Ready to Start:** Yes ✅  
**Dependencies Resolved:** Yes (Epic 19 provides device/entity registry)  
**Estimated Completion:** 5-7 days from start  

**Next Step:** Begin Story 23.1 - Context Hierarchy Tracking

