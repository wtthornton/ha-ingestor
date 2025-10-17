# Historical Event Count Implementation Plan

## Problem Statement

The dashboard's "Total Events" metric resets on service restarts, losing historical data. The counts should be cumulative from database startup, not session-based.

## Current Architecture Analysis

### Data Flow

```
Dashboard (Port 3000)
    ↓ (useStatistics hook → apiService.getStatistics())
Admin API (Port 8003/8004)
    ↓ (aggregates from service health endpoints)
WebSocket Service (Port 8001) /health endpoint
Enrichment Pipeline (Port 8002) /health endpoint
    ↓ (both services have session-scoped counters)
InfluxDB (Port 8086)
    └─ Contains historical event data
```

### Current Issues

1. **WebSocket Ingestion Service**
   - ✅ `HistoricalEventCounter` class created
   - ✅ Integrated into `main.py`
   - ✅ Set on `health_handler` via `set_historical_counter()`
   - ✅ Health endpoint returns combined totals
   - ⚠️ InfluxDB query parsing issue: "Error parsing grouped count result: '_field'"

2. **Enrichment Pipeline Service**
   - ✅ `HistoricalEventCounter` class created
   - ✅ Integrated into `main.py`
   - ❌ **NOT** set on `health_handler` (missing `set_historical_counter()` call)
   - ❌ `get_service_status()` uses wrong field name: `'total_events_processed'` instead of `'normalized_events'`
   - ❌ Health endpoint returns 0 for all totals

### Root Causes

#### Issue 1: Enrichment Pipeline Missing Historical Counter Setup
**Location:** `services/enrichment-pipeline/src/main.py`

The enrichment pipeline creates `HistoricalEventCounter` but never passes it to the health check handler:

```python
# Line ~434: health_handler.set_service(service) is called
# BUT: health_handler.set_historical_counter(service.historical_counter) is NOT called
```

**Impact:** The health check handler doesn't have access to historical totals.

#### Issue 2: Wrong Field Name in get_service_status()
**Location:** `services/enrichment-pipeline/src/main.py` line 394

```python
session_total = normalization_stats.get('total_events_processed', 0)  # WRONG
# Should be:
session_total = normalization_stats.get('normalized_events', 0)  # CORRECT
```

The `DataNormalizer.get_normalization_statistics()` returns `normalized_events`, not `total_events_processed`.

**Impact:** session_total is always 0, so combined_total is always 0.

#### Issue 3: InfluxDB Query Result Parsing
**Location:** `services/websocket-ingestion/src/historical_event_counter.py`

The InfluxDB query is working but the result parsing is failing with:
`Error parsing grouped count result: '_field'`

This suggests the query result structure doesn't match expectations.

## Implementation Plan

### Phase 1: Fix Enrichment Pipeline Integration ✅ (Partially Complete)

1. ✅ Fix field name in `get_service_status()`
   - Changed `'total_events_processed'` to `'normalized_events'`
   
2. ❌ **TO DO:** Add historical counter to health handler
   ```python
   # services/enrichment-pipeline/src/main.py
   # After line 434 where health_handler.set_service(service) is called:
   
   health_handler.set_historical_counter(service.historical_counter)
   ```

### Phase 2: Fix InfluxDB Query Parsing

**Location:** Both `historical_event_counter.py` files

The current query structure:
```python
query = f'from(bucket: "{bucket}") ' \
        f'|> range(start: 0) ' \
        f'|> filter(fn: (r) => r._measurement == "{measurement}") ' \
        f'|> drop(columns: ["_start", "_stop", "_field", "_measurement"]) ' \
        f'|> group() ' \
        f'|> count()'
```

**Issue:** The `count()` function needs a column to count. When we drop `_field`, the count has nothing to work with.

**Solution Options:**

**Option A: Count records before dropping columns**
```python
query = f'from(bucket: "{bucket}") ' \
        f'|> range(start: 0) ' \
        f'|> filter(fn: (r) => r._measurement == "{measurement}") ' \
        f'|> count() ' \  # Count first
        f'|> group() ' \   # Then group
        f'|> sum()'        # Sum all counts
```

**Option B: Use a specific field to count**
```python
query = f'from(bucket: "{bucket}") ' \
        f'|> range(start: 0) ' \
        f'|> filter(fn: (r) => r._measurement == "{measurement}") ' \
        f'|> filter(fn: (r) => r._field == "state") ' \  # Pick a field that exists
        f'|> count()'
```

**Option C: Query the raw record count directly**
```python
# Use InfluxDB's internal table count
query = f'from(bucket: "{bucket}") ' \
        f'|> range(start: 0) ' \
        f'|> filter(fn: (r) => r._measurement == "{measurement}") ' \
        f'|> count(column: "_time")'  # Count timestamps (always present)
```

**Recommended:** Option C - count `_time` column which always exists.

### Phase 3: Test and Verify

1. Rebuild services
2. Restart services
3. Verify logs show correct initialization
4. Check health endpoints for correct totals
5. Verify dashboard displays correct values

### Phase 4: Update Documentation

Create completion document with:
- Changes made
- Test results
- Expected behavior
- Future considerations

## Expected Behavior After Fix

### WebSocket Ingestion Service `/health`
```json
{
  "subscription": {
    "total_events_received": 250,      // Historical (150) + Session (100)
    "session_events_received": 100,     // Current session only
    "historical_events_received": 150   // From database
  }
}
```

### Enrichment Pipeline Service `/health`
```json
{
  "normalization": {
    "normalized_events": 100,           // Current session stat
    "total_events_processed": 250,      // Historical (150) + Session (100)
    "session_events_processed": 100,    // Current session only
    "historical_events_processed": 150  // From database
  }
}
```

### Dashboard Display
- **Total Events**: 250 (persists across restarts)
- **Events This Session**: 100 (resets on restart)

## Files to Modify

1. ✅ `services/enrichment-pipeline/src/main.py` (field name fix)
2. ❌ `services/enrichment-pipeline/src/main.py` (add set_historical_counter call)
3. ❌ `services/websocket-ingestion/src/historical_event_counter.py` (fix query)
4. ❌ `services/enrichment-pipeline/src/historical_event_counter.py` (fix query)
5. ❌ Rebuild and restart services

## Testing Steps

1. Check current event count in InfluxDB:
   ```bash
   docker-compose exec influxdb influx query '
     from(bucket: "home_assistant_events")
       |> range(start: 0)
       |> filter(fn: (r) => r._measurement == "home_assistant_events")
       |> count(column: "_time")
   '
   ```

2. Restart services and verify historical count matches database

3. Process new events and verify session count increments

4. Verify dashboard shows: `total = historical + session`

## Rollback Plan

If issues occur:
1. Revert `historical_event_counter.py` changes
2. Services will still work with session-only counts
3. Historical counting feature disabled gracefully

## Future Enhancements

1. Cache historical count (only query on startup, not every health check)
2. Add metrics for historical count query performance
3. Consider storing cumulative totals in a separate InfluxDB measurement
4. Add configuration option to enable/disable historical counting

## Context7 Research Needed

- InfluxDB Flux query language best practices for counting records
- InfluxDB Python client API documentation for query result parsing
- Proper error handling patterns for InfluxDB queries

