# Air Quality Service

Fetches real-time Air Quality Index (AQI) data from AirNow API for health-based automation.

## Purpose

Enable Home Assistant automations to respond to air quality changes - close windows when AQI is poor, adjust HVAC filtration, send health alerts.

## Features

- Fetches AQI every hour from AirNow
- Tracks PM2.5, PM10, Ozone levels
- Logs AQI category changes
- Caches data with 1-hour TTL
- Graceful fallback to cached data
- Health check + current AQI API endpoints

## Environment Variables

Required:
- `AIRNOW_API_KEY` - AirNow API key (free from https://docs.airnowapi.org/)
- `INFLUXDB_TOKEN` - InfluxDB token

Optional:
- `LATITUDE` - Location latitude (default: "36.1699")
- `LONGITUDE` - Location longitude (default: "-115.1398")
- `SERVICE_PORT` - Port (default: "8012")

## Setup

Get free API key from https://docs.airnowapi.org/

Add to `.env`:
```bash
AIRNOW_API_KEY=your_api_key_here
LATITUDE=36.1699
LONGITUDE=-115.1398
```

## InfluxDB Schema

```
Measurement: air_quality
Tags:
  location: "36.1699,-115.1398"
  category: "Good" | "Moderate" | "Unhealthy"
  parameter: "PM2.5" | "PM10" | "Ozone"
Fields:
  aqi: integer (0-500)
  pm25: integer
  pm10: integer
  ozone: integer
```

## Automation Examples

```yaml
automation:
  - alias: "Close Windows When AQI Poor"
    trigger:
      - platform: numeric_state
        entity_id: sensor.aqi
        above: 100
    action:
      - service: cover.close_cover
        entity_id: cover.all_windows
      - service: notify.mobile_app
        data:
          message: "Poor air quality - windows closed (AQI: {{ states('sensor.aqi') }})"
```

## License

MIT License

