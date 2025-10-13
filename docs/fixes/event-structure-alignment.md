# Event Structure Alignment Fix

## Problem Statement

The enrichment pipeline validation and normalization logic was written to handle Home Assistant's raw WebSocket event structure, but the WebSocket ingestion service preprocesses events using `EventProcessor.extract_event_data()` which flattens the structure before sending via HTTP.

## Current Architecture

```
Home Assistant → WebSocket Client → EventProcessor → HTTP Client → Enrichment Service
                                   ↓ (flattens)                    ↓ (expects nested)
```

### Event Structure Flow

1. **Home Assistant Raw Event:**
```json
{
  "id": 18,
  "type": "event",
  "event": {
    "event_type": "state_changed",
    "data": {
      "entity_id": "light.bedroom",
      "new_state": {...},
      "old_state": {...}
    },
    "time_fired": "...",
    "origin": "LOCAL"
  }
}
```

2. **After EventProcessor.extract_event_data():**
```json
{
  "event_type": "state_changed",
  "entity_id": "light.bedroom",
  "domain": "light",
  "new_state": {
    "state": "on",
    "attributes": {...},
    "last_changed": "...",
    "last_updated": "..."
  },
  "old_state": {...},
  "state_change": {
    "from": "off",
    "to": "on",
    "changed": true
  },
  "time_fired": "...",
  "origin": "LOCAL",
  "context": {...}
}
```

3. **What Enrichment Service Expects (WRONG):**
```json
{
  "event_type": "state_changed",
  "data": {
    "entity_id": "light.bedroom",
    "new_state": {...},
    "old_state": {...}
  }
}
```

## Solution Design

### Chosen Approach: Update Enrichment Service

**Rationale:**
- WebSocket service's preprocessing is valuable and reduces payload size
- Clear separation of concerns: WebSocket handles HA-specific extraction
- No breaking changes to WebSocket service
- Aligns with microservice best practices

### Implementation Changes

#### 1. Data Validator Updates

**File:** `services/enrichment-pipeline/src/data_validator.py`

**Changes:**
- Line 97-99: Update to extract `entity_id` from top level, not `event['data']['entity_id']`
- Line 162-163: Update `_validate_event_structure` to check for `entity_id` at top level, not `data` field
- All validation methods should work with flattened structure

**Before:**
```python
event_data = event.get('data', {})
entity_id = event_data.get('entity_id', '')
```

**After:**
```python
entity_id = event.get('entity_id', '')
```

#### 2. Data Normalizer Updates

**File:** `services/enrichment-pipeline/src/data_normalizer.py`

**Changes:**
- Line 82, 94: Update entity_id extraction from `event_data.get('data', {}).get('entity_id')` to `event_data.get('entity_id')`
- All normalization helper methods should work with flattened structure
- Ensure no assumptions about nested `data` field

#### 3. Main Service Updates

**File:** `services/enrichment-pipeline/src/main.py`

**Changes:**
- Add debug logging to trace event flow (already added)
- Ensure HTTP endpoint handler expects flattened structure
- Update any references to nested structure

#### 4. Quality Metrics Restoration

**Files:** Multiple

**Changes:**
- Uncomment quality metrics initialization
- Uncomment quality dashboard initialization
- Uncomment quality reporting initialization
- Ensure all quality metric calls use correct event structure

### Testing Strategy

#### Unit Tests
1. Test `DataValidationEngine.validate_event()` with flattened structure
2. Test `DataNormalizer.normalize_event()` with flattened structure
3. Test all helper methods with correct structure

#### Integration Tests
1. Send test event from WebSocket service to enrichment service
2. Verify event passes validation
3. Verify event is normalized correctly
4. Verify event is written to InfluxDB with correct fields

#### End-to-End Tests
1. Trigger state change in Home Assistant
2. Verify event flows through entire pipeline
3. Verify data appears in InfluxDB
4. Verify dashboard shows correct metrics

### Rollout Plan

#### Phase 1: Fix Core Validation & Normalization (Current)
- [x] Add comprehensive debug logging
- [ ] Update data_validator.py to handle flattened structure
- [ ] Update data_normalizer.py to handle flattened structure
- [ ] Test with live events
- [ ] Verify events pass validation

#### Phase 2: Verify Data Flow
- [ ] Confirm events reach InfluxDB
- [ ] Verify InfluxDB schema is correct
- [ ] Check dashboard displays data
- [ ] Monitor for any errors

#### Phase 3: Restore Quality Features
- [ ] Uncomment quality metrics initialization
- [ ] Test quality metrics collection
- [ ] Uncomment quality dashboard routes
- [ ] Test quality dashboard endpoints
- [ ] Uncomment quality reporting
- [ ] Verify quality reports generate correctly

#### Phase 4: Cleanup & Documentation
- [ ] Remove all debug logging
- [ ] Remove all "TEMPORARILY DISABLED" comments
- [ ] Update API documentation
- [ ] Update architecture diagrams
- [ ] Add integration tests

### Success Criteria

1. ✅ Events pass validation without errors
2. ✅ Events are normalized successfully
3. ✅ Events are written to InfluxDB
4. ✅ Dashboard shows non-zero event counts
5. ✅ No HTTP 500 errors from enrichment service
6. ✅ WebSocket service circuit breaker stays closed
7. ✅ Quality metrics are collected
8. ✅ Quality dashboard displays metrics

### Risk Mitigation

**Risk:** Breaking existing InfluxDB writes
**Mitigation:** 
- Test InfluxDB schema after changes
- Verify measurement names and field names
- Check backward compatibility with existing data

**Risk:** Performance degradation
**Mitigation:**
- Monitor processing latency
- Check memory usage
- Verify no memory leaks with quality metrics

**Risk:** Data loss during transition
**Mitigation:**
- Keep debug logging until stable
- Monitor error rates
- Have rollback plan ready

### Files Modified

1. `services/enrichment-pipeline/src/data_validator.py` - Validation logic
2. `services/enrichment-pipeline/src/data_normalizer.py` - Normalization logic
3. `services/enrichment-pipeline/src/main.py` - Service initialization and handlers

### Files to Review (Not Modified Yet)

1. `services/enrichment-pipeline/src/influxdb_writer.py` - Verify field mapping
2. `services/enrichment-pipeline/src/quality_metrics.py` - Verify event structure assumptions
3. `services/enrichment-pipeline/tests/*` - Update test fixtures

## Implementation Status

- [x] Problem identified
- [x] Solution designed
- [x] Debug logging added
- [ ] Validator updated (partial)
- [ ] Normalizer updated (partial)
- [ ] Tests updated
- [ ] Quality features restored
- [ ] Documentation updated

