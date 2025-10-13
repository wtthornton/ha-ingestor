# API Comprehensive Reference - Complete Endpoint Documentation

**Last Updated:** October 13, 2025  
**API Version:** v4.0 (Post Epic 13 & Epic 21)  
**Status:** Production Ready

---

## 🎯 Overview

The HA Ingestor system provides a dual-API architecture (as of Epic 13) with specialized services for different concerns:

- **Admin API (Port 8003→8004)**: System monitoring, health checks, Docker management
- **Data API (Port 8006)**: Feature data hub for events, devices, sports, analytics, alerts

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│              Health Dashboard (Port 3000)                     │
│                      nginx proxy                              │
└──────────────────┬────────────────────────┬───────────────────┘
                   │                        │
      System Monitoring & Control  Feature Data Queries
                   │                        │
                   ▼                        ▼
┌─────────────────────────────┐  ┌──────────────────────────────┐
│   Admin API (8003→8004)     │  │     Data API (8006)          │
│                             │  │                              │
│ SYSTEM MONITORING:          │  │ FEATURE DATA:                │
│ • Health checks             │  │ • Events (8 endpoints)       │
│ • Docker management (5)     │  │ • Devices & Entities (5)     │
│ • Service monitoring (4)    │  │ • Sports data (9) [Epic 12]  │
│ • Configuration (3)         │  │ • HA automation (4) [Epic 12]│
│ • Statistics (2)            │  │ • Analytics (4)              │
│ • Integration mgmt (2)      │  │ • Alerts (6)                 │
│ • Admin WebSocket (/ws)     │  │ • Integrations (2)           │
│                             │  │ • Data WebSocket (/api/v1/ws)│
│ ~22 endpoints               │  │ ~40 endpoints                │
└─────────────────────────────┘  └──────────────────────────────┘
           │                                 │
           └────────────┬────────────────────┘
                        ▼
               ┌─────────────────┐
               │  InfluxDB 2.7   │
               │   Port 8086     │
               └─────────────────┘
```

---

## 🔧 Admin API Endpoints (Port 8003→8004)

**Base URL:** `http://localhost:8003`  
**Purpose:** System monitoring, health checks, Docker container management  
**Container Port:** 8004 (mapped from 8003)  
**Authentication:** Optional (configurable via `ENABLE_AUTH`)

### Health & Monitoring

#### 1. System Health Check
```http
GET /health
```
**Description:** Basic health status of admin-api service  
**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "admin-api",
  "uptime": "0:05:23.123456",
  "timestamp": "2025-10-13T12:00:00"
}
```

#### 2. Comprehensive Health Status
```http
GET /api/v1/health
```
**Description:** Detailed health status of all system services  
**Response:** `200 OK`
```json
{
  "overall_status": "healthy",
  "admin_api_status": "healthy",
  "services": {
    "websocket_ingestion": {
      "status": "healthy",
      "connection": { "is_connected": true },
      "event_processing": { "events_per_minute": 16.28 }
    },
    "enrichment_pipeline": { "status": "healthy" },
    "data_retention": { "status": "healthy" },
    "influxdb": { "status": "healthy" }
  }
}
```

#### 3. Service Health Checks
```http
GET /api/v1/health/services
```
**Description:** Health status of individual services  
**Response:** `200 OK` - Service health details

#### 4. Dependency Graph
```http
GET /api/v1/health/dependencies
```
**Description:** Service dependency visualization data  
**Response:** `200 OK` - Graph data for dependency visualization

### Docker Container Management

#### 5. List All Containers
```http
GET /api/v1/docker/containers
```
**Description:** List all Docker containers with status  
**Response:** `200 OK`
```json
{
  "containers": [
    {
      "id": "abc123",
      "name": "ha-ingestor-admin",
      "status": "running",
      "image": "ha-ingestor-admin-api:latest"
    }
  ]
}
```

#### 6. Start Container
```http
POST /api/v1/docker/containers/{container_name}/start
```
**Description:** Start a stopped Docker container  
**Response:** `200 OK`

#### 7. Stop Container
```http
POST /api/v1/docker/containers/{container_name}/stop
```
**Description:** Stop a running Docker container  
**Response:** `200 OK`

#### 8. Restart Container
```http
POST /api/v1/docker/containers/{container_name}/restart
```
**Description:** Restart a Docker container  
**Response:** `200 OK`

#### 9. Get Container Logs
```http
GET /api/v1/docker/containers/{container_name}/logs?tail=100
```
**Description:** Retrieve container logs  
**Query Parameters:**
- `tail` (optional): Number of log lines to retrieve  
**Response:** `200 OK` - Log entries

### Configuration Management

#### 10. List Integrations
```http
GET /api/v1/integrations
```
**Description:** List all configured integrations  
**Response:** `200 OK`
```json
{
  "integrations": [
    {
      "name": "Home Assistant",
      "status": "connected",
      "type": "websocket"
    },
    {
      "name": "Weather API",
      "status": "connected",
      "type": "http"
    }
  ]
}
```

#### 11. Update Integration Configuration
```http
PUT /api/v1/integrations/{integration_name}
```
**Description:** Update integration settings  
**Request Body:**
```json
{
  "url": "http://homeassistant.local:8123",
  "token": "your-access-token"
}
```
**Response:** `200 OK`

#### 12. Test Integration Connection
```http
POST /api/v1/integrations/{integration_name}/test
```
**Description:** Test integration connectivity  
**Response:** `200 OK` - Connection test results

### Statistics

#### 13. System Statistics
```http
GET /api/v1/stats
```
**Description:** Overall system statistics  
**Response:** `200 OK`
```json
{
  "events_processed": 42156,
  "events_per_minute": 16.28,
  "uptime": "5 days, 3 hours",
  "storage_used": "2.5 GB"
}
```

#### 14. Service Statistics
```http
GET /api/v1/stats/services
```
**Description:** Per-service statistics  
**Response:** `200 OK` - Service-specific metrics

### WebSocket

#### 15. Admin WebSocket Connection
```
WS /ws
```
**Description:** Real-time system monitoring updates  
**Protocol:** WebSocket  
**Events:** System alerts, service status changes

---

## 📊 Data API Endpoints (Port 8006)

**Base URL:** `http://localhost:8006`  
**Purpose:** Feature data hub - events, devices, sports, analytics, alerts  
**Authentication:** Optional (configurable via `ENABLE_AUTH`)  
**Created:** Epic 13 (October 2025)

### Health Check

#### 1. Data API Health
```http
GET /health
```
**Description:** Health status of data-api service  
**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "data-api",
  "uptime": "0:05:23.123456",
  "influxdb_connected": true
}
```

---

### Events Endpoints (8 total)

#### 2. Get Recent Events
```http
GET /api/v1/events?limit=100&offset=0
```
**Description:** Retrieve recent Home Assistant events from InfluxDB  
**Query Parameters:**
- `limit` (optional, default: 100): Number of events to return
- `offset` (optional, default: 0): Pagination offset
- `entity_id` (optional): Filter by entity
- `start_time` (optional): ISO 8601 start time
- `end_time` (optional): ISO 8601 end time

**Response:** `200 OK`
```json
{
  "events": [
    {
      "id": "event_123",
      "entity_id": "sensor.temperature",
      "state": "72.5",
      "timestamp": "2025-10-13T12:00:00Z",
      "attributes": { "unit": "°F" }
    }
  ],
  "total": 42156,
  "limit": 100,
  "offset": 0
}
```

#### 3. Get Event by ID
```http
GET /api/v1/events/{event_id}
```
**Description:** Retrieve specific event details  
**Response:** `200 OK` - Event details

#### 4. Search Events
```http
POST /api/v1/events/search
```
**Description:** Advanced event search with filters  
**Request Body:**
```json
{
  "entity_ids": ["sensor.temperature", "sensor.humidity"],
  "start_time": "2025-10-13T00:00:00Z",
  "end_time": "2025-10-13T23:59:59Z",
  "states": ["on", "off"]
}
```
**Response:** `200 OK` - Filtered events

#### 5. Get Event Statistics
```http
GET /api/v1/events/stats?start_time=...&end_time=...
```
**Description:** Event statistics and aggregations  
**Response:** `200 OK`
```json
{
  "total_events": 42156,
  "events_by_entity": {
    "sensor.temperature": 1234,
    "light.living_room": 567
  },
  "events_per_hour": 175.2
}
```

#### 6. Get Events by Entity
```http
GET /api/v1/events/entity/{entity_id}?limit=100
```
**Description:** Get events for specific entity  
**Response:** `200 OK` - Entity-specific events

#### 7. Get Events Timeline
```http
GET /api/v1/events/timeline?entity_id=...&start_time=...&end_time=...
```
**Description:** Timeline view of events  
**Response:** `200 OK` - Chronological event data

#### 8. Get Events Count
```http
GET /api/v1/events/count?entity_id=...
```
**Description:** Count events matching criteria  
**Response:** `200 OK` - Event counts

#### 9. Export Events
```http
GET /api/v1/events/export?format=csv&start_time=...&end_time=...
```
**Description:** Export events in CSV/JSON format  
**Query Parameters:**
- `format`: csv or json
- `start_time`, `end_time`: Date range
**Response:** `200 OK` - File download

---

### Devices & Entities Endpoints (5 total)

#### 10. List All Devices
```http
GET /api/v1/devices
```
**Description:** Get all discovered Home Assistant devices  
**Response:** `200 OK`
```json
{
  "devices": [
    {
      "id": "device_abc123",
      "name": "Living Room Light",
      "manufacturer": "Philips",
      "model": "Hue Bulb",
      "entities": ["light.living_room"]
    }
  ],
  "total": 42
}
```

#### 11. Get Device Details
```http
GET /api/v1/devices/{device_id}
```
**Description:** Get specific device information  
**Response:** `200 OK` - Device details with entities

#### 12. List All Entities
```http
GET /api/v1/entities
```
**Description:** Get all Home Assistant entities  
**Response:** `200 OK`
```json
{
  "entities": [
    {
      "entity_id": "sensor.temperature",
      "friendly_name": "Temperature Sensor",
      "state": "72.5",
      "domain": "sensor",
      "device_id": "device_abc123"
    }
  ],
  "total": 156
}
```

#### 13. Get Entity Details
```http
GET /api/v1/entities/{entity_id}
```
**Description:** Get specific entity information  
**Response:** `200 OK` - Entity details

#### 14. Get Entity History
```http
GET /api/v1/entities/{entity_id}/history?start_time=...&end_time=...
```
**Description:** Get historical data for entity  
**Response:** `200 OK` - Historical state changes

---

### Sports Data Endpoints (9 total) - Epic 12

#### 15. Get Live Games
```http
GET /api/v1/sports/games/live?league=nfl
```
**Description:** Get currently active games  
**Query Parameters:**
- `league` (optional): nfl or nhl
- `team` (optional): Filter by team abbreviation

**Response:** `200 OK`
```json
{
  "games": [
    {
      "id": "401234567",
      "league": "nfl",
      "status": "live",
      "home_team": "KC",
      "away_team": "BUF",
      "home_score": 24,
      "away_score": 21,
      "quarter": 3,
      "time_remaining": "8:42"
    }
  ]
}
```

#### 16. Get Upcoming Games
```http
GET /api/v1/sports/games/upcoming?league=nfl&days=7
```
**Description:** Get scheduled upcoming games  
**Response:** `200 OK` - Upcoming games list

#### 17. Get Historical Games
```http
GET /api/v1/sports/games/history?team=KC&season=2024&limit=20
```
**Description:** Get past games from InfluxDB (Epic 12)  
**Query Parameters:**
- `team` (required): Team abbreviation
- `season` (optional): Season year
- `limit` (optional, default: 20): Number of games

**Response:** `200 OK`
```json
{
  "games": [
    {
      "id": "401234567",
      "date": "2024-10-12",
      "home_team": "KC",
      "away_team": "DEN",
      "home_score": 31,
      "away_score": 14,
      "result": "W"
    }
  ],
  "total": 156
}
```

#### 18. Get Game Timeline
```http
GET /api/v1/sports/games/timeline/{game_id}
```
**Description:** Get score progression timeline from InfluxDB  
**Response:** `200 OK`
```json
{
  "game_id": "401234567",
  "timeline": [
    { "quarter": 1, "time": "12:00", "home_score": 0, "away_score": 0 },
    { "quarter": 1, "time": "8:42", "home_score": 7, "away_score": 0 }
  ]
}
```

#### 19. Get Season Schedule
```http
GET /api/v1/sports/schedule/{team}?season=2024
```
**Description:** Get full season schedule for team  
**Response:** `200 OK` - Complete season schedule

#### 20. Get Team Statistics
```http
GET /api/v1/sports/teams/{team}/stats?season=2024
```
**Description:** Get team statistics from historical data  
**Response:** `200 OK` - Season statistics

#### 21. Get League Standings
```http
GET /api/v1/sports/standings?league=nfl
```
**Description:** Get current league standings  
**Response:** `200 OK` - Standings data

#### 22. Get Game Details
```http
GET /api/v1/sports/games/{game_id}
```
**Description:** Get detailed game information  
**Response:** `200 OK` - Complete game details

#### 23. Search Games
```http
POST /api/v1/sports/games/search
```
**Description:** Advanced game search  
**Request Body:**
```json
{
  "teams": ["KC", "BUF"],
  "start_date": "2024-09-01",
  "end_date": "2024-12-31",
  "status": ["completed", "live"]
}
```
**Response:** `200 OK` - Filtered games

---

### Home Assistant Automation Endpoints (4 total) - Epic 12

#### 24. Get Game Status for HA
```http
GET /api/v1/ha/game-status/{team}
```
**Description:** Real-time game status optimized for HA automations  
**Response:** `200 OK`
```json
{
  "team": "KC",
  "has_game_today": true,
  "game_status": "live",
  "is_winning": true,
  "score_differential": 3,
  "time_remaining": "8:42",
  "quarter": 3
}
```

#### 25. Get Game Context for HA
```http
GET /api/v1/ha/game-context/{team}
```
**Description:** Rich context for HA automations  
**Response:** `200 OK`
```json
{
  "team": "KC",
  "opponent": "BUF",
  "venue": "home",
  "is_prime_time": true,
  "game_importance": "high",
  "playoff_implications": true
}
```

#### 26. Register Webhook
```http
POST /api/v1/ha/webhooks/register
```
**Description:** Register webhook for game events  
**Request Body:**
```json
{
  "url": "http://homeassistant.local/webhook/game_update",
  "events": ["game_start", "score_change", "game_end"],
  "teams": ["KC", "BUF"]
}
```
**Response:** `201 Created`

#### 27. List Webhooks
```http
GET /api/v1/ha/webhooks
```
**Description:** Get registered webhooks  
**Response:** `200 OK` - Webhook list

---

### Analytics Endpoints (4 total)

#### 28. Get System Analytics
```http
GET /api/v1/analytics/system?start_time=...&end_time=...
```
**Description:** System-wide analytics and metrics  
**Response:** `200 OK`
```json
{
  "period": {
    "start": "2025-10-13T00:00:00Z",
    "end": "2025-10-13T23:59:59Z"
  },
  "metrics": {
    "total_events": 42156,
    "events_per_hour": 175.2,
    "unique_entities": 156,
    "error_rate": 0.002
  }
}
```

#### 29. Get Entity Analytics
```http
GET /api/v1/analytics/entities/{entity_id}?days=30
```
**Description:** Analytics for specific entity  
**Response:** `200 OK` - Entity-specific analytics

#### 30. Get Performance Metrics
```http
GET /api/v1/analytics/performance
```
**Description:** System performance metrics  
**Response:** `200 OK` - Performance data

#### 31. Get Usage Statistics
```http
GET /api/v1/analytics/usage?groupBy=day&days=30
```
**Description:** Usage statistics over time  
**Response:** `200 OK` - Usage trends

---

### Alert Endpoints (6 total)

#### 32. List All Alerts
```http
GET /api/v1/alerts?status=active&severity=high
```
**Description:** Get system alerts  
**Query Parameters:**
- `status` (optional): active, acknowledged, resolved
- `severity` (optional): low, medium, high, critical

**Response:** `200 OK`
```json
{
  "alerts": [
    {
      "id": "alert_123",
      "severity": "high",
      "status": "active",
      "message": "High event processing latency",
      "timestamp": "2025-10-13T12:00:00Z"
    }
  ],
  "total": 3
}
```

#### 33. Get Alert Details
```http
GET /api/v1/alerts/{alert_id}
```
**Description:** Get specific alert information  
**Response:** `200 OK` - Alert details

#### 34. Create Alert
```http
POST /api/v1/alerts
```
**Description:** Create new alert  
**Request Body:**
```json
{
  "severity": "high",
  "message": "Custom alert message",
  "source": "manual"
}
```
**Response:** `201 Created`

#### 35. Acknowledge Alert
```http
POST /api/v1/alerts/{alert_id}/acknowledge
```
**Description:** Acknowledge an alert  
**Response:** `200 OK`

#### 36. Resolve Alert
```http
POST /api/v1/alerts/{alert_id}/resolve
```
**Description:** Mark alert as resolved  
**Response:** `200 OK`

#### 37. Delete Alert
```http
DELETE /api/v1/alerts/{alert_id}
```
**Description:** Delete an alert  
**Response:** `204 No Content`

---

### Integration Endpoints (2 total)

#### 38. List Services
```http
GET /api/v1/services
```
**Description:** List all integrated services  
**Response:** `200 OK`
```json
{
  "services": [
    {
      "name": "influxdb",
      "status": "connected",
      "version": "2.7"
    },
    {
      "name": "sports-data",
      "status": "connected",
      "version": "1.0"
    }
  ]
}
```

#### 39. Get Service Status
```http
GET /api/v1/services/{service_name}/status
```
**Description:** Get specific service status  
**Response:** `200 OK` - Service details

---

### WebSocket

#### 40. Data WebSocket Connection
```
WS /api/v1/ws
```
**Description:** Real-time data updates for events, sports, analytics  
**Protocol:** WebSocket  
**Events:**
- `event` - New Home Assistant events
- `game_update` - Sports game status changes
- `alert` - New system alerts
- `metric_update` - Real-time metrics

**Example Message:**
```json
{
  "type": "event",
  "data": {
    "entity_id": "sensor.temperature",
    "state": "72.5",
    "timestamp": "2025-10-13T12:00:00Z"
  }
}
```

---

## 🔐 Authentication

Both APIs support optional authentication:

### API Key Authentication (Header)
```http
X-API-Key: your-api-key-here
```

### JWT Token Authentication (Header)
```http
Authorization: Bearer your-jwt-token-here
```

### Configuration
Set `ENABLE_AUTH=false` in environment variables to disable authentication (development only).

---

## 🌐 Nginx Routing

Dashboard nginx configuration routes requests to appropriate API:

```nginx
# Admin API - System monitoring
location /api/v1/docker/ {
    proxy_pass http://admin-api:8004;
}

location /api/v1/health {
    proxy_pass http://admin-api:8004;
}

# Data API - Feature data
location /api/v1/events/ {
    proxy_pass http://data-api:8006;
}

location /api/v1/devices/ {
    proxy_pass http://data-api:8006;
}

location /api/v1/sports/ {
    proxy_pass http://data-api:8006;
}

location /api/v1/analytics/ {
    proxy_pass http://data-api:8006;
}

location /api/v1/alerts/ {
    proxy_pass http://data-api:8006;
}
```

---

## 📊 Endpoint Summary

| API | Category | Endpoint Count |
|-----|----------|----------------|
| **Admin API** | Health & Monitoring | 4 |
| | Docker Management | 5 |
| | Configuration | 3 |
| | Statistics | 2 |
| | WebSocket | 1 |
| **Admin API Total** | | **~22 endpoints** |
| **Data API** | Events | 8 |
| | Devices & Entities | 5 |
| | Sports Data | 9 |
| | HA Automation | 4 |
| | Analytics | 4 |
| | Alerts | 6 |
| | Integrations | 2 |
| | WebSocket | 1 |
| **Data API Total** | | **~40 endpoints** |
| **Grand Total** | | **~62 endpoints** |

---

## 🔗 Related Documentation

- **[Architecture Overview](architecture/index.md)** - System architecture
- **[Source Tree](architecture/source-tree.md)** - Service structure
- **[Epic 13 Story](stories/epic-13-admin-api-service-separation.md)** - API separation details
- **[Epic 12 Story](stories/epic-12-sports-data-influxdb-persistence.md)** - Sports persistence
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Deployment instructions

---

**Document Version:** 4.0  
**Last Updated:** October 13, 2025  
**Status:** Production Ready  
**Maintained By:** HA Ingestor Team

