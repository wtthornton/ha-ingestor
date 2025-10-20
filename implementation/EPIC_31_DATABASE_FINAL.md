# Epic 31: Database Architecture - FINAL

## WHERE WEATHER DATA GOES NOW ✅

### BEFORE (Event Enrichment) ❌

**Bucket:** `home_assistant_events`  
**Measurement:** `home_assistant_events`  
**Problem:** Weather MIXED with events (coupling, sparse fields)

```sql
home_assistant_events measurement {
  entity_id: "sensor.temp"        ← Event data
  state: "72"                      ← Event data
  weather_temp: 21.5               ← Weather data (MIXED!)
  weather_humidity: 45             ← Weather data (MIXED!)
  weather_condition: "Clear"       ← Weather data (MIXED!)
}
```

**Issues:**
- Weather and events coupled
- Sparse fields (most events have NO weather)
- Can't query weather independently
- Weather API failures block ALL events

---

### AFTER (Standalone Service) ✅

**Bucket:** `weather_data` (SEPARATE)  
**Measurement:** `weather`  
**Solution:** Weather SEPARATE from events (clean, decoupled)

```sql
weather measurement {
  location: "Las Vegas"    ← Weather-specific tag
  condition: "Clear"       ← Weather-specific tag
  temperature: 21.56       ← Weather field
  humidity: 26             ← Weather field
  pressure: 1014           ← Weather field
  wind_speed: 1.54         ← Weather field
}
```

**Benefits:**
- ✅ Weather and events decoupled
- ✅ No sparse fields (every weather point complete)
- ✅ Can query weather independently
- ✅ Weather issues don't affect events
- ✅ Independent retention (180 days vs 365 days)

---

## DATABASE BUCKETS

### InfluxDB Structure

**Organization:** `ha-ingestor`  
**Token:** `ha-ingestor-token`

**Buckets:**
1. **home_assistant_events** (365 days) ✅
   - Home Assistant state changes
   - Device events
   - Service calls
   - NO weather data (after Epic 31)

2. **weather_data** (180 days) ✅ **CREATED**
   - Weather measurements from weather-api
   - Updated every 15 minutes
   - Location: Las Vegas (configurable)

3. **sports_data** (90 days) ✅
   - Sports scores and game data
   - Team-based filtering

4. **system_metrics** (30 days) ✅
   - System health metrics
   - Performance data

---

## QUERY EXAMPLES

### Query Current Weather
```sql
-- Simple weather query (NEW capability!)
SELECT * FROM weather
WHERE location = 'Las Vegas'
ORDER BY time DESC
LIMIT 1

-- Result: {temperature: 21.56, condition: "Clear", ...}
```

### Query Weather History
```sql
-- Weather trends over week
SELECT mean(temperature) as avg_temp, condition
FROM weather
WHERE time > now() - 7d
GROUP BY time(1h), condition
```

### Query Events with Weather Correlation
```sql
-- JOIN events with weather (5-minute time window)
SELECT e.entity_id, e.state, w.temperature, w.condition
FROM home_assistant_events e
LEFT JOIN weather w
  ON time_window(e.time, 5m) = time_window(w.time, 5m)
WHERE e.domain = 'climate'
AND time > now() - 24h
```

### Query Historical Events (Backward Compatible)
```sql
-- Old events with embedded weather (before Epic 31)
SELECT * FROM home_assistant_events
WHERE weather_condition = 'Rain'
AND time < '2025-10-20'  -- Before migration

-- Still works! ✅
```

---

## SUMMARY

### Database Changes

**What Changed:**
- Weather data now goes to **separate `weather_data` bucket**
- Events no longer have weather fields (clean schema)
- Backward compatible (historical data preserved)

**What Stayed Same:**
- Home Assistant events still go to `home_assistant_events`
- Historical queries still work
- No data migration required

**Benefits:**
- ✅ Clean separation of concerns
- ✅ Independent query/retention policies
- ✅ Better InfluxDB best practices
- ✅ No coupling between weather and events

---

**Created:** `weather_data` bucket (180-day retention)  
**Updated:** Event schema (no weather fields in new events)  
**Status:** ✅ **Database architecture clean and optimized**

