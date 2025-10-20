# Epic 31: Cleanup Plan

## Cleanup Required After Weather Migration

### 1. Delete Old Weather Files from websocket-ingestion ❌

**Found:**
- `services/websocket-ingestion/src/weather_cache.py` (8,531 bytes)
- `services/websocket-ingestion/src/weather_client.py` (7,840 bytes)
- `services/websocket-ingestion/src/weather_enrichment.py` (9,377 bytes)

**Action:** DELETE - These are no longer used (migrated to weather-api)

### 2. Remove Weather Fields from InfluxDB Writes ❌

**Found:** `services/enrichment-pipeline/src/influxdb_wrapper.py` still writes:
- weather_condition (tag)
- weather_temp (field)
- weather_humidity (field)
- weather_pressure (field)

**Action:** Remove weather field writes (keep historical data intact)

### 3. Update Documentation ❌

**Found:** `docs/architecture/database-schema.md` says:
- "Weather enrichment is now fully operational"
- Lists weather_condition tag as active

**Action:** Update to reflect new standalone weather-api architecture

### 4. Clean Environment Variables ❌

**Found:** `infrastructure/env.production` has:
- WEATHER_API_KEY (should only be in weather-api now)
- WEATHER_ENRICHMENT_ENABLED=false (keep as documentation)

**Action:** Add comment that WEATHER_API_KEY is for weather-api service only

### 5. Database ✅

**Status:** NO cleanup needed
- Historical events with weather fields: Keep as-is (backward compatible)
- weather_data bucket: Already exists for new weather-api data
- No data migration required

---

## Recommended Cleanup Actions

### HIGH PRIORITY (Do Now)
1. Delete old weather files from websocket-ingestion (26KB dead code)
2. Remove weather field writes from enrichment-pipeline
3. Update database-schema.md documentation

### LOW PRIORITY (Optional)
4. Clean up environment variable comments
5. Archive old weather code to git branch

---

**Cleanup Impact:** Remove ~26KB dead code, prevent writing unused fields

