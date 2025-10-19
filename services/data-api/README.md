# Data API Service

**Feature Data Hub for Home Assistant Ingestor**

FastAPI microservice providing access to feature data including HA events, devices, sports data, analytics, and Home Assistant automation integration.

---

## 📊 Overview

The Data API service is a specialized microservice that handles all feature-related data access, separated from system monitoring (admin-api). It provides:

- HA event queries from InfluxDB
- Device and entity browsing (SQLite metadata storage)
- Integration management
- Alert management
- Analytics and metrics queries
- Sports data (historical and real-time)
- Home Assistant automation endpoints
- Real-time WebSocket streaming

**Database Architecture (Story 22.1-22.2):**
- **InfluxDB**: Time-series data (events, metrics, sports scores)
- **SQLite**: Metadata (devices, entities, webhooks, preferences)
  - Devices table with indexes on area_id, manufacturer, integration
  - Entities table with foreign key to devices
  - Fast queries (<10ms vs ~50ms with InfluxDB)

---

## 🚀 Quick Start

### Development

```bash
# Install dependencies
cd services/data-api
pip install -r requirements.txt

# Run service
python -m uvicorn src.main:app --reload --port 8006
```

### Docker

```bash
# Build
docker build -t homeiq-data-api -f services/data-api/Dockerfile .

# Run
docker run -p 8006:8006 --env-file .env homeiq-data-api
```

### Docker Compose

```bash
# Start with all services
docker-compose up data-api

# Or start entire stack
docker-compose up
```

---

## 🔌 API Endpoints

### Health & Status
```
GET /health                    # Service health check
GET /api/info                  # API information
```

### Events (Story 13.2)
```
GET /api/v1/events             # Query HA events
GET /api/v1/events/{id}        # Get specific event
POST /api/v1/events/search     # Search events
GET /api/v1/events/stats       # Event statistics
```

### Devices & Entities (Story 13.2 + Epic 22)
```
GET /api/devices               # List devices (SQLite)
GET /api/devices/{id}          # Device details (SQLite)
GET /api/entities              # List entities (SQLite)
GET /api/entities/{id}         # Entity details (SQLite)
GET /api/integrations          # List integrations (InfluxDB)
```

### Internal Endpoints (October 2025)
```
POST /internal/devices/bulk_upsert   # Bulk upsert devices (called by websocket-ingestion)
POST /internal/entities/bulk_upsert  # Bulk upsert entities (called by websocket-ingestion)
```

**Purpose**: Allow websocket-ingestion to store discovered devices/entities directly to SQLite without manual sync.

### Sports Data (Story 13.4 - Epic 12)
```
GET /api/v1/sports/games/live      # Live games
GET /api/v1/sports/games/history   # Historical games
GET /api/v1/sports/schedule/{team} # Team schedule
```

### Home Assistant Automation (Story 13.4 - Epic 12)
```
GET /api/v1/ha/game-status/{team}   # Quick game status (<50ms)
GET /api/v1/ha/game-context/{team}  # Rich game context
POST /api/v1/ha/webhooks/register   # Register webhook
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATA_API_HOST` | Host address | `0.0.0.0` |
| `DATA_API_PORT` | Service port | `8006` |
| `INFLUXDB_URL` | InfluxDB URL | `http://influxdb:8086` |
| `INFLUXDB_TOKEN` | InfluxDB auth token | Required |
| `INFLUXDB_ORG` | InfluxDB organization | `homeiq` |
| `INFLUXDB_BUCKET` | InfluxDB bucket | `home_assistant_events` |
| `DATABASE_URL` | SQLite database URL | `sqlite+aiosqlite:///./data/metadata.db` |
| `SQLITE_TIMEOUT` | Connection timeout (seconds) | `30` |
| `SQLITE_CACHE_SIZE` | Cache size (KB, negative) | `-64000` (64MB) |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENABLE_AUTH` | Enable API authentication | `false` |
| `API_KEY` | API key (if auth enabled) | - |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

### Example `.env` File

```bash
# Data API Configuration
DATA_API_PORT=8006
ENABLE_AUTH=false

# InfluxDB Configuration
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-token-here
INFLUXDB_ORG=homeiq
INFLUXDB_BUCKET=home_assistant_events

# SQLite Configuration (Story 22.1)
DATABASE_URL=sqlite+aiosqlite:///./data/metadata.db
SQLITE_TIMEOUT=30
SQLITE_CACHE_SIZE=-64000

# Logging
LOG_LEVEL=INFO
```

---

## 🧪 Testing

```bash
# Run all tests
pytest services/data-api/tests/

# Run with coverage
pytest services/data-api/tests/ --cov=src --cov-report=html

# Run specific test file
pytest services/data-api/tests/test_main.py -v
```

---

## 🏗️ Architecture

### Service Separation

The HA Ingestor system uses two API services:

**admin-api** (port 8003): System monitoring & control
- Health checks
- Docker management
- System configuration
- System statistics

**data-api** (port 8006): Feature data hub ← THIS SERVICE
- HA event queries
- Device/entity browsing
- Sports data
- Analytics
- HA automation integration

### Data Flow (Updated October 2025)

```
┌─────────────────────┐
│ Home Assistant      │
│ @ 192.168.1.86:8123 │
└──────────┬──────────┘
           │
           │ WebSocket Discovery (on connect)
           ↓
┌───────────────────────────┐
│ websocket-ingestion       │
│ POST /internal/bulk_upsert│
└──────────┬────────────────┘
           │
           ↓
┌───────────────────────────┐
│ Data API (8006)           │
│                           │
│ ┌─────────┐ ┌──────────┐ │
│ │ SQLite  │ │ InfluxDB │ │
│ │Metadata │ │Time-Series│ │
│ └─────────┘ └──────────┘ │
└──────────┬────────────────┘
           │
           ↓
┌───────────────────────────┐
│ Dashboard (3000)          │
│ HA Automation Triggers    │
└───────────────────────────┘
```

### Database Access

**SQLite (Primary for Metadata)**:
- `devices` - Device registry (99 devices, <10ms queries)
- `entities` - Entity registry (100+ entities, <10ms queries)
- `webhooks` - Webhook registrations

**InfluxDB (Time-Series Data)**:
- `home_assistant_events` - HA state changes
- `nfl_scores`, `nhl_scores` - Sports data
- `air_quality`, `carbon_intensity` - Environmental data
- `smart_meter` - Power consumption
- And all other measurements

---

## 📈 Performance

**Response Time Targets**:
- Health check: <20ms
- Event queries: <200ms (p95)
- Device queries: <100ms (p95)
- HA automation endpoints: <50ms (p95)

**Resource Usage**:
- Memory: 256-512 MB
- CPU: 0.5-1.0 cores
- Disk: <100 MB

**Scaling**:
- Can scale horizontally (2-4 instances)
- InfluxDB connection pooling (max 10 connections)
- Query result caching (5-minute TTL)

---

## 🔐 Security

### Authentication

Authentication is **optional** for data-api (default: disabled).

Enable with:
```bash
ENABLE_AUTH=true
API_KEY=your-secret-api-key
```

### API Key Usage

```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8006/api/v1/events
```

---

## 🛠️ Development

### Project Structure

```
services/data-api/
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── events_endpoints.py      # Event queries (Story 13.2)
│   ├── devices_endpoints.py     # Device browsing (Story 13.2)
│   ├── sports_endpoints.py      # Sports data (Story 13.4)
│   └── ha_automation_endpoints.py  # HA automation (Story 13.4)
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── Dockerfile                   # Production image
├── Dockerfile.dev               # Development image
├── requirements.txt             # Dependencies
├── requirements-prod.txt        # Pinned production deps
└── README.md                    # This file
```

### Adding New Endpoints

Follow the FastAPI router pattern:

```python
# src/my_endpoints.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/my-endpoint")
async def my_endpoint():
    return {"data": "..."}

# src/main.py
from .my_endpoints import router as my_router
app.include_router(my_router, tags=["My Feature"])
```

---

## 📚 Related Documentation

- [Epic 13: Admin API Service Separation](../../docs/stories/epic-13-admin-api-service-separation.md)
- [Admin API Separation Analysis](../../implementation/analysis/ADMIN_API_SEPARATION_ANALYSIS.md)
- [Architecture Overview](../../docs/architecture.md)
- [Tech Stack](../../docs/architecture/tech-stack.md)
- [API Documentation](../../docs/API_DOCUMENTATION.md)

---

## 🔍 Troubleshooting

### Service won't start

**Check InfluxDB connection**:
```bash
curl http://localhost:8086/health
```

**Check logs**:
```bash
docker logs homeiq-data-api
```

### Queries are slow

**Check InfluxDB performance**:
```bash
curl http://localhost:8006/health
# Look at avg_query_time_ms
```

**Enable query logging**:
```bash
LOG_LEVEL=DEBUG
```

### Dashboard can't connect

**Verify nginx routing**:
```bash
docker logs homeiq-dashboard
```

**Test endpoint directly**:
```bash
curl http://localhost:8006/health
```

---

## 📝 Status

**Current Implementation** (Story 13.1): ✅ COMPLETE
- [x] Service foundation created
- [x] Docker configuration
- [x] Health endpoint
- [x] InfluxDB client
- [x] Basic testing

**Next Steps** (Story 13.2):
- [ ] Migrate events endpoints
- [ ] Migrate devices endpoints
- [ ] Update dashboard

---

**Service Version**: 1.0.0  
**Created**: 2025-10-13  
**Part of**: Epic 13 - Admin API Service Separation  
**Status**: Foundation Complete, Feature Migration In Progress

