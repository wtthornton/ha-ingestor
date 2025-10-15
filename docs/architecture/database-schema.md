# Database Schema

## Hybrid Database Architecture (Epic 22)

This system uses a **hybrid database architecture** optimizing for different data types:

- **InfluxDB 2.7**: Time-series data (events, metrics, sports scores)
- **SQLite 3.45+**: Metadata and relational data (devices, entities, webhooks)

---

## InfluxDB Schema Design

**Database:** `home_assistant`
**Organization:** `home_assistant`
**Primary Bucket:** `home_assistant_events` (365 days retention)
**Additional Buckets:** 
- `sports_data` (90 days retention)
- `weather_data` (180 days retention) 
- `system_metrics` (30 days retention)

**Status:** ✅ Schema validated and deployed (January 2025)

### Primary Measurement: `home_assistant_events`

**Purpose:** Store all Home Assistant events with enrichment data for time-series analysis

#### Tags (for filtering and grouping):
- `entity_id` - Home Assistant entity identifier (e.g., "sensor.living_room_temperature")
- `domain` - Entity domain (sensor, switch, light, binary_sensor, etc.)
- `device_class` - Device classification (temperature, motion, humidity, etc.)
- `area` - Room/area location (living_room, bedroom, kitchen, etc.)
- `device_name` - Friendly device name
- `integration` - HA integration source (zwave, mqtt, zigbee, etc.)
- `weather_condition` - Current weather condition (clear, cloudy, rain, etc.)
- `time_of_day` - Time period (morning, afternoon, evening, night)
- **[Epic 23.2]** `device_id` - Physical device identifier for device-level aggregation ✅
- **[Epic 23.2]** `area_id` - Room/area ID for spatial analytics ✅
- **[Epic 23.4]** `entity_category` - Entity classification (null, diagnostic, config) ✅

#### Fields (measurements and values):
- `state_value` - Current state value (string)
- `previous_state` - Previous state value (string)
- `normalized_value` - Standardized numeric value (float)
- `confidence` - Sensor confidence level if applicable (float)
- `duration_seconds` - Time in current state (integer)
- `weather_temp` - Current temperature in Celsius (float)
- `weather_humidity` - Current humidity percentage (float)
- `weather_pressure` - Current atmospheric pressure in hPa (float)
- `unit_of_measurement` - Unit of measurement (string)
- **[Epic 23.1]** `context_id` - Event context identifier for correlation (string) ✅
- **[Epic 23.1]** `context_parent_id` - Parent automation context for causality tracking (string) ✅
- **[Epic 23.1]** `context_user_id` - User who triggered the event (string) ✅
- **[Epic 23.3]** `duration_in_state_seconds` - Time entity was in previous state (float) ✅
- **[Epic 23.5]** `manufacturer` - Device manufacturer for reliability analysis (string) ✅
- **[Epic 23.5]** `model` - Device model for reliability analysis (string) ✅
- **[Epic 23.5]** `sw_version` - Device firmware version for version correlation (string) ✅

### Schema Examples

#### Temperature Sensor Event:
```
Measurement: home_assistant_events
Tags:
  entity_id: sensor.living_room_temperature
  domain: sensor
  device_class: temperature
  area: living_room
  device_id: aeotec_multisensor_6        ← Epic 23.2
  area_id: living_room                   ← Epic 23.2
  weather_condition: clear
  time_of_day: evening
Fields:
  state_value: "22.5"
  normalized_value: 22.5
  weather_temp: 18.2
  weather_humidity: 65.0
  weather_pressure: 1013.25
  unit_of_measurement: "°C"
  context_id: "abc123"                   ← Epic 23.1
  context_parent_id: "automation_xyz"    ← Epic 23.1
  duration_in_state_seconds: 123.45      ← Epic 23.3
  manufacturer: "Aeotec"                 ← Epic 23.5
  model: "ZW100 MultiSensor 6"           ← Epic 23.5
  sw_version: "1.10"                     ← Epic 23.5
Timestamp: 2024-12-19T15:30:00Z
```

#### Switch Event:
```
Measurement: home_assistant_events
Tags:
  entity_id: switch.living_room_lamp
  domain: switch
  device_class: switch
  area: living_room
  weather_condition: cloudy
  time_of_day: evening
Fields:
  state_value: "on"
  previous_state: "off"
  normalized_value: 1.0
Timestamp: 2024-12-19T15:30:00Z
```

### Continuous Queries (Downsampling)

#### Hourly Summaries:
```sql
CREATE CONTINUOUS QUERY "hourly_summaries" ON "home_assistant"
BEGIN
  SELECT 
    mean("normalized_value") as avg_value,
    min("normalized_value") as min_value,
    max("normalized_value") as max_value,
    count("state_value") as event_count
  INTO "home_assistant"."autogen"."hourly_events"
  FROM "home_assistant"."autogen"."home_assistant_events"
  GROUP BY time(1h), "entity_id", "domain", "device_class"
END
```

#### Daily Summaries:
```sql
CREATE CONTINUOUS QUERY "daily_summaries" ON "home_assistant"
BEGIN
  SELECT 
    mean("normalized_value") as avg_value,
    min("normalized_value") as min_value,
    max("normalized_value") as max_value,
    count("state_value") as event_count,
    sum("energy_consumption") as total_energy
  INTO "home_assistant"."autogen"."daily_events"
  FROM "home_assistant"."autogen"."home_assistant_events"
  GROUP BY time(1d), "entity_id", "domain", "device_class"
END
```

### Retention Policies (Current Configuration)

#### Primary Bucket: `home_assistant_events`
- **Retention:** 365 days (1 year) ✅
- **Purpose:** Home Assistant event data with Epic 23 enhancements

#### Sports Data Bucket: `sports_data`
- **Retention:** 90 days ✅
- **Purpose:** Sports scores and game data

#### Weather Data Bucket: `weather_data`
- **Retention:** 180 days ✅
- **Purpose:** Weather enrichment data

#### System Metrics Bucket: `system_metrics`
- **Retention:** 30 days ✅
- **Purpose:** System performance and health metrics

**Note:** All buckets are configured and validated as of January 2025

---

## SQLite Schema Design (Epic 22 + October 2025 Enhancement)

**Database Files:**
- `data/metadata.db` (data-api service) - Devices and entities
- `data/webhooks.db` (sports-data service) - Webhook subscriptions

**Data Population** (Updated October 2025):
- **Devices & Entities**: Direct from Home Assistant WebSocket discovery
- **Method**: POST to `/internal/devices/bulk_upsert` (automated on connection)
- **Frequency**: On WebSocket connect/reconnect
- **Current Data**: 99 real devices, 100+ real entities ✅

**Configuration:**
- **WAL Mode**: Enabled for concurrent reads/writes
- **Synchronous**: NORMAL (fast, safe)
- **Cache Size**: 64MB
- **Foreign Keys**: Enabled

### Devices Table (data-api)

**Purpose:** Store Home Assistant device metadata for fast lookups and relational queries

**Schema:**
```sql
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    manufacturer TEXT,
    model TEXT,
    sw_version TEXT,
    area_id TEXT,
    integration TEXT,
    last_seen TIMESTAMP,
    created_at TIMESTAMP
);

CREATE INDEX idx_device_area ON devices(area_id);
CREATE INDEX idx_device_integration ON devices(integration);
CREATE INDEX idx_device_manufacturer ON devices(manufacturer);
```

**Fields:**
- `device_id`: Unique device identifier (primary key)
- `name`: Friendly device name
- `manufacturer`: Device manufacturer (e.g., "Philips", "Sonoff")
- `model`: Device model number
- `sw_version`: Software/firmware version
- `area_id`: Room/area location (e.g., "living_room", "bedroom")
- `integration`: HA integration source (e.g., "zwave", "mqtt", "zigbee")
- `last_seen`: Last time device was active
- `created_at`: First discovery timestamp

**Example Row:**
```json
{
  "device_id": "abc123def456",
  "name": "Living Room Light",
  "manufacturer": "Philips",
  "model": "Hue White A19",
  "sw_version": "1.88.1",
  "area_id": "living_room",
  "integration": "hue",
  "last_seen": "2025-01-14T12:30:00Z",
  "created_at": "2024-06-15T10:00:00Z"
}
```

### Entities Table (data-api)

**Purpose:** Store Home Assistant entity metadata with foreign key relationship to devices

**Schema:**
```sql
CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    device_id TEXT REFERENCES devices(device_id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    platform TEXT,
    unique_id TEXT,
    area_id TEXT,
    disabled BOOLEAN DEFAULT 0,
    created_at TIMESTAMP
);

CREATE INDEX idx_entity_device ON entities(device_id);
CREATE INDEX idx_entity_domain ON entities(domain);
CREATE INDEX idx_entity_area ON entities(area_id);
```

**Fields:**
- `entity_id`: Unique entity identifier (e.g., "light.living_room_lamp")
- `device_id`: Foreign key to devices table (CASCADE delete)
- `domain`: Entity domain (e.g., "light", "sensor", "switch")
- `platform`: Integration platform
- `unique_id`: Unique ID within platform
- `area_id`: Room/area location
- `disabled`: Whether entity is disabled
- `created_at`: First discovery timestamp

**Example Row:**
```json
{
  "entity_id": "light.living_room_lamp",
  "device_id": "abc123def456",
  "domain": "light",
  "platform": "hue",
  "unique_id": "00:17:88:01:02:34:56:78-0b",
  "area_id": "living_room",
  "disabled": false,
  "created_at": "2024-06-15T10:00:00Z"
}
```

**Foreign Key Relationship:**
```
devices (1) ----< entities (N)
  └─ device_id ──> device_id
```

### Webhooks Table (sports-data)

**Purpose:** Store webhook subscriptions for game event notifications

**Schema:**
```sql
CREATE TABLE webhooks (
    webhook_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    events TEXT NOT NULL,
    secret TEXT NOT NULL,
    team TEXT,
    created_at TIMESTAMP,
    total_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    last_success TEXT,
    last_failure TEXT,
    enabled BOOLEAN DEFAULT 1
);

CREATE INDEX idx_webhooks_team ON webhooks(team);
```

**Fields:**
- `webhook_id`: Unique webhook identifier (UUID)
- `url`: Webhook delivery URL
- `events`: JSON array of subscribed events (e.g., '["game_started", "score_changed"]')
- `secret`: HMAC secret for signature verification
- `team`: Optional team filter (e.g., "sf", "dal")
- `created_at`: Registration timestamp
- `total_calls`: Successful delivery count
- `failed_calls`: Failed delivery count
- `last_success`: Last successful delivery timestamp (ISO string)
- `last_failure`: Last failed delivery timestamp (ISO string)
- `enabled`: Whether webhook is active

**Example Row:**
```json
{
  "webhook_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com/webhook/sports",
  "events": "[\"game_started\", \"score_changed\", \"game_ended\"]",
  "secret": "secret_key_at_least_16_chars",
  "team": "sf",
  "created_at": "2025-01-14T10:00:00Z",
  "total_calls": 45,
  "failed_calls": 2,
  "last_success": "2025-01-14T12:30:00Z",
  "last_failure": "2025-01-13T15:20:00Z",
  "enabled": true
}
```

---

## Query Performance Comparison

| Operation | InfluxDB (Before) | SQLite (After) | Improvement |
|-----------|-------------------|----------------|-------------|
| Get device by ID | ~50ms | <10ms | **5x faster** |
| List devices with filter | ~100ms | <15ms | **6-7x faster** |
| List entities by domain | ~40ms | <5ms | **8x faster** |
| Device with entity count (JOIN) | ~120ms (2 queries) | <10ms (1 query) | **12x faster** |

---

## Backup Strategy

### InfluxDB Backups
- Automated backups via InfluxDB CLI
- Backup retention: 30 days
- Location: `./backups/influxdb/`

### SQLite Backups
- Simple file copy (database files are self-contained)
- Backup command: `cp data/*.db backups/sqlite/`
- Can backup while database is running (WAL mode safe)
- Location: `./backups/sqlite/`

**Backup Script:**
```bash
# Backup both databases
mkdir -p backups/influxdb backups/sqlite
influx backup backups/influxdb/
cp services/data-api/data/metadata.db backups/sqlite/
cp services/sports-data/data/webhooks.db backups/sqlite/
```

