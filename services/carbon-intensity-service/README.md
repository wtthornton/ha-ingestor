# Carbon Intensity Service

Fetches real-time grid carbon intensity data from WattTime API and stores it in InfluxDB for carbon-aware automation.

## Purpose

Enable Home Assistant automations to schedule energy-intensive tasks during periods of clean energy (low carbon intensity), reducing environmental impact and potentially saving costs during renewable energy peaks.

## Features

- Fetches carbon intensity every 15 minutes
- Caches data with 15-minute TTL
- Graceful fallback to cached data if API unavailable
- Stores data in InfluxDB with forecasts
- Health check endpoint for monitoring
- Automatic retry on failures

## Environment Variables

Required:
- `WATTTIME_API_TOKEN` - WattTime API authentication token
- `INFLUXDB_TOKEN` - InfluxDB authentication token

Optional:
- `GRID_REGION` - Grid region code (default: "CAISO_NORTH")
- `INFLUXDB_URL` - InfluxDB URL (default: "http://influxdb:8086")
- `INFLUXDB_ORG` - InfluxDB organization (default: "home_assistant")
- `INFLUXDB_BUCKET` - InfluxDB bucket (default: "events")
- `SERVICE_PORT` - Health check port (default: "8010")

## Setup

### 1. Get WattTime API Token

```bash
# Register for free account at https://www.watttime.org/api-documentation/
# Free tier: 100 calls/day (sufficient for 15-min intervals = 96 calls/day)

curl -X POST https://api.watttime.org/register \
  -d '{"username":"your_email@example.com","password":"your_password","email":"your_email@example.com","org":"your_org"}'

# Login to get token
curl -X POST https://api.watttime.org/login \
  -d '{"username":"your_email@example.com","password":"your_password"}'
```

### 2. Configure Environment

Add to `.env`:
```bash
WATTTIME_API_TOKEN=your_token_here
GRID_REGION=CAISO_NORTH  # or your region
```

### 3. Run with Docker Compose

Service is included in main `docker-compose.yml`.

## InfluxDB Schema

### Measurement: carbon_intensity

**Tags:**
- `region` - Grid region (e.g., "CAISO_NORTH")
- `grid_operator` - Grid operator abbreviation (e.g., "CAISO")

**Fields:**
- `carbon_intensity_gco2_kwh` (float) - Carbon intensity in gCO2/kWh
- `renewable_percentage` (float) - Percentage of renewable energy
- `fossil_percentage` (float) - Percentage of fossil fuel energy
- `forecast_1h` (float) - Forecast for next hour
- `forecast_24h` (float) - Forecast for 24 hours ahead

## Query Examples

### Get Current Carbon Intensity

```flux
from(bucket: "events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "carbon_intensity")
  |> filter(fn: (r) => r._field == "carbon_intensity_gco2_kwh")
  |> last()
```

### Find Low-Carbon Periods

```flux
from(bucket: "events")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "carbon_intensity")
  |> filter(fn: (r) => r._field == "carbon_intensity_gco2_kwh")
  |> filter(fn: (r) => r._value < 200)
```

### Get Daily Average Renewable Percentage

```flux
from(bucket: "events")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "carbon_intensity")
  |> filter(fn: (r) => r._field == "renewable_percentage")
  |> aggregateWindow(every: 1d, fn: mean)
```

## Automation Examples

### Home Assistant YAML

```yaml
# Create sensor for carbon intensity
sensor:
  - platform: influxdb
    api_version: 2
    host: influxdb
    port: 8086
    token: !secret influxdb_token
    organization: home_assistant
    bucket: events
    queries:
      - name: "Grid Carbon Intensity"
        query: >
          from(bucket: "events")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "carbon_intensity")
            |> filter(fn: (r) => r._field == "carbon_intensity_gco2_kwh")
            |> last()
        value_template: "{{ value }}"
        unit_of_measurement: "gCO2/kWh"

# Automation: Charge EV during clean energy
automation:
  - alias: "Charge EV During Clean Energy"
    trigger:
      - platform: numeric_state
        entity_id: sensor.grid_carbon_intensity
        below: 200
    condition:
      - condition: state
        entity_id: binary_sensor.ev_plugged_in
        state: "on"
      - condition: numeric_state
        entity_id: sensor.ev_battery_level
        below: 90
    action:
      - service: switch.turn_on
        entity_id: switch.ev_charger
      - service: notify.mobile_app
        data:
          message: "EV charging started - grid is clean ({{ states('sensor.grid_carbon_intensity') }} gCO2/kWh)"
```

## Health Check

```bash
curl http://localhost:8010/health

# Response:
{
  "status": "healthy",
  "service": "carbon-intensity-service",
  "uptime_seconds": 3600,
  "last_successful_fetch": "2025-10-10T15:30:00",
  "total_fetches": 96,
  "failed_fetches": 2,
  "success_rate": 0.979,
  "timestamp": "2025-10-10T16:00:00"
}
```

## Troubleshooting

### API Token Issues

```bash
# Test WattTime API manually
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.watttime.org/v3/forecast?region=CAISO_NORTH"
```

### View Service Logs

```bash
docker-compose logs carbon-intensity-service
```

### Verify Data in InfluxDB

```bash
# Access InfluxDB UI
open http://localhost:8086

# Or query via CLI
docker exec -it influxdb influx query \
  'from(bucket:"events") |> range(start:-1h) |> filter(fn: (r) => r._measurement == "carbon_intensity")'
```

## Grid Regions

Common WattTime region codes:
- `CAISO_NORTH` - Northern California
- `CAISO_SOUTH` - Southern California
- `ERCOT` - Texas
- `PJM` - Mid-Atlantic and Midwest
- `MISO` - Midwest
- `NYISO` - New York
- `ISONE` - New England
- `SPP` - Southwest Power Pool

See WattTime API documentation for complete list.

## Development

### Run Tests

```bash
cd services/carbon-intensity-service
pytest tests/ -v
```

### Run Locally

```bash
cd services/carbon-intensity-service
python -m src.main
```

## License

MIT License - See main project LICENSE file

