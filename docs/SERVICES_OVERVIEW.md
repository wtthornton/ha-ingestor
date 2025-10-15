# Services Overview - Home Assistant Ingestor

## 📋 Complete Service Reference

This document provides a comprehensive overview of all services in the Home Assistant Ingestor system.

---

## 🎯 Core Services

### 1. WebSocket Ingestion Service
**Port:** 8001 (external)  
**Technology:** Python 3.11, aiohttp  
**Purpose:** Home Assistant WebSocket client

**Key Features:**
- Real-time WebSocket connection to Home Assistant
- Automatic authentication and reconnection
- Event subscription management
- Health monitoring and metrics

**Health Check:** `http://localhost:8001/health`

**README:** [services/websocket-ingestion/README.md](../services/websocket-ingestion/README.md)

---

### 2. Enrichment Pipeline Service
**Port:** 8002 (external)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** Multi-source data enrichment and validation

**Key Features:**
- Event validation and normalization
- Multi-source data enrichment coordination
- Weather context integration
- Carbon intensity, pricing, air quality enrichment
- Calendar event correlation
- Smart meter data integration

**Health Check:** `http://localhost:8002/health`

**README:** [services/enrichment-pipeline/README.md](../services/enrichment-pipeline/README.md)

---

### 3. Data Retention Service (Enhanced)
**Port:** 8080 (external)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** Advanced data lifecycle management

**Key Features:**
- **Tiered Storage:** Hot/Warm/Cold retention with automatic downsampling
- **Materialized Views:** Pre-computed aggregations for fast queries
- **S3 Archival:** Automatic archival to Amazon S3/Glacier
- **Storage Analytics:** Comprehensive monitoring and optimization
- **Backup & Restore:** Automated backup with retention policies
- **Data Cleanup:** Intelligent data lifecycle management

**New Modules (October 2025):**
- `materialized_views.py` - Fast query performance
- `tiered_retention.py` - Hot/warm/cold storage management
- `s3_archival.py` - S3/Glacier integration
- `storage_analytics.py` - Storage monitoring and optimization
- `scheduler.py` - Automated task scheduling
- `retention_endpoints.py` - REST API endpoints

**Health Check:** `http://localhost:8080/health`

**API Documentation:** `http://localhost:8080/docs`

**README:** [services/data-retention/README.md](../services/data-retention/README.md)

---

### 4. Admin API Service
**Port:** 8003 (external)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** System administration and monitoring

**Key Features:**
- Centralized API gateway
- Health monitoring for all services
- Configuration management
- System metrics and statistics
- Event querying and filtering

**Health Check:** `http://localhost:8003/health`

**API Documentation:** `http://localhost:8003/docs`

**README:** [services/admin-api/README.md](../services/admin-api/README.md)

---

### 5. Health Dashboard
**Port:** 3000 (external)  
**Technology:** React 18.2, TypeScript, nginx  
**Purpose:** Web-based monitoring and administration

**Key Features:**
- Real-time system monitoring
- Service health visualization
- Event feed and filtering
- Configuration management
- Mobile-responsive design
- Dark/light theme support

**Access:** `http://localhost:3000`

**README:** [services/health-dashboard/README.md](../services/health-dashboard/README.md)

---

### 6. InfluxDB
**Port:** 8086 (external)  
**Technology:** InfluxDB 2.7  
**Purpose:** Time-series database

**Key Features:**
- High-performance time-series storage
- Tiered storage with downsampling
- Web UI for data exploration
- Flux query language support

**Web UI:** `http://localhost:8086`

---

## 🌐 External Data Services

### 7. Carbon Intensity Service (NEW)
**Port:** 8010 (internal only)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** Carbon intensity data integration

**Key Features:**
- Real-time carbon intensity data from National Grid
- Regional carbon metrics
- Renewable energy percentage
- Carbon footprint calculations

**Data Source:** National Grid ESO API

**README:** [services/carbon-intensity-service/README.md](../services/carbon-intensity-service/README.md)

---

### 8. Electricity Pricing Service (NEW)
**Port:** 8011 (internal only)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** Real-time electricity pricing

**Key Features:**
- Multi-provider support (Octopus Energy, Agile, etc.)
- Time-of-use tariff information
- Peak/off-peak pricing
- Cost optimization data

**Supported Providers:**
- Octopus Energy
- Agile tariffs
- Dynamic pricing schemes

**README:** [services/electricity-pricing-service/README.md](../services/electricity-pricing-service/README.md)

---

### 9. Air Quality Service (NEW)
**Port:** 8012 (internal only)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** Air quality monitoring

**Key Features:**
- Air quality index (AQI)
- Pollutant levels (PM2.5, PM10, NO2, O3, etc.)
- Health recommendations
- Government and OpenAQ data sources

**Data Sources:**
- OpenAQ
- Government air quality APIs

**README:** [services/air-quality-service/README.md](../services/air-quality-service/README.md)

---

### 10. Calendar Service (NEW)
**Port:** 8013 (internal only)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** Calendar integration

**Key Features:**
- Multi-calendar support (Google, Outlook, iCal)
- Event-based automation triggers
- Holiday and schedule tracking
- Event correlation with home automation

**Supported Calendars:**
- Google Calendar
- Microsoft Outlook
- iCal/CalDAV

**README:** [services/calendar-service/README.md](../services/calendar-service/README.md)

---

### 11. Smart Meter Service (NEW)
**Port:** 8014 (internal only)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** Smart meter data integration

**Key Features:**
- Real-time energy consumption data
- Multi-protocol support (SMETS2, P1, etc.)
- Cost calculations
- Usage analytics

**Supported Protocols:**
- SMETS2 (UK standard)
- P1 (Netherlands standard)
- Custom protocols

**README:** [services/smart-meter-service/README.md](../services/smart-meter-service/README.md)

---

### 12. Weather API Service
**Port:** Internal only  
**Technology:** Python 3.11, FastAPI  
**Purpose:** Weather data integration

**Key Features:**
- OpenWeatherMap API integration
- Location-based weather data
- Weather context for events
- Caching and rate limiting
- Integrated into websocket-ingestion service

**Data Source:** OpenWeatherMap

**README:** [services/weather-api/README.md](../services/weather-api/README.md)

---

### 13. Sports Data Service ⚡ NEW
**Port:** 8005 (external)  
**Technology:** Python 3.11, FastAPI  
**Purpose:** NFL & NHL sports data integration

**Key Features:**
- **FREE ESPN API** (no API key required)
- Team-based filtering (user selects favorite teams)
- Live game status with real-time updates
- Upcoming games (next 24-48 hours)
- Smart caching strategy:
  - Live games: 15-second TTL
  - Upcoming games: 5-minute TTL
- Dashboard integration with Setup Wizard
- API usage tracking and metrics

**Endpoints:**
- `/api/v1/games/live` - Get live games for selected teams
- `/api/v1/games/upcoming` - Get upcoming games
- `/api/v1/teams` - Get available teams (NFL & NHL)
- `/api/v1/user/teams` - Manage selected teams
- `/api/v1/metrics/api-usage` - Track API usage

**Health Check:** `http://localhost:8005/health`

**API Documentation:** `http://localhost:8005/docs`

**README:** [services/sports-data/README.md](../services/sports-data/README.md)

**Status:** ✅ Production Ready

---

### 14. Log Aggregator Service
**Port:** 8015 (external)  
**Technology:** Python 3.11  
**Purpose:** Centralized log aggregation

**Key Features:**
- Collects logs from all Docker containers
- JSON log parsing and aggregation
- Real-time log streaming
- Log search and filtering

**Health Check:** `http://localhost:8015/health`

**README:** [services/log-aggregator/README.md](../services/log-aggregator/README.md)

---

### 15. HA Simulator Service
**Port:** N/A (test utility)  
**Technology:** Python 3.11  
**Purpose:** Test event generator

**Key Features:**
- Simulates Home Assistant events
- Configurable event generation
- Used for testing and development
- YAML-based configuration

**README:** [services/ha-simulator/README.md](../services/ha-simulator/README.md)

---

## 📊 Service Statistics

### Core Services
- **Total:** 8 services (including sports-data and log-aggregator)
- **External Ports:** 8 services
- **Technology:** Python/FastAPI, React/TypeScript, InfluxDB
- **Container Size:** 40-80MB (Alpine-based)

### External Data Services
- **Total:** 6 services
- **All Internal:** Communication via internal Docker network
- **Technology:** Python/FastAPI
- **Container Size:** 40-45MB (Alpine-based)

### Overall System
- **Total Services:** 15 (14 microservices + InfluxDB)
- **Microservices:** Python (12), React (1), InfluxDB (1), Simulator (1)
- **Total Container Size:** ~600MB (71% reduction with Alpine)
- **Architecture:** Event-driven microservices

---

## 🔍 Service Dependencies

```
Home Assistant → WebSocket Ingestion → Enrichment Pipeline → InfluxDB
                        ↓                       ↑                    ↑
                  (Weather Enrichment)          |                    |
                                                |              Data Retention
                        ┌───────────────────────┴──────┐            ↓
                        │                              │        S3/Glacier
                External Data Services          Sports Data
                - Carbon Intensity              (ESPN API)
                - Electricity Pricing                  
                - Air Quality                          
                - Calendar                             
                - Smart Meter                          
                        │                              │
                        └──────────────┬───────────────┘
                                       ↓
                Admin API ← Health Dashboard (11 tabs)
                    ↑            ↑
              Log Aggregator  Sports Tab
```

---

## 📚 Additional Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference
- **[Docker Services Reference](DOCKER_COMPOSE_SERVICES_REFERENCE.md)** - Docker configuration details
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Architecture Documentation](architecture.md)** - System architecture
- **[User Manual](USER_MANUAL.md)** - User guide and configuration

---

**Last Updated:** October 2025  
**Version:** 4.0  
**Status:** Production Ready

