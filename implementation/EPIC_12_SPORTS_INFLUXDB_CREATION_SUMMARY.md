# Epic 12 Creation Summary - Sports Data InfluxDB Persistence

**Date**: 2025-10-13  
**Agent**: BMad Master  
**Task**: Create brownfield epic for sports data InfluxDB persistence and HA automation hub  
**Status**: ✅ Complete - Ready for Review

---

## 📋 Executive Summary

Successfully created **Epic 12: Sports Data InfluxDB Persistence & HA Automation Hub** following BMAD brownfield methodology. This epic transforms the sports-data service from a transient cache-only system into a persistent time-series hub that stores all game data in InfluxDB and provides endpoints for Home Assistant automations.

---

## 🎯 Epic Overview

### Scope Definition

**What's Being Added:**
1. InfluxDB persistence layer for all sports data (schedules + live scores)
2. Historical query endpoints for dashboard analytics
3. Home Assistant automation endpoints with webhooks
4. 2-year data retention with automatic cleanup

**What's NOT Included** (per user requirements):
- ❌ Player statistics (removed from scope)
- ❌ Injury reports (removed from scope)
- ❌ Team standings (optional Phase 2)
- ❌ Advanced analytics (optional Phase 2)

**Architecture Pattern Change:**
- **Before**: Pattern B (On-demand pull, cache-only, transient)
- **After**: Hybrid Pattern A+B (Persistent + cached, enables historical queries)

---

## 📊 Epic Structure

### File Created
**Location**: `docs/stories/epic-12-sports-data-influxdb-persistence.md`  
**Size**: ~780 lines  
**Format**: BMAD brownfield epic template

### Three Stories Defined

#### **Story 12.1: InfluxDB Persistence Layer Implementation** (3 days)
**Goal**: Add InfluxDB client and batch writing to persist all game data

**Key Components**:
- `src/influxdb_writer.py` - Batch writer following websocket-ingestion pattern
- `src/influxdb_schema.py` - Schema definitions (measurements, tags, fields)
- Async writes (non-blocking, doesn't slow API)
- Health check integration
- Unit tests with mocked client

**Measurements Created**:
- `nfl_scores` - NFL game scores and status
- `nhl_scores` - NHL game scores and status
- Tags: game_id, season, week, teams, status, conference, division
- Fields: home_score, away_score, quarter/period, time_remaining

**Acceptance Criteria**: 8 specific criteria including write latency, error handling, health checks

---

#### **Story 12.2: Historical Data Query Endpoints** (3 days)
**Goal**: Create FastAPI endpoints to query historical sports data

**New Endpoints**:
- `/api/v1/games/history` - Query historical games with filters
- `/api/v1/games/timeline/{game_id}` - Score progression over time
- `/api/v1/games/schedule/{team}` - Season schedule with context

**Key Components**:
- `src/influxdb_query.py` - SQL query builders
- Pagination support (max 1000 results)
- Query result caching (5-minute TTL)
- Computed stats (wins, losses, win percentage)

**Acceptance Criteria**: 9 specific criteria including response times (<100ms), pagination, caching

---

#### **Story 12.3: HA Automation Endpoints & Webhooks** (3 days)
**Goal**: Create specialized endpoints for Home Assistant automations

**New Endpoints**:
- `/api/v1/ha/game-status/{team}` - Quick status check
- `/api/v1/ha/game-context/{team}` - Rich game context
- `/api/v1/ha/webhooks/register` - Webhook registration

**Webhook Events**:
- Game start (when status changes to "live")
- Game end (when status changes to "finished")
- Score updates (significant changes)

**Key Components**:
- `src/ha_automation_endpoints.py` - HA-specific APIs
- Background task for event detection (15-second polling)
- Webhook delivery with retry (3 attempts, exponential backoff)
- HMAC signature validation for security
- Webhook storage (JSON file or InfluxDB)

**Acceptance Criteria**: 9 specific criteria including response times (<50ms), webhook delivery (<30s), security

---

## 🏗️ Architecture Integration

### InfluxDB Schema Design

**NFL Scores Measurement**:
```
Measurement: nfl_scores
Tags (9): game_id, season, week, home_team, away_team, status, 
          home_conference, away_conference, home_division, away_division
Fields (4): home_score, away_score, quarter, time_remaining
Timestamp: Game start time or current time for live updates
```

**NHL Scores Measurement** (similar with hockey-specific fields)

**Retention Policy**: `sports_data_2y` (730 days)

**Storage Estimate**: <20 MB per team per season

---

### Data Flow Transformation

**Current (Cache-Only)**:
```
ESPN API → Sports Service → Cache (15s TTL) → Dashboard
                                    ↓
                              Cache Expires
                                    ↓
                                Data Lost
```

**Enhanced (With InfluxDB)**:
```
ESPN API → Sports Service → Cache (fast reads) → Dashboard
                ↓
          InfluxDB Writer (async)
                ↓
          InfluxDB (persistence)
                ↓
          Historical Queries + HA Automations
```

**Key Design Decision**: Cache REMAINS for speed, InfluxDB ADDED for persistence (no performance regression)

---

## 🎯 User Requirements Addressed

✅ **Schedules**: All upcoming games stored in InfluxDB  
✅ **Real-time scores**: All live game updates persisted  
✅ **No player stats**: Scope limited to games only  
✅ **All data stored**: 2-year retention in time-series database  
✅ **HA automation endpoints**: Dedicated APIs with webhooks  
✅ **Hub functionality**: Historical data accessible for automations  
✅ **Maintainability**: Follows existing patterns from websocket-ingestion

---

## 🔐 Compatibility & Safety

### Backward Compatibility Guarantees

**Existing Endpoints Unchanged**:
- ✅ `/api/v1/games/live` - Continues working from cache
- ✅ `/api/v1/games/upcoming` - Continues working from cache
- ✅ `/api/v1/teams` - Continues working unchanged

**No Breaking Changes**:
- ✅ Cache layer intact (15s/5min TTL)
- ✅ API response formats unchanged
- ✅ Dashboard continues working without modifications
- ✅ Service starts even if InfluxDB unavailable (graceful degradation)

### Risk Mitigation

**Primary Risk**: InfluxDB writes impact API performance

**Mitigations**:
- Async, non-blocking writes (separate from request handling)
- Circuit breaker pattern (disable writes if DB down)
- Cache provides fallback for reads
- Health check shows clear status

**Rollback Plan**: Set `INFLUXDB_ENABLED=false` → restart → <5 minutes

---

## 📈 Success Criteria

### Performance Targets
- ✅ Live score writes: <1 second latency
- ✅ Historical queries: <100ms response time
- ✅ HA automation endpoints: <50ms response time
- ✅ Webhook delivery: <30 seconds from event

### Storage Targets
- ✅ <20 MB per team per season
- ✅ 2-year retention with auto-cleanup
- ✅ Batch writes (100 points, 10-second flush)

### Quality Targets
- ✅ No regression in existing endpoints
- ✅ >80% unit test coverage for new code
- ✅ Integration tests for DB writes/queries
- ✅ E2E test with HA webhook integration

---

## 🏠 Home Assistant Integration Examples

### Example 1: Turn on TV when game starts
```yaml
automation:
  - alias: "Patriots Game - TV On"
    trigger:
      - platform: webhook
        webhook_id: patriots_game_start
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.living_room_tv
```

### Example 2: Flash lights when team scores
```yaml
automation:
  - alias: "Patriots Score - Flash Lights"
    trigger:
      - platform: webhook
        webhook_id: patriots_score_update
    condition:
      - condition: template
        value_template: "{{ trigger.json.score_change > 0 }}"
    action:
      - service: light.turn_on
        data:
          flash: long
          color_name: "blue"
```

### Example 3: Pre-game routine (1 hour before)
```yaml
automation:
  - alias: "Pre-Game Setup"
    trigger:
      - platform: time_pattern
        minutes: "/15"
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.patriots_game_status', 'upcoming') and
             (as_timestamp(start_time) - now().timestamp()) < 3600 }}
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.game_day
```

---

## 📝 Dependencies & Prerequisites

### Infrastructure (Already Available)
- ✅ InfluxDB 2.7 running (port 8086)
- ✅ InfluxDB token with write permissions
- ✅ Docker Compose orchestration
- ✅ ESPN API access (no authentication required)

### Code Dependencies
- ✅ Existing sports-data service codebase
- 📦 influxdb-client-3 (add to requirements.txt)
- ✅ Existing patterns from websocket-ingestion service

### External Dependencies
- 🔧 Home Assistant test instance (for E2E webhook testing)

---

## ⏱️ Estimated Timeline

| Story | Implementation | Testing | Total |
|-------|---------------|---------|-------|
| 12.1: InfluxDB Persistence | 2 days | 1 day | 3 days |
| 12.2: Historical Queries | 2 days | 1 day | 3 days |
| 12.3: HA Automation | 2 days | 1 day | 3 days |
| **Epic Total** | **6 days** | **3 days** | **9 days** |

**With Buffer**: ~2 weeks for complete epic implementation

---

## 📚 Documentation Updates Required

### Technical Documentation
- [ ] Update `EXTERNAL_API_CALL_TREES.md` - Change sports-data from Pattern B to hybrid
- [ ] Update architecture diagram showing InfluxDB integration
- [ ] Add InfluxDB schema documentation
- [ ] Document webhook registration process

### User Documentation
- [ ] README: Add InfluxDB environment variables
- [ ] README: Add HA automation examples (3 provided)
- [ ] README: Add troubleshooting section
- [ ] API docs: FastAPI auto-generates /docs page

### Architecture Documentation
- [ ] Document Pattern A+B hybrid approach
- [ ] Update data flow diagrams
- [ ] Document retention policies
- [ ] Add storage capacity planning

---

## ✅ Validation Checklist

### BMAD Brownfield Compliance
- [x] Epic follows brownfield template structure
- [x] Scope limited to 3 stories (appropriate for brownfield epic)
- [x] Existing system context documented
- [x] Integration points clearly identified
- [x] Compatibility requirements specified
- [x] Risk mitigation planned
- [x] Rollback plan defined

### Technical Compliance
- [x] Follows existing InfluxDB patterns (websocket-ingestion)
- [x] Reuses existing infrastructure (InfluxDB, Docker)
- [x] Maintains backward compatibility (all existing endpoints unchanged)
- [x] Performance targets defined and measurable
- [x] Storage targets defined and reasonable

### Requirements Compliance
- [x] Schedules stored in InfluxDB
- [x] Real-time scores stored in InfluxDB
- [x] No player statistics (scope removed as requested)
- [x] HA automation endpoints designed
- [x] Hub functionality enabled (historical data + webhooks)
- [x] All data persisted with 2-year retention

---

## 🚀 Next Steps

### Immediate Actions
1. **Review Epic**: Stakeholders review epic scope and acceptance criteria
2. **Validate Schema**: Review InfluxDB schema design with data team
3. **Approve Stories**: Confirm story breakdown and sequencing
4. **Create Detailed Stories**: Story Manager develops full stories with tasks

### Development Sequence
1. **Story 12.1** (Foundation): InfluxDB integration enables persistence
2. **Story 12.2** (Analytics): Historical queries enable dashboard features
3. **Story 12.3** (Automation): HA integration enables smart home use cases

### Success Validation
- Run existing sports-data tests (ensure no regression)
- Verify InfluxDB connection and writes
- Test historical query performance
- E2E test with Home Assistant instance
- Monitor storage usage and retention

---

## 📊 Impact Assessment

### Benefits
- ✅ **Historical Analysis**: Season stats, win/loss trends, score timelines
- ✅ **Smart Automations**: HA can react to game events (start, end, scores)
- ✅ **Data Persistence**: No more data loss when cache expires
- ✅ **Hub Functionality**: Central sports data repository for all services
- ✅ **Pattern Alignment**: Matches other services (air-quality, carbon-intensity)

### Costs
- 💾 **Storage**: <20 MB per team per season (minimal)
- ⚡ **Performance**: Async writes, no impact on API response times
- 🔧 **Complexity**: Moderate (follows existing patterns)
- 📚 **Maintenance**: InfluxDB maintenance (retention, backups)

### Risk Level
**Overall Risk**: LOW
- No breaking changes to existing functionality
- Follows proven patterns from websocket-ingestion
- Easy rollback (environment variable)
- Graceful degradation if InfluxDB unavailable

---

## 🎉 Conclusion

Epic 12 successfully scoped and documented following BMAD brownfield methodology. The epic:

- ✅ **Addresses User Requirements**: All specified needs covered
- ✅ **Maintains Compatibility**: No breaking changes to existing system
- ✅ **Follows Best Practices**: Reuses existing patterns and infrastructure
- ✅ **Enables New Use Cases**: HA automations + historical analytics
- ✅ **Manageable Scope**: 3 stories, ~2 weeks implementation
- ✅ **Low Risk**: Multiple safeguards and rollback plan

**Status**: 📋 **READY FOR REVIEW AND STORY DEVELOPMENT**

---

**Epic Document**: `docs/stories/epic-12-sports-data-influxdb-persistence.md`  
**Created by**: BMad Master Agent  
**Date**: 2025-10-13  
**Version**: 1.0

