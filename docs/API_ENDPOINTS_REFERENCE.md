# ⛔ SUPERSEDED - See API_REFERENCE.md

> **This document has been SUPERSEDED by [api/API_REFERENCE.md](api/API_REFERENCE.md)**  
> **Last Updated:** October 20, 2025  
> **Status:** Historical reference only - will be archived in next cleanup
> 
> **Please use:** [api/API_REFERENCE.md](api/API_REFERENCE.md) - Single source of truth for all API documentation

---

# API Endpoints Reference

## 🎯 **Overview**

This document provides a comprehensive reference for all API endpoints available in the HA Ingestor system. The system provides both individual service endpoints and a unified Admin API for centralized access.

---

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Admin API      │    │  Individual     │
│   (Frontend)    │◄──►│   (Port 8003)    │◄──►│  Services       │
│   (Port 3000)   │    │                  │    │  (Various)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

- **Dashboard**: Frontend React application with nginx proxy
- **Admin API**: Centralized API gateway aggregating all services
- **Individual Services**: Direct access to specific service endpoints

---

## 🌐 **Service Endpoints**

### WebSocket Ingestion Service
**Base URL:** `http://localhost:8001`

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "websocket-ingestion",
  "uptime": "0:05:23.123456",
  "timestamp": "2025-10-10T21:12:46.242617",
  "connection": {
    "is_running": true,
    "connection_attempts": 1,
    "successful_connections": 1,
    "failed_connections": 0
  },
  "subscription": {
    "is_subscribed": true,
    "active_subscriptions": 1,
    "total_events_received": 42,
    "events_by_type": {
      "state_changed": 42
    },
    "last_event_time": "2025-10-10T21:12:39.436996",
    "event_rate_per_minute": 16.28
  }
}
```

### Enrichment Pipeline Service
**Base URL:** `http://localhost:8002`

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "enrichment-pipeline",
  "uptime": "0:05:23.123456",
  "timestamp": "2025-10-10T21:12:46.242617"
}
```

### Data Retention Service
**Base URL:** `http://localhost:8080`

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "data-retention",
  "uptime": "0:05:23.123456",
  "timestamp": "2025-10-10T21:12:46.242617"
}
```

### Weather API Service
**Base URL:** Internal (no external access)

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "weather-api",
  "uptime": "0:05:23.123456",
  "timestamp": "2025-10-10T21:12:46.242617"
}
```

---

## 🔧 **Admin API Endpoints**

**Base URL:** `http://localhost:8003`

### Health Status (Simplified)
```http
GET /api/v1/health
```

**Description:** Simplified health endpoint used by the dashboard

**Response:**
```json
{
  "overall_status": "healthy",
  "admin_api_status": "healthy",
  "ingestion_service": {
    "status": "healthy",
    "websocket_connection": {
      "is_connected": true,
      "last_connection_time": "2025-10-10T21:19:09.413712",
      "connection_attempts": 1,
      "last_error": null
    },
    "event_processing": {
      "status": "healthy",
      "events_per_minute": 16.28,
      "total_events": 42,
      "error_rate": 0
    },
    "weather_enrichment": {
      "enabled": true,
      "cache_hits": 0,
      "api_calls": 0,
      "last_error": null
    },
    "influxdb_storage": {
      "is_connected": true,
      "last_write_time": "2025-10-10T21:19:09.413712",
      "write_errors": 0
    }
  },
  "timestamp": "2025-10-10T21:19:09.413712"
}
```

### Health Status (Comprehensive)
```http
GET /health
```

**Description:** Comprehensive health endpoint with detailed service information

**Response:**
```json
{
  "overall_status": "healthy",
  "admin_api_status": "healthy",
  "ingestion_service": {
    "status": "healthy",
    "websocket_connection": {
      "is_connected": true,
      "last_connection_time": "2025-10-10T21:19:09.413712",
      "connection_attempts": 1,
      "last_error": null
    },
    "event_processing": {
      "status": "healthy",
      "events_per_minute": 16.28,
      "last_event_time": "2025-10-10T21:12:39.436996",
      "processing_lag": 0,
      "total_events_received": 42
    },
    "weather_enrichment": {
      "enabled": true,
      "cache_hits": 0,
      "api_calls": 0,
      "last_error": null
    },
    "influxdb_storage": {
      "is_connected": true,
      "last_write_time": "2025-10-10T21:19:09.413712",
      "write_errors": 0
    },
    "timestamp": "2025-10-10T21:19:09.413712"
  },
  "timestamp": "2025-10-10T21:19:09.413712"
}
```

### Statistics
```http
GET /api/v1/stats?period={period}
```

**Parameters:**
- `period` (optional): Time period for statistics (`1h`, `24h`, `7d`, `30d`)

**Response:**
```json
{
  "timestamp": "2025-10-10T21:19:14.650353",
  "period": "1h",
  "metrics": {
    "total_events": 42,
    "events_per_minute": 16.28,
    "processing_time_avg": 0.123,
    "error_rate": 0
  },
  "trends": {
    "events_per_minute": {
      "current": 16.28,
      "previous": 15.42,
      "change_percent": 5.6
    }
  },
  "alerts": []
}
```

### Service Health Check
```http
GET /api/v1/services/health
```

**Description:** Check health of all individual services

**Response:**
```json
{
  "websocket-ingestion": {
    "status": "healthy",
    "response_time": 0.123,
    "health_data": {
      "status": "healthy",
      "service": "websocket-ingestion",
      "connection": {
        "is_running": true,
        "connection_attempts": 1
      },
      "subscription": {
        "is_subscribed": true,
        "total_events_received": 42
      }
    }
  },
  "enrichment-pipeline": {
    "status": "healthy",
    "response_time": 0.045
  },
  "influxdb": {
    "status": "healthy",
    "response_time": 0.089
  }
}
```

---

## 🎛️ **Dashboard API Endpoints**

**Base URL:** `http://localhost:3000` (via nginx proxy)

### Health Status
```http
GET /api/health
```

**Description:** Proxied to Admin API `/api/v1/health`

### Statistics
```http
GET /api/stats?period={period}
```

**Description:** Proxied to Admin API `/api/v1/stats`

---

## 🔍 **InfluxDB Endpoints**

**Base URL:** `http://localhost:8086`

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "name": "influxdb",
  "message": "ready for queries and writes",
  "status": "pass",
  "version": "2.7.1",
  "commit": "e1c7dd910f"
}
```

### Web Interface
```http
GET /
```

**Description:** InfluxDB web interface for data exploration

---

## 📊 **Response Status Codes**

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Endpoint not found |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | Proxy error (nginx) |
| 503 | Service Unavailable | Service temporarily unavailable |

### Health Status Values

| Status | Description |
|--------|-------------|
| `healthy` | Service operating normally |
| `degraded` | Service has issues but functional |
| `unhealthy` | Service not functioning properly |
| `unknown` | Status cannot be determined |

---

## 🔧 **Authentication**

### Home Assistant Token
Required for WebSocket connection:
```bash
# Set in environment
export HOME_ASSISTANT_TOKEN="your-long-lived-token"

# Or in .env file
HOME_ASSISTANT_TOKEN=your-long-lived-token
```

### InfluxDB Authentication
```bash
# Set in environment
export INFLUXDB_TOKEN="your-influxdb-token"
export INFLUXDB_ORG="your-org"
export INFLUXDB_BUCKET="your-bucket"
```

---

## 📝 **Usage Examples**

### Check System Health
```bash
# Check overall system health
curl http://localhost:8003/api/v1/health

# Check individual service
curl http://localhost:8001/health
```

### Get Statistics
```bash
# Get 1-hour statistics
curl "http://localhost:8003/api/v1/stats?period=1h"

# Get 24-hour statistics
curl "http://localhost:8003/api/v1/stats?period=24h"
```

### Monitor WebSocket Connection
```bash
# Check WebSocket service status
curl http://localhost:8001/health | jq '.connection'

# Check subscription status
curl http://localhost:8001/health | jq '.subscription'
```

### Test Dashboard API
```bash
# Test dashboard health endpoint
curl http://localhost:3000/api/health

# Test dashboard stats endpoint
curl "http://localhost:3000/api/stats?period=1h"
```

---

## 🚨 **Error Handling**

### Common Error Responses

#### Service Unavailable
```json
{
  "error": "Service unavailable",
  "message": "WebSocket service is not responding",
  "status_code": 503
}
```

#### Authentication Failed
```json
{
  "error": "Authentication failed",
  "message": "Invalid Home Assistant token",
  "status_code": 401
}
```

#### Invalid Parameters
```json
{
  "error": "Invalid parameters",
  "message": "Invalid period parameter. Must be one of: 1h, 24h, 7d, 30d",
  "status_code": 400
}
```

---

## 📋 **Monitoring & Alerts**

### Health Check Monitoring
```bash
# Monitor all services
watch -n 5 'curl -s http://localhost:8003/api/v1/health | jq'

# Monitor WebSocket specifically
watch -n 5 'curl -s http://localhost:8001/health | jq'
```

### Performance Monitoring
```bash
# Monitor event rate
watch -n 10 'curl -s http://localhost:8001/health | jq ".subscription.event_rate_per_minute"'

# Monitor connection status
watch -n 5 'curl -s http://localhost:8001/health | jq ".connection"'
```

---

## 📚 **Related Documentation**

- [WebSocket Troubleshooting Guide](WEBSOCKET_TROUBLESHOOTING.md)
- [Dashboard 502 Fix Summary](DASHBOARD_502_FIX_SUMMARY.md)
- [Docker Structure Guide](DOCKER_STRUCTURE_GUIDE.md)
- [Main README](README.md)
