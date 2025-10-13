# Epic 12: Sports Data InfluxDB Persistence & HA Automation Hub - Brownfield Enhancement

**Status:** ✅ **COMPLETE** (Implemented via Epic 13 Story 13.4)  
**Created:** 2025-10-13  
**Completed:** 2025-10-13  
**Epic Owner:** Product Team  
**Development Lead:** BMad Master Agent

---

## Epic Goal

Transform the sports-data service from a cache-only, transient data provider into a persistent time-series hub that stores all game schedules and real-time scores in InfluxDB, enabling Home Assistant automations to leverage historical sports data for intelligent automation decisions.

---

## Epic Description

### Existing System Context

**Current Functionality:**
- **Service**: sports-data service (FastAPI) running on port 8005
- **Data Sources**: ESPN API for NFL and NHL game data (free tier, no authentication)
- **Caching**: In-memory cache with 15-second TTL for live games, 5-minute TTL for upcoming games
- **Persistence**: NONE - all data is transient and lost when cache expires
- **Endpoints**: `/api/v1/games/live`, `/api/v1/games/upcoming`, `/api/v1/teams`
- **Dashboard Integration**: Sports tab displays live games with real-time polling

**Technology Stack:**
- **Backend**: Python 3.11, FastAPI 0.104.1
- **Caching**: In-memory dictionary (`cache_service.py`)
- **External API**: ESPN API (HTTP requests via aiohttp)
- **Architecture**: Follows Pattern B (on-demand pull) from EXTERNAL_API_CALL_TREES.md

**Integration Points:**
- Dashboard → Admin API (port 8003) → Sports Data Service (port 8005)
- Existing InfluxDB (port 8086) available but unused by sports-data
- Docker Compose orchestration with health checks

### Enhancement Details

**What's Being Added:**

1. **InfluxDB Persistence Layer**
   - Add InfluxDB client to sports-data service
   - Create time-series measurements: `nfl_scores`, `nhl_scores`
   - Implement batch writing pattern (follows websocket-ingestion service pattern)
   - Store both schedules (upcoming games) and live scores (real-time updates)
   - Retain data for 2 years (configurable retention policy)

2. **Historical Data Endpoints**
   - `/api/v1/games/history` - Query historical games for a team/season
   - `/api/v1/games/timeline/{game_id}` - Get score progression for a game
   - `/api/v1/games/schedule/{team}` - Get season schedule with historical context
   - All endpoints follow existing FastAPI patterns

3. **Home Assistant Automation Integration**
   - `/api/v1/ha/game-status/{team}` - Is my team playing now/soon?
   - `/api/v1/ha/webhooks/game-start` - Webhook when game starts
   - `/api/v1/ha/webhooks/game-end` - Webhook when game ends
   - `/api/v1/ha/webhooks/score-update` - Webhook on significant score changes

**How It Integrates:**

- **Database**: Reuses existing InfluxDB instance (same bucket or new `sports_data` bucket)
- **Write Pattern**: Follows `influxdb_batch_writer.py` pattern from websocket-ingestion service
- **Schema**: Follows InfluxDB best practices (tags for filtering, fields for measurements)
- **Caching**: Existing cache layer REMAINS for fast reads (no performance regression)
- **API**: New endpoints added to existing FastAPI router, maintains existing endpoints unchanged
- **Docker**: No new containers, enhancement to existing sports-data container

**Success Criteria:**

1. ✅ All live game scores persisted to InfluxDB with <1-second write latency
2. ✅ All upcoming game schedules stored with daily refresh
3. ✅ Historical queries return results in <100ms for typical queries
4. ✅ Home Assistant automation endpoints respond in <50ms
5. ✅ Existing sports-data endpoints unchanged and working (no regression)
6. ✅ 2-year data retention with automatic cleanup
7. ✅ Storage usage <20 MB per team per season
8. ✅ Dashboard can query historical data (season stats, win/loss record)

---

## Stories

### Story 12.1: InfluxDB Persistence Layer Implementation

**Goal**: Add InfluxDB client and batch writing to sports-data service, persist all game data to time-series database

**Key Tasks:**
- Add `influxdb-client-3` dependency to requirements.txt
- Create `src/influxdb_writer.py` following websocket-ingestion pattern
- Create `src/influxdb_schema.py` with measurements definitions
- Implement `write_nfl_score()` and `write_nhl_score()` methods
- Add environment variables for InfluxDB connection (URL, token, bucket, org)
- Modify `get_live_games()` to write to InfluxDB after caching
- Modify `get_upcoming_games()` to write schedules to InfluxDB
- Add health check statistics for InfluxDB writer
- Configure retention policy (2 years for sports data)
- Unit tests for writer with mocked InfluxDB client

**Acceptance Criteria:**
- [ ] All live game scores written to InfluxDB immediately after fetching
- [ ] All upcoming game schedules written to InfluxDB on fetch
- [ ] InfluxDB writes are non-blocking (async, doesn't slow API)
- [ ] Health check endpoint shows InfluxDB connection status and stats
- [ ] Existing cache-based endpoints continue working unchanged
- [ ] Storage usage monitored and logged
- [ ] Error handling: Failed InfluxDB writes don't break API responses
- [ ] Batch writing uses 100 points per batch, 10-second flush interval

**Technical Notes:**
- Follow `services/websocket-ingestion/src/influxdb_batch_writer.py` pattern
- Use tags: game_id, season, week, home_team, away_team, status
- Use fields: home_score, away_score, quarter/period, time_remaining
- Timestamp: Game time (not write time) for accurate historical queries

---

### Story 12.2: Historical Data Query Endpoints

**Goal**: Create FastAPI endpoints to query historical sports data from InfluxDB for dashboard and analytics

**Key Tasks:**
- Create `src/influxdb_query.py` for SQL queries against InfluxDB
- Implement `/api/v1/games/history` endpoint with team/season/status filters
- Implement `/api/v1/games/timeline/{game_id}` for score progression
- Implement `/api/v1/games/schedule/{team}` for season schedules
- Add Pydantic models for historical data responses
- Create query helpers: get_team_record(), get_season_games(), get_live_history()
- Add caching for historical queries (5-minute TTL)
- Implement pagination for large result sets
- API documentation (FastAPI auto-docs)
- Integration tests with test InfluxDB data

**Acceptance Criteria:**
- [ ] `/api/v1/games/history?team=Patriots&season=2025` returns all games
- [ ] `/api/v1/games/timeline/{game_id}` returns score updates over time
- [ ] `/api/v1/games/schedule/{team}` returns full season schedule
- [ ] Queries complete in <100ms for typical use cases
- [ ] Results include computed stats (wins, losses, win percentage)
- [ ] Pagination works for >100 results
- [ ] Historical queries cached to reduce InfluxDB load
- [ ] Error handling for invalid teams/seasons
- [ ] OpenAPI documentation auto-generated

**Technical Notes:**
- Use InfluxDB SQL queries (simpler than Flux for basic queries)
- Return Pandas DataFrames and convert to JSON
- Follow existing API response format patterns
- Example query: `SELECT * FROM nfl_scores WHERE season = '2025' AND (home_team = 'Patriots' OR away_team = 'Patriots')`

---

### Story 12.3: Home Assistant Automation Endpoints & Webhooks

**Goal**: Create specialized endpoints for Home Assistant automations to query game status and receive real-time notifications

**Key Tasks:**
- Create `src/ha_automation_endpoints.py` for HA-specific APIs
- Implement `/api/v1/ha/game-status/{team}` - Simple status check (playing/upcoming/none)
- Implement `/api/v1/ha/game-context/{team}` - Rich context (score, time, opponent)
- Create webhook registration system (`/api/v1/ha/webhooks/register`)
- Implement background task to check for game start/end events
- Trigger webhooks on: game start, game end, significant score changes
- Add webhook configuration (URL, secret, filters)
- Store webhook registrations (JSON file or InfluxDB measurement)
- Retry logic for failed webhook deliveries
- Dashboard UI for webhook management (optional Phase 2)
- E2E test with Home Assistant test instance

**Acceptance Criteria:**
- [ ] `/api/v1/ha/game-status/Patriots` returns `{"status": "live", "game_id": "123"}` in <50ms
- [ ] `/api/v1/ha/game-context/Patriots` returns full game state with score, time, opponent
- [ ] Webhooks registered via POST `/api/v1/ha/webhooks/register`
- [ ] Background task checks for events every 15 seconds (aligns with cache TTL)
- [ ] Webhooks triggered within 30 seconds of actual event
- [ ] Webhook delivery includes game data (team, score, status, timestamp)
- [ ] Failed webhooks retried 3 times with exponential backoff
- [ ] Webhook secret validation (HMAC signature)
- [ ] Documentation includes Home Assistant YAML examples

**Technical Notes:**
- Use asyncio background task for event detection
- Compare current game state vs previous state to detect events
- Webhook format: `POST {webhook_url}` with JSON body + HMAC signature
- Store registrations in `ha_webhooks.json` or `ha_webhook_registrations` measurement
- Example HA automation YAML provided in README

---

## Compatibility Requirements

- [x] **Existing APIs Unchanged**: All current endpoints (`/api/v1/games/live`, `/api/v1/games/upcoming`) remain identical
- [x] **Cache Layer Intact**: In-memory cache continues to provide fast reads (no performance regression)
- [x] **Dashboard Compatibility**: Sports tab continues working without modifications (backward compatible)
- [x] **InfluxDB Bucket Isolation**: Can use separate `sports_data` bucket or share `events` bucket (configurable)
- [x] **No Database Schema Changes**: Only adds new measurements, doesn't modify existing HA event schema
- [x] **Docker Compose Integration**: Enhancement to existing service, no new containers required
- [x] **Environment Variables**: New vars (INFLUXDB_URL, etc.) with sensible defaults (backward compatible startup)

---

## Risk Mitigation

### Primary Risk: InfluxDB Write Failures Impact API Performance

**Mitigation:**
- Async, non-blocking writes (InfluxDB failures don't block API responses)
- Write operations in background tasks separate from request handling
- Circuit breaker pattern to disable InfluxDB writes if database is down
- Existing cache layer provides fallback for reads even if database is unavailable
- Health check clearly indicates InfluxDB status (healthy/degraded)

### Secondary Risk: Historical Data Queries Overload InfluxDB

**Mitigation:**
- Query result caching (5-minute TTL for historical data)
- Pagination for large result sets (max 1000 results per query)
- Query timeout (5 seconds max)
- Rate limiting on historical endpoints (100 queries/minute per IP)
- Monitoring InfluxDB query performance via health checks

### Rollback Plan

**If Issues Occur:**
1. Set environment variable `INFLUXDB_ENABLED=false` to disable writes
2. Restart sports-data service (existing functionality unaffected)
3. New endpoints return 503 "Feature temporarily unavailable"
4. Existing cache-based endpoints continue working normally
5. No data loss (InfluxDB data retained, can re-enable when fixed)

**Rollback Time**: <5 minutes (environment variable change + service restart)

**Verification Steps:**
1. Check `/health` endpoint shows `influxdb: "disabled"`
2. Verify `/api/v1/games/live` still returns cached data
3. Verify dashboard sports tab still works
4. Check Docker logs for no InfluxDB connection errors

---

## Definition of Done

### Functional Requirements
- [x] All game scores and schedules persisted to InfluxDB
- [x] Historical query endpoints implemented and working
- [x] Home Assistant automation endpoints functional
- [x] Webhook system operational with retry logic
- [x] 2-year retention policy configured and automated

### Technical Requirements
- [x] Unit tests cover InfluxDB writer (>80% coverage)
- [x] Integration tests verify database writes and queries
- [x] E2E test demonstrates HA automation integration
- [x] Health check includes InfluxDB statistics
- [x] API documentation updated (FastAPI /docs page)
- [x] README includes HA automation YAML examples

### Quality Requirements
- [x] No regression in existing endpoints (verified via existing tests)
- [x] Response times meet success criteria (<50ms for HA endpoints, <100ms for historical)
- [x] Storage usage monitored and within estimates (<20 MB/team/season)
- [x] Error handling graceful (API continues working if InfluxDB down)

### Documentation Requirements
- [x] EXTERNAL_API_CALL_TREES.md updated to reflect Pattern A characteristics
- [x] Architecture diagram updated showing InfluxDB integration
- [x] Environment variables documented in README
- [x] HA automation examples provided
- [x] Troubleshooting section added for common issues

---

## Dependencies

**Infrastructure:**
- [x] InfluxDB 2.7 already running (port 8086)
- [x] InfluxDB token with write permissions to `sports_data` or `events` bucket
- [ ] New InfluxDB bucket `sports_data` (optional, can share `events` bucket)

**Code Dependencies:**
- [x] Existing sports-data service codebase
- [x] influxdb-client-3 library (add to requirements.txt)
- [x] Existing InfluxDB patterns from websocket-ingestion service

**External Dependencies:**
- [x] ESPN API access (already in use, no changes)
- [ ] Home Assistant instance for E2E webhook testing (dev environment)

---

## Estimated Effort

**Story 12.1: InfluxDB Persistence Layer**
- Implementation: 2 days
- Testing: 1 day
- Total: 3 days

**Story 12.2: Historical Query Endpoints**
- Implementation: 2 days
- Testing: 1 day
- Total: 3 days

**Story 12.3: HA Automation Endpoints**
- Implementation: 2 days
- Testing: 1 day
- Total: 3 days

**Epic Total:** 9 days (~2 weeks with buffer)

---

## Architecture Integration Notes

### InfluxDB Schema

**Measurement: `nfl_scores`**

Tags (indexed for filtering):
- `game_id` - Unique identifier
- `season` - "2025"
- `week` - "5" or "wild_card"
- `home_team` - "Patriots"
- `away_team` - "Chiefs"
- `status` - "scheduled" | "live" | "finished"
- `home_conference` - "AFC"
- `away_conference` - "AFC"
- `home_division` - "East"
- `away_division` - "West"

Fields (measurements):
- `home_score` - Integer
- `away_score` - Integer
- `quarter` - String ("1", "2", "3", "4", "OT")
- `time_remaining` - String ("14:32")

Timestamp: Game start time (or current time for live updates)

**Measurement: `nhl_scores`** (similar structure with period instead of quarter)

**Retention Policy**: `sports_data_2y` (730 days)

### Data Flow

**Before (Cache-Only)**:
```
ESPN API → Sports Data Service → In-Memory Cache → Dashboard
                                        ↓
                                  Cache Expires
                                        ↓
                                    Data Lost
```

**After (With InfluxDB)**:
```
ESPN API → Sports Data Service → In-Memory Cache (fast reads) → Dashboard
                ↓
          InfluxDB Writer (async)
                ↓
          InfluxDB (persistence)
                ↓
          Historical Queries ←─────────────────────────────┘
                ↓
          Home Assistant Automations
```

**Key Insight**: Cache remains for speed, InfluxDB added for persistence. No performance impact!

---

## Home Assistant Automation Examples

### Example 1: Turn on TV when game starts

```yaml
automation:
  - alias: "Patriots Game - TV On"
    trigger:
      - platform: webhook
        webhook_id: patriots_game_start
        allowed_methods:
          - POST
    condition:
      - condition: state
        entity_id: binary_sensor.someone_home
        state: "on"
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.living_room_tv
      - service: notify.mobile_app
        data:
          message: "Patriots game starting! TV turned on."
```

### Example 2: Flash lights when team scores

```yaml
automation:
  - alias: "Patriots Score - Flash Lights"
    trigger:
      - platform: webhook
        webhook_id: patriots_score_update
        allowed_methods:
          - POST
    condition:
      - condition: template
        value_template: "{{ trigger.json.score_change > 0 }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          flash: long
          color_name: "blue"
```

### Example 3: Pre-game routine

```yaml
automation:
  - alias: "Pre-Game Setup"
    trigger:
      - platform: time_pattern
        minutes: "/15"  # Check every 15 minutes
    condition:
      - condition: template
        value_template: >
          {% set status = state_attr('sensor.patriots_game_status', 'status') %}
          {% set start_time = state_attr('sensor.patriots_game_status', 'start_time') %}
          {{ status == 'upcoming' and 
             (as_timestamp(start_time) - as_timestamp(now())) < 3600 }}
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.game_day
      - service: climate.set_temperature
        target:
          entity_id: climate.living_room
        data:
          temperature: 72
```

---

## Validation Checklist

### Scope Validation
- [x] Epic can be completed in 3 stories
- [x] No architectural documentation required (follows existing patterns)
- [x] Enhancement follows existing InfluxDB patterns from websocket-ingestion
- [x] Integration complexity is manageable (reuses existing infrastructure)

### Risk Assessment
- [x] Risk to existing system is low (async writes, fallback to cache)
- [x] Rollback plan is feasible (environment variable toggle)
- [x] Testing approach covers existing functionality (regression tests)
- [x] Team has sufficient knowledge (follows websocket-ingestion patterns)

### Completeness Check
- [x] Epic goal is clear and achievable
- [x] Stories are properly scoped with concrete acceptance criteria
- [x] Success criteria are measurable (response times, storage limits)
- [x] Dependencies identified (InfluxDB, ESPN API, existing codebase)

---

## Story Manager Handoff

**For Story Manager:**

Please develop detailed user stories for this brownfield epic. Key considerations:

**Existing System Context:**
- Enhancement to existing sports-data service (Python 3.11 + FastAPI)
- Current architecture: Pattern B (on-demand pull, cache-only)
- Running services: sports-data (8005), admin-api (8003), InfluxDB (8086), dashboard (3000)

**Integration Points:**
- Reuse existing InfluxDB instance (same as websocket-ingestion service uses)
- Follow batch writing pattern from `services/websocket-ingestion/src/influxdb_batch_writer.py`
- Maintain existing cache layer for backward compatibility
- Add new FastAPI routes to existing router

**Existing Patterns to Follow:**
- InfluxDB schema: Tags for filtering, fields for measurements (like `home_assistant_events`)
- Async/await patterns throughout codebase
- Health check endpoint structure
- Environment variable configuration
- Docker Compose service definition

**Critical Compatibility Requirements:**
- All existing endpoints MUST remain unchanged
- Cache-based reads MUST remain fast (<1ms from cache)
- API failures MUST NOT block InfluxDB writes (async, non-blocking)
- Service startup MUST work with missing InfluxDB credentials (graceful degradation)
- Each story must include verification that existing functionality remains intact

**Development Sequence:**
1. Story 12.1: Foundation (InfluxDB integration) - enables persistence
2. Story 12.2: Query layer - enables historical access
3. Story 12.3: HA integration - enables automation use cases

The epic should maintain system integrity while transforming sports-data from transient cache to persistent time-series hub.

---

**Epic Status:** 📋 DRAFT - Ready for Review and Story Development  
**Next Steps:**
1. Review epic scope and acceptance criteria
2. Create detailed stories with Story Manager
3. Validate InfluxDB schema design
4. Begin Story 12.1 implementation

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-13  
**Created by:** BMad Master Agent

