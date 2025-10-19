# Complete Data Flow and Call Tree Analysis
**Last Updated:** 2025-10-16  
**Last Validated:** October 19, 2025 ✅  
**Status:** Comprehensive Review Complete

**Validation Status (Oct 19, 2025):**
- ✅ All service integrations verified
- ✅ Database paths and configurations confirmed
- ✅ Epic 22 hybrid architecture validated
- ✅ Epic 23 enhancements documented and verified
- ✅ All service ports and communication patterns accurate

## Executive Summary

This document provides a complete analysis of all data flows, service integrations, API calls, and data processing paths in the Home Assistant Ingestor system. It serves as the definitive reference for understanding how data moves through the system.

## System Architecture Overview

```
┌─────────────────┐
│ Home Assistant  │
│   WebSocket     │
└────────┬────────┘
         │ WebSocket Protocol
         │ (auth token)
         ↓
┌─────────────────────────────────┐
│ WebSocket Ingestion Service    │  Port 8001
│ - Event Reception               │
│ - Event Processing              │
│ - Weather Enrichment            │
│ - Batch Processing              │
│ - Device/Entity Discovery       │
└────────┬────────────────────────┘
         │ HTTP POST
         │ /events endpoint
         ↓
┌─────────────────────────────────┐
│ Enrichment Pipeline Service     │  Port 8002
│ - Data Validation               │
│ - Data Normalization            │
│ - Quality Metrics               │
└────────┬────────────────────────┘
         │ InfluxDB Line Protocol
         ↓
┌─────────────────────────────────┐
│ InfluxDB                        │  Port 8086
│ Bucket: home_assistant_events   │
│ - Time-series event data        │
│ - Sports scores                 │
│ - Analytics data                │
└─────────────────────────────────┘
         ↑ Queries
         │
┌─────────────────────────────────┐
│ Data API Service                │  Port 8006
│ - Event Queries                 │
│ - Device/Entity Browsing        │
│ - Sports Data                   │
│ - Analytics Endpoints           │
└────────┬────────────────────────┘
         │ REST API
         │ SQLite (metadata)
         ↓
┌─────────────────────────────────┐
│ Health Dashboard (React)        │  Port 3000
│ - 12 Interactive Tabs           │
│ - Real-time Polling             │
│ - Data Visualization            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Admin API Service               │  Port 8003
│ - Health Monitoring             │
│ - Docker Management             │
│ - System Statistics             │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Sports Data Service             │  Port 8005
│ - ESPN API Integration          │
│ - InfluxDB Storage              │
│ - SQLite Webhooks (Epic 22.3)   │
│ - Event Detection               │
└─────────────────────────────────┘
```

---

## 1. Primary Data Ingestion Flow

### 1.1 Home Assistant → WebSocket Ingestion Service

**Entry Point:** `services/websocket-ingestion/src/main.py`

**Call Flow:**
```
1. WebSocketIngestionService.start()
   ├─ Initialize high-volume processing components
   │  ├─ MemoryManager (max 1024MB default)
   │  ├─ EventQueue (maxsize 10000)
   │  ├─ BatchProcessor (batch_size 100, timeout 5s)
   │  └─ AsyncEventProcessor (max_workers 10)
   │
   ├─ Initialize WeatherEnrichmentService (if API key present)
   │  └─ Weather API client with caching
   │
   ├─ Initialize InfluxDBConnectionManager
   │  └─ Connection to InfluxDB for device/entity storage
   │
   └─ Initialize ConnectionManager
      ├─ Create HomeAssistantWebSocketClient
      ├─ Connect to HA WebSocket (with retry logic)
      │  ├─ Authenticate with long-lived token
      │  ├─ Subscribe to 'state_changed' events
      │  └─ Start device/entity discovery
      │
      └─ Set up event handlers:
         ├─ _on_connect() → triggers discovery
         ├─ _on_disconnect() → triggers reconnection
         ├─ _on_message() → processes incoming messages
         └─ _on_event() → processes state_changed events
```

**Event Processing Pipeline:**
```
2. Event Received from HA WebSocket
   ↓
3. ConnectionManager._on_message()
   ├─ EventSubscriptionManager.handle_event_message()
   ├─ EventProcessor.process_event()
   │  ├─ Validate event structure
   │  ├─ Extract event data
   │  │  ├─ entity_id, domain
   │  │  ├─ old_state, new_state
   │  │  ├─ context (id, parent_id, user_id) - Epic 23.1
   │  │  ├─ device_id, area_id - Epic 23.2 (from DiscoveryService)
   │  │  ├─ duration_in_state - Epic 23.3
   │  │  └─ device_metadata - Epic 23.5
   │  └─ Return processed_event
   │
   ↓
4. ConnectionManager._on_event(processed_event)
   └─ Call registered on_event handler
      ↓
5. WebSocketIngestionService._on_event(processed_event)
   ├─ WeatherEnrichmentService.enrich_event() (if enabled)
   │  ├─ Check if event needs weather data
   │  ├─ Fetch weather from cache (TTL 15 min)
   │  └─ Add weather fields to event
   │
   └─ BatchProcessor.add_event(processed_event)
      ├─ Add to batch queue
      └─ When batch full or timeout:
         └─ Call _process_batch()
```

**Batch Processing:**
```
6. WebSocketIngestionService._process_batch(batch)
   ├─ AsyncEventProcessor.process_event() for each event
   │  └─ High-performance async processing
   │
   └─ SimpleHTTPClient.send_event() for each event
      └─ POST http://enrichment-pipeline:8002/events
         ├─ Headers: Content-Type: application/json
         ├─ Body: Processed event data
         └─ Fire-and-forget (non-blocking)
```

**Discovery Service (Epic 23):**
```
7. DiscoveryService.discover_all()
   ├─ Call HA WebSocket API: config/device_registry/list
   ├─ Call HA WebSocket API: config/entity_registry/list
   ├─ Call HA WebSocket API: config/config_entries/list
   ├─ Store in memory dictionaries:
   │  ├─ self.devices: {device_id → device_data}
   │  ├─ self.entities: {entity_id → entity_data}
   │  ├─ self.entity_to_device: {entity_id → device_id}
   │  └─ self.device_to_area: {device_id → area_id}
   │
   └─ Write to InfluxDB for persistence
      └─ influxdb_manager.write_device_registry()
      └─ influxdb_manager.write_entity_registry()
```

---

## 2. Enrichment Pipeline Processing

**Entry Point:** `services/enrichment-pipeline/src/main.py`

**Call Flow:**
```
1. POST /events endpoint
   └─ events_handler(request)
      ├─ Validate service is running
      ├─ Parse JSON event data
      ├─ Validate structure
      └─ Call service.process_event(event_data)
```

**Event Processing:**
```
2. EnrichmentPipelineService.process_event(event_data)
   ├─ DataValidationEngine.validate_event(event_data)
   │  ├─ Check required fields
   │  ├─ Validate data types
   │  ├─ Check value ranges
   │  └─ Return ValidationResult (is_valid, errors, warnings)
   │
   ├─ DataNormalizer.normalize_event(event_data)
   │  ├─ Convert to standard format
   │  ├─ Flatten nested structures
   │  ├─ Add timestamps
   │  ├─ Generate point tags and fields
   │  └─ Return normalized_event
   │
   └─ InfluxDBClientWrapper.write_event(normalized_event)
      ├─ Convert to InfluxDB Line Protocol
      ├─ Write to bucket: home_assistant_events
      └─ Return success/failure
```

**InfluxDB Schema:**
```
Measurement: state_changed
Tags:
  - entity_id
  - domain
  - event_type
  - device_id (Epic 23.2)
  - area_id (Epic 23.2)
  - context_id (Epic 23.1)
  - context_parent_id (Epic 23.1)
Fields:
  - state (string)
  - old_state (string)
  - attributes (JSON string)
  - duration_in_state (float, seconds) - Epic 23.3
  - weather_* (various weather fields if enriched)
  - device_manufacturer (string) - Epic 23.5
  - device_model (string) - Epic 23.5
Timestamp: event time_fired or current time
```

---

## 3. Data API Service (Port 8006)

**Entry Point:** `services/data-api/src/main.py`

### 3.1 Architecture Overview

The Data API is the **Feature Data Hub** that provides:
- Event queries from InfluxDB
- Device/Entity metadata from SQLite (Epic 22)
- Sports data and analytics
- Home Assistant automation endpoints
- Energy correlation data

**Database Strategy (Epic 22):**
```
┌─────────────────┐
│   InfluxDB      │  Time-series data
│  - Events       │  Optimized for time-range queries
│  - Metrics      │  
│  - Sports       │
└─────────────────┘

┌─────────────────┐
│    SQLite       │  Metadata
│  - Devices      │  Optimized for relational queries
│  - Entities     │  ACID transactions, foreign keys
└─────────────────┘
```

### 3.2 Key Endpoints

**Events Endpoints** (`events_endpoints.py`):
```
GET /api/v1/events/stats
├─ Query InfluxDB for event statistics
├─ Time-based aggregation
└─ Return: event counts, rates, top entities

POST /api/v1/events/search
├─ Text search across events
├─ Filter by entity_id, event_type, time range
├─ Epic 23 filters: device_id, area_id, entity_category
└─ Return: List[EventData]

GET /api/v1/events/automation-trace/{context_id}
├─ Trace automation chain via context.parent_id
├─ Recursive query up to max_depth
└─ Return: Full automation causality chain (Epic 23.1)

GET /api/v1/events/spatial-analytics
├─ Aggregate events by area_id
├─ Calculate area activity patterns
└─ Return: Area-based statistics (Epic 23.2)

GET /api/v1/events/duration-analytics
├─ Analyze duration_in_state patterns
├─ Identify anomalies (too short, too long)
└─ Return: Duration statistics (Epic 23.3)
```

**Devices & Entities Endpoints** (`devices_endpoints.py`):
```
GET /api/devices
├─ Query: SELECT Device, COUNT(Entity) FROM devices
│         LEFT JOIN entities ON device_id
│         WHERE filters...
│         GROUP BY device_id LIMIT ?
├─ Filters: manufacturer, model, area_id, platform
└─ Return: DevicesListResponse (5-10ms vs 50ms InfluxDB)

GET /api/devices/{device_id}
├─ Query: SELECT * FROM devices WHERE device_id = ?
└─ Return: DeviceResponse with entity count

GET /api/entities
├─ Query: SELECT * FROM entities WHERE filters...
├─ Filters: domain, platform, area_id, device_id, disabled
└─ Return: EntitiesListResponse

GET /api/devices/reliability
├─ Query SQLite for device metadata
├─ Query InfluxDB for event reliability
├─ Calculate: availability, event frequency, last_seen
└─ Return: Reliability metrics by device (Epic 23.5)
```

**Sports Endpoints** (`sports_endpoints.py`):
```
GET /api/v1/sports/games/history
├─ Query InfluxDB sports bucket
├─ Filters: team, season, status
├─ Pagination support
└─ Return: PaginatedGamesResponse

GET /api/v1/sports/games/timeline/{game_id}
├─ Query score progression from InfluxDB
└─ Return: GameTimelineResponse

GET /api/v1/sports/schedule/{team}
├─ Query team schedule from InfluxDB
├─ Calculate statistics (wins, losses, streaks)
└─ Return: TeamScheduleResponse
```

**Analytics Endpoints** (`analytics_endpoints.py`):
```
GET /api/v1/analytics/realtime
├─ Query InfluxDB last 5 minutes
├─ Calculate: events/sec, active entities, top domains
└─ Return: Real-time metrics

GET /api/v1/analytics/entity-activity
├─ Query InfluxDB for entity change frequency
├─ Group by entity_id, time window
└─ Return: Entity activity rankings

GET /api/v1/analytics/area-activity
├─ Query InfluxDB grouped by area_id (Epic 23.2)
├─ Calculate per-area event rates
└─ Return: Area activity heatmap data
```

**Energy Endpoints** (`energy_endpoints.py`):
```
GET /api/v1/energy/correlation
├─ Query InfluxDB for energy sensor data
├─ Query weather/carbon/pricing data
├─ Calculate correlations
└─ Return: Correlation analysis

GET /api/v1/energy/recommendations
├─ Analyze historical patterns
├─ Weather/carbon/pricing lookups
└─ Return: Energy optimization suggestions
```

---

## 4. Admin API Service (Port 8003)

**Entry Point:** `services/admin-api/src/main.py`

### 4.1 Purpose

System monitoring and control:
- Health checks for all services
- Docker container management
- System statistics
- Alert management
- Metrics collection

### 4.2 Key Endpoints

**Health Endpoints** (`health_endpoints.py`):
```
GET /api/v1/health
├─ Check all service health:
│  ├─ GET http://websocket-ingestion:8001/health
│  ├─ GET http://enrichment-pipeline:8002/health
│  ├─ GET http://data-api:8006/health
│  ├─ GET http://sports-data:8005/health
│  └─ ... (all services)
├─ Check InfluxDB connection
└─ Return: Aggregated health status

GET /api/v1/health/services
├─ Individual service health checks
└─ Return: Per-service health details

GET /api/v1/health/dependencies
├─ Check external dependencies:
│  ├─ InfluxDB
│  ├─ Home Assistant (if enabled)
│  └─ Weather API (if enabled)
└─ Return: Dependency status
```

**Docker Management** (`docker_endpoints.py`):
```
POST /api/v1/docker/restart/{service_name}
├─ Connect to Docker socket
├─ Find container by name
├─ docker restart {container}
└─ Return: Restart status

GET /api/v1/docker/containers
├─ List all project containers
└─ Return: Container status, ports, health

POST /api/v1/docker/scale/{service_name}
├─ Scale service replicas
└─ Return: Scaling result
```

**Statistics Endpoints** (`stats_endpoints.py`):
```
GET /api/v1/stats
├─ Query InfluxDB for system statistics:
│  ├─ Total events count
│  ├─ Events per service
│  ├─ Processing rates
│  ├─ Error rates
│  └─ Storage usage
└─ Return: System-wide statistics

GET /api/v1/stats/timeseries
├─ Query InfluxDB for historical metrics
├─ Time-based aggregation
└─ Return: Time-series data for charts
```

**Monitoring Endpoints** (`monitoring_endpoints.py`):
```
GET /api/v1/monitoring/metrics
├─ Collect metrics from all services
├─ Aggregate system-wide metrics
└─ Return: Prometheus-compatible metrics

GET /api/v1/monitoring/logs
├─ Query centralized logs
├─ Filter by service, level, time
└─ Return: Log entries

GET /api/v1/monitoring/alerts
├─ Query active alerts
├─ Alert history
└─ Return: Alert data
```

---

## 5. Sports Data Service (Port 8005)

**Entry Point:** `services/sports-data/src/main.py`

### 5.1 Architecture

```
┌──────────────────┐
│   ESPN API       │  Free public API
│  (no API key)    │
└────────┬─────────┘
         │ HTTP GET
         ↓
┌──────────────────────────────┐
│ SportsAPIClient              │
│ - Live games fetch           │
│ - Upcoming games fetch       │
│ - Team-based filtering       │
│ - Caching (15s live, 5m up)  │
└────────┬─────────────────────┘
         │
         ├─→ InfluxDB (game scores)
         │
         └─→ SQLite (webhooks) - Epic 22.3
```

### 5.2 Data Flow

**Live Games:**
```
1. GET /api/v1/games/live?team_ids=sf,dal
   ├─ SportsAPIClient.get_live_games(league, teams)
   │  ├─ Check cache (TTL 15s)
   │  ├─ If miss: HTTP GET to ESPN API
   │  ├─ Filter by team IDs
   │  └─ Cache result
   │
   ├─ InfluxDBWriter.write_games(games, sport)
   │  ├─ Convert to InfluxDB points
   │  ├─ Measurement: nfl_games / nhl_games
   │  ├─ Tags: game_id, home_team, away_team, status
   │  └─ Fields: home_score, away_score, quarter, time
   │
   └─ Return: GameList response
```

**Event Detection (Epic 12.3):**
```
2. GameEventDetector (background task, runs every 15s)
   ├─ Fetch current live games
   ├─ Compare with previous state
   ├─ Detect events:
   │  ├─ game_started: status changed to 'live'
   │  ├─ score_changed: score difference detected
   │  └─ game_ended: status changed to 'finished'
   │
   └─ WebhookManager.trigger_webhooks(event, game)
      ├─ Query SQLite: SELECT * FROM webhooks WHERE events LIKE ?
      ├─ Filter by team (if specified)
      ├─ For each webhook:
      │  ├─ Generate HMAC-SHA256 signature
      │  ├─ POST to webhook URL
      │  ├─ Headers:
      │  │  ├─ X-Webhook-Signature
      │  │  ├─ X-Webhook-Event
      │  │  └─ X-Webhook-Timestamp
      │  └─ Body: JSON event data
      │
      └─ Log delivery status to SQLite
```

**Webhooks (Epic 12.3, SQLite Storage Epic 22.3):**
```
3. POST /api/v1/webhooks/register
   ├─ WebhookManager.register(url, events, secret, team)
   │  ├─ Generate webhook_id (UUID)
   │  ├─ Store in SQLite:
   │  │  INSERT INTO webhooks (webhook_id, url, events, secret_hash, team)
   │  └─ Return webhook_id
   │
   └─ Return: Registration confirmation

4. GET /api/v1/webhooks/list
   ├─ Query SQLite: SELECT * FROM webhooks
   ├─ Hide secrets (show only hashes)
   └─ Return: List of webhooks

5. DELETE /api/v1/webhooks/{webhook_id}
   ├─ Delete from SQLite: DELETE FROM webhooks WHERE id = ?
   └─ Return: 204 No Content
```

**Home Assistant Integration (Epic 12.3):**
```
6. GET /api/v1/ha/game-status/{team}
   ├─ Fetch live game for team
   ├─ Return simplified status:
   │  ├─ is_playing (bool)
   │  ├─ score
   │  ├─ opponent
   │  └─ time_remaining
   └─ For HA binary_sensor/sensor entities

7. GET /api/v1/ha/game-context/{team}
   ├─ Fetch game + historical context
   ├─ Return full context:
   │  ├─ Current game status
   │  ├─ Recent performance (last 5 games)
   │  ├─ Season record
   │  └─ Recommendations for automation
   └─ For HA automations with rich context
```

---

## 6. External Service Integrations

### 6.1 Weather API Integration

**Location:** `services/websocket-ingestion/src/weather_enrichment.py`

**Flow:**
```
1. WeatherEnrichmentService.enrich_event(event)
   ├─ Check if event should be enriched (all by default)
   ├─ Get location (from config or entity attributes)
   ├─ Check cache (TTL 15 minutes)
   │  └─ Key: f"weather:{location}"
   │
   ├─ If cache miss:
   │  ├─ HTTP GET to weather API (OpenWeather, etc.)
   │  ├─ Parse response
   │  └─ Cache result
   │
   └─ Add weather fields to event:
      ├─ weather_temp
      ├─ weather_humidity
      ├─ weather_condition
      ├─ weather_wind_speed
      └─ weather_timestamp
```

### 6.2 Other External Services (Planned)

**Carbon Intensity Service** (Port 8010):
- Fetches carbon intensity data from grid APIs
- Enriches energy events with carbon data
- Used for green energy optimization

**Electricity Pricing Service** (Port 8011):
- Fetches real-time electricity prices
- Used for cost optimization recommendations
- Integration with energy correlation

**Air Quality Service** (Port 8012):
- Fetches air quality data
- Correlates with HVAC/ventilation events

---

## 7. Database Operations

### 7.1 InfluxDB (Time-Series Data)

**Connection Details:**
- URL: `http://influxdb:8086`
- Org: `homeassistant`
- Bucket: `home_assistant_events`
- Auth: Token-based

**Write Operations:**
```
Enrichment Pipeline → InfluxDB
├─ Batch writes (100 events per batch)
├─ Line Protocol format
├─ Async, non-blocking
└─ Circuit breaker pattern

Sports Data → InfluxDB
├─ Game scores every 15s (live)
├─ Game scores every 5m (upcoming)
├─ Fire-and-forget writes
└─ Circuit breaker pattern
```

**Read Operations:**
```
Data API → InfluxDB
├─ Flux query language
├─ Time-range queries (range(start: -1h))
├─ Aggregations (group by time, tags)
├─ Filters (filter by tags)
└─ Connection pooling

Admin API → InfluxDB
├─ Statistics queries
├─ Metrics aggregation
└─ Health checks
```

**Query Patterns:**
```flux
// Event count by domain (last 1 hour)
from(bucket: "home_assistant_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "state_changed")
  |> group(columns: ["domain"])
  |> count()

// Automation trace (context.parent_id)
from(bucket: "home_assistant_events")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "state_changed")
  |> filter(fn: (r) => r.context_parent_id == "{context_id}")

// Area activity (Epic 23.2)
from(bucket: "home_assistant_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r.area_id != "")
  |> group(columns: ["area_id"])
  |> aggregateWindow(every: 5m, fn: count)
```

### 7.2 SQLite (Metadata - Epic 22)

**Data API Database** (`data/metadata.db`):
```sql
-- Devices table
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    manufacturer TEXT,
    model TEXT,
    sw_version TEXT,
    area_id TEXT,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entities table
CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    device_id TEXT,
    domain TEXT NOT NULL,
    platform TEXT NOT NULL,
    unique_id TEXT,
    area_id TEXT,
    disabled BOOLEAN DEFAULT 0,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- Indexes for fast queries
CREATE INDEX idx_devices_manufacturer ON devices(manufacturer);
CREATE INDEX idx_devices_area ON devices(area_id);
CREATE INDEX idx_entities_device ON entities(device_id);
CREATE INDEX idx_entities_domain ON entities(domain);
CREATE INDEX idx_entities_platform ON entities(platform);
```

**Sports Data Database** (`data/webhooks.db` - Epic 22.3):
```sql
-- Webhooks table
CREATE TABLE webhooks (
    webhook_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    events TEXT NOT NULL,  -- JSON array
    secret_hash TEXT NOT NULL,
    team TEXT,
    sport TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP
);

-- Webhook delivery log
CREATE TABLE webhook_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webhook_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    status_code INTEGER,
    success BOOLEAN,
    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (webhook_id) REFERENCES webhooks(webhook_id)
);
```

**Performance Benefits (Epic 22):**
- Device/entity queries: **<10ms** (vs ~50ms InfluxDB)
- Proper foreign key relationships
- ACID transactions for critical data
- Concurrent-safe (WAL mode enabled)
- Complex JOINs for relational queries

---

## 8. Frontend Data Flow

**Health Dashboard** (Port 3000):
```
React Components
├─ Dashboard.tsx (main container)
├─ 12 Tab Components:
│  ├─ OverviewTab → GET /api/v1/health
│  ├─ ServicesTab → GET /api/v1/health/services
│  ├─ DevicesTab → GET /api/devices
│  ├─ EventsTab → GET /api/v1/events/stats
│  ├─ SportsTab → GET /api/v1/sports/games/live
│  ├─ DataSourcesTab → GET /api/v1/integrations
│  ├─ EnergyTab → GET /api/v1/energy/correlation
│  ├─ AnalyticsTab → GET /api/v1/analytics/realtime
│  ├─ AlertsTab → GET /api/v1/alerts
│  ├─ LogsTab → GET /api/v1/monitoring/logs
│  ├─ ConfigurationTab → GET /api/v1/config
│  └─ DependenciesTab → GET /api/v1/health/dependencies
│
└─ Polling Strategy:
   ├─ Overview: Every 5s
   ├─ Services: Every 10s
   ├─ Events/Logs: Every 5s
   ├─ Sports: Every 15s (live), 5m (upcoming)
   └─ Others: Every 30s
```

**API Service Layer** (`services/api.ts`):
```typescript
// Centralized API calls
const apiClient = {
  baseURL: 'http://localhost:8006',  // Data API
  adminURL: 'http://localhost:8003', // Admin API
  
  // Example: Fetch devices
  async getDevices(filters) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${this.baseURL}/api/devices?${params}`);
    return response.json();
  },
  
  // Example: Fetch live sports
  async getLiveSports(teamIds) {
    const response = await fetch(
      `http://localhost:8005/api/v1/games/live?team_ids=${teamIds.join(',')}`
    );
    return response.json();
  }
};
```

---

## 9. Service Communication Matrix

| Source Service | Destination Service | Protocol | Port | Purpose |
|----------------|---------------------|----------|------|---------|
| Home Assistant | websocket-ingestion | WebSocket | 8001 | Event streaming |
| websocket-ingestion | enrichment-pipeline | HTTP POST | 8002 | Event forwarding |
| enrichment-pipeline | InfluxDB | HTTP | 8086 | Data storage |
| data-api | InfluxDB | HTTP | 8086 | Data queries |
| data-api | SQLite | Direct | N/A | Metadata queries |
| admin-api | All Services | HTTP GET | Various | Health checks |
| admin-api | InfluxDB | HTTP | 8086 | Statistics |
| sports-data | ESPN API | HTTP GET | 443 | Sports data |
| sports-data | InfluxDB | HTTP | 8086 | Game scores |
| sports-data | Webhooks | HTTP POST | Various | Event notifications |
| health-dashboard | data-api | HTTP GET | 8006 | Data fetching |
| health-dashboard | admin-api | HTTP GET | 8003 | Monitoring |
| health-dashboard | sports-data | HTTP GET | 8005 | Sports data |

---

## 10. Service Ports Reference

| Service | Internal Port | External Port | Purpose |
|---------|---------------|---------------|---------|
| websocket-ingestion | 8001 | 8001 | HA event ingestion |
| enrichment-pipeline | 8002 | 8002 | Data processing |
| admin-api | 8004 | 8003 | System monitoring (port mapping) |
| data-api | 8006 | 8006 | Feature data hub |
| sports-data | 8005 | 8005 | Sports data API |
| health-dashboard | 3000 | 3000 | React frontend |
| InfluxDB | 8086 | 8086 | Time-series database |
| data-retention | 8080 | 8080 | Data lifecycle management |
| carbon-intensity | 8010 | 8010 | Carbon data |
| electricity-pricing | 8011 | 8011 | Pricing data |
| air-quality | 8012 | 8012 | Air quality data |
| calendar-service | 8013 | 8013 | Calendar integration |
| smart-meter | 8014 | 8014 | Smart meter data |
| log-aggregator | 8015 | 8015 | Centralized logging |
| energy-correlator | 8017 | 8017 | Energy analysis |
| ai-automation-service | 8018 | 8018 | AI automation |

---

## 11. Epic 23 Enhanced Data Flows

### 11.1 Automation Causality Tracking (Story 23.1)

**Context Tracking:**
```
Event 1: User presses button
├─ context.id: "abc123"
├─ context.parent_id: null
└─ Trigger: button.living_room pressed

Event 2: Automation triggers
├─ context.id: "def456"
├─ context.parent_id: "abc123"  ← Links to Event 1
└─ Action: Turn on lights

Event 3: Light turns on
├─ context.id: "ghi789"
├─ context.parent_id: "def456"  ← Links to Event 2
└─ State: light.living_room on

Query: GET /api/v1/events/automation-trace/abc123
└─ Returns: [Event 1, Event 2, Event 3] with full causality chain
```

### 11.2 Spatial Analytics (Story 23.2)

**Device and Area Enrichment:**
```
1. Event received: light.living_room changed
2. EventProcessor looks up entity in DiscoveryService
3. Found: entity → device_id → area_id
4. Event enriched with:
   ├─ device_id: "abc123def"
   ├─ area_id: "living_room"
   └─ Stored in InfluxDB tags

Query: GET /api/v1/events/spatial-analytics?area_id=living_room
└─ Returns: Activity patterns for living room
```

### 11.3 Time-Based Analytics (Story 23.3)

**Duration Tracking:**
```
1. old_state.last_changed: "2025-01-01T10:00:00Z"
2. new_state.last_changed: "2025-01-01T10:05:30Z"
3. Calculated: duration_in_state = 330 seconds
4. Stored in InfluxDB field

Query: GET /api/v1/events/duration-analytics?entity_id=light.bedroom
└─ Returns: Average duration, anomalies, patterns
```

### 11.4 Device Reliability (Story 23.5)

**Metadata Tracking:**
```
1. Device metadata fetched from Discovery Service:
   ├─ manufacturer: "Philips"
   ├─ model: "Hue Bulb"
   ├─ sw_version: "1.2.3"

2. Enriched in event:
   ├─ device_manufacturer: "Philips"
   ├─ device_model: "Hue Bulb"

3. Reliability analysis:
   ├─ Event frequency by device
   ├─ Availability calculation
   ├─ Last seen tracking
   └─ Problem device detection

Query: GET /api/devices/reliability
└─ Returns: Device reliability scores and metrics
```

---

## 12. Error Handling and Resilience

### 12.1 Circuit Breaker Pattern

**Sports Data InfluxDB Writes:**
```
CircuitBreaker States:
├─ CLOSED: Normal operation
├─ OPEN: After 3 consecutive failures
└─ HALF_OPEN: Testing after timeout (60s)

Failure Handling:
├─ Log error
├─ Increment failure counter
├─ If threshold reached: Open circuit
└─ Continue serving from cache
```

### 12.2 Retry Logic

**WebSocket Connection Manager:**
```
Retry Configuration:
├─ max_retries: -1 (infinite, recommended for production)
├─ base_delay: 1s
├─ max_delay: 300s (5 minutes)
├─ backoff_multiplier: 2
└─ jitter_range: 10%

Retry Sequence:
1st retry: ~1s delay
2nd retry: ~2s delay
3rd retry: ~4s delay
4th retry: ~8s delay
...
20th retry: 300s delay (capped)
```

### 12.3 Graceful Degradation

**Service Availability:**
```
If InfluxDB unavailable:
├─ Data API returns cached data
├─ Events logged but not persisted
├─ Health status: "degraded"
└─ Continue operating with fallbacks

If Weather API unavailable:
├─ Events not enriched with weather
├─ Log warning
└─ Continue event processing

If Sports API unavailable:
├─ Return cached game data
├─ Circuit breaker opens
└─ Dashboard shows stale data with warning
```

---

## 13. Performance Characteristics

### 13.1 Throughput

**WebSocket Ingestion:**
- Max workers: 10
- Processing rate limit: 1000 events/sec
- Batch size: 100 events
- Batch timeout: 5 seconds
- Queue size: 10,000 events

**Enrichment Pipeline:**
- Async processing
- Non-blocking writes to InfluxDB
- Validation: <1ms per event
- Normalization: <2ms per event
- InfluxDB write: <10ms per batch

**Data API:**
- SQLite queries: <10ms (devices/entities)
- InfluxDB queries: 50-500ms (time-series)
- Connection pooling enabled
- Query caching (5-15 minutes TTL)

### 13.2 Latency

**End-to-End Event Flow:**
```
HA → WS Service: ~50ms (network + processing)
WS → Enrichment: ~20ms (HTTP + validation)
Enrichment → InfluxDB: ~10ms (write)
Total: ~80ms event ingestion latency
```

**API Response Times:**
- Health endpoints: <50ms
- Device list: <10ms (SQLite)
- Event queries: 100-500ms (InfluxDB, depends on time range)
- Sports data: 15s cache, <50ms hit, 200-500ms miss

---

## 14. Data Retention and Lifecycle

**InfluxDB Retention Policies:**
```
home_assistant_events bucket:
├─ Default retention: 30 days
├─ Downsampling (planned):
│  ├─ 1h resolution: 90 days
│  └─ 1d resolution: 1 year
└─ Managed by data-retention service
```

**SQLite Data:**
```
Devices/Entities:
├─ Persist indefinitely
├─ Updated on discovery
└─ Soft delete (marked inactive)

Webhooks:
├─ Persist until explicitly deleted
├─ Delivery log: 30 days retention
└─ Cleanup via scheduled task
```

---

## 15. Security Considerations

### 15.1 Authentication

**API Authentication:**
```
Admin API (Port 8003):
├─ API key required (ENABLE_AUTH=true)
├─ Bearer token in Authorization header
└─ Validates against configured API_KEY

Data API (Port 8006):
├─ API key optional (ENABLE_AUTH=false default)
├─ For public data access
└─ Rate limiting recommended
```

**Home Assistant Authentication:**
```
WebSocket Connection:
├─ Long-lived access token required
├─ Stored in environment variable
└─ Never logged or exposed
```

### 15.2 Webhook Security

**HMAC Signature Verification:**
```
POST webhook with:
├─ X-Webhook-Signature: HMAC-SHA256(secret, payload)
├─ X-Webhook-Event: event_type
└─ X-Webhook-Timestamp: ISO timestamp

Receiver should:
├─ Calculate HMAC with stored secret
├─ Compare signatures (constant-time comparison)
├─ Check timestamp (reject if >5 minutes old)
└─ Verify event type matches subscription
```

---

## 16. Monitoring and Observability

### 16.1 Logging

**Structured Logging (shared/logging_config.py):**
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "service": "websocket-ingestion",
  "operation": "event_processing",
  "correlation_id": "abc123",
  "entity_id": "light.living_room",
  "event_type": "state_changed",
  "processing_time_ms": 15.3
}
```

**Correlation IDs:**
- Generated for each request/event
- Propagated through all services
- Enables distributed tracing

### 16.2 Health Checks

**Health Check Endpoints:**
```
All services expose /health:
{
  "status": "healthy|degraded|unhealthy",
  "service": "service-name",
  "timestamp": "ISO timestamp",
  "uptime_seconds": 12345,
  "dependencies": {
    "influxdb": {"status": "connected"},
    "sqlite": {"status": "healthy"}
  }
}
```

### 16.3 Metrics

**Metrics Collected:**
- Event processing rate (events/sec)
- API request rate (requests/sec)
- Query latency (p50, p95, p99)
- Error rate (errors/min)
- Service uptime
- Database connection pool status
- Cache hit rate

---

## 17. Summary and Key Takeaways

### 17.1 Data Flow Summary

1. **Home Assistant** emits events via WebSocket
2. **WebSocket Ingestion** receives, enriches, and batches events
3. **Enrichment Pipeline** validates, normalizes, and writes to InfluxDB
4. **Data API** serves queries from InfluxDB and SQLite
5. **Admin API** monitors health and manages system
6. **Sports Data** fetches from ESPN, stores in InfluxDB, triggers webhooks
7. **Health Dashboard** polls APIs and displays real-time data

### 17.2 Key Design Patterns

- **Circuit Breaker**: Resilient external service calls
- **Batch Processing**: High-throughput event handling
- **Hybrid Database**: InfluxDB (time-series) + SQLite (metadata)
- **Event Enrichment**: Context, weather, device, area data
- **Correlation Tracking**: Distributed tracing with correlation IDs
- **Webhook Notifications**: Event-driven integrations
- **Polling Strategy**: HTTP polling instead of WebSockets for simplicity

### 17.3 Performance Optimizations

- **SQLite for Metadata**: 5-10x faster than InfluxDB for relational queries
- **Caching**: Weather (15m), Sports (15s live, 5m upcoming), API queries (5-15m)
- **Async Processing**: Non-blocking I/O throughout
- **Batch Writes**: InfluxDB writes batched for efficiency
- **Connection Pooling**: Database connection reuse

### 17.4 Scalability Considerations

- **Horizontal Scaling**: Services can be replicated (except WebSocket Ingestion)
- **Queue-Based**: Event queue handles burst traffic
- **Database Performance**: InfluxDB scales well for time-series, SQLite sufficient for current metadata volume
- **Caching Layer**: Reduces API calls and database load

---

**End of Document**

This call tree serves as the single source of truth for understanding data flows in the Home Assistant Ingestor system.

