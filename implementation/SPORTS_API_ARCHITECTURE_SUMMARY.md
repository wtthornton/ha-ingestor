# Sports API Integration - Architecture Summary

**Date**: October 11, 2025  
**Architect**: Winston 🏗️  
**Document**: `docs/architecture/sports-api-integration.md`  
**Status**: ✅ Complete - Ready for Implementation

---

## Executive Summary

A complete architecture plan for integrating **API-SPORTS (NFL, NCAA, and NHL)** into the Home Assistant Ingestor ecosystem has been designed following established patterns and Context7 KB best practices.

---

## Key Deliverables

### 1. Service Architecture ✅
- **Microservice design** following existing weather-api and enrichment-pipeline patterns
- **aiohttp-based HTTP client** with connection pooling and retry logic (Context7 KB)
- **Modular structure** supporting NFL, NHL, and future sports (NCAA, MLB, NBA, etc.)
- **Shared authentication** and rate limiting across all sports APIs

### 2. InfluxDB Schema Design ⭐ (Section 5)

Comprehensive time-series database schema optimized for sports data:

#### **Measurements Defined:**
- **`nfl_scores`** - Live and historical NFL game scores
- **`nhl_scores`** - Live and historical NHL game scores  
- **`nfl_player_stats`** - Player statistics by game/season
- **`nfl_injuries`** - Injury reports with status tracking
- **`nfl_standings`** / **`nhl_standings`** - League standings and rankings

#### **Schema Best Practices Applied:**
✅ **Tag Strategy**: Team names, conferences, divisions, game IDs (indexed for fast queries)  
✅ **Field Strategy**: Numeric scores, timestamps, status fields (actual data)  
✅ **Low Cardinality**: Tag cardinality kept under 10K unique values per tag  
✅ **Batch Writing**: 100 points per batch with 10-second flush interval  
✅ **Retention Policies**: 
  - Events: 2 years (`sports_events_2y`)
  - Stats: 2 years (`sports_stats_2y`)
  - Standings: 5 years (`sports_standings_5y`)

#### **Performance Optimization:**
- **Batch writing** with exponential backoff retry (Context7 KB pattern)
- **Write callbacks** for success/error/retry monitoring
- **Connection pooling** and reuse
- **Efficient tagging** for fast time-range and team queries

#### **Query Patterns Provided:**
```sql
-- Live scores
SELECT * FROM nfl_scores WHERE status = 'live' AND time > now() - 4h

-- Team season performance
SELECT * FROM nfl_scores WHERE season = '2025' AND (home_team = 'Patriots' OR away_team = 'Patriots')

-- Player season aggregation
SELECT SUM(passing_yards), AVG(qb_rating) FROM nfl_player_stats 
WHERE player_id = 'abc123' AND season = '2025' GROUP BY player_name
```

### 3. Rate Limiting & Caching ✅
- **Token bucket algorithm** with configurable rate limits
- **Intelligent caching** with TTL-based expiration:
  - Live scores: 15 seconds
  - Recent scores: 5 minutes
  - Fixtures/Standings: 1 hour
  - Historical data: 1 day
- **Circuit breaker pattern** for API resilience

### 4. Data Models ✅
- **Pydantic models** for type safety:
  - `NFLScore`, `NHLScore` - Game scores with metadata
  - `NFLStanding`, `NHLStanding` - League standings
  - `NFLPlayer`, `NFLInjury` - Player stats and injuries
- **Validation** and **serialization** built-in

### 5. Integration Plan ✅
- **Enrichment pipeline** integration for Home Assistant event enrichment
- **Admin API** endpoints for configuration
- **Dashboard** queries for visualization
- **WebSocket ingestion** compatibility

### 6. Deployment Configuration ✅
- **Docker Compose** service definition
- **Environment variables** template (`infrastructure/env.sports.template`)
- **Health checks** and monitoring
- **Resource requirements** (0.5 CPU, 512MB RAM)

### 7. Error Handling ✅
- **Circuit breaker** for API failures
- **Exponential backoff** retry logic
- **Comprehensive logging** with correlation IDs
- **Graceful degradation** (serve stale cache when API unavailable)

### 8. Testing Strategy ✅
- **Unit tests** (90%+ coverage target)
- **Integration tests** for API clients and InfluxDB
- **E2E tests** with Playwright for dashboard
- **Mock patterns** for API responses

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Language | Python | 3.11 | Async service |
| HTTP Framework | aiohttp | 3.9.1 | HTTP client/server |
| Time-Series DB | InfluxDB | 2.7 | Sports data storage |
| InfluxDB Client | influxdb-client-3 | 3.x | Python client |
| Caching | In-memory (Phase 1) | - | Response caching |
| Testing | pytest | 7.4.3 | Unit/integration tests |
| Containerization | Docker | 24+ | Deployment |

---

## InfluxDB Implementation Highlights

### Batch Writer Implementation
```python
class SportsInfluxDBWriter:
    """High-performance batch writer for sports data"""
    
    # Features:
    # - Batch size: 100 points (configurable)
    # - Flush interval: 10 seconds
    # - Exponential backoff retry (2^n * 5s)
    # - Success/error/retry callbacks
    # - Performance metrics tracking
    
    async def write_nfl_score(self, score: Dict[str, Any]) -> bool:
        """Write NFL score with proper tags and fields"""
        point = Point("nfl_scores") \
            .tag("game_id", score['game_id']) \
            .tag("season", str(score['season'])) \
            .tag("week", str(score['week'])) \
            .tag("home_team", score['home_team']) \
            .tag("away_team", score['away_team']) \
            .tag("status", score['status']) \
            .field("home_score", int(score['home_score'])) \
            .field("away_score", int(score['away_score'])) \
            .time(score['date'])
        
        self.client.write(point)
```

### Example Queries
```python
# Live games dashboard
live_games = await client.query(
    query="SELECT * FROM nfl_scores WHERE status = 'live' AND time > now() - 4h",
    language='sql',
    mode='pandas'
)

# Player season stats
player_stats = await client.query(
    query="""
        SELECT player_name, SUM(passing_yards) as total_yards, AVG(qb_rating) as avg_rating
        FROM nfl_player_stats 
        WHERE player_id = 'abc123' AND season = '2025'
        GROUP BY player_name
    """,
    language='sql',
    mode='pandas'
)
```

---

## Service Structure

```
services/sports-api/
├── src/
│   ├── main.py                      # Service entry point
│   ├── api_client.py                # Base API-SPORTS client
│   ├── nfl_client.py                # NFL-specific methods
│   ├── nhl_client.py                # NHL-specific methods
│   ├── influxdb_writer.py           # ⭐ InfluxDB batch writer
│   ├── influxdb_schema.py           # ⭐ Schema definitions
│   ├── rate_limiter.py              # Token bucket rate limiter
│   ├── cache_manager.py             # TTL-based caching
│   ├── endpoints.py                 # HTTP endpoints
│   └── models.py                    # Pydantic models
├── tests/
│   ├── test_nfl_client.py
│   ├── test_influxdb_writer.py      # ⭐ InfluxDB tests
│   └── ...
└── Dockerfile
```

---

## Next Steps

### Phase 1: Implementation (2-3 weeks)
1. **Set up service structure** following architecture
2. **Implement API clients** (NFL, NHL)
3. **Build InfluxDB writer** with batch writing
4. **Add rate limiting and caching**
5. **Create unit and integration tests**
6. **Deploy to development environment**

### Phase 2: Integration (1 week)
1. **Integrate with enrichment pipeline**
2. **Add admin API endpoints**
3. **Create dashboard UI components**
4. **End-to-end testing**
5. **Performance optimization**

### Phase 3: Production (1 week)
1. **Production deployment**
2. **Monitoring and alerting setup**
3. **Documentation and runbooks**
4. **User acceptance testing**

---

## Key Design Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| **aiohttp for HTTP** | Context7 KB best practices, existing pattern | High - Core technology |
| **InfluxDB batch writing** | High performance, proven pattern | High - Data storage optimization |
| **Tag-based schema** | Efficient time-series queries | High - Query performance |
| **In-memory caching (Phase 1)** | Simpler deployment | Medium - Redis in Phase 2 |
| **Token bucket rate limiter** | Flexible, handles bursts | Medium - API quota management |
| **Single service architecture** | Shared rate limiting, simpler orchestration | High - Architectural decision |

---

## Context7 KB Research Applied

### aiohttp Client Patterns (/aio-libs/aiohttp)
✅ ClientSession with connection pooling  
✅ TCPConnector with limit configuration  
✅ ClientTimeout for request timeouts  
✅ Graceful shutdown pattern  
✅ Retry middleware with exponential backoff

### InfluxDB Python Patterns (/influxcommunity/influxdb3-python)
✅ Point class for data construction  
✅ Batch writing with WriteOptions  
✅ Success/error/retry callbacks  
✅ Query modes (SQL, InfluxQL, Pandas)  
✅ Tag and field best practices

---

## Files Created

1. **`docs/architecture/sports-api-integration.md`** (main architecture document)
   - 15 sections covering all aspects
   - **Section 5: Comprehensive InfluxDB review** ⭐
   - Code examples and implementation patterns
   - Query patterns and optimization strategies

2. **`docs/SPORTS_API_ARCHITECTURE_SUMMARY.md`** (this file)
   - Executive summary and highlights
   - Quick reference for implementation

---

## Review Checklist

- [x] Architecture aligns with existing patterns
- [x] Rate limiting strategy is sound  
- [x] Security considerations addressed
- [x] Testing strategy is comprehensive
- [x] Deployment plan is clear
- [x] Future scalability considered
- [x] **InfluxDB schema optimized for time-series queries** ⭐
- [x] **Batch writing pattern follows best practices** ⭐
- [x] **Data retention policies defined** ⭐
- [x] **Query patterns documented** ⭐
- [x] **Performance optimization strategies included** ⭐

---

## Contact

**Architect**: Winston (BMad Master Architect Agent)  
**Date**: October 11, 2025  
**Status**: Ready for implementation

For questions or clarifications, reference the main architecture document:  
📄 `docs/architecture/sports-api-integration.md`

---

**Next Action**: Review architecture document and approve for implementation phase.

