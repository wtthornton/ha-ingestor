# Epic 31: Database Architecture Review

## Where Weather Data Goes Now

### BEFORE (Event Enrichment Pattern)

**Bucket:** `home_assistant_events`  
**Measurement:** `home_assistant_events`

**Schema:**
```
home_assistant_events {
  tags: {
    entity_id: "sensor.bedroom_temp"
    domain: "sensor"
    weather_condition: "Clear"  ← Weather embedded as tag
  }
  fields: {
    state: "72"
    weather_temp: 21.5  ← Weather embedded as field
    weather_humidity: 45  ← Weather embedded as field
    weather_pressure: 1013  ← Weather embedded as field
  }
}
```

**Issue:** Weather data MIXED with Home Assistant event data (sparse fields, coupling)

---

### AFTER (Standalone API Pattern)

**Bucket:** `weather_data` (separate bucket)  
**Measurement:** `weather`

**Schema:**
```
weather {
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
}
```

**Benefits:**
- ✅ Clean separation (weather not mixed with events)
- ✅ No sparse fields (weather always complete)
- ✅ Independent retention (180 days vs 365 days for events)
- ✅ Better InfluxDB best practices

---

## CURRENT STATUS

### ✅ Service is Writing

**Code:**
```python
# services/weather-api/src/main.py line 177-187
point = Point("weather") \
    .tag("location", weather['location']) \
    .tag("condition", weather['condition']) \
    .field("temperature", float(weather['temperature'])) \
    .field("humidity", int(weather['humidity'])) \
    .field("pressure", int(weather['pressure'])) \
    .field("wind_speed", float(weather['wind_speed'])) \
    .field("cloudiness", int(weather['cloudiness'])) \
    .time(datetime.fromisoformat(weather['timestamp']))

self.influxdb_client.write(point)
```

**Configuration:**
```yaml
# docker-compose.yml
INFLUXDB_BUCKET=weather_data
```

### ⚠️ Bucket Missing

**Error from logs:**
```
Error writing to InfluxDB: (404)
HTTP response body: {"code":"not found","message":"bucket \"weather_data\" not found"}
```

**Issue:** `weather_data` bucket doesn't exist in InfluxDB yet

---

## SOLUTION OPTIONS

### Option 1: Create weather_data Bucket (Recommended)

**Command:**
```bash
docker exec homeiq-influxdb influx bucket create \
  --name weather_data \
  --org <correct_org_name> \
  --retention 180d \
  --token <correct_token>
```

**Issue:** Need correct org name and token (current attempt failed with 401)

### Option 2: Use Existing Bucket Temporarily

**Change:** Write to `home_assistant_events` bucket initially

**Pro:** Works immediately
**Con:** Not clean separation

### Option 3: Auto-Create Bucket

**Add to weather-api startup:**
```python
# Create bucket if doesn't exist
try:
    bucket_api.create_bucket(bucket_name="weather_data", retention=180*24*3600)
except BucketAlreadyExists:
    pass
```

---

## RECOMMENDATION

**Use Option 1:** Create separate `weather_data` bucket

**Why:**
- ✅ Clean separation (weather not in events)
- ✅ Independent retention (180 days)
- ✅ Better InfluxDB best practices
- ✅ Follows architecture design

**Current Workaround:**
- Weather API is fetching and caching correctly ✅
- Only InfluxDB writes are failing (404)
- Service still usable for dashboard queries
- Can create bucket when we have correct InfluxDB credentials

---

## DATABASE COMPARISON

| Aspect | BEFORE | AFTER |
|--------|--------|-------|
| **Bucket** | home_assistant_events | weather_data (separate) |
| **Measurement** | home_assistant_events | weather |
| **Location** | Mixed with HA events | Standalone |
| **Retention** | 365 days | 180 days |
| **Schema** | Sparse weather fields | Complete weather records |
| **Coupling** | Tightly coupled | Decoupled |
| **Query** | SELECT * WHERE weather_condition | SELECT * FROM weather |

---

## IMPACT ON QUERIES

### OLD Queries (Still Work for Historical)
```sql
-- Old events with embedded weather
SELECT * FROM home_assistant_events
WHERE weather_condition = 'Rain'
AND time > now() - 30d
```

### NEW Queries (For Current Data)
```sql
-- Query weather_data bucket
SELECT * FROM weather
WHERE condition = 'Rain'
AND time > now() - 7d

-- JOIN with events (time-window correlation)
SELECT e.*, w.temperature, w.condition
FROM home_assistant_events e
LEFT JOIN weather w
  ON time_window(e.time, 5m) = time_window(w.time, 5m)
```

---

## SUMMARY

**Where Weather Goes Now:**
- ✅ **Separate `weather_data` bucket**
- ✅ **Measurement:** `weather`
- ✅ **Tags:** location, condition
- ✅ **Fields:** temperature, humidity, pressure, wind_speed, cloudiness

**Current Status:**
- ✅ Service fetching weather correctly
- ✅ Service caching correctly
- ⚠️ Bucket needs to be created (404 error)
- ✅ Can create bucket with correct InfluxDB credentials

**Action Needed:**
Create `weather_data` bucket in InfluxDB or use existing bucket temporarily

