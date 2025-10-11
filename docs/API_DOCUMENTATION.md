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
