# API Reference - Complete Endpoint Documentation

**Last Updated:** October 20, 2025  
**API Version:** v4.0  
**Status:** ✅ Production Ready

> **📌 This is the SINGLE SOURCE OF TRUTH for all HA Ingestor API documentation.**  
> **Supersedes:** API_DOCUMENTATION.md, API_COMPREHENSIVE_REFERENCE.md, API_ENDPOINTS_REFERENCE.md

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication](#authentication)
4. [Admin API](#admin-api) (Port 8003)
5. [Data API](#data-api) (Port 8006)
6. [Sports Data Service](#sports-data-service) (Port 8005)
7. [AI Automation Service](#ai-automation-service) (Port 8018)
8. [Statistics API](#statistics-api)
9. [Error Handling](#error-handling)
10. [Integration Examples](#integration-examples)

---

## Overview

### System Purpose

The HA Ingestor is an **API-first platform** designed for Home Automation data management and intelligent automation.

**Primary Consumers:**
- Home Assistant automations (webhook triggers, fast status APIs <50ms)
- External analytics platforms (historical queries, trends)
- Cloud integrations (mobile apps, voice assistants)
- Third-party systems (API access to all data sources)

**Deployment:** Single-tenant, self-hosted (one per home)

### Base URLs

| Service | Port | Base URL | Purpose |
|---------|------|----------|---------|
| **Admin API** | 8003 | `http://localhost:8003` | System monitoring, Docker management |
| **Data API** | 8006 | `http://localhost:8006` | Feature data (events, devices, sports, analytics) |
| **Sports Data** | 8005 | `http://localhost:8005` | ESPN sports integration (NFL/NHL) |
| **AI Automation** | 8018 | `http://localhost:8018` | Automation suggestions & conversational AI |
| **Dashboard** | 3000 | `http://localhost:3000` | Frontend (nginx proxy to APIs) |
| **InfluxDB** | 8086 | `http://localhost:8086` | Time-series database |

---

## Architecture

### Epic 13 API Separation (October 2025)

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
│ • Health checks             │  │ • Events (8 endpoints)       │
│ • Docker management (5)     │  │ • Devices & Entities (5)     │
│ • Service monitoring (4)    │  │ • Sports data (9)            │
│ • Configuration (3)         │  │ • HA automation (4)          │
│ • Statistics (8)            │  │ • Analytics (4)              │
│ • WebSocket (/ws)           │  │ • Alerts (6)                 │
│                             │  │ • WebSocket (/api/v1/ws)     │
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

## Authentication

### Local Network (Development)
```bash
# No authentication required for local access
curl http://localhost:8003/health
```

### Remote Access (Production)
```bash
# API Key Authentication
curl -H "X-API-Key: your-api-key" http://api.domain.com/health

# JWT Token Authentication
curl -H "Authorization: Bearer your-jwt-token" http://api.domain.com/health
```

### Configuration
Set `ENABLE_AUTH=false` in environment variables to disable authentication (development only).

---

## Admin API

**Base URL:** `http://localhost:8003`  
**Purpose:** System monitoring, health checks, Docker container management

### Health Endpoints

#### GET /health
Basic health status of admin-api service.

**Response:**
```json
{
  "status": "healthy",
  "service": "admin-api",
  "uptime": "0:05:23.123456",
  "timestamp": "2025-10-20T12:00:00Z"
}
```

#### GET /api/v1/health
Comprehensive health status of all system services.

**Response:**
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
  },
  "timestamp": "2025-10-20T12:00:00Z"
}
```

#### GET /api/v1/health/services
Health status of individual services.

#### GET /api/v1/health/dependencies
Service dependency visualization data.

### Docker Management Endpoints

#### GET /api/v1/docker/containers
List all Docker containers with status.

```json
{
  "containers": [
    {
      "id": "abc123",
      "name": "homeiq-admin",
      "status": "running",
      "image": "homeiq-admin-api:latest"
    }
  ]
}
```

#### POST /api/v1/docker/containers/{container_name}/start
Start a stopped container.

#### POST /api/v1/docker/containers/{container_name}/stop
Stop a running container.

#### POST /api/v1/docker/containers/{container_name}/restart
Restart a container.

#### GET /api/v1/docker/containers/{container_name}/logs?tail=100
Retrieve container logs.

### Statistics Endpoints

See [Statistics API](#statistics-api) section for detailed documentation.

### Configuration Endpoints

#### GET /api/v1/integrations
List all configured integrations.

#### PUT /api/v1/integrations/{integration_name}
Update integration settings.

#### POST /api/v1/integrations/{integration_name}/test
Test integration connectivity.

### WebSocket

#### WS /ws
Real-time system monitoring updates.

**Events:** System alerts, service status changes

---

## Data API

**Base URL:** `http://localhost:8006`  
**Purpose:** Feature data hub - events, devices, sports, analytics, alerts

### Health Check

#### GET /health
```json
{
  "status": "healthy",
  "service": "data-api",
  "uptime": "0:05:23.123456",
  "influxdb_connected": true
}
```

### Events Endpoints (8 total)

#### GET /api/v1/events
Retrieve recent Home Assistant events.

**Query Parameters:**
- `limit` (default: 100): Number of events
- `offset` (default: 0): Pagination offset
- `entity_id` (optional): Filter by entity
- `start_time` (optional): ISO 8601 start time
- `end_time` (optional): ISO 8601 end time

**Response:**
```json
{
  "events": [
    {
      "id": "event_123",
      "entity_id": "sensor.temperature",
      "state": "72.5",
      "timestamp": "2025-10-20T12:00:00Z",
      "attributes": { "unit": "°F" }
    }
  ],
  "total": 42156,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/v1/events/{event_id}
Retrieve specific event details.

#### POST /api/v1/events/search
Advanced event search with filters.

#### GET /api/v1/events/stats
Event statistics and aggregations.

#### GET /api/v1/events/entity/{entity_id}
Get events for specific entity.

#### GET /api/v1/events/timeline
Timeline view of events.

#### GET /api/v1/events/count
Count events matching criteria.

#### GET /api/v1/events/export?format=csv
Export events in CSV/JSON format.

### Devices & Entities Endpoints (5 total)

#### GET /api/v1/devices
Get all discovered Home Assistant devices.

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

#### GET /api/v1/devices/{device_id}
Get specific device information.

#### GET /api/v1/entities
Get all Home Assistant entities.

#### GET /api/v1/entities/{entity_id}
Get specific entity information.

#### GET /api/v1/entities/{entity_id}/history
Get historical data for entity.

### WebSocket

#### WS /api/v1/ws
Real-time data updates.

**Events:**
- `event` - New Home Assistant events
- `game_update` - Sports game status changes
- `alert` - New system alerts
- `metric_update` - Real-time metrics

---

## Sports Data Service

**Base URL:** `http://localhost:8005`  
**Purpose:** ESPN sports data with InfluxDB persistence and Home Assistant webhooks

### Real-Time Endpoints

#### GET /api/v1/games/live
Get currently live games.

**Query Parameters:**
- `league` (optional): "NFL" or "NHL"
- `team_ids` (optional): Comma-separated team IDs

**Response:**
```json
{
  "games": [
    {
      "id": "401547402",
      "league": "NFL",
      "status": "live",
      "home_team": {"abbreviation": "ne", "name": "Patriots"},
      "away_team": {"abbreviation": "kc", "name": "Chiefs"},
      "score": {"home": 21, "away": 17},
      "period": {"current": 3, "time_remaining": "10:32"}
    }
  ]
}
```

#### GET /api/v1/games/upcoming
Get upcoming games in next N hours.

### Historical Query Endpoints

#### GET /api/v1/games/history
Query historical games with filters.

**Query Parameters:**
- `sport` (default: "nfl"): "nfl" or "nhl"
- `team` (optional): Team name filter
- `season` (optional): Season year
- `status` (optional): "scheduled", "live", or "finished"
- `page` (default: 1): Page number
- `page_size` (default: 100, max: 1000): Results per page

#### GET /api/v1/games/timeline/{game_id}
Get score progression for a specific game.

#### GET /api/v1/games/schedule/{team}
Get full season schedule for a team.

### Home Assistant Automation Endpoints

#### GET /api/v1/ha/game-status/{team}
Quick game status check for HA automations (<50ms).

```json
{
  "team": "ne",
  "status": "playing",
  "game_id": "401547402",
  "opponent": "kc",
  "start_time": "2025-10-20T13:00:00Z"
}
```

#### GET /api/v1/ha/game-context/{team}
Full game context for advanced automations.

### Webhook Management

#### POST /api/v1/webhooks/register
Register webhook for game event notifications.

**Request:**
```json
{
  "url": "http://homeassistant.local:8123/api/webhook/your_webhook_id",
  "events": ["game_started", "score_changed", "game_ended"],
  "secret": "your-secure-secret-min-16-chars",
  "team": "ne",
  "sport": "nfl"
}
```

**Webhook Delivery:**
- Fire-and-forget (non-blocking)
- 3 retries with exponential backoff (1s, 2s, 4s)
- 5-second timeout
- HMAC-SHA256 signed

#### GET /api/v1/webhooks/list
List all registered webhooks.

#### DELETE /api/v1/webhooks/{webhook_id}
Unregister a webhook.

---

## AI Automation Service

**Base URL:** `http://localhost:8018`  
**Purpose:** Intelligent automation suggestions with conversational refinement

### Analysis Endpoints

#### GET /health
Service health check.

#### GET /api/analysis/status
Current analysis status and pattern statistics.

#### POST /api/analysis/analyze-and-suggest
Run complete analysis pipeline.

**Request:**
```json
{
  "days": 30,
  "max_suggestions": 10,
  "min_confidence": 0.7,
  "time_of_day_enabled": true,
  "co_occurrence_enabled": true
}
```

### Conversational Flow Endpoints

#### POST /api/v1/suggestions/generate
Generate new automation suggestion.

#### POST /api/v1/suggestions/{suggestion_id}/refine
Refine suggestion based on user input.

**Request:**
```json
{
  "user_input": "Make it blue and only on weekdays",
  "conversation_context": true
}
```

#### POST /api/v1/suggestions/{suggestion_id}/approve
Approve suggestion and generate Home Assistant YAML.

**Response:**
```json
{
  "suggestion_id": "suggestion-1",
  "status": "yaml_generated",
  "automation_yaml": "alias: 'Living Room Light'\ntrigger:\n  - platform: time\n    at: '18:00:00'",
  "ready_to_deploy": true
}
```

#### GET /api/v1/suggestions/devices/{device_id}/capabilities
Get device capabilities.

### Performance Metrics

- **Small datasets** (< 50k events): 1-2 minutes
- **Large datasets** (50k+ events): 2-3 minutes
- **API response times:** 50-5000ms depending on operation

---

## Statistics API

**Base URL:** `http://localhost:8003`

### Core Endpoints

#### GET /api/v1/stats
Comprehensive system statistics.

**Query Parameters:**
- `period` (optional): `1h`, `24h`, `7d`, `30d` (default: `1h`)
- `service` (optional): Filter by service name

#### GET /api/v1/stats/services
Statistics for all services.

#### GET /api/v1/stats/metrics
Query specific metrics with filtering.

**Query Parameters:**
- `metric_name` (optional): Specific metric
- `service` (optional): Filter by service
- `limit` (optional): Max results (default: 100, max: 200)

#### GET /api/v1/stats/performance
Performance analytics with optimization recommendations.

#### GET /api/v1/stats/alerts
Active system alerts sorted by severity.

### Real-Time Metrics (Dashboard Optimized)

#### GET /api/v1/real-time-metrics
**NEW in Oct 2025** - Consolidated metrics endpoint optimized for dashboards.

**Key Benefits:**
- Single API call (replaces 6-10 individual calls)
- 5-10ms response time
- Consistent timestamps
- Graceful degradation

**Response:**
```json
{
  "events_per_hour": 45000,
  "api_calls_active": 5,
  "data_sources_active": ["influxdb", "websocket", "home-assistant"],
  "api_metrics": [
    {
      "service": "websocket-ingestion",
      "status": "active",
      "events_per_hour": 180.0,
      "uptime_seconds": 1196.3
    }
  ],
  "health_summary": {
    "healthy": 2,
    "unhealthy": 13,
    "total": 15,
    "health_percentage": 13.3
  },
  "timestamp": "2025-10-20T12:00:00Z"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Endpoint not found |
| 408 | Request Timeout | Operation timed out |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | Proxy error (nginx) |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "parameter_name",
    "issue": "Specific issue description"
  },
  "request_id": "req-123"
}
```

### Rate Limiting

API endpoints are rate-limited to prevent abuse:
- **General endpoints**: 100 requests per minute
- **Export endpoints**: 10 requests per minute
- **Configuration endpoints**: 20 requests per minute
- **AI refinement**: 1 per 5 seconds, max 10 per suggestion

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## Integration Examples

### Home Assistant Automation

```yaml
automation:
  - alias: "49ers Score Alert"
    trigger:
      platform: webhook
      webhook_id: sports_score_change
      local_only: true
    condition:
      - condition: template
        value_template: "{{ trigger.json.team == 'sf' }}"
      - condition: template
        value_template: "{{ trigger.json.score_diff.home > 0 }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          effect: flash
          rgb_color: [170, 0, 0]
          flash: long
```

### External Analytics Dashboard

```python
import requests

API_BASE = "http://localhost:8006/api/v1"

# Get season statistics
response = requests.get(
    f"{API_BASE}/sports/teams/sf/stats",
    params={"season": 2025}
)
stats = response.json()
```

### Voice Assistant Integration

```javascript
// Alexa skill backend
const response = await axios.get(
    `http://localhost:8006/api/v1/ha/game-status/${team}`,
    { timeout: 500 }
);
```

### Dashboard Real-Time Updates

```typescript
// Single API call for all metrics
async function updateDashboard() {
  const response = await fetch('http://localhost:8003/api/v1/real-time-metrics');
  const metrics = await response.json();
  
  updateEventRate(metrics.events_per_hour);
  updateServiceHealth(metrics.health_summary);
  updateServiceList(metrics.api_metrics);
}

// Refresh every 5 seconds
setInterval(updateDashboard, 5000);
```

---

## Endpoint Summary

| API | Category | Count |
|-----|----------|-------|
| **Admin API** | Health & Monitoring | 4 |
| | Docker Management | 5 |
| | Configuration | 3 |
| | Statistics | 8 |
| | WebSocket | 1 |
| **Data API** | Events | 8 |
| | Devices & Entities | 5 |
| | Analytics | 4 |
| | Alerts | 6 |
| | Integrations | 2 |
| | WebSocket | 1 |
| **Sports Data** | Real-Time | 2 |
| | Historical | 3 |
| | HA Automation | 2 |
| | Webhooks | 3 |
| **AI Automation** | Analysis | 3 |
| | Conversational Flow | 4 |
| **Grand Total** | | **~65 endpoints** |

---

## Related Documentation

- **[Architecture Overview](../architecture/index.md)** - System architecture
- **[Source Tree](../architecture/source-tree.md)** - Service structure
- **[Deployment Guide](../DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[Epic 13 Story](../stories/epic-13-admin-api-service-separation.md)** - API separation details

---

**Document Version:** 4.0  
**Last Updated:** October 20, 2025  
**Status:** ✅ Production Ready  
**Maintained By:** HA Ingestor Team

