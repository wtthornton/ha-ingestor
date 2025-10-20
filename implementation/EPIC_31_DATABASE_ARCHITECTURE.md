# Epic 31: Database Architecture - BEFORE vs AFTER

## DATABASE STRATEGY COMPARISON

### BEFORE Epic 31 (Event Enrichment)

**Architecture:**
```
Weather API → websocket-ingestion → Enrich Event → InfluxDB
                                         ↓
                          event.weather = {temp, humidity, ...}
                                         ↓
                            home_assistant_events bucket
                            home_assistant_events measurement
```

**InfluxDB Schema:**
```sql
Bucket: home_assistant_events
Measurement: home_assistant_events

Point {
  tags: {
    entity_id: "sensor.bedroom_temp"
    domain: "sensor"
    weather_condition: "Clear"  ← Weather tag
  }
  fields: {
    state: "72"
    weather_temp: 21.5  ← Weather field
    weather_humidity: 45  ← Weather field
    weather_pressure: 1013  ← Weather field
    wind_speed: 1.54  ← Weather field
  }
  timestamp: 2025-10-20T03:00:00Z
}
```

**Issues:**
- ❌ Weather data MIXED with Home Assistant events
- ❌ Sparse fields (most events don't have weather)
- ❌ Tight coupling (weather API blocks event processing)
- ❌ Can't query weather independently
- ❌ InfluxDB anti-pattern (mixing unrelated data)

---

### AFTER Epic 31 (Standalone API)

**Architecture:**
```
Home Assistant Events:
  websocket-ingestion → InfluxDB (home_assistant_events bucket)
                          NO weather data

Weather Data:
  weather-api service → InfluxDB (weather_data bucket)
       ↓
  Fetch every 15 min → Cache → Store
```

**InfluxDB Schema (NEW):**
```sql
Bucket: weather_data (SEPARATE)
Measurement: weather

Point {
  tags: {
    location: "Las Vegas"
    condition: "Clear"
  }
  fields: {
    temperature: 21.56
    humidity: 26
    pressure: 1014
    wind_speed: 1.54
    cloudiness: 0
  }
  timestamp: 2025-10-20T03:34:23Z
}
```

**Benefits:**
- ✅ Weather data SEPARATE from events (clean)
- ✅ No sparse fields (every weather point is complete)
- ✅ Decoupled (weather API doesn't block events)
- ✅ Can query weather independently
- ✅ InfluxDB best practice (separate data sources)

---

## CURRENT DATABASE STATE

### Home Assistant Events Bucket

**Bucket:** `home_assistant_events`  
**Measurement:** `home_assistant_events`  
**Status:** ✅ Working

**Contains:**
- All Home Assistant events (state changes, calls, etc.)
- **Historical:** Old events MAY have weather fields (before Epic 31)
- **Current:** New events do NOT have weather fields (after Epic 31)

**Backward Compatibility:**
```sql
-- Old queries still work (for historical data)
SELECT * FROM home_assistant_events
WHERE weather_condition = 'Rain'
AND time < '2025-10-20'  -- Before Epic 31

-- Returns: Historical events with embedded weather ✅
```

### Weather Data Bucket

**Bucket:** `weather_data`  
**Measurement:** `weather`  
**Status:** ⚠️ **BUCKET DOESN'T EXIST YET**

**Should Contain:**
- Standalone weather measurements
- Fetched every 15 minutes by weather-api
- Independent of Home Assistant events

**Current Issue:**
```
Error writing to InfluxDB: (404)
Message: bucket "weather_data" not found
```

**Solution:** Create the bucket or use existing bucket temporarily

---

## WEATHER DATA FLOW NOW

### Step-by-Step

**1. Background Loop (every 15 min):**
```
weather-api service runs continuous fetch loop
```

**2. Fetch from OpenWeatherMap:**
```
GET https://api.openweathermap.org/data/2.5/weather?q=Las Vegas
Response: {temp: 21.56, humidity: 26, condition: "Clear", ...}
```

**3. Cache (15-min TTL):**
```python
cached_weather = {
  'temperature': 21.56,
  'humidity': 26,
  'condition': 'Clear',
  ...
}
cache_time = datetime.utcnow()
```

**4. Store in InfluxDB:**
```python
point = Point("weather") \
    .tag("location", "Las Vegas") \
    .tag("condition", "Clear") \
    .field("temperature", 21.56) \
    .field("humidity", 26)

influxdb_client.write(point)  # → weather_data bucket
```

**5. Serve via API:**
```
GET http://localhost:8009/current-weather
→ Returns cached data (fast!)
```

**6. Dashboard Displays:**
```tsx
useEffect(() => {
  fetch('http://localhost:8009/current-weather')
    .then(data => setWeather(data))
}, [])

// Shows: 21.6°C - Clear
```

---

## BUCKET STATUS

### Existing Buckets (Working)
- ✅ `home_assistant_events` (365 days retention)
- ✅ `sports_data` (90 days retention)
- ✅ `system_metrics` (30 days retention)

### Missing Bucket (Needs Creation)
- ⚠️ `weather_data` (should have 180 days retention)

**Impact:**
- Weather API fetches correctly ✅
- Weather API caches correctly ✅
- Weather API serves data correctly ✅
- InfluxDB writes fail (404 bucket not found) ⚠️

**Workaround:**
- Service is fully functional for dashboard
- Historical storage not critical for MVP
- Can create bucket when needed

---

## QUERY PATTERNS

### Query Weather Independently (NEW)
```sql
-- Get current weather from weather_data bucket
SELECT * FROM weather
WHERE location = 'Las Vegas'
ORDER BY time DESC
LIMIT 1

-- Weather trends over time
SELECT mean(temperature), condition
FROM weather
WHERE time > now() - 7d
GROUP BY time(1h), condition
```

### Query Events with Weather Correlation (NEW)
```sql
-- Time-window JOIN for correlation
SELECT e.entity_id, e.state, w.temperature, w.condition
FROM home_assistant_events e
LEFT JOIN weather w
  ON time_window(e.time, 5m) = time_window(w.time, 5m)
WHERE e.domain = 'climate'
AND time > now() - 24h
```

### Query Historical Events (OLD - Still Works)
```sql
-- Historical events with embedded weather
SELECT * FROM home_assistant_events
WHERE weather_condition IS NOT NULL
AND time < '2025-10-20'
```

---

## SUMMARY

**Where Weather Goes Now:**
- **Bucket:** `weather_data` (separate from events)
- **Measurement:** `weather`
- **Tags:** location, condition
- **Fields:** temperature, humidity, pressure, wind_speed, cloudiness
- **Frequency:** Every 15 minutes

**Current Status:**
- ✅ Weather fetching: Working
- ✅ Weather caching: Working
- ✅ Weather API: Working
- ⚠️ InfluxDB storage: Bucket needs creation

**Action Required:**
- Create `weather_data` bucket in InfluxDB
- OR use existing bucket temporarily

**Impact:**
- Service is functional for dashboard (cache works)
- Historical storage will work once bucket created
- No critical issue (cache serves API requests)

