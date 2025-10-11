# Smart Meter Service

Collects real-time power consumption data from smart meters for device-level energy monitoring.

## Purpose

Track whole-home and circuit-level power consumption to identify energy waste, detect phantom loads, and optimize device usage.

## Features

- Fetches consumption every 5 minutes
- Circuit-level breakdown
- Phantom load detection (3am baseline)
- High consumption alerting (>10kW)
- Adapter pattern for multiple meter types
- Stores in InfluxDB

## Environment Variables

Required:
- `INFLUXDB_TOKEN` - InfluxDB token

Optional:
- `METER_TYPE` - Meter type (default: "generic")
- `METER_API_TOKEN` - Meter API token
- `METER_DEVICE_ID` - Meter device ID
- `SERVICE_PORT` - Port (default: "8014")

## Supported Meters

Currently: Generic (mock data)
Future: Emporia Vue, Sense

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

