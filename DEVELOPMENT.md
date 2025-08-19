# Development Setup Guide

## Prerequisites

- Python 3.12+
- Home Assistant instance: **http://192.168.1.86:8123/** ✅ (Confirmed available)
- MQTT broker (typically runs on same network as Home Assistant)
- InfluxDB instance for testing

## Quick Setup

### 1. Environment Configuration

Copy the environment template and configure it for your setup:

```bash
cp env.example .env
```

Edit `.env` with your specific values:

```bash
# Your Home Assistant instance (confirmed)
HA_WS_URL=ws://192.168.1.86:8123/api/websocket
HA_WS_TOKEN=your_long_lived_access_token

# MQTT broker (typically same network as HA)
HA_MQTT_HOST=192.168.1.86
HA_MQTT_PORT=1883
HA_MQTT_USERNAME=your_mqtt_username
HA_MQTT_PASSWORD=your_mqtt_password

# InfluxDB for testing
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=home_assistant_events
```

### 2. Home Assistant Access Token ✅

**Token received and configured!** Your Home Assistant long-lived access token has been saved to the configuration.

**Token Details:**
- **Instance:** http://192.168.1.86:8123/
- **Token:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (truncated for security)
- **Expires:** 2035-01-19 (valid for ~10 years)
- **Status:** Ready for development use

### 3. MQTT Configuration

If you're using Home Assistant's built-in MQTT broker:
- **Host:** `192.168.1.86` (same as your HA instance)
- **Port:** `1883` (default MQTT port)
- **Username/Password:** Check your Home Assistant MQTT integration settings

If you're using a separate Mosquitto broker:
- **Host:** Your MQTT broker IP address
- **Port:** Your MQTT broker port
- **Username/Password:** Your MQTT broker credentials

### 4. Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 5. Test Configuration

```bash
# Test Home Assistant WebSocket connection
poetry run python -c "
import asyncio
import websockets
import json

async def test_ws():
    uri = 'ws://192.168.1.86:8123/api/websocket'
    async with websockets.connect(uri) as websocket:
        # Send auth message
        auth_msg = {
            'type': 'auth',
            'access_token': 'YOUR_TOKEN_HERE'
        }
        await websocket.send(json.dumps(auth_msg))
        response = await websocket.recv()
        print(f'Auth response: {response}')

# Run test with your actual token
asyncio.run(test_ws())
"

# Test MQTT connection (requires paho-mqtt)
poetry run python -c "
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f'Connected with result code {rc}')

client = mqtt.Client()
client.on_connect = on_connect
client.username_pw_set('your_username', 'your_password')
client.connect('192.168.1.86', 1883, 60)
client.loop_start()
"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=ha_ingestor

# Run specific test categories
poetry run pytest -m "unit"
poetry run pytest -m "integration"
```

### Code Quality

```bash
# Format code
poetry run ruff format .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy ha_ingestor/
```

### Running the Service

```bash
# Run in development mode
poetry run python -m ha_ingestor.main

# Run with debug logging
LOG_LEVEL=DEBUG poetry run python -m ha_ingestor.main
```

## Testing with Your Home Assistant Instance

### 1. Monitor MQTT Topics

Use an MQTT client to monitor what topics your Home Assistant is publishing:

```bash
# Install mosquitto-clients for testing
# Ubuntu/Debian: sudo apt install mosquitto-clients
# macOS: brew install mosquitto

# Subscribe to all Home Assistant topics
mosquitto_sub -h 192.168.1.86 -p 1883 -u your_username -P your_password -t "homeassistant/#" -v
```

### 2. Test WebSocket Events

Create a simple test script to verify WebSocket connectivity:

```python
# test_websocket.py
import asyncio
import websockets
import json

async def test_home_assistant_ws():
    uri = 'ws://192.168.1.86:8123/api/websocket'
    async with websockets.connect(uri) as websocket:
        # Authenticate
        auth_msg = {
            'type': 'auth',
            'access_token': 'YOUR_TOKEN_HERE'
        }
        await websocket.send(json.dumps(auth_msg))
        response = await websocket.recv()
        print(f'Auth: {response}')

        # Subscribe to events
        subscribe_msg = {
            'id': 1,
            'type': 'subscribe_events'
        }
        await websocket.send(json.dumps(subscribe_msg))
        response = await websocket.recv()
        print(f'Subscribe: {response}')

        # Listen for events
        print("Listening for events...")
        for i in range(10):  # Listen for 10 events
            try:
                event = await asyncio.wait_for(websocket.recv(), timeout=30)
                print(f'Event {i+1}: {event}')
            except asyncio.TimeoutError:
                print("No events received in 30 seconds")
                break

if __name__ == "__main__":
    asyncio.run(test_home_assistant_ws())
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Verify Home Assistant is running at http://192.168.1.86:8123/
   - Check your access token is valid
   - Ensure WebSocket API is enabled in Home Assistant

2. **MQTT Connection Failed**
   - Verify MQTT broker is running
   - Check username/password credentials
   - Ensure MQTT integration is configured in Home Assistant

3. **InfluxDB Connection Failed**
   - Verify InfluxDB is running
   - Check token and organization settings
   - Ensure bucket exists

### Debug Mode

Enable debug logging to see detailed connection information:

```bash
LOG_LEVEL=DEBUG poetry run python -m ha_ingestor.main
```

## Next Steps

Once you have the basic connectivity working:

1. **Phase 1**: Implement core MQTT and WebSocket ingestion
2. **Phase 2**: Add health checks and monitoring
3. **Phase 3**: Optimize performance and add filtering
4. **Phase 4**: Enterprise features and deployment
5. **Phase 5**: Scale and polish

See `.agent-os/product/roadmap.md` for detailed development phases.
