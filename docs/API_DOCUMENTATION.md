# 📚 Home Assistant Ingestor - API Documentation

## 🎯 **System Purpose**

### **API Data Hub for Home Automation**

This system is an **API-first platform** designed to serve:

**Primary Consumers** (External Systems):
1. **Home Assistant Automations** - Webhook triggers, fast status APIs (<50ms), entity sensors
2. **External Analytics Platforms** - Historical queries, trends, statistics
3. **Cloud Integrations** - Mobile apps, voice assistants, custom dashboards
4. **Third-Party Systems** - API access to all collected data sources

**Secondary Consumer** (Admin Interface):
- Home administrator monitoring dashboard (occasional viewing)

**Deployment**: Single-tenant, self-hosted (one per home, small to xlarge)

---

## 🌐 **API Overview**

### **Base URLs**

**Epic 13 API Separation** (Current Architecture):

**Data API (Feature Data Hub)** - **Primary API for External Consumers** ⭐
```
http://localhost:8006/api/v1
```
**Purpose**: Feature data queries (events, devices, sports, analytics, alerts)  
**Consumers**: Home Assistant, external integrations, analytics platforms  
**Performance**: Optimized for automation (<50ms target)

**Admin API (System Monitoring)**
```
http://localhost:8003/api/v1
```
**Purpose**: System health, Docker management, configuration  
**Consumers**: Admin dashboard, monitoring tools  
**Performance**: General purpose

**Sports Data Service** (Internal, proxied via data-api)
```
http://localhost:8005/api/v1
```
**Purpose**: ESPN sports data integration (NFL/NHL)  
**Consumers**: data-api (proxied), future webhook system

**Data Retention API**
```
http://localhost:8080
```
**Purpose**: Data lifecycle management, cleanup policies

**Enrichment Pipeline API** (Internal)
```
http://localhost:8002
```
**Purpose**: Data normalization and validation

**WebSocket Ingestion API** (Internal)
```
http://localhost:8001
```
**Purpose**: Home Assistant WebSocket connection

**External Data Services (Internal Only)**
- Carbon Intensity Service: `http://carbon-intensity-service:8010`
- Electricity Pricing Service: `http://electricity-pricing-service:8011`
- Air Quality Service: `http://air-quality-service:8012`
- Calendar Service: `http://calendar-service:8013`
- Smart Meter Service: `http://smart-meter-service:8014`
- Weather API Service: `http://weather-api:8000`

### **Authentication**

**Local Network**: Optional (trusted network)
```bash
# No auth required for local access (single home deployment)
```

**Remote Access**: API key required
```bash
Authorization: Bearer <your-api-key>
```

**Webhook Delivery**: HMAC-SHA256 signatures
```bash
X-Webhook-Signature: <hmac-sha256-hex>
X-Webhook-Event: score_changed
```

### **Response Format**
All API responses follow this format:
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully"
}
```

### **Performance SLAs**

**For Home Assistant Automations** (Critical Path):
- Status endpoints: <50ms (e.g., `/api/v1/ha/game-status/{team}`)
- Event webhooks: <5s delivery (with retries)
- Entity sensor updates: <100ms

**For Analytics Platforms** (Non-Critical):
- Historical queries: <500ms
- Statistical aggregations: <1s
- Bulk exports: <10s

**For Admin Dashboard** (Monitoring):
- Health checks: <200ms
- Statistics: <1s
- Service management: <2s

---

## 🔌 **API Consumer Integration Examples**

### **Use Case 1: Home Assistant Automation (Primary)**

**Scenario**: Flash living room lights when 49ers score

```yaml
# Home Assistant configuration.yaml
automation:
  - alias: "49ers Score Alert"
    trigger:
      # Option A: Webhook (Epic 12 - recommended)
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
          rgb_color: [170, 0, 0]  # 49ers red
          flash: long

  - alias: "Game Day Scene"
    trigger:
      # Option B: State change (Epic 12 - entity sensor)
      platform: state
      entity_id: sensor.49ers_game_status
      to: "playing"
    action:
      - scene: scene.game_day
      - service: notify.mobile_app
        data:
          message: "49ers game started!"
```

**API Endpoints Needed** (Epic 12):
- POST webhook to HA when score changes
- GET /api/v1/ha/game-status/sf (<50ms)
- Entity sensor integration

---

### **Use Case 2: External Analytics Dashboard**

**Scenario**: Cloud dashboard queries historical sports data

```python
# External Python app
import requests

API_BASE = "http://home-ingestor.local:8006/api/v1"

# Get season statistics
response = requests.get(
    f"{API_BASE}/sports/teams/sf/stats",
    params={"season": 2025}
)

stats = response.json()
# {
#   "wins": 10,
#   "losses": 3,
#   "avg_points_scored": 27.4,
#   "avg_points_allowed": 19.2,
#   "point_differential": 8.2,
#   "win_percentage": 0.769
# }

# Get game timeline
response = requests.get(
    f"{API_BASE}/sports/games/401547413/timeline"
)

timeline = response.json()
# [
#   {"time": "2025-10-14T13:00:00Z", "home": 0, "away": 0, "quarter": 1},
#   {"time": "2025-10-14T13:15:00Z", "home": 7, "away": 0, "quarter": 1},
#   ...
# ]
```

**API Endpoints Needed** (Epic 12 Phase 2):
- GET /api/v1/sports/teams/{team}/stats
- GET /api/v1/sports/games/{id}/timeline
- GET /api/v1/sports/games/history

---

### **Use Case 3: Voice Assistant Integration**

**Scenario**: "Alexa, what's the 49ers score?"

```javascript
// Alexa skill backend
const axios = require('axios');

exports.handler = async function(event) {
    const team = event.request.intent.slots.team.value; // "49ers"
    
    // Query fast status API
    const response = await axios.get(
        `http://home-ingestor.local:8006/api/v1/ha/game-status/${team}`,
        { timeout: 500 }  // Must respond in <500ms for voice
    );
    
    const status = response.data;
    
    if (status.status === "no_game") {
        return {
            response: {
                outputSpeech: {
                    type: "PlainText",
                    text: `The ${team} are not playing right now.`
                }
            }
        };
    }
    
    return {
        response: {
            outputSpeech: {
                type: "PlainText",
                text: `The ${team} are ${status.is_winning ? "winning" : "losing"} 
                       ${status.score.team} to ${status.score.opponent} 
                       in the ${status.quarter} quarter.`
            }
        }
    };
};
```

**API Requirements**:
- Response time: <50ms (voice UX)
- Always available (even during HA restarts)
- Simple JSON format

---

## 🔍 **Admin API Endpoints**

### **Base URL**: `http://localhost:8003/api/v1`

## 🔍 **Health Endpoints**

### **GET /health**
Get overall system health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "services": {
      "websocket-ingestion": "healthy",
      "enrichment-pipeline": "healthy",
      "data-retention": "healthy",
      "admin-api": "healthy"
    }
  }
}
```

### **GET /services/health**
Get services health status (alias for /services).

**Response:**
```json
{
  "services": {
    "influxdb": {"status": "healthy", "uptime": "3m"},
    "websocket-ingestion": {"status": "healthy", "uptime": "2m"},
    "enrichment-pipeline": {"status": "healthy", "uptime": "2m"},
    "weather-api": {"status": "healthy", "uptime": "3m"},
    "data-retention": {"status": "healthy", "uptime": "3m"},
    "admin-api": {"status": "healthy", "uptime": "1m"}
  },
  "timestamp": "2025-01-05T18:20:00Z"
}
```

### **GET /dependencies/health**
Get dependencies health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "dependencies": {
      "influxdb": {
        "status": "healthy",
        "url": "http://influxdb:8086",
        "last_check": "2025-01-05T18:20:00Z",
        "response_time_ms": 5.2
      },
      "websocket-ingestion": {
        "status": "healthy", 
        "url": "http://websocket-ingestion:8001",
        "last_check": "2025-01-05T18:20:00Z",
        "response_time_ms": 3.1
      },
      "enrichment-pipeline": {
        "status": "healthy",
        "url": "http://enrichment-pipeline:8002", 
        "last_check": "2025-01-05T18:20:00Z",
        "response_time_ms": 2.8
      }
    },
    "overall_status": "healthy",
    "timestamp": "2025-01-05T18:20:00Z"
  }
}
```

### **GET /config**
Get system configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "version": "1.0.0",
      "environment": "production",
      "log_level": "INFO"
    },
    "services": {
      "influxdb": {
        "url": "http://influxdb:8086",
        "org": "ha-ingestor",
        "bucket": "home_assistant_events"
      },
      "websocket_ingestion": {
        "port": 8001,
        "enable_home_assistant": false
      },
      "enrichment_pipeline": {
        "port": 8002
      }
    },
    "features": {
      "weather_enrichment": true,
      "data_retention": true,
      "monitoring": true
    }
  }
}
```

### **GET /events/recent**
Get recent events (alias for /events).

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "event-1",
      "timestamp": "2025-01-05T18:20:00Z",
      "entity_id": "sensor.temperature",
      "event_type": "state_changed",
      "new_state": {"state": "22.5", "attributes": {"unit_of_measurement": "°C"}},
      "old_state": {"state": "22.3", "attributes": {"unit_of_measurement": "°C"}},
      "source": "websocket-ingestion"
    }
  ],
  "timestamp": "2025-01-05T18:20:00Z"
}
```

### **GET /health/{service}**
Get health status for a specific service.

**Parameters:**
- `service` (path): Service name (websocket-ingestion, enrichment-pipeline, data-retention, admin-api)

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "details": {
      "uptime": "2h 30m",
      "version": "1.0.0",
      "last_check": "2024-01-01T00:00:00Z"
    }
  }
}
```

## 📊 **Statistics Endpoints**

### **GET /stats**
Get system statistics and metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "events_processed": 1250,
    "events_per_minute": 45,
    "error_rate": 0.02,
    "uptime": "2h 30m",
    "services": {
      "websocket-ingestion": {
        "events_received": 1250,
        "connection_status": "connected",
        "last_event": "2024-01-01T00:00:00Z"
      },
      "enrichment-pipeline": {
        "events_processed": 1250,
        "weather_enrichments": 1200,
        "processing_latency_ms": 150
      }
    }
  }
}
```

## 🔧 **Configuration Endpoints**

### **GET /config**
Get current system configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "home_assistant": {
      "url": "ws://ha-instance:8123/api/websocket",
      "connected": true,
      "last_connection": "2024-01-01T00:00:00Z"
    },
    "weather_api": {
      "provider": "openweathermap",
      "location": "London,GB",
      "last_update": "2024-01-01T00:00:00Z"
    },
    "influxdb": {
      "url": "http://influxdb:8086",
      "connected": true,
      "database": "home_assistant"
    }
  }
}
```

### **PUT /config**
Update system configuration.

**Request Body:**
```json
{
  "home_assistant": {
    "url": "ws://new-ha-instance:8123/api/websocket",
    "access_token": "new-token"
  },
  "weather_api": {
    "api_key": "new-api-key",
    "location": "New York,US"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully"
}
```

## 📈 **Events Endpoints**

### **GET /events/recent**
Get recent events with optional filtering.

**Query Parameters:**
- `limit` (int): Number of events to return (default: 100, max: 1000)
- `entity_id` (string): Filter by entity ID
- `event_type` (string): Filter by event type
- `since` (string): ISO timestamp to filter events since

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "event_id": "event-123",
      "timestamp": "2024-01-01T00:00:00Z",
      "entity_id": "sensor.temperature",
      "event_type": "state_changed",
      "old_state": "20.5",
      "new_state": "21.0",
      "weather_context": {
        "temperature": 15.2,
        "humidity": 65,
        "condition": "clear"
      }
    }
  ]
}
```

### **GET /events/stats**
Get event statistics and metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_events": 1250,
    "events_today": 450,
    "events_this_hour": 45,
    "top_entities": [
      {"entity_id": "sensor.temperature", "count": 120},
      {"entity_id": "light.living_room", "count": 85}
    ],
    "event_types": {
      "state_changed": 1000,
      "service_called": 200,
      "automation_triggered": 50
    }
  }
}
```

## 🔍 **Monitoring Endpoints**

### **GET /monitoring/metrics/current**
Get current system metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "cpu_usage_percent": 45.2,
    "memory_usage_mb": 1024,
    "disk_usage_percent": 65.8,
    "network_io": {
      "bytes_sent": 1024000,
      "bytes_received": 2048000
    },
    "events_per_second": 0.75,
    "error_rate": 0.02
  }
}
```

### **GET /monitoring/logs**
Get recent log entries.

**Query Parameters:**
- `limit` (int): Number of log entries (default: 100)
- `level` (string): Filter by log level (DEBUG, INFO, WARNING, ERROR)
- `service` (string): Filter by service name

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "level": "INFO",
      "service": "websocket-ingestion",
      "component": "main",
      "message": "Event processed successfully",
      "event_id": "event-123",
      "entity_id": "sensor.temperature"
    }
  ]
}
```

### **GET /monitoring/alerts/active**
Get currently active alerts.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "alert_id": "alert-123",
      "alert_type": "high_cpu_usage",
      "severity": "warning",
      "message": "CPU usage is above 80%",
      "timestamp": "2024-01-01T00:00:00Z",
      "details": {
        "current_value": 85.2,
        "threshold": 80.0
      }
    }
  ]
}
```

## 🔧 **Alert Management Endpoints**

### **POST /monitoring/alerts/{alert_id}/acknowledge**
Acknowledge an active alert.

**Parameters:**
- `alert_id` (path): Alert identifier

**Response:**
```json
{
  "success": true,
  "message": "Alert acknowledged successfully"
}
```

### **POST /monitoring/alerts/{alert_id}/resolve**
Resolve an active alert.

**Parameters:**
- `alert_id` (path): Alert identifier

**Response:**
```json
{
  "success": true,
  "message": "Alert resolved successfully"
}
```

### **GET /monitoring/config/alert-rules**
Get configured alert rules.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "rule_name": "high_cpu_usage",
      "metric_name": "cpu_usage_percent",
      "threshold": 80.0,
      "severity": "warning",
      "enabled": true
    }
  ]
}
```

### **POST /monitoring/config/alert-rules**
Create a new alert rule.

**Request Body:**
```json
{
  "rule_name": "high_memory_usage",
  "metric_name": "memory_usage_mb",
  "threshold": 2048,
  "severity": "critical",
  "enabled": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Alert rule created successfully"
}
```

## 💾 **Backup and Restore Endpoints**

### **GET /backups**
Get list of available backups.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "backup_id": "backup-123",
      "backup_type": "full",
      "created_at": "2024-01-01T00:00:00Z",
      "size_mb": 1024,
      "status": "completed"
    }
  ]
}
```

### **POST /backup**
Create a new backup.

**Request Body:**
```json
{
  "backup_type": "full"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "backup_id": "backup-124",
    "status": "started"
  }
}
```

### **POST /restore**
Restore from a backup.

**Request Body:**
```json
{
  "backup_id": "backup-123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Restore started successfully"
}
```

## 📤 **Export Endpoints**

### **GET /monitoring/export/logs**
Export log data in various formats.

**Query Parameters:**
- `format` (string): Export format (json, csv, html)
- `limit` (int): Number of entries to export
- `since` (string): ISO timestamp to filter since

**Response:**
- **JSON**: Returns JSON array of log entries
- **CSV**: Returns CSV file download
- **HTML**: Returns HTML report

---

## 🔬 **Enrichment Pipeline API**

### **Base URL**: `http://localhost:8002`

The Enrichment Pipeline API provides endpoints for event processing, validation, normalization, and enrichment. It receives events from the WebSocket Ingestion Service, validates and normalizes them, and writes enriched data to InfluxDB.

### **GET /health**
Get enrichment pipeline service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "enrichment-pipeline",
  "uptime": "0:15:30.123456",
  "timestamp": "2025-10-13T02:30:00.000000",
  "is_running": true,
  "normalization": {
    "normalized_events": 1250,
    "normalization_errors": 2,
    "last_normalized_time": "2025-10-13T02:29:58.123456"
  },
  "validation": {
    "total_validations": 1252,
    "valid_count": 1250,
    "invalid_count": 2,
    "warning_count": 15
  },
  "influxdb": {
    "connected": true,
    "url": "http://influxdb:8086",
    "org": "ha-ingestor",
    "bucket": "home_assistant_events"
  }
}
```

### **POST /events**
Submit a single event for processing and enrichment.

**Request Body:**
```json
{
  "event_type": "state_changed",
  "timestamp": "2025-10-13T02:30:00.123456",
  "entity_id": "sensor.living_room_temperature",
  "domain": "sensor",
  "time_fired": "2025-10-13T02:30:00.123456",
  "origin": "LOCAL",
  "context": {
    "id": "abc123",
    "parent_id": null,
    "user_id": null
  },
  "old_state": {
    "state": "22.3",
    "attributes": {
      "unit_of_measurement": "°C",
      "friendly_name": "Living Room Temperature"
    },
    "last_changed": "2025-10-13T02:25:00.123456",
    "last_updated": "2025-10-13T02:29:55.123456"
  },
  "new_state": {
    "state": "22.5",
    "attributes": {
      "unit_of_measurement": "°C",
      "friendly_name": "Living Room Temperature"
    },
    "last_changed": "2025-10-13T02:30:00.123456",
    "last_updated": "2025-10-13T02:30:00.123456"
  },
  "state_change": {
    "from": "22.3",
    "to": "22.5",
    "changed": true
  },
  "weather": {
    "temperature": 15.2,
    "humidity": 65,
    "condition": "clear"
  },
  "weather_enriched": true,
  "weather_location": "Las Vegas, NV, US",
  "raw_data": {
    "event_type": "state_changed",
    "data": {
      "entity_id": "sensor.living_room_temperature",
      "old_state": {},
      "new_state": {}
    }
  }
}
```

**Response (Success):**
```json
{
  "status": "success",
  "event_id": "evt_abc123"
}
```

**Response (Failure):**
```json
{
  "status": "failed",
  "reason": "processing_failed"
}
```

**Status Codes:**
- `200 OK`: Event processed successfully
- `400 Bad Request`: Invalid event data or missing required fields
- `500 Internal Server Error`: Processing error occurred
- `503 Service Unavailable`: Service is not running

### **POST /process-event**
Alternative endpoint for processing a single event (alias for `/events`).

### **POST /process-events**
Submit multiple events for batch processing.

**Request Body:**
```json
{
  "events": [
    {
      "event_type": "state_changed",
      "entity_id": "sensor.temperature",
      ...
    },
    {
      "event_type": "state_changed",
      "entity_id": "sensor.humidity",
      ...
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "processed": 2,
  "failed": 0,
  "results": [
    {"event_id": "evt_1", "status": "success"},
    {"event_id": "evt_2", "status": "success"}
  ]
}
```

### **GET /status**
Get enrichment pipeline processing statistics and status.

**Response:**
```json
{
  "is_running": true,
  "start_time": "2025-10-13T02:00:00.000000",
  "uptime_seconds": 1800.5,
  "normalization": {
    "normalized_events": 1250,
    "normalization_errors": 2,
    "success_rate": 99.84
  },
  "validation": {
    "total_validations": 1252,
    "valid_count": 1250,
    "invalid_count": 2,
    "warning_count": 15,
    "validation_rate": 99.84
  },
  "influxdb_writes": {
    "total_writes": 1250,
    "successful_writes": 1248,
    "failed_writes": 2,
    "success_rate": 99.84
  }
}
```

### **Event Structure Requirements**

The Enrichment Pipeline expects events in a **flattened structure** where key fields are at the top level of the event object. This structure is produced by the WebSocket Ingestion Service's `EventProcessor`.

#### Required Fields:
- `event_type` (string): Type of event (e.g., "state_changed", "call_service")
- `entity_id` (string): Entity identifier in format `domain.object_id` (e.g., "sensor.temperature")
- `domain` (string): Home Assistant domain (e.g., "sensor", "light", "switch")

#### State Change Events - Required Fields:
- `new_state` (object): Current state information
  - `state` (string): The state value
  - `attributes` (object): State attributes
  - `last_changed` (string): ISO timestamp when state last changed
  - `last_updated` (string): ISO timestamp when state was last updated
- `old_state` (object): Previous state (same structure as new_state, may be null/empty)

#### Optional Fields:
- `timestamp` (string): Event processing timestamp
- `time_fired` (string): When the event was fired in Home Assistant
- `origin` (string): Event origin (e.g., "LOCAL", "REMOTE")
- `context` (object): Event context with id, parent_id, user_id
- `state_change` (object): State change summary with from, to, changed fields
- `weather` (object): Weather enrichment data
- `weather_enriched` (boolean): Whether weather data was added
- `weather_location` (string): Location used for weather data
- `raw_data` (object): Original Home Assistant event data

#### Validation Rules:
1. **Entity ID Format**: Must match pattern `domain.object_id` (e.g., `sensor.temperature`)
2. **Known Domains**: Warns if domain is not in the known domains list
3. **State Value**: Must not be null (empty string is allowed)
4. **Timestamps**: Should be valid ISO 8601 format
5. **Event Structure**: Top-level fields are validated, nested state objects are validated separately

#### Example Valid Event:
```json
{
  "event_type": "state_changed",
  "entity_id": "light.living_room",
  "domain": "light",
  "new_state": {
    "state": "on",
    "attributes": {
      "brightness": 255,
      "color_mode": "rgb"
    },
    "last_changed": "2025-10-13T02:30:00Z",
    "last_updated": "2025-10-13T02:30:00Z"
  },
  "old_state": {
    "state": "off",
    "attributes": {},
    "last_changed": "2025-10-13T02:25:00Z",
    "last_updated": "2025-10-13T02:25:00Z"
  }
}
```

#### Common Validation Errors:
- `Missing entity_id`: Event must include entity_id at top level
- `Invalid entity_id format`: Entity ID must match `domain.object_id` pattern
- `Missing required field in state`: State objects must include state, last_changed, last_updated
- `State value is None`: State value cannot be null

---

## 🗄️ **Data Retention API**

### **Base URL**: `http://localhost:8080`

The Data Retention API provides endpoints for managing data lifecycle, cleanup policies, and storage monitoring.

### **GET /health**
Get data retention service health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-05T18:20:00Z",
  "service_status": {
    "cleanup_service": true,
    "storage_monitor": true,
    "compression_service": true,
    "backup_service": true,
    "policy_count": 1
  }
}
```

### **GET /stats**
Get comprehensive service statistics.

**Response:**
```json
{
  "service_status": {
    "cleanup_service": true,
    "storage_monitor": true,
    "compression_service": true,
    "backup_service": true,
    "policy_count": 1
  },
  "policy_statistics": {
    "total_policies": 1,
    "enabled_policies": 1,
    "disabled_policies": 0
  }
}
```

### **GET /policies**
Get all retention policies.

**Response:**
```json
{
  "policies": [
    {
      "name": "default",
      "description": "Default 1-year retention policy",
      "retention_period": 1,
      "retention_unit": "years",
      "enabled": true,
      "created_at": "2025-01-05T18:20:00Z",
      "updated_at": "2025-01-05T18:20:00Z"
    }
  ]
}
```

### **POST /policies**
Add a new retention policy.

**Request Body:**
```json
{
  "name": "sensor_data",
  "description": "Retain sensor data for 6 months",
  "retention_period": 6,
  "retention_unit": "months",
  "enabled": true
}
```

### **POST /cleanup**
Run data cleanup for specific policy or all policies.

**Request Body:**
```json
{
  "policy_name": "sensor_data"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cleanup_results": [
      {
        "policy_name": "sensor_data",
        "records_deleted": 1500,
        "space_freed_mb": 25.6,
        "execution_time_ms": 1250
      }
    ]
  }
}
```

### **POST /backup**
Create a backup.

**Request Body:**
```json
{
  "backup_type": "full",
  "include_data": true,
  "include_config": true,
  "include_logs": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "backup_id": "backup-20250105-182000",
    "backup_type": "full",
    "size_mb": 1024,
    "created_at": "2025-01-05T18:20:00Z"
  }
}
```

### **GET /backups**
Get backup history.

**Response:**
```json
{
  "success": true,
  "data": {
    "backups": [
      {
        "backup_id": "backup-20250105-182000",
        "backup_type": "full",
        "size_mb": 1024,
        "created_at": "2025-01-05T18:20:00Z",
        "status": "completed"
      }
    ]
  }
}
```

### **GET /monitoring/export/metrics**
Export metrics data.

**Query Parameters:**
- `format` (string): Export format (json, csv)
- `time_range` (string): Time range (hour, day, week, month)

**Response:**
- **JSON**: Returns JSON object with metrics
- **CSV**: Returns CSV file download

## 🏈 **Sports Data Service API** (Epic 12)

### **Base URL**
```
http://localhost:8005/api/v1
```

**Purpose:** ESPN sports data with InfluxDB persistence, historical queries, and Home Assistant automation webhooks

**Features:**
- Real-time NFL/NHL game data
- 2-year historical data storage
- Team statistics and season records
- Event-driven webhooks (game_started, score_changed, game_ended)
- Fast HA automation endpoints (<50ms)

---

### **Real-Time Endpoints**

#### **GET /api/v1/games/live**
Get currently live games for selected teams.

**Query Parameters:**
- `league` (string, optional): "NFL" or "NHL"
- `team_ids` (string, optional): Comma-separated team IDs (e.g., "ne,sf,dal")

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
  ],
  "count": 1,
  "filtered_by_teams": ["ne", "kc"]
}
```

#### **GET /api/v1/games/upcoming**
Get upcoming games in next N hours.

**Query Parameters:**
- `league` (string, optional): "NFL" or "NHL"
- `hours` (int, default: 24): Hours to look ahead
- `team_ids` (string, optional): Comma-separated team IDs

---

### **Historical Query Endpoints** (Story 12.2)

#### **GET /api/v1/games/history**
Query historical games with filters.

**Query Parameters:**
- `sport` (string, default: "nfl"): "nfl" or "nhl"
- `team` (string, optional): Team name filter
- `season` (string, optional): Season year (e.g., "2025")
- `status` (string, optional): "scheduled", "live", or "finished"
- `page` (int, default: 1): Page number
- `page_size` (int, default: 100): Results per page (max 1000)

**Response:**
```json
{
  "games": [
    {
      "game_id": "401547402",
      "sport": "nfl",
      "season": "2025",
      "week": "5",
      "home_team": "Patriots",
      "away_team": "Chiefs",
      "home_score": 21,
      "away_score": 17,
      "status": "finished",
      "time": "2025-10-14T13:00:00Z"
    }
  ],
  "total": 16,
  "page": 1,
  "page_size": 100,
  "total_pages": 1
}
```

**Performance:** <100ms for typical queries (single season, single team)

#### **GET /api/v1/games/timeline/{game_id}**
Get score progression for a specific game.

**Path Parameters:**
- `game_id` (string, required): Unique game identifier

**Query Parameters:**
- `sport` (string, default: "nfl"): "nfl" or "nhl"

**Response:**
```json
{
  "game_id": "401547402",
  "home_team": "Patriots",
  "away_team": "Chiefs",
  "timeline": [
    {
      "time": "2025-10-14T13:00:00Z",
      "home_score": 0,
      "away_score": 0,
      "quarter": "1",
      "time_remaining": "15:00"
    },
    {
      "time": "2025-10-14T13:15:00Z",
      "home_score": 7,
      "away_score": 0,
      "quarter": "1",
      "time_remaining": "10:32"
    }
  ],
  "final_score": {"home": 21, "away": 17},
  "duration_minutes": 180
}
```

#### **GET /api/v1/games/schedule/{team}**
Get full season schedule for a team with statistics.

**Path Parameters:**
- `team` (string, required): Team name (e.g., "Patriots")

**Query Parameters:**
- `season` (string, required): Season year (e.g., "2025")
- `sport` (string, default: "nfl"): "nfl" or "nhl"

**Response:**
```json
{
  "team": "Patriots",
  "season": "2025",
  "games": [...],
  "statistics": {
    "games_played": 16,
    "wins": 12,
    "losses": 4,
    "ties": 0,
    "win_percentage": 0.750,
    "points_for": 384,
    "points_against": 312,
    "point_differential": 72
  }
}
```

---

### **Home Assistant Automation Endpoints** (Story 12.3)

#### **GET /api/v1/ha/game-status/{team}**
Quick game status check for HA automations.

**Path Parameters:**
- `team` (string, required): Team abbreviation (e.g., "ne", "sf")

**Query Parameters:**
- `sport` (string, default: "nfl"): "nfl" or "nhl"

**Response:**
```json
{
  "team": "ne",
  "status": "playing",  // "playing", "upcoming", or "none"
  "game_id": "401547402",
  "opponent": "kc",
  "start_time": "2025-10-14T13:00:00Z"
}
```

**Performance:** <50ms (optimized for automation conditionals)

**Use Case:** HA automation conditions
```yaml
condition:
  - condition: template
    value_template: "{{ states.sensor.patriots_status.state == 'playing' }}"
```

#### **GET /api/v1/ha/game-context/{team}**
Full game context for advanced automations.

**Path Parameters:**
- `team` (string, required): Team abbreviation

**Query Parameters:**
- `sport` (string, default: "nfl"): "nfl" or "nhl"

**Response:**
```json
{
  "team": "ne",
  "status": "playing",
  "current_game": {
    "id": "401547402",
    "score": {"home": 21, "away": 17},
    "quarter": 3,
    "time_remaining": "10:32"
  },
  "next_game": null
}
```

---

### **Webhook Management Endpoints** (Story 12.3)

#### **POST /api/v1/webhooks/register**
Register webhook for game event notifications.

**Request Body:**
```json
{
  "url": "http://homeassistant.local:8123/api/webhook/your_webhook_id",
  "events": ["game_started", "score_changed", "game_ended"],
  "secret": "your-secure-secret-min-16-chars",
  "team": "ne",
  "sport": "nfl"
}
```

**Response:**
```json
{
  "webhook_id": "uuid-generated-id",
  "url": "http://homeassistant.local:8123/api/webhook/your_webhook_id",
  "events": ["game_started", "score_changed", "game_ended"],
  "team": "ne",
  "message": "Webhook registered successfully"
}
```

**Webhook Payload (Delivered to your URL):**
```json
{
  "event": "score_changed",
  "event_type": "score_changed",
  "game_id": "401547402",
  "league": "NFL",
  "home_team": "ne",
  "away_team": "kc",
  "score": {"home": 21, "away": 17},
  "status": "live",
  "home_diff": 7,
  "away_diff": 0,
  "previous_score": {"home": 14, "away": 17},
  "timestamp": "2025-10-14T14:23:15Z"
}
```

**Webhook Headers:**
```
Content-Type: application/json
X-Webhook-Signature: hmac-sha256-signature
X-Webhook-Event: score_changed
X-Webhook-Timestamp: 2025-10-14T14:23:15Z
X-Webhook-ID: uuid-generated-id
User-Agent: SportsDataService/2.0
```

**HMAC Signature Verification:**
```python
import hmac
import hashlib

def verify_signature(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

**Event Types:**
- `game_started` - When game goes live
- `score_changed` - When score changes during game
- `game_ended` - When game becomes final

**Delivery:**
- Fire-and-forget (non-blocking)
- 3 retries with exponential backoff (1s, 2s, 4s)
- 5-second timeout
- HMAC-SHA256 signed

#### **GET /api/v1/webhooks/list**
List all registered webhooks.

**Response:**
```json
{
  "webhooks": [
    {
      "id": "uuid",
      "url": "http://homeassistant.local:8123/api/webhook/test",
      "events": ["game_started", "score_changed"],
      "secret": "***",  // Hidden for security
      "team": "ne",
      "created_at": "2025-10-14T17:20:15.464239",
      "total_calls": 42,
      "failed_calls": 0,
      "enabled": true
    }
  ]
}
```

#### **DELETE /api/v1/webhooks/{webhook_id}**
Unregister a webhook.

**Path Parameters:**
- `webhook_id` (string, required): Webhook identifier

**Response:** 204 No Content

---

### **Health Endpoint**

#### **GET /health**
Service health check with InfluxDB status (Story 12.1).

**Response:**
```json
{
  "status": "healthy",
  "service": "sports-data",
  "timestamp": "2025-10-14T17:14:41.858820",
  "cache_status": true,
  "api_status": true,
  "influxdb": {
    "enabled": true,
    "writes_success": 1234,
    "writes_failed": 0,
    "last_error": null,
    "circuit_breaker": "closed"
  }
}
```

---

### **Home Assistant Integration Example**

**Step 1: Register Webhook**
```bash
curl -X POST "http://localhost:8005/api/v1/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://homeassistant.local:8123/api/webhook/patriots_game",
    "events": ["game_started", "score_changed", "game_ended"],
    "secret": "your-secure-secret-min-16-chars",
    "team": "ne",
    "sport": "nfl"
  }'
```

**Step 2: Create HA Automation**
```yaml
automation:
  - alias: "Patriots Score - Flash Lights"
    trigger:
      - platform: webhook
        webhook_id: "patriots_game"
    condition:
      - "{{ trigger.json.event == 'score_changed' }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          flash: long
          rgb_color: [0, 32, 91]  # Patriots blue
```

**Step 3: Query Status in Automations**
```yaml
sensor:
  - platform: rest
    name: "Patriots Game Status"
    resource: http://localhost:8005/api/v1/ha/game-status/ne?sport=nfl
    scan_interval: 300
    value_template: "{{ value_json.status }}"
```

**Result:** ⚡ Lights flash when Patriots score! (11-16s latency)

---

### **Event Detection**

**Background Process:**
- Checks for game events every 15 seconds
- Compares current vs previous game state
- Triggers webhooks on state changes

**Events Detected:**
- Game status changes (scheduled → live → final)
- Score changes during live games
- Game start/end transitions

**Latency:** 11-16 seconds total
- ESPN API lag: ~10 seconds
- Detection check: 0-15 seconds
- Webhook delivery: ~1 second

---

## 🚨 **Error Responses**

### **400 Bad Request**
```json
{
  "success": false,
  "error": "bad_request",
  "message": "Invalid request parameters",
  "details": {
    "field": "limit",
    "issue": "Value must be between 1 and 1000"
  }
}
```

### **401 Unauthorized**
```json
{
  "success": false,
  "error": "unauthorized",
  "message": "Invalid or missing API key"
}
```

### **404 Not Found**
```json
{
  "success": false,
  "error": "not_found",
  "message": "Resource not found"
}
```

### **500 Internal Server Error**
```json
{
  "success": false,
  "error": "internal_error",
  "message": "An internal error occurred",
  "request_id": "req-123"
}
```

## 📋 **Rate Limiting**

API endpoints are rate-limited to prevent abuse:
- **General endpoints**: 100 requests per minute
- **Export endpoints**: 10 requests per minute
- **Configuration endpoints**: 20 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 🔗 **WebSocket API**

### **Connection**
```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/ws');
```

### **Authentication**
```javascript
ws.onopen = function() {
  ws.send(JSON.stringify({
    type: 'auth',
    api_key: 'your-api-key'
  }));
};
```

### **Subscribe to Events**
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'events'
}));
```

### **Event Messages**
```javascript
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'event') {
    console.log('New event:', data.event);
  }
};
```

---

**📚 This API documentation provides complete reference for all Home Assistant Ingestor endpoints!**
