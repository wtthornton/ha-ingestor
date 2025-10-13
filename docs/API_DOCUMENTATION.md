# 📚 Home Assistant Ingestor - API Documentation

## 🌐 **API Overview**

### **Base URLs**

**Core Services**

**Admin API (Primary)**
```
http://localhost:8003/api/v1
```

**Data Retention API**
```
http://localhost:8080
```

**Enrichment Pipeline API**
```
http://localhost:8002
```

**WebSocket Ingestion API**
```
http://localhost:8001
```

**External Data Services (Internal)**
- Carbon Intensity Service: `http://carbon-intensity-service:8010` (internal only)
- Electricity Pricing Service: `http://electricity-pricing-service:8011` (internal only)
- Air Quality Service: `http://air-quality-service:8012` (internal only)
- Calendar Service: `http://calendar-service:8013` (internal only)
- Smart Meter Service: `http://smart-meter-service:8014` (internal only)
- Weather API Service: `http://weather-api:8000` (internal only)

### **Authentication**
All API endpoints require authentication using an API key:
```bash
Authorization: Bearer <your-api-key>
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
