# Database Schema

### InfluxDB Schema Design

**Database:** `home_assistant`
**Organization:** `home_assistant`
**Bucket:** `events`
**Retention Policy:** 1 year (365 days)

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

#### Fields (measurements and values):
- `state_value` - Current state value (string)
- `previous_state` - Previous state value (string)
- `normalized_value` - Standardized numeric value (float)
- `confidence` - Sensor confidence level if applicable (float)
- `duration_seconds` - Time in current state (integer)
- `energy_consumption` - Energy usage in kWh if applicable (float)
- `weather_temp` - Current temperature in Celsius (float)
- `weather_humidity` - Current humidity percentage (float)
- `weather_pressure` - Current atmospheric pressure in hPa (float)
- `unit_of_measurement` - Unit of measurement (string)

### Schema Examples

#### Temperature Sensor Event:
```
Measurement: home_assistant_events
Tags:
  entity_id: sensor.living_room_temperature
  domain: sensor
  device_class: temperature
  area: living_room
  weather_condition: clear
  time_of_day: evening
Fields:
  state_value: "22.5"
  normalized_value: 22.5
  weather_temp: 18.2
  weather_humidity: 65.0
  weather_pressure: 1013.25
  unit_of_measurement: "°C"
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
  energy_consumption: 0.05
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

### Retention Policies

#### Raw Data:
- **Policy Name:** `raw_data_policy`
- **Duration:** 365 days (1 year)
- **Replication:** 1 (single instance)
- **Shard Duration:** 7 days

#### Hourly Summaries:
- **Policy Name:** `hourly_summary_policy`
- **Duration:** 730 days (2 years)
- **Replication:** 1
- **Shard Duration:** 30 days

#### Daily Summaries:
- **Policy Name:** `daily_summary_policy`
- **Duration:** 1825 days (5 years)
- **Replication:** 1
- **Shard Duration:** 90 days
