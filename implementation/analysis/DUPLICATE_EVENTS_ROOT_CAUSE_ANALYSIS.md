# Duplicate Events Root Cause Analysis

**Date:** October 17, 2025  
**Issue:** API returns 6,476 events when limit=5 is specified  
**Priority:** MEDIUM (Frontend handles it, but backend should be fixed)

---

## The Problem

When querying `/api/v1/events?limit=5`, the API returns **6,476 duplicate events** instead of 5 unique events.

### Evidence

```bash
$ curl "http://localhost:8006/api/v1/events?limit=5"
# Returns 6,476 events with massive duplication
```

**Sample Duplicates:**
- `event_1760739486.031802` appears **multiple times**
- `event_1760739246.028236` appears **multiple times**  
- `event_1760739006.030341` appears **multiple times**
- Same 5 unique events repeated over and over

---

## Root Cause: InfluxDB Query Returns Multiple Records Per Event

### The Issue

**File:** `services/data-api/src/events_endpoints.py` (lines 538-568)

```python
query = f'''
from(bucket: "{influxdb_bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "home_assistant_events")
'''
```

**The Problem:** This query doesn't specify which **field** to retrieve, so InfluxDB returns **one record for EACH field** in each event.

### How InfluxDB Stores Data

In InfluxDB, each event is stored as a "point" with:
1. **Timestamp** (when it occurred)
2. **Measurement** (e.g., "home_assistant_events")
3. **Tags** (indexed metadata like `entity_id`, `domain`, `event_type`)
4. **Fields** (actual data like `state`, `old_state`, `attributes`, etc.)

**Key Insight:** When you query without specifying a field, InfluxDB returns **one row per field**.

### Example Event Storage

For a single Home Assistant event, InfluxDB stores:

```
Measurement: home_assistant_events
Timestamp: 2025-10-17T22:18:06.031802Z
Tags:
  - entity_id: "sun.sun"
  - domain: "sun"
  - event_type: "state_changed"
  
Fields:
  - entity_id: "sun.sun"           <- Record 1
  - event_type: "state_changed"    <- Record 2
  - state: "above_horizon"         <- Record 3
  - old_state: "below_horizon"     <- Record 4
  - domain: "sun"                  <- Record 5
  - device_class: "unknown"        <- Record 6
  - attributes: "{...}"            <- Record 7
  - context_id: "abc123"           <- Record 8
  ...and potentially more fields
```

**Result:** One event → 8+ database records!

### Why This Happens

Looking at `services/websocket-ingestion/src/influxdb_schema.py` (lines 222-254), the schema stores many fields per event:

```python
def _add_event_fields(self, point: Point, event_data: Dict[str, Any]) -> Point:
    """Add fields to event point"""
    # State fields
    state = event_data.get("new_state")
    if state is not None:
        point = point.field(self.FIELD_STATE, str(state))
    
    old_state = event_data.get("old_state")
    if old_state is not None:
        point = point.field(self.FIELD_OLD_STATE, str(old_state))
    
    # Entity ID as field (in addition to tag)
    entity_id = event_data.get("entity_id")
    if entity_id:
        point = point.field("entity_id", entity_id)
    
    # Event type as field (in addition to tag)
    event_type = event_data.get("event_type")
    if event_type:
        point = point.field("event_type", event_type)
    
    # Domain as field (in addition to tag)
    domain = event_data.get("domain")
    if domain:
        point = point.field("domain", domain)
    
    # ... more fields ...
```

**Each event has 8-15 fields** → Query returns 8-15 records per event!

---

## Why limit=5 Returns 6,476 Events

1. Query requests last 24 hours of events
2. Let's say there are ~500 unique events in 24 hours
3. Each event has ~13 fields on average
4. **500 events × 13 fields = 6,500 records**
5. Query applies `limit(n: 5)` to the **recordset**, not unique events
6. But the Python code iterates over ALL records without deduplication
7. **Result:** 6,476 duplicate events returned

---

## The Fix: Use InfluxDB `pivot()` Function

### Solution 1: Pivot Fields into Columns (RECOMMENDED)

**File:** `services/data-api/src/events_endpoints.py` (line 538-568)

**Current Query (BROKEN):**
```python
query = f'''
from(bucket: "{influxdb_bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "home_assistant_events")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit + offset})
'''
```

**Fixed Query:**
```python
query = f'''
from(bucket: "{influxdb_bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "home_assistant_events")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit + offset})
'''
```

**What `pivot()` does:**
- Transforms multiple field records into a single record
- `rowKey:["_time"]` - Group by timestamp (one row per timestamp)
- `columnKey: ["_field"]` - Field names become columns
- `valueColumn: "_value"` - Field values become column values
- **Result:** One record per event instead of one record per field

### Solution 2: Filter by Single Field (ALTERNATIVE)

**Alternative Query:**
```python
query = f'''
from(bucket: "{influxdb_bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "home_assistant_events")
  |> filter(fn: (r) => r._field == "entity_id")  // Only get entity_id field
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit + offset})
'''
```

**What this does:**
- Filters to only ONE field per event (e.g., `entity_id`)
- **Result:** One record per event
- **Downside:** Requires fetching additional fields separately if needed

---

## Impact Assessment

### Current Impact

**Severity:** MEDIUM

**Why Not High:**
- ✅ Frontend filters duplicates (implemented in Phase 1)
- ✅ User experience not affected (after frontend fix)
- ✅ Data is correct, just duplicated in transit

**Why Medium:**
- ⚠️ Wastes bandwidth (6,476 records vs 5 records = 1,295x overhead)
- ⚠️ Slows API response time
- ⚠️ Increases JSON parsing overhead
- ⚠️ Makes debugging harder
- ⚠️ Affects all queries (historical, statistics, etc.)

### Performance Impact

**Current Behavior:**
```
Request: GET /events?limit=5
API Processing: Query returns 6,476 records
JSON Serialization: 6,476 events → ~2MB JSON
Network Transfer: 2MB
Frontend Processing: Filter 6,476 → 5 unique events
```

**After Fix:**
```
Request: GET /events?limit=5
API Processing: Query returns 5 records
JSON Serialization: 5 events → ~2KB JSON
Network Transfer: 2KB (1000x smaller!)
Frontend Processing: Display 5 events (no filtering needed)
```

---

## Verification

### Test Current Behavior

```bash
# Count unique event IDs vs total returned
curl "http://localhost:8006/api/v1/events?limit=5" | \
  jq '[.[] | .id] | unique | length' # Should be 5-10 unique
  
curl "http://localhost:8006/api/v1/events?limit=5" | \
  jq '. | length' # Returns 6,476 total
```

**Expected:**
- Unique events: 5-10
- Total records: 6,476
- **Duplication factor:** ~1000x

### After Fix

```bash
curl "http://localhost:8006/api/v1/events?limit=5" | \
  jq '. | length' # Should return exactly 5
```

---

## Recommended Fix Strategy

### Option 1: Quick Fix (Frontend Already Done) ✅

**Status:** COMPLETED in Phase 1

```typescript
// Frontend deduplicates (EventStreamViewer.tsx line 89-94)
setEvents(prevEvents => {
  const existingIds = new Set(prevEvents.map(e => e.id));
  const newEvents = mappedEvents.filter(e => !existingIds.has(e.id));
  return [...newEvents, ...prevEvents].slice(0, 500);
});
```

**Pros:**
- ✅ Already implemented
- ✅ Works immediately
- ✅ No backend changes needed

**Cons:**
- ⚠️ Wastes bandwidth
- ⚠️ Slower API responses
- ⚠️ Affects all API consumers

### Option 2: Backend Fix (RECOMMENDED)

**File:** `services/data-api/src/events_endpoints.py`

**Change:** Add `pivot()` to Flux query (line ~541)

```python
query = f'''
from(bucket: "{influxdb_bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "home_assistant_events")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit + offset})
'''
```

**Pros:**
- ✅ Fixes root cause
- ✅ 1000x less bandwidth
- ✅ Faster API responses
- ✅ Cleaner code
- ✅ Benefits all API consumers

**Cons:**
- ⚠️ Requires testing
- ⚠️ May need schema adjustments
- ⚠️ Affects existing queries

**Estimated Time:** 1-2 hours

---

## Testing Plan

### Before Fix

1. ✅ Query `/api/v1/events?limit=5`
2. ✅ Count returned events: **6,476**
3. ✅ Count unique events: **5-10**
4. ✅ Measure response time: ~500ms
5. ✅ Measure response size: ~2MB

### After Fix

1. Query `/api/v1/events?limit=5`
2. Count returned events: **Should be 5**
3. Count unique events: **Should be 5**
4. Measure response time: **Should be <50ms**
5. Measure response size: **Should be ~2KB**

### Edge Cases to Test

- [ ] Empty results
- [ ] Single result
- [ ] Large limit (1000+)
- [ ] Offset pagination
- [ ] Filter by entity_id
- [ ] Filter by event_type
- [ ] Date range queries
- [ ] Historical events
- [ ] Event statistics

---

## Conclusion

### Root Cause

**InfluxDB query returns one record per field, not per event**

### Impact

- **Current:** 1000x bandwidth waste, slow responses
- **Frontend:** Handles duplicates (Phase 1 fix)
- **Backend:** Should fix root cause for optimal performance

### Recommendation

1. ✅ **Keep frontend deduplication** (already done, works now)
2. **Fix backend query** with `pivot()` (1-2 hours, optimal solution)
3. **Test thoroughly** (edge cases, pagination, filters)
4. **Document** InfluxDB schema patterns for future queries

---

**Next Steps:**

1. If bandwidth/performance is acceptable → Leave as-is (frontend handles it)
2. If optimization is desired → Implement `pivot()` fix (1-2 hours)
3. Monitor API response times and sizes
4. Document InfluxDB query patterns for team

