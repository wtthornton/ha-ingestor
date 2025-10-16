# Changelog

All notable changes to the HA-Ingestor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-16

### Added - Epic AI-2: Device Intelligence System

#### New Features
- **Universal Device Capability Discovery** - Automatic detection of device features from Zigbee2MQTT (6,000+ device models supported)
- **Feature Utilization Analysis** - Calculates how much of device capabilities users actually use
- **Smart Feature Suggestions** - LLM-powered recommendations for unused features (LED notifications, power monitoring, etc.)
- **Unified Daily Batch Job** - Combined pattern detection + device intelligence in single efficient 3 AM job
- **Combined Suggestions** - Merges pattern-based and feature-based suggestions with unified ranking

#### New Components (Story 2.1-2.5)
- **Story 2.1:** `capability_parser.py` - Universal parser for Zigbee2MQTT device capabilities
- **Story 2.1:** `capability_batch.py` - Batch device capability update (replaces 24/7 listener)
- **Story 2.2:** `device_capabilities` table - Stores device model → features mapping
- **Story 2.2:** `device_feature_usage` table - Tracks configured vs available features per device
- **Story 2.3:** `feature_analyzer.py` - Analyzes device utilization and identifies opportunities
- **Story 2.4:** `feature_suggestion_generator.py` - Generates LLM-powered feature suggestions
- **Story 2.5:** Enhanced `daily_analysis.py` - 6-phase unified job (AI-1 + AI-2)

#### API Endpoints
- `GET /api/device-intelligence/utilization` - Device utilization metrics
- `GET /api/device-intelligence/opportunities` - Unused feature opportunities  
- `POST /api/device-intelligence/capabilities/refresh` - Manual capability refresh

#### Performance Improvements
- **99% Resource Reduction** - 2.5 hrs/month vs 730 hrs/month (batch vs real-time)
- **Shared Data Query** - Single InfluxDB fetch for both pattern detection and feature analysis
- **Optimized Architecture** - 1 unified service vs 2 separate services

#### Documentation
- 5 new story files (`story-ai2-*.md`)
- Architecture document (`architecture-device-intelligence.md`)
- 10+ implementation guides in `implementation/`
- Deployment guide (`DEPLOYMENT_STORY_AI2-5.md`)
- Quick reference (`QUICK_REFERENCE_AI2.md`)

### Changed

- **Daily Analysis Job** - Now runs 6 phases instead of 4 (added device capability update and feature analysis)
- **Suggestion Types** - Now generates both `pattern_automation` and `feature_discovery` suggestions
- **MQTT Notification** - Enhanced to include both Epic AI-1 and Epic AI-2 statistics
- **Health Endpoint** - Now includes device intelligence stats
- **Logging** - Unified format showing both pattern and feature analysis results

### Technical Details

- **Test Coverage:** 56/56 unit tests passing (100%)
- **Lines of Code:** ~3,500 new lines + 2,000 test lines
- **Database:** 2 new tables, 6 new CRUD operations
- **Alembic Migration:** `20251016_095206_add_device_intelligence_tables.py`
- **Docker Image:** Successfully built and tested

---

## [1.0.0] - 2025-01-XX

### Added - Epic AI-1: Pattern Automation

#### New Features
- **Time-of-Day Pattern Detection** - KMeans clustering to find consistent usage times
- **Co-Occurrence Detection** - Identifies devices frequently used together
- **Anomaly Detection** - Spots unusual manual interventions
- **LLM-Powered Suggestions** - OpenAI GPT-4o-mini generates automation YAML
- **Daily Scheduler** - Automatic analysis at 3 AM
- **MQTT Integration** - Notifications published to Home Assistant

#### Components (Story 1.1-1.9)
- `pattern_analyzer/time_of_day.py` - Time-of-day pattern detector
- `pattern_analyzer/co_occurrence.py` - Co-occurrence pattern detector
- `llm/openai_client.py` - OpenAI API integration
- `scheduler/daily_analysis.py` - Daily batch job scheduler
- `database/` - SQLite with Alembic migrations
- `api/` - RESTful API for suggestions and deployment

#### API Endpoints
- `GET /api/suggestions` - List automation suggestions
- `POST /api/deploy/{id}` - Deploy automation to Home Assistant
- `GET /api/patterns` - List detected patterns
- `POST /api/analysis/trigger` - Manual analysis trigger
- `GET /api/analysis/status` - Check analysis status

---

## [0.9.0] - 2025-01-XX

### Added - Epic 23: Enhanced Event Data Capture

- **Automation Tracing** - Track which automations triggered events
- **Spatial Analytics** - Enhanced area/floor tracking
- **Time Metrics** - Processing time and latency tracking
- **Device Reliability** - Event counts by manufacturer/model

---

## [0.8.0] - 2024-12-XX

### Added - Epic 22: Hybrid Database Architecture

- **SQLite Integration** - Metadata storage alongside InfluxDB
- **Direct HA → SQLite Storage** - Device and entity registry sync
- **5-10x Faster Queries** - Optimized query performance
- **Eliminated Sync Scripts** - Automated WebSocket-based sync

---

## [0.7.0] - 2024-11-XX

### Added - Data Enrichment Platform

- **Weather API Integration** - OpenWeatherMap data enrichment
- **Carbon Intensity Service** - UK carbon intensity data
- **Electricity Pricing Service** - Octopus Energy API integration
- **Air Quality Service** - Air quality index tracking
- **Calendar Service** - Google Calendar event correlation
- **Smart Meter Service** - Energy consumption tracking

---

## [0.6.0] - 2024-10-XX

### Added - Health Dashboard

- **React/TypeScript Dashboard** - System monitoring and health visualization
- **Real-time Metrics** - WebSocket connection status, event rates, service health
- **Device Management** - Device registry viewing and filtering
- **Performance Monitoring** - API latency, database performance, error rates

---

## [0.5.0] - 2024-09-XX

### Added - Core Infrastructure

- **WebSocket Ingestion** - Real-time Home Assistant event capture
- **InfluxDB Storage** - Time-series event storage
- **Data API** - RESTful API for historical queries
- **MQTT Integration** - Event-driven notification system
- **Docker Compose** - Multi-service orchestration

---

## Version History

- **2.0.0** (2025-10-16) - Epic AI-2: Device Intelligence System ✅
- **1.0.0** (2025-01-XX) - Epic AI-1: Pattern Automation ✅
- **0.9.0** (2025-01-XX) - Epic 23: Enhanced Event Data Capture ✅
- **0.8.0** (2024-12-XX) - Epic 22: Hybrid Database Architecture ✅
- **0.7.0** (2024-11-XX) - Data Enrichment Platform ✅
- **0.6.0** (2024-10-XX) - Health Dashboard ✅
- **0.5.0** (2024-09-XX) - Core Infrastructure ✅

---

## Notable Architectural Decisions

### Real-time → Batch Migration (v2.0.0)
**Decision:** Changed from 24/7 MQTT listener to daily batch query  
**Rationale:** Device capabilities are static metadata (change monthly), suggestions are batched daily  
**Impact:** 99% resource reduction (291x less uptime), same user experience  
**Documentation:** `implementation/REALTIME_VS_BATCH_ANALYSIS.md`

### Hybrid Database (v0.8.0)
**Decision:** Added SQLite alongside InfluxDB  
**Rationale:** Fast metadata queries, direct HA device registry sync  
**Impact:** 5-10x faster device/entity queries, eliminated manual sync scripts  

### Single-Tenant Architecture (v0.5.0)
**Decision:** Built for single-home deployment  
**Rationale:** Simplified design, no multi-tenancy complexity  
**Impact:** Lower resource usage, easier maintenance, focused feature set

