# Epic 31: Weather API Service Migration - BMAD Implementation Summary

**Created:** October 19, 2025  
**Status:** Epic and Stories Created ✅  
**Methodology:** BMAD Brownfield Enhancement + Context7 Verification  

---

## Epic Overview

**Epic 31: Weather API Service Migration - Brownfield Enhancement**

**Location:** `docs/prd/epic-31-weather-api-service-migration.md`

### Problem Statement

Weather data integration uses an **architectural anomaly** - it's the ONLY external data source that embeds data into Home Assistant events instead of using a standalone API service like all others:

| Service | Pattern | Port |
|---------|---------|------|
| Weather | ❌ Event Enrichment | None |
| Sports | ✅ External API | 8005 |
| Carbon | ✅ External API | 8010 |
| Electricity | ✅ External API | 8011 |
| Air Quality | ✅ External API | 8012 |

### Solution

Migrate weather to standalone **weather-api service (Port 8009)** following the proven sports-data pattern.

---

## Research Foundation

**Comprehensive Analysis:** `implementation/analysis/WEATHER_ARCHITECTURE_ANALYSIS.md` (1,200 lines)

**Key Findings:**
- YES, the current weather architecture was a mistake
- Architectural inconsistency causes confusion and technical debt
- External API pattern is industry best practice for microservices
- Trade-off: Lose exact temporal correlation, gain architectural consistency

**Web Research:** Event-driven architecture best practices (2024)
- Recommendation: External API for consistency with other integrations
- InfluxDB best practices: Avoid sparse fields, use separate measurements

**Context7 Verification:**
- FastAPI patterns validated ✅
- InfluxDB3 Python client patterns validated ✅
- Caching with LRU and TTL validated ✅
- Lifespan context managers validated ✅

---

## Epic Structure

### 5 Stories (3-4 Weeks Total Effort)

**Story 31.1: Weather API Service Foundation** ✅ **CREATED**
- **Effort:** 1 week (40 hours)
- **Location:** `docs/stories/31.1-weather-api-service-foundation.md`
- **Focus:** FastAPI service skeleton, Docker deployment, health checks
- **AC:** 10 acceptance criteria covering service structure, health endpoints, Docker config
- **Tasks:** 8 tasks with 40+ subtasks
- **Reference:** sports-data service template

**Story 31.2: Weather Data Collection & InfluxDB Persistence** ⏳ **PENDING**
- **Effort:** 1 week (40 hours)
- **Focus:** Migrate OpenWeatherMap client, caching, InfluxDB writes
- **AC:** Weather data fetching, 15-min cache TTL, continuous background loop
- **Reference:** carbon-intensity-service, air-quality-service patterns

**Story 31.3: Weather API Endpoints & Query Support** ⏳ **PENDING**
- **Effort:** 4-5 days (32-40 hours)
- **Focus:** GET endpoints (/current-weather, /forecast, /historical)
- **AC:** REST API endpoints, cache statistics, query performance
- **Reference:** sports-data historical query endpoints

**Story 31.4: Event Pipeline Decoupling** ⏳ **PENDING**
- **Effort:** 2-3 days (16-24 hours)
- **Focus:** Remove weather enrichment from websocket-ingestion
- **AC:** Event pipeline decoupled, historical data preserved
- **Reference:** Existing websocket-ingestion/enrichment-pipeline code

**Story 31.5: Dashboard & Query Integration** ⏳ **PENDING**
- **Effort:** 2-3 days (16-24 hours)
- **Focus:** Dashboard updates, time-window JOIN queries
- **AC:** Weather API client, analytics queries updated, weather widget
- **Reference:** Dashboard sports integration pattern

---

## Technical Approach

### Architecture Pattern

**OLD (Event Enrichment):**
```
HA Event → websocket-ingestion → weather_client → Enrich → InfluxDB
```

**NEW (External API):**
```
HA Event → websocket-ingestion → InfluxDB (no weather)

weather-api:8009 → OpenWeatherMap → Cache → InfluxDB (weather_data)
                                        ↓
                                  Dashboard queries directly
```

### Technology Stack (Context7 Verified)

- **Framework:** FastAPI 0.104.1 with lifespan context managers
- **HTTP Client:** aiohttp 3.9.1 (async OpenWeatherMap calls)
- **Database:** InfluxDB 2.7 (weather_data measurement)
- **Caching:** In-memory with 15-minute TTL
- **Docker:** Alpine-based multi-stage builds
- **Testing:** pytest 7.4+ with pytest-asyncio
- **Logging:** Structured JSON with correlation IDs

### Key Patterns (From Context7)

**1. FastAPI Lifespan:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize weather client, cache, InfluxDB
    yield
    # Cleanup resources
```

**2. InfluxDB3 Python Client:**
```python
point = Point("weather") \
    .tag("location", location) \
    .tag("condition", condition) \
    .field("temperature", temp) \
    .field("humidity", humidity)
client.write(point)
```

**3. Caching with TTL:**
```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

---

## Benefits & Trade-offs

### Benefits ✅

1. **Architectural Consistency** - All external APIs follow same pattern
2. **Independent Scaling** - Weather service can scale separately
3. **Performance Isolation** - Weather API issues don't block events
4. **Feature Expansion** - Easy to add forecasts, alerts, trends
5. **Better Monitoring** - Dedicated health checks and metrics
6. **Reduced Coupling** - Event pipeline independent of weather

### Trade-offs ⚠️

1. **Temporal Correlation Loss** - Use 5-min time windows (95% accuracy)
2. **Query Complexity** - Need JOINs for weather correlation
3. **Dashboard Updates** - 2-3 days to update UI
4. **Additional Service** - One more service to manage

---

## Success Metrics

**Performance Targets:**
- Event processing: 30% faster (remove weather blocking)
- Weather API calls: 80% reduction (better caching)
- Weather query response: <100ms (95th percentile)
- API uptime: >99.9%
- Cache hit rate: >85%

**Quality Targets:**
- All 10 acceptance criteria met (Story 31.1)
- All existing functionality preserved (no regression)
- 100% Context7 best practices compliance
- Minimum 80% test coverage

---

## Risk Mitigation

**Primary Risk:** Loss of exact temporal correlation

**Mitigations:**
1. 5-minute time window JOINs (95% accuracy)
2. Continuous background fetch (every 5 minutes)
3. 15-minute cache TTL (balance freshness vs API usage)
4. Preserve historical embedded weather (no data loss)

**Rollback Plan:**
- Keep enrichment code in separate branch
- Feature flag to re-enable if needed
- Can revert Docker Compose in <5 minutes
- Non-destructive rollback (historical data safe)

---

## Next Steps

### Immediate (Story Manager)

1. **Create Story 31.2** - Weather Data Collection & InfluxDB Persistence
   - Migrate `services/websocket-ingestion/src/weather_client.py`
   - Implement caching layer (15-min TTL)
   - Add InfluxDB writer to weather_data measurement
   - Continuous background fetch loop

2. **Create Story 31.3** - Weather API Endpoints & Query Support
   - Implement GET /current-weather
   - Implement GET /forecast (24-hour)
   - Implement GET /historical (time-range)
   - Add cache statistics endpoint

3. **Create Story 31.4** - Event Pipeline Decoupling
   - Remove weather enrichment from websocket-ingestion
   - Update enrichment-pipeline
   - Add deprecation notices
   - Schema compatibility for historical queries

4. **Create Story 31.5** - Dashboard & Query Integration
   - Add weather API client to dashboard
   - Update analytics with time-window JOINs
   - Weather widget on Data Sources tab
   - Update documentation

### Implementation Phase (After Story Creation)

1. **Week 1-2:** Stories 31.1 + 31.2 (Foundation + Data Collection)
2. **Week 3:** Story 31.3 (API Endpoints)
3. **Week 4:** Stories 31.4 + 31.5 (Decoupling + Integration)
4. **Week 5:** Testing, validation, documentation

---

## Documentation Artifacts

### Created ✅

1. **Epic Document:** `docs/prd/epic-31-weather-api-service-migration.md`
   - Complete epic definition with 5 stories
   - Compatibility requirements and risk mitigation
   - Technical notes with Context7 verification
   - Story Manager handoff instructions

2. **Story 31.1:** `docs/stories/31.1-weather-api-service-foundation.md`
   - 10 acceptance criteria
   - 8 tasks with 40+ subtasks
   - Complete dev notes with testing standards
   - Reference implementations and patterns
   - Context7 verification notes

3. **Research Analysis:** `implementation/analysis/WEATHER_ARCHITECTURE_ANALYSIS.md`
   - 1,200 lines of detailed comparison
   - All 5 external data services analyzed
   - Web research findings
   - Pros/cons analysis (15 detailed points)
   - Migration path with code examples

4. **Summary:** `implementation/EPIC_31_WEATHER_MIGRATION_SUMMARY.md` (this file)
   - Complete overview of epic and stories
   - Technical approach and patterns
   - Next steps and timeline

### Pending ⏳

5. **Story 31.2:** Weather Data Collection & InfluxDB Persistence
6. **Story 31.3:** Weather API Endpoints & Query Support
7. **Story 31.4:** Event Pipeline Decoupling
8. **Story 31.5:** Dashboard & Query Integration
9. **Update:** `docs/prd/epic-list.md` (add Epic 31)

---

## Context7 Validation Summary

**Libraries Verified:**
- ✅ `/fastapi/fastapi` - Microservice patterns, lifespan, dependencies, CORS
- ✅ `/influxcommunity/influxdb3-python` - Point class, tag/field writing, batch writes

**Patterns Validated:**
- ✅ FastAPI lifespan context managers (startup/shutdown)
- ✅ Dependency injection with `Depends` and `yield`
- ✅ InfluxDB Point class with tags and fields
- ✅ Caching with LRU and TTL
- ✅ Health check endpoint patterns
- ✅ CORS middleware configuration
- ✅ Structured logging with correlation IDs

**Best Practices Confirmed:**
- ✅ Multi-stage Docker builds (Alpine-based)
- ✅ Non-root user execution
- ✅ Environment variable configuration
- ✅ Graceful error handling
- ✅ Comprehensive test coverage

---

## References

**Internal Documents:**
- Epic: `docs/prd/epic-31-weather-api-service-migration.md`
- Story 31.1: `docs/stories/31.1-weather-api-service-foundation.md`
- Analysis: `implementation/analysis/WEATHER_ARCHITECTURE_ANALYSIS.md`
- Tech Stack: `docs/architecture/tech-stack.md`
- Source Tree: `docs/architecture/source-tree.md`
- Coding Standards: `docs/architecture/coding-standards.md`

**Reference Implementations:**
- `services/sports-data/src/main.py` - FastAPI service template
- `services/carbon-intensity-service/src/main.py` - External API pattern
- `services/air-quality-service/src/main.py` - InfluxDB writer pattern
- `services/websocket-ingestion/src/weather_client.py` - Current weather client

**Context7 Libraries:**
- FastAPI: `/fastapi/fastapi`
- InfluxDB3 Python: `/influxcommunity/influxdb3-python`

---

**Epic Owner:** Architecture Team  
**Priority:** Medium-High (Technical Debt Reduction)  
**Target Completion:** Q1 2026  
**Methodology:** BMAD Brownfield Enhancement  
**Validation:** Context7 MCP Best Practices ✅

