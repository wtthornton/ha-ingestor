# Context7 Research Documentation

## Overview
This document contains comprehensive research gathered from Context7 for the Home Assistant Ingestion Layer project, including detailed documentation for all key technologies and frameworks.

## Technology Stack Research

### 1. Python aiohttp (/aio-libs/aiohttp)
**Trust Score: 9.3 | Code Snippets: 1139**

#### WebSocket Client Implementation
```python
import aiohttp

async def connect_and_use_websocket(url):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            await ws.send_str('Hello WebSocket!')
            msg = await ws.receive()
            print(f"Received message: {msg.data}")
```

#### Key Features for Our Project
- **Async WebSocket Support**: Native `async with` statement support for client WebSockets
- **Connection Management**: Automatic resource management and connection closing
- **Error Handling**: Built-in error handling for WebSocket connections
- **Timeout Configuration**: Configurable timeouts for WebSocket operations

#### WebSocket Connection Parameters
```python
ws_connect(url, *, 
    method='GET', 
    protocols=(), 
    timeout=sentinel,
    auth=None,
    autoclose=True,
    autoping=True,
    heartbeat=None,
    origin=None, 
    params=None, 
    headers=None, 
    proxy=None, 
    proxy_auth=None, 
    ssl=True, 
    verify_ssl=None, 
    fingerprint=None, 
    ssl_context=None, 
    proxy_headers=None, 
    compress=0, 
    max_msg_size=4194304
)
```

#### HTTP Client Usage
```python
import aiohttp
import asyncio

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://python.org') as response:
            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])
            html = await response.text()
            print("Body:", html[:15], "...")

asyncio.run(main())
```

### 2. InfluxDB 2.x (/influxdata/docs-v2)
**Trust Score: 8.1 | Code Snippets: 18,809**

#### Python Client Setup
```python
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

url = "http://localhost:8086"
token = "your-token"
org = "your-org"
bucket = "your-bucket"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
```

#### Writing Data Points
```python
# Create points for Home Assistant events
point1 = Point("home_assistant_events") \
    .tag("entity_id", "sensor.living_room_temperature") \
    .tag("domain", "sensor") \
    .tag("device_class", "temperature") \
    .tag("area", "living_room") \
    .field("state_value", "22.5") \
    .field("normalized_value", 22.5) \
    .field("weather_temp", 18.2) \
    .field("weather_humidity", 65.0) \
    .time(datetime.datetime.utcnow(), WritePrecision.NS)

# Write points
write_api.write(bucket=bucket, org=org, record=[point1])
```

#### Querying Data
```python
# Query recent events
query = '''
from(bucket: "events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "home_assistant_events")
  |> filter(fn: (r) => r._field == "state_value")
'''

table = client.query_api().query(query=query, org=org)
```

#### Downsampling Queries
```python
# Hourly summaries
query = '''
SELECT
  DATE_BIN(INTERVAL '1 hour', time) AS time,
  room,
  AVG(temp) AS temp,
  AVG(hum) AS hum,
  AVG(co) AS co
FROM home
WHERE time >= now() - INTERVAL '24 hours'
GROUP BY 1, room
ORDER BY 1
'''

table = influxdb_raw.query(query=query, language="sql")
data_frame = table.to_pandas()
```

### 3. Docker Compose (/docker/compose)
**Trust Score: 9.9 | Code Snippets: 63**

#### Basic Service Configuration
```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/code
  redis:
    image: redis
```

#### Multi-Service Setup for Our Project
```yaml
services:
  ha-ingestor:
    build: .
    environment:
      - HA_URL=ws://homeassistant.local:8123/api/websocket
      - HA_TOKEN=${HA_ACCESS_TOKEN}
      - INFLUXDB_URL=http://influxdb:8086
      - WEATHER_API_KEY=${WEATHER_API_KEY}
    depends_on:
      - influxdb
      - weather-service
    volumes:
      - ./logs:/app/logs

  influxdb:
    image: influxdb:2.7
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=password
      - DOCKER_INFLUXDB_INIT_ORG=homeassistant
      - DOCKER_INFLUXDB_INIT_BUCKET=events
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2

volumes:
  influxdb_data:
```

#### Development Commands
```bash
# Start services
docker compose up

# Run specific service
docker compose run web bash

# View logs
docker compose logs -f web

# Stop and remove containers
docker compose down --remove-orphans
```

### 4. Home Assistant WebSocket API (/home-assistant/developers.home-assistant)
**Trust Score: 10 | Code Snippets: 1,824**

#### Authentication Flow
```json
// Server sends auth_required
{
  "type": "auth_required",
  "ha_version": "2021.5.3"
}

// Client sends auth
{
  "type": "auth",
  "access_token": "ABCDEFGHIJKLMNOPQ"
}

// Server responds with auth_ok
{
  "type": "auth_ok",
  "ha_version": "2021.5.3"
}
```

#### Event Subscription
```json
{
  "id": 1,
  "type": "subscribe_events",
  "event_type": "state_changed"
}
```

#### Event Message Format
```json
{
   "id": 5,
   "type":"event",
   "event":{
      "data":{},
      "event_type":"test_event",
      "time_fired":"2016-11-26T01:37:24.265429+00:00",
      "origin":"LOCAL"
   }
}
```

#### Ping/Pong Heartbeat
```json
// Client sends ping
{
    "id": 19,
    "type": "ping"
}

// Server responds with pong
{
    "id": 19,
    "type": "pong"
}
```

#### WebSocket Command Implementation
```python
from homeassistant.components import websocket_api

@websocket_api.websocket_command(
    {
        vol.Required("type"): "frontend/get_panels",
        vol.Optional("preload_panels"): bool,
    }
)
@callback
def ws_get_panels(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Handle the websocket command."""
    panels = ...
    connection.send_result(msg["id"], {"panels": panels})
```

### 5. React TypeScript (/microsoft/typescript)
**Trust Score: 9.9 | Code Snippets: 15,930**

#### Component Definition
```typescript
import * as React from 'react';

interface MyProps {
    x: string;
    y: MyInnerProps;
}

interface MyInnerProps {
    value: string;
}

export function MyComponent(_props: MyProps) {
    return <span>my component</span>;
}
```

#### Component with PropTypes
```typescript
class Component extends ReactComponent {
    static propTypes = {
        foo: PropTypes.number,
        bar: PropTypes.node,
        baz: PropTypes.string.isRequired,
    };
    static defaultProps = {
        foo: 42,
    }
}
```

#### JSX Elements
```typescript
/// <reference path="/.lib/react16.d.ts" />
/* @jsxImportSource react */
import "./preact";
const props2 = { answer: 42 }
const a2 = <div key="foo" {...props2}>text</div>;
const b2 = <div {...props2} key="bar">text</div>;
```

## Implementation Guidelines

### WebSocket Client Implementation
1. **Use aiohttp ClientSession** for WebSocket connections
2. **Implement proper authentication** with Home Assistant access tokens
3. **Handle reconnection** with exponential backoff
4. **Subscribe to state_changed events** for comprehensive data capture
5. **Implement heartbeat** with ping/pong for connection health

### InfluxDB Integration
1. **Use Point class** for type-safe data construction
2. **Implement proper tagging** for efficient querying
3. **Set up retention policies** for data management
4. **Use batch writes** for optimal performance
5. **Implement downsampling** for long-term storage

### Docker Compose Setup
1. **Define all services** in a single compose file
2. **Use environment variables** for configuration
3. **Set up proper networking** between services
4. **Configure volumes** for persistent data
5. **Implement health checks** for service monitoring

### Home Assistant Integration
1. **Follow authentication flow** properly
2. **Subscribe to appropriate events** (state_changed)
3. **Handle event data** according to HA's format
4. **Implement error handling** for connection issues
5. **Use proper message IDs** for request/response correlation

### React TypeScript Frontend
1. **Define proper interfaces** for all data models
2. **Use TypeScript strict mode** for better type safety
3. **Implement proper error handling** in components
4. **Use React hooks** for state management
5. **Follow React best practices** for component design

## Key Takeaways

1. **aiohttp** provides excellent async WebSocket support with proper resource management
2. **InfluxDB 2.x** offers powerful time-series capabilities with Python client libraries
3. **Docker Compose** enables easy orchestration of multi-service applications
4. **Home Assistant WebSocket API** provides real-time event streaming with proper authentication
5. **React TypeScript** ensures type safety and maintainable frontend code

This research provides the foundation for implementing a robust, scalable Home Assistant ingestion layer with proper error handling, data enrichment, and monitoring capabilities.


