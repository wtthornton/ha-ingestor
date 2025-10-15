# Smart Meter Service

Collects real-time power consumption data from smart meters for device-level energy monitoring.

## Purpose

Track whole-home and circuit-level power consumption to identify energy waste, detect phantom loads, and optimize device usage.

## Features

- Fetches consumption every 5 minutes
- Circuit-level breakdown via Home Assistant sensors
- Phantom load detection (3am baseline)
- High consumption alerting (>10kW)
- Adapter pattern for multiple meter types
- Stores in InfluxDB (`smart_meter` and `smart_meter_circuit` measurements)
- Fallback to mock data if no adapter configured

## Environment Variables

Required:
- `INFLUXDB_TOKEN` - InfluxDB token

Home Assistant Integration:
- `METER_TYPE` - Set to `home_assistant` (default)
- `HOME_ASSISTANT_URL` - HA URL (e.g., `http://homeassistant:8123`)
- `HOME_ASSISTANT_TOKEN` - Long-lived access token

Optional:
- `SERVICE_PORT` - Port (default: "8014")
- `INFLUXDB_URL` - InfluxDB URL (default: "http://influxdb:8086")
- `INFLUXDB_ORG` - InfluxDB org (default: "home_assistant")
- `INFLUXDB_BUCKET` - InfluxDB bucket (default: "events")

## Supported Adapters

### ✅ Home Assistant (Implemented)
**Type:** `home_assistant`

Pulls energy data from Home Assistant sensors. Automatically discovers power sensors.

**Expected HA Sensors:**
- Whole-home power: `sensor.total_power`, `sensor.power_total`, `sensor.home_power`, or `sensor.power_consumption` (in Watts)
- Daily energy: `sensor.daily_energy`, `sensor.energy_daily`, or `sensor.energy_today` (in kWh)
- Circuit sensors: Any sensor with:
  - `entity_id` starting with `sensor.power_*`
  - `device_class: power`
  - `unit_of_measurement: W` or `kW`

**Features:**
- Automatic sensor discovery
- Multiple sensor name patterns supported
- Handles unavailable/unknown states gracefully
- Converts kW to W automatically
- Falls back to mock data if connection fails

### 🚧 Future Adapters
- **Emporia Vue** - Hardware energy monitor
- **Sense** - AI-powered energy monitor
- **Shelly EM** - Local MQTT integration
- **IoTaWatt** - Local REST API

## InfluxDB Schema

```
Measurement: smart_meter
Tags:
  meter_type: "generic" | "emporia" | "sense"
Fields:
  total_power_w: float
  daily_kwh: float

Measurement: smart_meter_circuit
Tags:
  circuit_name: string
Fields:
  power_w: float
  percentage: float
```

## License

MIT License

