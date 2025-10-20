# Critical Fix Plan - Event Processing Issues
**Date:** October 20, 2025  
**Priority:** 🚨 CRITICAL  
**Estimated Time:** 30 minutes

=============================================================================
ISSUES IDENTIFIED
=============================================================================

## 🚨 Issue #1: Event Processing Completely Blocked (CRITICAL)

**Service:** websocket-ingestion  
**Error:** `AttributeError: 'WebSocketIngestionService' object has no attribute 'weather_enrichment'`  
**Location:** Line 360 in `/services/websocket-ingestion/src/main.py`  
**Impact:** 100% of Home Assistant events fail to process

**Root Cause Analysis:**
```python
# Line 64: Attribute commented out (never initialized)
# self.weather_enrichment: Optional[WeatherEnrichmentService] = None

# Line 91: Feature disabled
self.weather_enrichment_enabled = False

# Lines 147-152: Conditional init (never executes because enabled=False)
if self.weather_api_key and self.weather_enrichment_enabled:
    self.weather_enrichment = WeatherEnrichmentService(...)

# Line 360: Code tries to use non-existent attribute ❌
if self.weather_enrichment:  # AttributeError!
    processed_event = await self.weather_enrichment.enrich_event(processed_event)
```

**Why This Happened:**
- Epic 31 disabled weather enrichment (moved to weather-api service)
- Removed initialization but forgot to remove usage
- Code never tested after Epic 31 deployment

**Fix Strategy:**
Since weather enrichment is permanently disabled, remove all references.

---

## ⚠️ Issue #2: Webhook Event Detector InfluxDB Error (MEDIUM)

**Service:** data-api  
**Error:** "Error in webhook event detector: InfluxDB client not connected"  
**Impact:** Webhook-based game alerts may not work  
**Frequency:** Recurring every few seconds

**Root Cause:** Unknown (need to investigate)

---

## ⚠️ Issue #3: Setup Service Integration Warnings (LOW)

**Service:** ha-setup-service  
**Warning:** Only 2/6 integrations healthy, Admin API integration failing  
**Impact:** Non-critical, service functional  
**Health Score:** 88/100 (acceptable)

=============================================================================
FIX PLAN
=============================================================================

## Fix #1: Remove Weather Enrichment References (CRITICAL)

**File:** `services/websocket-ingestion/src/main.py`

**Changes Required:**

### Change 1: Initialize attribute to None (line ~64)
```python
# Current (commented out):
# self.weather_enrichment: Optional[WeatherEnrichmentService] = None

# Fix: Uncomment and set to None
self.weather_enrichment: Optional[WeatherEnrichmentService] = None
```

### Change 2: Remove usage in event processing (lines 360-368)
```python
# Current (REMOVE THIS):
if self.weather_enrichment:
    processed_event = await self.weather_enrichment.enrich_event(processed_event)
    log_with_context(
        logger, "DEBUG", "Event enriched with weather data",
        operation="weather_enrichment",
        correlation_id=corr_id,
        event_type=event_type,
        entity_id=entity_id
    )

# Fix: Remove entire block or replace with:
# Weather enrichment removed in Epic 31 - use weather-api service (Port 8009)
# Enrichment happens downstream if needed
```

**Estimated Time:** 5 minutes  
**Risk:** Very low (removing dead code)  
**Testing:** Deploy and check if events process

---

## Fix #2: Webhook Detector InfluxDB Connection (MEDIUM)

**Investigation Required:**
1. Find where webhook detector is initialized
2. Check InfluxDB client initialization sequence
3. Ensure client is available before detector starts
4. Add proper error handling

**File:** Likely `services/data-api/src/ha_automation_endpoints.py`

**Estimated Time:** 15 minutes  
**Risk:** Low  
**Testing:** Check if webhook errors stop

---

## Fix #3: Setup Service Integration Issues (LOW - Optional)

**Investigation Required:**
1. Check what admin-api integration is failing
2. Review setup-service health checks
3. May be related to Fix #1 or #2

**Estimated Time:** 10 minutes  
**Priority:** Low (service is functional)

=============================================================================
EXECUTION SEQUENCE
=============================================================================

### Phase 1: Critical Fix (Immediate)
1. ✅ Analyze websocket-ingestion code
2. Fix weather_enrichment attribute issue
3. Rebuild websocket-ingestion service
4. Restart service
5. Monitor logs for event processing
6. Verify events flow to InfluxDB

### Phase 2: Medium Priority Fix
7. Investigate webhook detector issue
8. Fix InfluxDB client connection
9. Test webhook functionality

### Phase 3: Validation
10. Run full health check
11. Verify all services healthy
12. Confirm events processing end-to-end
13. Test Epic 32 refactored UI with live data

### Phase 4: Documentation
14. Update fix documentation
15. Commit fixes to Git
16. Create completion report

=============================================================================
SUCCESS CRITERIA
=============================================================================

- ✅ websocket-ingestion: No AttributeError
- ✅ Events processing: >0 events per minute
- ✅ InfluxDB: Receiving writes
- ✅ Dashboard: Showing live events
- ✅ All services: 100% healthy
- ✅ Epic 32 components: Working with live data

=============================================================================

**Status:** READY TO EXECUTE  
**Next Step:** Fix websocket-ingestion main.py

