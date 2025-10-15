# InfluxDB Schema Reset & Validation Plan

## Overview

This document provides a comprehensive plan to reset InfluxDB and ensure the data structure is 100% correct with the new hybrid architecture (InfluxDB + SQLite) implemented in Epic 22.

## Current Issues Identified

### Schema Inconsistencies
1. **Retention Policy Mismatch**: Documentation shows 1 year, initialization script shows 30 days
2. **Missing Epic 23 Fields**: New context tracking, device metadata, and spatial analytics fields not consistently implemented
3. **Tag/Field Structure**: Implementation differs from documented schema
4. **Bucket Organization**: Inconsistent naming between docs and configuration

### Hybrid Architecture Requirements
- **InfluxDB 2.7**: Time-series data (events, metrics, sports scores)
- **SQLite 3.45+**: Metadata and relational data (devices, entities, webhooks)
- **Data Separation**: Clear boundaries between time-series and relational data

## Correct InfluxDB Schema Structure

### Database Configuration
```yaml
Organization: "ha-ingestor"
Buckets:
  - home_assistant_events (365 days retention)
  - sports_data (90 days retention)
  - weather_data (180 days retention)
  - system_metrics (30 days retention)
```

### Primary Measurement: `home_assistant_events`

#### Tags (Indexed for filtering/grouping)
```yaml
Primary Tags:
  entity_id: "sensor.living_room_temperature"
  domain: "sensor|switch|light|binary_sensor|etc"
  device_class: "temperature|motion|humidity|etc"
  area: "living_room|bedroom|kitchen|etc"
  device_name: "Living Room Temperature Sensor"

Epic 23 Enhanced Tags:
  device_id: "physical_device_identifier"        # Epic 23.2
  area_id: "room_area_id"                       # Epic 23.2
  entity_category: "null|diagnostic|config"     # Epic 23.4
  integration: "zwave|mqtt|zigbee|etc"
  weather_condition: "clear|cloudy|rain|etc"
  time_of_day: "morning|afternoon|evening|night"
```

#### Fields (Measurements and values)
```yaml
Core Fields:
  state_value: "current_state_string"
  previous_state: "previous_state_string"
  normalized_value: 22.5                        # float
  unit_of_measurement: "°C|%|hPa|etc"
  confidence: 0.95                              # float (if applicable)

Epic 23 Enhanced Fields:
  context_id: "event_context_identifier"        # Epic 23.1
  context_parent_id: "parent_automation_context" # Epic 23.1
  context_user_id: "user_who_triggered_event"   # Epic 23.1
  duration_seconds: 3600                        # integer (time in current state)
  energy_consumption: 0.5                       # float (kWh if applicable)

Weather Enrichment Fields:
  weather_temp: 22.5                            # float (°C)
  weather_humidity: 45.0                        # float (%)
  weather_pressure: 1013.25                     # float (hPa)

Device Metadata Fields:
  manufacturer: "Z-Wave Alliance"               # Epic 23.5
  model: "ZW100"                                # Epic 23.5
  sw_version: "1.0.0"                           # Epic 23.5
```

## SQLite Schema (Metadata Storage)

### Device Table
```sql
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    manufacturer TEXT,
    model TEXT,
    sw_version TEXT,
    area_id TEXT,
    integration TEXT,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Entity Table
```sql
CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    device_id TEXT REFERENCES devices(device_id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    platform TEXT,
    unique_id TEXT,
    area_id TEXT,
    disabled BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Reset Execution Plan

### Phase 1: Pre-Reset Analysis & Backup

#### 1.1 Current State Assessment
```bash
# Check current InfluxDB status
docker compose exec influxdb influx ping

# List current buckets
docker compose exec influxdb influx bucket list

# Check current data volume
docker compose exec influxdb influx query 'from(bucket:"home_assistant_events") |> range(start: -30d) |> count()'

# Export current schema (if any data exists)
docker compose exec influxdb influx query 'from(bucket:"home_assistant_events") |> range(start: -1d) |> limit(n:1) |> schema.fieldsAsCols()'
```

#### 1.2 Data Backup (if needed)
```bash
# Create backup directory
mkdir -p ./backups/influxdb/$(date +%Y%m%d_%H%M%S)

# Export all data (if you want to preserve any existing data)
docker compose exec influxdb influx query 'from(bucket:"home_assistant_events") |> range(start: -365d)' > ./backups/influxdb/$(date +%Y%m%d_%H%M%S)/full_export.csv
```

### Phase 2: Service Shutdown
```bash
# Stop all services that write to InfluxDB
docker compose stop websocket-ingestion enrichment-pipeline data-api sports-data

# Verify services are stopped
docker compose ps --filter "status=exited"
```

### Phase 3: InfluxDB Reset
```bash
# Remove InfluxDB container and volumes
docker compose down influxdb
docker volume rm ha-ingestor_influxdb_data ha-ingestor_influxdb_config

# Recreate InfluxDB with clean state
docker compose up -d influxdb

# Wait for InfluxDB to be ready
docker compose exec influxdb influx ping
```

### Phase 4: Schema Initialization
```bash
# Run the schema reset script
./scripts/reset-influxdb-schema.sh
```

### Phase 5: Validation
```bash
# Verify buckets were created correctly
docker compose exec influxdb influx bucket list

# Verify retention policies
docker compose exec influxdb influx bucket list --json | jq '.[] | {name: .name, retention: .retentionRules[0].everySeconds}'

# Test data writing
docker compose exec influxdb influx write \
  --bucket "home_assistant_events" \
  --org "ha-ingestor" \
  --token "ha-ingestor-token" \
  --host "http://localhost:8086" \
  --precision ns \
  "home_assistant_events,entity_id=sensor.test_temperature,domain=sensor,device_class=temperature state_value=\"22.5\",normalized_value=22.5 $(date +%s%N)"

# Verify data was written
docker compose exec influxdb influx query \
  --org "ha-ingestor" \
  --token "ha-ingestor-token" \
  --host "http://localhost:8086" \
  "from(bucket: \"home_assistant_events\") |> range(start: -1h) |> limit(n:1)"
```

### Phase 6: Service Restart
```bash
# Start services in correct order
docker compose up -d influxdb
sleep 10  # Wait for InfluxDB to be fully ready

docker compose up -d websocket-ingestion enrichment-pipeline data-api sports-data

# Verify all services are healthy
docker compose ps --filter "health=healthy"
```

## Validation Checklist

### ✅ InfluxDB Configuration
- [ ] Organization `ha-ingestor` exists
- [ ] Bucket `home_assistant_events` exists with 365-day retention
- [ ] Bucket `sports_data` exists with 90-day retention
- [ ] Bucket `weather_data` exists with 180-day retention
- [ ] Bucket `system_metrics` exists with 30-day retention
- [ ] Admin token `ha-ingestor-token` works

### ✅ Schema Structure
- [ ] All Epic 23 tags are present in schema
- [ ] All Epic 23 fields are present in schema
- [ ] Weather enrichment fields are present
- [ ] Device metadata fields are present
- [ ] Context tracking fields are present

### ✅ Data Flow
- [ ] WebSocket ingestion can write to InfluxDB
- [ ] Enrichment pipeline can read/write to InfluxDB
- [ ] Data API can query InfluxDB
- [ ] Sports data can write to sports_data bucket
- [ ] Weather data can write to weather_data bucket

### ✅ SQLite Integration
- [ ] Device metadata is stored in SQLite
- [ ] Entity metadata is stored in SQLite
- [ ] Foreign key relationships work
- [ ] WAL mode is enabled
- [ ] Database is accessible from data-api service

## Rollback Plan

If issues occur during reset:

1. **Stop all services**: `docker compose stop`
2. **Restore InfluxDB volumes**: Restore from backup if available
3. **Restart services**: `docker compose up -d`
4. **Verify data integrity**: Check that data is accessible

## Post-Reset Verification

### Data Writing Test
```bash
# Test event writing
curl -X POST http://localhost:8001/health
# Should show healthy status

# Test enrichment pipeline
curl -X GET http://localhost:8002/health
# Should show healthy status

# Test data API
curl -X GET http://localhost:8006/health
# Should show healthy status
```

### Dashboard Verification
```bash
# Access dashboard
open http://localhost:3000

# Verify:
# - InfluxDB shows as healthy
# - Data is being written
# - Events are visible in Events tab
# - Devices are visible in Devices tab
```

## Success Criteria

The reset is successful when:
1. ✅ All InfluxDB buckets exist with correct retention policies
2. ✅ Schema includes all Epic 23 enhancements
3. ✅ Services can write and read from InfluxDB
4. ✅ SQLite metadata storage is working
5. ✅ Dashboard shows healthy status
6. ✅ Data flow from HA → WebSocket → Enrichment → InfluxDB works
7. ✅ API endpoints return data correctly

## Next Steps

After successful reset:
1. Monitor system for 24 hours
2. Verify data retention policies are working
3. Check query performance
4. Update documentation with any schema changes
5. Create monitoring alerts for schema validation
