# Epic 31: Weather API Service Migration - Brownfield Enhancement

## Epic Goal

Migrate weather data integration from event enrichment pattern to standalone external API service pattern, achieving architectural consistency with all other external data sources (sports, carbon intensity, electricity pricing, air quality) and eliminating coupling between weather API and event processing pipeline.

## Epic Description

### Existing System Context

**Current Implementation:**
- Weather data is embedded into Home Assistant events during enrichment
- Weather client integrated into websocket-ingestion service (Port 8001)
- Weather data stored as fields in `home_assistant_events` InfluxDB measurement
- Separate `weather_data` InfluxDB bucket exists but underutilized
- No direct API endpoint to query current weather conditions
- Weather API failures can slow down entire event processing pipeline

**Technology Stack:**
- Python 3.11 with asyncio
- OpenWeatherMap API for weather data
- InfluxDB 2.7 for time-series storage
- FastAPI for service APIs
- aiohttp for async HTTP operations
- Docker Compose orchestration

**Integration Points:**
- websocket-ingestion service (currently embeds weather)
- enrichment-pipeline service (currently processes embedded weather)
- InfluxDB (home_assistant_events and weather_data buckets)
- Health dashboard (needs to query weather independently)

**Architectural Inconsistency:**
Weather is the ONLY external data source using event enrichment. All others use standalone API services:
- **sports-data** (Port 8005) - ESPN API integration
- **carbon-intensity-service** (Port 8010) - WattTime API
- **electricity-pricing-service** (Port 8011) - Awattar API  
- **air-quality-service** (Port 8012) - AirNow API

### Enhancement Details

**What's Being Added/Changed:**

1. **New weather-api Service (Port 8009)**
   - Standalone FastAPI service following sports-data pattern
   - REST API endpoints: `/current-weather`, `/forecast`, `/historical`
   - Independent caching layer (15-minute TTL)
   - Health check and metrics endpoints
   - InfluxDB writer (weather_data measurement only)

2. **Event Pipeline Decoupling**
   - Remove weather enrichment from websocket-ingestion
   - Remove weather fields from home_assistant_events schema
   - Update queries to use time-window JOINs when weather correlation needed

3. **Dashboard Updates**
   - Add weather API client to frontend
   - Update analytics queries for weather correlation

**How It Integrates:**

```
OLD FLOW (Event Enrichment):
HA Event → websocket-ingestion → weather_client.py → Enrich Event → InfluxDB

NEW FLOW (External API):
HA Event → websocket-ingestion → InfluxDB (no weather)
                                          
weather-api (Port 8009) → OpenWeatherMap → Cache → InfluxDB (weather_data)
                        ↓
                   Dashboard queries directly
```

**Success Criteria:**

- [ ] weather-api service running on Port 8009 with 100% uptime
- [ ] All external data services follow same architectural pattern
- [ ] Weather API calls reduced by 80% (better caching)
- [ ] Event processing 30% faster (no weather API blocking)
- [ ] Dashboard can query current weather in <100ms
- [ ] Historical events retain existing embedded weather data (no migration)
- [ ] Weather correlation queries achieve 95% accuracy with 5-minute time windows

### Stories

**5 focused stories to complete migration:**

1. **Story 31.1:** Weather API Service Foundation
   - Create FastAPI service skeleton following sports-data template
   - Implement health check, metrics, and basic endpoints
   - Configure Docker deployment on Port 8009

2. **Story 31.2:** Weather Data Collection & InfluxDB Persistence
   - Migrate OpenWeatherMap client from websocket-ingestion
   - Implement caching layer with 15-minute TTL
   - Write weather data to InfluxDB weather_data measurement
   - Add continuous background fetch loop

3. **Story 31.3:** Weather API Endpoints & Query Support
   - Implement GET /current-weather endpoint
   - Implement GET /forecast endpoint (24-hour)
   - Implement GET /historical endpoint (time-range queries)
   - Add cache statistics endpoint

4. **Story 31.4:** Event Pipeline Decoupling
   - Remove weather enrichment from websocket-ingestion service
   - Update enrichment-pipeline to skip weather processing
   - Preserve schema compatibility for historical queries
   - Add deprecation notices in code

5. **Story 31.5:** Dashboard & Query Integration
   - Add weather API client to health dashboard
   - Update analytics queries with time-window JOINs
   - Add weather widget to Data Sources tab
   - Update documentation and architecture diagrams

### Compatibility Requirements

- [x] Existing APIs remain unchanged (no breaking changes)
- [x] Database schema changes are backward compatible (historical data preserved)
- [x] UI changes follow existing patterns (sports-data widget pattern)
- [x] Performance impact is positive (30% faster event processing)
- [x] Historical queries continue to work (COALESCE handles old/new schema)

### Risk Mitigation

**Primary Risk:** Loss of exact temporal correlation between events and weather

**Mitigation Strategies:**
1. Use 5-minute time windows for JOIN queries (95% accuracy maintained)
2. Implement continuous background weather fetch (every 5 minutes)
3. Cache weather data with 15-minute TTL (balance freshness vs API usage)
4. Preserve historical embedded weather data (no data loss)
5. Test queries extensively before production deployment

**Rollback Plan:**
1. Keep weather enrichment code in separate branch
2. Feature flag to re-enable enrichment if needed
3. Can revert Docker Compose to previous version in <5 minutes
4. Historical data unaffected (rollback is non-destructive)

**Secondary Risks:**
- **Dashboard dependency:** Mitigate with loading states and error handling
- **API rate limits:** Mitigate with longer cache TTL (15 min → 30 min if needed)
- **Query complexity:** Provide query templates and documentation

### Definition of Done

- [ ] All 5 stories completed with acceptance criteria met
- [ ] weather-api service deployed and healthy (Port 8009)
- [ ] Event processing pipeline decoupled from weather
- [ ] Dashboard updated with weather API integration
- [ ] All existing weather correlation queries working
- [ ] Integration points verified (InfluxDB, Docker Compose)
- [ ] No regression in existing features (event processing, dashboards)
- [ ] Documentation updated (architecture diagrams, API docs)
- [ ] Performance benchmarks show 30% improvement
- [ ] Code review completed with architecture team approval

### Technical Notes

**Context7 Verification:**
- FastAPI lifespan context managers validated ✅
- InfluxDB3 Python client patterns validated ✅
- Caching with LRU and TTL patterns validated ✅
- Dependency injection with `yield` validated ✅
- Health check endpoint patterns validated ✅

**Reference Implementations:**
- `services/sports-data/src/main.py` - FastAPI service template
- `services/carbon-intensity-service/src/main.py` - External API pattern
- `services/air-quality-service/src/main.py` - InfluxDB writer pattern

**Performance Targets:**
- Weather API response time: <100ms (cached)
- Weather API response time: <2s (fresh fetch)
- Event processing speedup: 30% (remove weather blocking)
- API call reduction: 80% (better caching)

### Dependencies

**Hard Dependencies:**
- Epic 13 (Admin API Service Separation) - ✅ Complete
- Epic 22 (SQLite Metadata Storage) - ✅ Complete
- Docker Compose infrastructure - ✅ Exists

**Soft Dependencies:**
- Health Dashboard (Epic 5) - ✅ Complete (needs updates)
- InfluxDB schema (Epic 3) - ✅ Complete (weather_data bucket exists)

### Estimated Effort

**Total**: 3-4 weeks (120-160 hours)

**Story Breakdown:**
- Story 31.1: 1 week (40 hours) - Service foundation, Docker, health checks
- Story 31.2: 1 week (40 hours) - Weather client migration, InfluxDB integration
- Story 31.3: 4-5 days (32-40 hours) - API endpoints, query support
- Story 31.4: 2-3 days (16-24 hours) - Pipeline decoupling, testing
- Story 31.5: 2-3 days (16-24 hours) - Dashboard integration, documentation

**Risk Buffer:** +1 week (20%) for unforeseen issues

### Success Metrics

**Quantitative:**
- Event processing latency: Reduced by 30%
- Weather API calls: Reduced by 80%
- Weather query response time: <100ms (95th percentile)
- API uptime: >99.9%
- Cache hit rate: >85%

**Qualitative:**
- Architectural consistency achieved (all external APIs follow same pattern)
- Easier to add weather features (forecasts, alerts)
- Better developer experience (clear separation of concerns)
- Improved maintainability (independent scaling, testing)

### Validation Checklist

**Scope Validation:**
- [x] Epic can be completed in 5 stories
- [x] Architectural changes are well-defined
- [x] Enhancement follows existing patterns (sports-data template)
- [x] Integration complexity is manageable

**Risk Assessment:**
- [x] Risk to existing system is low (gradual migration)
- [x] Rollback plan is feasible (feature flags, branches)
- [x] Testing approach covers existing functionality (regression tests)
- [x] Team has sufficient knowledge of integration points (similar to sports-data)

**Completeness Check:**
- [x] Epic goal is clear and achievable
- [x] Stories are properly scoped (1-2 weeks each)
- [x] Success criteria are measurable (latency, cache hit rate)
- [x] Dependencies are identified (Epic 13, 22 complete)

---

## Story Manager Handoff

**Story Manager - Please develop detailed user stories for this brownfield epic. Key considerations:**

**Existing System Context:**
- Enhancement to running system with 20 microservices (Python 3.11, FastAPI, InfluxDB 2.7)
- Integration points: websocket-ingestion, enrichment-pipeline, health-dashboard, InfluxDB
- Existing patterns to follow: sports-data service (Port 8005) is the reference implementation

**Critical Compatibility Requirements:**
- Historical data must remain accessible (no breaking changes)
- Event processing pipeline cannot be disrupted
- Dashboard must handle both old (embedded) and new (API) weather data
- Each story must include verification that existing functionality remains intact

**Technical Standards:**
- Follow Context7 FastAPI best practices (lifespan managers, dependency injection)
- Use InfluxDB3 Python client patterns (async writes, batching)
- Implement comprehensive health checks and metrics
- Include unit tests for all new code (pytest 7.4+)

**Reference Documents:**
- Tech Stack: `docs/architecture/tech-stack.md`
- Source Tree: `docs/architecture/source-tree.md`
- Coding Standards: `docs/architecture/coding-standards.md`
- Analysis: `implementation/analysis/WEATHER_ARCHITECTURE_ANALYSIS.md`

The epic should maintain system integrity while delivering architectural consistency and performance improvements. Use the sports-data service as the gold standard template for implementation patterns.

---

**Created:** October 19, 2025  
**Epic Owner:** Architecture Team  
**Priority:** Medium-High (Technical Debt Reduction)  
**Target Completion:** Q1 2026 (3-4 weeks development + 1 week validation)

