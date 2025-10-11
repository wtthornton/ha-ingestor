# Electricity Pricing Service

Fetches real-time electricity pricing and forecasts from utility APIs for cost-aware automation.

## Purpose

Enable Home Assistant automations to schedule high-energy tasks (EV charging, pool pumps, water heaters) during cheapest electricity hours, reducing energy costs by 20-40%.

## Features

- Fetches electricity pricing every hour
- 24-hour price forecasts
- Identifies cheapest and most expensive hours
- Caches data with 1-hour TTL
- Graceful fallback to cached data
- Stores current price and forecasts in InfluxDB
- Health check and utility API endpoints
- Multi-provider support (Awattar, more to come)

## Supported Providers

### Awattar (Default)
- **Region:** Germany, Austria
- **API:** https://api.awattar.de
- **Cost:** Free
- **Update Frequency:** Hourly
- **Currency:** EUR

*More providers (Tibber, Octopus Energy) can be added easily*

## Environment Variables

Required:
- `INFLUXDB_TOKEN` - InfluxDB authentication token

Optional:
- `PRICING_PROVIDER` - Provider name (default: "awattar")
- `PRICING_API_KEY` - API key (if provider requires it)
- `INFLUXDB_URL` - InfluxDB URL (default: "http://influxdb:8086")
- `INFLUXDB_ORG` - InfluxDB organization (default: "home_assistant")
- `INFLUXDB_BUCKET` - InfluxDB bucket (default: "events")
- `SERVICE_PORT` - Service port (default: "8011")

## Setup

Add to `.env`:
```bash
PRICING_PROVIDER=awattar
```

## InfluxDB Schema

### Measurement: electricity_pricing

**Tags:**
- `provider` - Provider name (e.g., "awattar")
- `currency` - Currency code (e.g., "EUR", "USD")

**Fields:**
- `current_price` (float) - Current price per kWh
- `peak_period` (boolean) - True if in peak pricing period

### Measurement: electricity_pricing_forecast

**Tags:**
- `provider` - Provider name

**Fields:**
- `price` (float) - Forecast price per kWh
- `hour_offset` (integer) - Hours from now (0-23)

## API Endpoints

### Get Cheapest Hours

```bash
curl http://localhost:8011/cheapest-hours?hours=4

# Response:
{
  "cheapest_hours": [2, 3, 4, 5],
  "provider": "awattar",
  "timestamp": "2025-10-10T16:00:00"
}
```

### Health Check

```bash
curl http://localhost:8011/health
```

## Query Examples

### Get Current Electricity Price

```flux
from(bucket: "events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "electricity_pricing")
  |> filter(fn: (r) => r._field == "current_price")
  |> last()
```

### Find Cheapest 4-Hour Window

```flux
from(bucket: "events")
  |> range(start: -1h, stop: now())
  |> filter(fn: (r) => r._measurement == "electricity_pricing_forecast")
  |> filter(fn: (r) => r._field == "price")
  |> sort(columns: ["_value"])
  |> limit(n: 4)
```

## Automation Examples

### Home Assistant - Charge EV During Cheap Hours

```yaml
automation:
  - alias: "Charge EV During Cheap Electricity"
    trigger:
      - platform: time_pattern
        hours: "*"
    condition:
      - condition: template
        value_template: >
          {{ now().hour in [2, 3, 4, 5] }}
      - condition: numeric_state
        entity_id: sensor.ev_battery_level
        below: 90
    action:
      - service: switch.turn_on
        entity_id: switch.ev_charger
```

## Troubleshooting

### View Service Logs

```bash
docker-compose logs electricity-pricing
```

### Test API Manually

```bash
# Awattar
curl https://api.awattar.de/v1/marketdata
```

## License

MIT License

