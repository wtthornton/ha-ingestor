# Device Intelligence Service

**Device Capability Discovery & Smart Recommendations**

Intelligent device analysis service that discovers device capabilities, monitors MQTT for Zigbee2MQTT devices, and provides smart recommendations for automations.

---

## 📊 Overview

**Port:** 8028
**Technology:** Python 3.11, FastAPI, MQTT, Async
**Container:** `homeiq-device-intelligence-service`
**Phase:** Phase 1 AI Containerization (October 2025)

### Purpose

Provide intelligent device analysis for:
- Device capability discovery via MQTT
- Smart automation recommendations
- Device compatibility checking
- Usage pattern analysis

---

## 🎯 Features

### Device Discovery

**MQTT Integration:**
- Listens to Zigbee2MQTT bridge topics
- Real-time device discovery
- Capability extraction from device definitions
- Manufacturer and model identification

**Capability Detection:**
- Light capabilities (brightness, color, temperature)
- Sensor types (temperature, humidity, motion, etc.)
- Switch capabilities
- Climate control features

### Smart Recommendations

**Automation Suggestions:**
- Device pairing recommendations
- Scene creation suggestions
- Optimization opportunities
- Compatibility warnings

**Pattern Analysis:**
- Device usage patterns
- Group similar devices
- Detect unused devices

---

## 🔌 API Endpoints

### Device Management

```bash
GET /devices
# List all discovered devices

Response:
{
  "devices": [
    {
      "id": "0x00158d0001234567",
      "friendly_name": "Living Room Motion",
      "model": "RTCGQ11LM",
      "manufacturer": "Xiaomi",
      "capabilities": ["occupancy", "battery"],
      "discovered_at": "2025-10-25T10:30:00Z"
    }
  ],
  "count": 1
}
```

```bash
GET /devices/{device_id}
# Get specific device details

Response:
{
  "id": "0x00158d0001234567",
  "friendly_name": "Living Room Motion",
  "model": "RTCGQ11LM",
  "manufacturer": "Xiaomi",
  "capabilities": {
    "occupancy": {
      "type": "binary",
      "access": "read"
    },
    "battery": {
      "type": "numeric",
      "unit": "%",
      "access": "read"
    }
  },
  "last_seen": "2025-10-25T14:25:00Z"
}
```

### Recommendations

```bash
POST /analyze
# Analyze devices and get recommendations

{
  "include_devices": ["light.*", "sensor.*"],
  "analysis_type": "automation_opportunities"
}

Response:
{
  "recommendations": [
    {
      "type": "motion_lighting",
      "confidence": 0.92,
      "devices": ["sensor.living_room_motion", "light.living_room"],
      "description": "Create motion-activated lighting for Living Room",
      "automation_yaml": "..."
    }
  ],
  "count": 1
}
```

### Compatibility

```bash
POST /check-compatibility
# Check if devices can work together

{
  "device_ids": ["0x001", "0x002", "0x003"]
}

Response:
{
  "compatible": true,
  "common_capabilities": ["brightness", "on_off"],
  "warnings": [],
  "suggestions": [
    "All devices support brightness control - can be grouped"
  ]
}
```

### Health

```bash
GET /health

Response:
{
  "status": "healthy",
  "mqtt_connected": true,
  "devices_discovered": 42,
  "zigbee2mqtt_version": "1.33.0"
}
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Service Configuration
DEVICE_INTELLIGENCE_PORT=8028
LOG_LEVEL=INFO

# MQTT Configuration
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_USERNAME=homeiq
MQTT_PASSWORD=your-password
MQTT_TOPIC_PREFIX=zigbee2mqtt

# Database
DEVICE_DB_PATH=/app/data/devices.db

# Analysis Settings
RECOMMENDATION_MIN_CONFIDENCE=0.7
CAPABILITY_CACHE_TTL=3600
```

---

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Start service (requires Mosquitto MQTT)
docker-compose up device-intelligence-service

# Check health
curl http://localhost:8028/health
```

### Standalone Docker

```bash
# Build
docker build -t homeiq-device-intelligence \
  -f services/device-intelligence-service/Dockerfile .

# Run
docker run -p 8028:8028 \
  -e MQTT_BROKER_HOST=mosquitto \
  -v device_data:/app/data \
  homeiq-device-intelligence
```

### Local Development

```bash
cd services/device-intelligence-service

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

---

## 📊 Performance

### Response Times
- Device list: <50ms
- Device details: <10ms
- Analyze (10 devices): 200-500ms
- Compatibility check: <100ms

### Resource Usage
- Memory: 128-256MB
- CPU: Low (event-driven)
- Storage: ~10MB (device database)
- Startup: 5-10 seconds

---

## 🏗️ Architecture

### System Design

```
Device Intelligence Service (8028)
├── MQTT Listener
│   ├── Subscribe to zigbee2mqtt/#
│   ├── Parse device messages
│   └── Update device registry
├── Capability Analyzer
│   ├── Extract capabilities
│   ├── Identify features
│   └── Build device profiles
├── Recommendation Engine
│   ├── Pattern matching
│   ├── Rule-based suggestions
│   └── Confidence scoring
└── API Layer
    ├── Device endpoints
    ├── Analysis endpoints
    └── Recommendation endpoints
```

### MQTT Topics

```
Subscribed Topics:
- zigbee2mqtt/bridge/devices    # Device list
- zigbee2mqtt/bridge/info       # Bridge info
- zigbee2mqtt/+                 # All device messages

Published Topics:
- homeiq/device_intelligence/status  # Service status
```

---

## 🧪 Testing

### Manual Testing

```bash
# List devices
curl http://localhost:8028/devices

# Get device details
curl http://localhost:8028/devices/0x001

# Get recommendations
curl -X POST http://localhost:8028/analyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_type": "automation_opportunities"}'

# Check compatibility
curl -X POST http://localhost:8028/check-compatibility \
  -H "Content-Type: application/json" \
  -d '{"device_ids": ["0x001", "0x002"]}'
```

---

## 🔍 Troubleshooting

### No Devices Discovered

**Check MQTT connection:**
```bash
# Verify MQTT broker is running
docker-compose ps mosquitto

# Check MQTT logs
docker-compose logs mosquitto

# Test MQTT connectivity
docker exec -it homeiq-device-intelligence-service \
  mosquitto_sub -h mosquitto -t 'zigbee2mqtt/#' -v
```

### Devices Not Updating

**Force refresh:**
```bash
# Zigbee2MQTT sends device list on bridge restart
# Or trigger manually via MQTT
mosquitto_pub -h mosquitto -t 'zigbee2mqtt/bridge/request/devices' -m ''
```

### Low Recommendation Confidence

**Adjust threshold:**
```bash
# Lower confidence threshold
RECOMMENDATION_MIN_CONFIDENCE=0.5
```

---

## 📚 Device Capability Reference

### Light Capabilities

```json
{
  "on_off": true,
  "brightness": true,
  "color_temp": true,
  "color_xy": true,
  "min_brightness": 1,
  "max_brightness": 254
}
```

### Sensor Capabilities

```json
{
  "temperature": {"min": -40, "max": 60, "unit": "°C"},
  "humidity": {"min": 0, "max": 100, "unit": "%"},
  "pressure": {"min": 300, "max": 1100, "unit": "hPa"},
  "occupancy": {"type": "binary"},
  "battery": {"type": "numeric", "unit": "%"}
}
```

---

## 📚 Related Documentation

- [AI Core Service](../ai-core-service/README.md) - AI orchestration
- [MQTT Documentation](https://mosquitto.org/documentation/)
- [Zigbee2MQTT](https://www.zigbee2mqtt.io/)
- [Home Assistant Device Registry](https://developers.home-assistant.io/docs/device_registry_index)

---

## 🤝 Integration

### Used By
- AI Core Service (8018)
- AI Automation Service (8024)
- Automation Miner (8029)

### Dependencies
- Mosquitto MQTT (1883)
- Zigbee2MQTT (via MQTT)
- Data API (8006)
- InfluxDB (8086)

---

## 🔧 Advanced Features

### Custom Device Profiles

```python
# Add custom device profile
{
  "model": "CUSTOM_SENSOR_V1",
  "manufacturer": "Custom",
  "capabilities": {
    "temperature": {...},
    "custom_reading": {...}
  },
  "automation_hints": [
    "temperature_alert",
    "trend_analysis"
  ]
}
```

### Automation Templates

```yaml
# Generated automation example
automation:
  - alias: "Motion Lighting - Living Room"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_motion
        to: "on"
    action:
      - service: light.turn_on
        entity_id: light.living_room
```

---

**Version:** 1.0.0 (Phase 1)
**Status:** ✅ Production Ready
**Last Updated:** October 25, 2025
**MQTT Protocol:** 3.1.1
