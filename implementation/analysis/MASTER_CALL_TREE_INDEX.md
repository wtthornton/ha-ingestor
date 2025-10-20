# Master Call Tree Documentation Index

**Project:** Home Assistant Ingestor  
**Last Updated:** October 20, 2025  
**Status:** ✅ Consolidated and validated against current architecture (Epic 31+)

---

## Overview

This is the master index for ALL call tree documentation in the Home Assistant Ingestor project. All documents have been validated against the current architecture after Epic 31 (enrichment-pipeline deprecation).

---

## 📚 Available Call Trees

### 1. Home Assistant Event Flow (Primary Data Path)

**Document:** [HA_EVENT_CALL_TREE.md](HA_EVENT_CALL_TREE.md)  
**Last Validated:** October 19, 2025 ✅

**Coverage:**
- Home Assistant WebSocket → websocket-ingestion
- Direct InfluxDB writes (Epic 31: enrichment-pipeline DEPRECATED)
- Device/entity discovery and storage
- Data-API query patterns
- Dashboard display

**Key Architecture (Epic 31 Update):**
```
Home Assistant WebSocket
        ↓
websocket-ingestion (Port 8001)
        ├─ Event processing
        ├─ Device/entity discovery
        └─ Batch processing
        ↓
InfluxDB (Direct Write - No enrichment-pipeline)
        ↓
data-api (Port 8006) - Queries
        ↓
health-dashboard (Port 3000) - Display
```

**Performance:**
- Throughput: 10,000+ events/second
- Latency: ~5-6s (batching), <100ms (direct)
- Batch size: 100 events
- Batch timeout: 5.0 seconds

---

### 2. AI Automation Subsystem (Daily 3 AM Job)

**Index:** [AI_AUTOMATION_CALL_TREE_INDEX.md](AI_AUTOMATION_CALL_TREE_INDEX.md)  
**Last Validated:** October 19, 2025 ✅

**Main Document:** [AI_AUTOMATION_CALL_TREE.md](AI_AUTOMATION_CALL_TREE.md)

**Phase Documents:**
1. [AI_AUTOMATION_MAIN_FLOW.md](AI_AUTOMATION_MAIN_FLOW.md) - Scheduler and execution
2. [AI_AUTOMATION_PHASE1_CAPABILITIES.md](AI_AUTOMATION_PHASE1_CAPABILITIES.md) - Device discovery
3. [AI_AUTOMATION_PHASE2_EVENTS.md](AI_AUTOMATION_PHASE2_EVENTS.md) - Historical events
4. [AI_AUTOMATION_PHASE3_PATTERNS.md](AI_AUTOMATION_PHASE3_PATTERNS.md) - Pattern detection
5. [AI_AUTOMATION_PHASE4_FEATURES.md](AI_AUTOMATION_PHASE4_FEATURES.md) - Feature analysis
6. [AI_AUTOMATION_PHASE5_OPENAI.md](AI_AUTOMATION_PHASE5_OPENAI.md) - OpenAI integration
7. [AI_AUTOMATION_PHASE5B_STORAGE.md](AI_AUTOMATION_PHASE5B_STORAGE.md) - Suggestion storage
8. [AI_AUTOMATION_PHASE6_MQTT.md](AI_AUTOMATION_PHASE6_MQTT.md) - MQTT notification

**Coverage:**
- Daily 3 AM automated analysis
- Device capability discovery
- Pattern detection algorithms
- OpenAI GPT-4o-mini integration
- Automation suggestion generation

**Performance:**
- Execution time: 2-4 minutes
- Cost: ~$0.50/year
- Output: ~10 suggestions/day

---

### 3. External API Integrations

**Document:** [EXTERNAL_API_CALL_TREES.md](EXTERNAL_API_CALL_TREES.md)

**Coverage:**
- Sports Data Service (ESPN API)
- Weather API Service  
- Carbon Intensity Service
- Air Quality Service
- Electricity Pricing Service
- Calendar Service
- Smart Meter Service

**Pattern:**
```
External API (ESPN, OpenWeatherMap, etc.)
        ↓
Service (sports-data, weather-api, etc.)
        ↓
InfluxDB (time-series storage)
        ↓
data-api (query endpoint)
        ↓
Dashboard (display)
```

---

### 4. Complete Data Flow Analysis

**Document:** [COMPLETE_DATA_FLOW_CALL_TREE.md](COMPLETE_DATA_FLOW_CALL_TREE.md)  
**Last Validated:** October 19, 2025 ✅

**Coverage:**
- All service integrations
- All database paths
- Epic 22: Hybrid database architecture (InfluxDB + SQLite)
- Epic 23: Analytics enhancements
- Complete system flow diagrams

---

### 5. Data Flow Call Tree (Alternative View)

**Document:** [DATA_FLOW_CALL_TREE.md](DATA_FLOW_CALL_TREE.md)

**Coverage:**
- Data flow patterns
- Service-to-service communication
- Database interaction patterns

---

## 🔍 Quick Navigation

### By Use Case

**"How does a Home Assistant event reach InfluxDB?"**
→ [HA_EVENT_CALL_TREE.md](HA_EVENT_CALL_TREE.md)

**"How does the 3 AM AI job work?"**
→ [AI_AUTOMATION_CALL_TREE_INDEX.md](AI_AUTOMATION_CALL_TREE_INDEX.md)

**"How do sports scores get into the system?"**
→ [EXTERNAL_API_CALL_TREES.md](EXTERNAL_API_CALL_TREES.md) → Sports Data Service

**"How does weather data flow?"**
→ [EXTERNAL_API_CALL_TREES.md](EXTERNAL_API_CALL_TREES.md) → Weather API Service

**"Where is enrichment-pipeline?"**
→ **DEPRECATED in Epic 31** - Events go directly to InfluxDB from websocket-ingestion

### By Technology

**InfluxDB (Time-Series):**
- [HA_EVENT_CALL_TREE.md](HA_EVENT_CALL_TREE.md) - Event writes
- [AI_AUTOMATION_PHASE2_EVENTS.md](AI_AUTOMATION_PHASE2_EVENTS.md) - Historical queries
- [EXTERNAL_API_CALL_TREES.md](EXTERNAL_API_CALL_TREES.md) - External data writes

**SQLite (Metadata):**
- [HA_EVENT_CALL_TREE.md](HA_EVENT_CALL_TREE.md) - Device/entity storage
- [AI_AUTOMATION_PHASE5B_STORAGE.md](AI_AUTOMATION_PHASE5B_STORAGE.md) - Suggestions table
- [EXTERNAL_API_CALL_TREES.md](EXTERNAL_API_CALL_TREES.md) - Sports webhooks

**OpenAI GPT-4o-mini:**
- [AI_AUTOMATION_PHASE5_OPENAI.md](AI_AUTOMATION_PHASE5_OPENAI.md)

**WebSocket:**
- [HA_EVENT_CALL_TREE.md](HA_EVENT_CALL_TREE.md) - HA connection

---

## 🏗️ Architecture Evolution

### Epic 31: Enrichment Pipeline Deprecation (October 2025)

**BEFORE Epic 31:**
```
HA → websocket-ingestion → enrichment-pipeline → InfluxDB
```

**AFTER Epic 31 (CURRENT):**
```
HA → websocket-ingestion → InfluxDB (direct write)
```

**Rationale:**
- Simplified architecture
- Reduced latency
- Fewer failure points
- External services (weather, etc.) consume from InfluxDB

**Affected Services:**
- ✅ **websocket-ingestion** - Now writes directly to InfluxDB
- ❌ **enrichment-pipeline** - DEPRECATED (service still exists for legacy support but not used)
- ✅ **weather-api** - Standalone service, queries InfluxDB for weather domain entities
- ✅ **External APIs** - All consume from InfluxDB

---

## 📊 Documentation Statistics

| Subsystem | Documents | Status | Lines |
|-----------|-----------|--------|-------|
| HA Event Flow | 1 | ✅ Validated | ~1,300 |
| AI Automation | 9 | ✅ Validated | ~2,800 |
| External APIs | 1 | Current | ~800 |
| Complete Data Flow | 1 | ✅ Validated | ~1,200 |
| Data Flow (Alt) | 1 | Current | ~600 |
| **Total** | **13** | **✅ Complete** | **~6,700** |

---

## 🔄 Maintenance

### Update Triggers

**Update call trees when:**
- Service architecture changes (like Epic 31)
- New services added
- Database schema changes
- Major epics completed (AI-1, AI-2, etc.)
- Performance characteristics change

### Validation Schedule

**Quarterly validation recommended:**
- Verify function names and signatures
- Check line numbers (±drift expected)
- Validate architecture diagrams
- Update performance metrics

**Last Validation:** October 19, 2025

---

## 🚫 Deprecated Documentation (Do Not Use)

The following concepts are **NO LONGER VALID** as of Epic 31:

| Concept | Status | Replacement |
|---------|--------|-------------|
| enrichment-pipeline service | ❌ DEPRECATED | websocket-ingestion writes directly to InfluxDB |
| HTTP POST to enrichment | ❌ REMOVED | Direct InfluxDB writes |
| Enrichment normalization | ❌ REMOVED | Inline normalization in websocket-ingestion |
| Weather enrichment in websocket | ❌ DEPRECATED | weather-api standalone service |

---

## Related Architecture Documentation

- **[Tech Stack](../../docs/architecture/tech-stack.md)** - Technology choices
- **[Source Tree](../../docs/architecture/source-tree.md)** - File organization
- **[Event Flow Architecture](../../docs/architecture/event-flow-architecture.md)** - High-level flow
- **[Database Schema](../../docs/architecture/database-schema.md)** - InfluxDB + SQLite schemas

---

**Last Updated:** October 20, 2025  
**Validation Status:** ✅ All call trees validated against Epic 31+ architecture  
**Total Coverage:** 13 documents, ~6,700 lines, 100% of system flows

---

**END OF MASTER CALL TREE INDEX**

