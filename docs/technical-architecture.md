# Home Assistant Ingestion Layer - Technical Architecture

## Project Overview

**Name:** Home Assistant Ingestion Layer  
**Description:** Docker-based ingestion layer to capture all local Home Assistant events into InfluxDB time series database  
**Scope:** Ingestion only - no pattern analysis or visualization  
**Approach:** Simple implementation with comprehensive data enrichment  

## Technical Requirements

### Event Capture
- **Method:** Home Assistant WebSocket API for real-time streaming
- **Authentication:** Long-lived access token
- **Event Types:** All state_changed events
- **Latency:** Sub-second processing

### Data Enrichment
- **Weather API Integration:** Environmental context data
- **User Presence Detection:** Behavioral pattern context
- **Event Normalization:** Standardized formats and units
- **Metadata Enrichment:** Device location, type, user associations

### Database
- **Technology:** InfluxDB time series database
- **Retention Policy:** 1 year for raw data
- **Schema:** Optimized for pattern analysis queries
- **Performance:** High write throughput

### Deployment
- **Platform:** Docker containers
- **Orchestration:** Docker Compose
- **Networking:** Internal Docker network
- **Storage:** Persistent data volumes

## Architecture Components

### 1. WebSocket Ingestion Service

**Purpose:** Real-time event capture from Home Assistant

**Technology Stack:**
- Python with aiohttp for WebSocket client
- Home Assistant WebSocket API
- Long-lived access token authentication

**Key Features:**
- Persistent WebSocket connection
- Automatic reconnection on failure
- Event subscription management
- Real-time event processing

**Configuration:**
```python
# WebSocket connection parameters
HA_URL = "ws://homeassistant.local:8123/api/websocket"
ACCESS_TOKEN = "your_long_lived_access_token"
EVENT_TYPES = ["state_changed"]
```

### 2. Data Enrichment Pipeline

**Purpose:** Enhance raw events with contextual data

**Components:**

#### Weather Integration
- **API:** OpenWeatherMap or similar
- **Data Points:** Temperature, humidity, pressure, conditions
- **Update Frequency:** Every 15 minutes
- **Storage:** Cached for performance

#### Presence Detection
- **Methods:** Device tracking, Bluetooth beacons, Wi-Fi presence
- **Data Points:** User location, presence status, activity level
- **Update Frequency:** Real-time
- **Privacy:** Local processing only

#### Data Normalization
- **Timestamp Standardization:** ISO 8601 format, UTC timezone
- **Unit Conversion:** Temperature (Celsius), energy (kWh), etc.
- **State Normalization:** Binary states (on/off → 1/0)
- **Entity Naming:** Consistent naming conventions

### 3. InfluxDB Schema Design

**Measurement:** `home_assistant_events`

**Tags (for filtering/grouping):**
- `entity_id` - Home Assistant entity identifier
- `domain` - Entity domain (sensor, switch, light, etc.)
- `device_class` - Device classification (temperature, motion, etc.)
- `area` - Room/area location
- `device_name` - Friendly device name
- `integration` - HA integration source (zwave, mqtt, etc.)
- `user_id` - Who triggered the event
- `automation_id` - If triggered by automation
- `weather_condition` - Current weather context
- `time_of_day` - Morning/afternoon/evening/night
- `day_of_week` - Monday-Sunday
- `season` - Spring/summer/fall/winter
- `device_group` - Related device groupings
- `priority_level` - Critical/normal/low priority
- `presence_status` - User presence state

**Fields (measurements/values):**
- `state_value` - Current state value
- `previous_state` - Previous state value
- `normalized_value` - Standardized numeric value
- `confidence` - Confidence level (for sensors)
- `duration_seconds` - How long in current state
- `trigger_source` - Manual/automation/scheduled
- `energy_consumption` - If applicable (kWh)
- `cost_impact` - Estimated cost impact
- `unit_of_measurement` - Unit (Celsius, %, etc.)
- `weather_temp` - Current temperature
- `weather_humidity` - Current humidity
- `weather_pressure` - Current pressure

**Retention Policies:**
- Raw data: 1 year
- Hourly summaries: 2 years
- Daily summaries: 5 years
- Monthly summaries: 10 years

### 4. Docker Deployment

**Services:**
- `ha-ingestor` - WebSocket client and enrichment service
- `influxdb` - Time series database
- `weather-service` - Weather API integration
- `presence-service` - User presence detection

**Docker Compose Configuration:**
```yaml
version: '3.8'
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
      - presence-service
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

  weather-service:
    image: weather-api-service:latest
    environment:
      - API_KEY=${WEATHER_API_KEY}
      - UPDATE_INTERVAL=900  # 15 minutes

  presence-service:
    image: presence-detection:latest
    environment:
      - DETECTION_METHOD=wifi_bluetooth
      - UPDATE_INTERVAL=30  # 30 seconds

volumes:
  influxdb_data:
```

## Data Flow

1. **Event Generation:** Home Assistant generates state_changed event
2. **WebSocket Capture:** WebSocket client receives event in real-time
3. **Enrichment Processing:** Pipeline adds weather and presence data
4. **Data Normalization:** Formats standardized for consistency
5. **Database Storage:** Event written to InfluxDB with full metadata
6. **Continuous Processing:** Continuous queries create downsampled summaries

## Implementation Phases

### Phase 1: Core WebSocket Ingestion
**Duration:** 1 week  
**Deliverables:**
- WebSocket connection handler
- Event subscription management
- Basic data parsing
- InfluxDB write operations

**Success Criteria:**
- Stable WebSocket connection
- All state_changed events captured
- Data successfully written to InfluxDB

### Phase 2: Data Enrichment Pipeline
**Duration:** 2-3 weeks  
**Deliverables:**
- Weather API integration
- Presence detection service
- Data normalization logic
- Metadata enrichment

**Success Criteria:**
- Weather data successfully integrated
- User presence detection working
- Comprehensive data enrichment

### Phase 3: InfluxDB Schema Setup
**Duration:** 1-2 weeks  
**Deliverables:**
- Database schema creation
- Continuous queries for downsampling
- Retention policies configuration
- Index optimization

**Success Criteria:**
- Optimized schema design
- Automatic downsampling working
- Efficient query performance

### Phase 4: Docker Orchestration
**Duration:** 3-5 days  
**Deliverables:**
- Docker Compose configuration
- Environment management
- Service health checks
- Logging configuration

**Success Criteria:**
- Complete containerized deployment
- All services running reliably
- Proper logging and monitoring

## Success Criteria

### Functional Requirements
- All Home Assistant events captured in real-time
- Weather data successfully integrated
- User presence detection working
- Data stored in InfluxDB with proper schema
- Docker deployment fully functional

### Performance Requirements
- Sub-second event processing latency
- High availability for ingestion service
- Efficient InfluxDB write operations
- Minimal resource usage

### Quality Requirements
- Comprehensive data enrichment
- Standardized data formats
- Proper error handling and logging
- Clean, maintainable code

## Future Considerations

### Pattern Analysis Capabilities
While not part of the current scope, the architecture supports:
- Multi-temporal aggregation (day/week/month/season/year)
- Anomaly detection
- Trend analysis
- Behavioral pattern recognition

### Scalability
- Horizontal scaling of ingestion services
- Database sharding for large datasets
- Load balancing for high-volume environments

### Integration Opportunities
- Grafana dashboards for visualization
- Machine learning pipelines for prediction
- External system integrations
- Mobile app development

---

*Architecture designed using BMAD-METHOD™ technical analysis framework*
