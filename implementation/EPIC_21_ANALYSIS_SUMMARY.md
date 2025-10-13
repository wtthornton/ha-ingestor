# Epic 21: Dashboard API Integration - Analysis Summary

**Date:** 2025-10-13  
**Analyst:** BMad Master Agent  
**Status:** Ready for Implementation  
**Priority:** HIGH - Critical for feature completeness

---

## 🎯 Executive Summary

### The Problem
The Health Dashboard (localhost:3000) is experiencing widespread connection failures and missing functionality across multiple tabs. Initial investigation revealed a **critical infrastructure gap**: the data-api service architecture created in Epic 13 exists in code but was **never deployed to production**.

### The Discovery
- ✅ **Code Complete**: Epic 13 successfully separated API concerns into admin-api (monitoring) and data-api (features)
- ✅ **Configuration Complete**: nginx routes configured, API clients structured correctly
- ❌ **Deployment Missing**: data-api container never built or started
- ❌ **Features Broken**: Dashboard expects data-api but finds nothing at port 8006

### The Impact
**Current State:**
- 12 dashboard tabs exist, only ~4 are functional
- WebSocket connection fails (404 error)
- Sports tab shows only setup wizard (no data integration)
- Events tab missing historical queries
- Analytics tab shows mock/placeholder data
- Alerts tab is non-functional placeholder

**Root Cause:**
All feature data endpoints route to `data-api:8006`, which doesn't exist. Dashboard gets connection refused/502 errors.

---

## 📊 Technical Analysis

### Architecture Review

**Current Architecture (As-Built):**
```
Dashboard (3000)
    ↓ nginx proxy
    ├─ /api/v1/* → admin-api:8003 (System monitoring) ✅ RUNNING
    └─ /api/v1/events, /api/devices, /api/v1/sports → data-api:8006 ❌ NOT RUNNING
```

**What Should Be Running:**
```
┌──────────────────────────────────────────────────────────────┐
│                    Dashboard (nginx)                          │
└───────────┬──────────────────────────────┬───────────────────┘
            │                              │
     System Monitoring              Feature Data
            │                              │
            ▼                              ▼
┌───────────────────────┐    ┌─────────────────────────────────┐
│  admin-api (8003)    │    │   data-api (8006)               │
│  ✅ DEPLOYED         │    │   ❌ NOT DEPLOYED               │
│                       │    │                                  │
│  - Health monitoring  │    │  - Events (8 endpoints)          │
│  - Docker management  │    │  - Devices (5 endpoints)         │
│  - System config      │    │  - Sports (9 endpoints) Epic 12  │
│  - Service control    │    │  - Analytics (4 endpoints)       │
│                       │    │  - Alerts (6 endpoints)          │
│                       │    │  - WebSocket streaming           │
└───────────────────────┘    └─────────────────────────────────┘
```

### Service Inventory

| Service | Code Status | Config Status | Deployment Status | Impact |
|---------|-------------|---------------|-------------------|---------|
| **admin-api** | ✅ Complete | ✅ Configured | ✅ Running (8003/8004) | Working correctly |
| **data-api** | ✅ Complete | ✅ Configured | ❌ **NOT RUNNING** | **All features broken** |
| **health-dashboard** | ✅ Complete | ✅ Configured | ✅ Running (3000) | Partially functional |
| sports-data | ✅ Complete | ✅ Configured | ✅ Running (8005) | Ready (not integrated) |
| InfluxDB | ✅ Complete | ✅ Configured | ✅ Running (8086) | Ready |

### Epic 12 Integration Gap

**Epic 12 Status:** ✅ Backend Complete, ❌ Frontend Missing

Epic 12 added **InfluxDB persistence** for sports data with:
- ✅ Historical query endpoints in data-api
- ✅ Game timeline tracking
- ✅ Season statistics computation
- ✅ HA automation webhooks
- ❌ Dashboard integration (only setup wizard implemented)

**Missing Dashboard Components:**
1. Live games display with polling
2. Historical data queries from InfluxDB
3. Game timeline visualization (score progression)
4. Season statistics cards
5. Team schedule view

---

## 🔍 Detailed Findings

### Finding 1: Data API Service Not Deployed
**Severity:** Critical  
**Impact:** All feature tabs non-functional

**Evidence:**
```bash
$ docker ps --filter "name=data-api"
NAMES     STATUS    PORTS
# <empty - no container running>

$ curl http://localhost:8006/health
curl: (7) Failed to connect to localhost port 8006: Connection refused
```

**Root Cause:**
- Epic 13 created service structure
- `docker-compose.yml` has data-api configuration
- **Never executed: `docker-compose up data-api`**
- Deployment step skipped or forgotten

### Finding 2: WebSocket Connection Error
**Severity:** High  
**Impact:** Real-time features broken

**Evidence:**
- Browser console: "WebSocket closed: 1005"
- Dashboard status indicator shows red "Error"
- Connection attempts to `/ws` (admin-api) instead of `/api/v1/ws` (data-api)

**Root Cause:**
- WebSocket service configured for old architecture
- Should connect to data-api for feature streaming
- Falls back to admin-api which only handles system metrics

### Finding 3: Sports Tab Incomplete
**Severity:** Medium  
**Impact:** Epic 12 features not user-accessible

**Evidence:**
- Only setup wizard visible
- No live games display
- No historical data queries
- Backend APIs exist and work (tested with curl)

**Root Cause:**
- Frontend implementation stopped at wizard
- Historical data components never built
- Epic 12 marked "complete" but dashboard integration missing

### Finding 4: Events Tab Limited
**Severity:** Medium  
**Impact:** Historical event queries unavailable

**Evidence:**
- EventStreamViewer only shows WebSocket stream
- No queries to `/api/v1/events` endpoint
- No event statistics or search functionality

**Root Cause:**
- Tab implementation focused on real-time only
- Historical query integration never added

### Finding 5: Analytics & Alerts Placeholder
**Severity:** Low-Medium  
**Impact:** Features appear complete but show mock data

**Evidence:**
- AnalyticsTab shows charts with hardcoded data
- AlertsTab is empty placeholder component
- No API calls to backend services

**Root Cause:**
- Tabs created for navigation structure
- Backend integration deferred and never completed

---

## 📋 Recommended Solution: Epic 21

### Overview
Create Epic 21 to address all identified gaps through 7 stories:

1. **Story 21.0** (CRITICAL): Deploy data-api service
2. **Story 21.1**: Fix WebSocket connection to data-api
3. **Story 21.2**: Complete Sports tab (Epic 12 integration)
4. **Story 21.3**: Add Events tab historical queries
5. **Story 21.4**: Implement Analytics tab real data
6. **Story 21.5**: Implement Alerts tab functionality
7. **Story 21.6**: Update OverviewTab enhanced health

### Story Priorities

**P0 - Blocker (Story 21.0):**
- Deploy data-api service
- **Duration:** 1-2 hours
- **Blocks:** All other stories

**P1 - High (Stories 21.1, 21.6):**
- Fix core connections and monitoring
- **Duration:** 2-3 days

**P2 - Medium (Stories 21.3, 21.4, 21.5):**
- Feature data integration
- **Duration:** 4-5 days

**P3 - Medium (Story 21.2):**
- Sports integration (large story)
- **Duration:** 5-7 days

### Success Criteria

✅ **All 12 dashboard tabs functional with real data**
- Overview: Enhanced health monitoring
- Custom: Saved layouts
- Services: Management controls
- Dependencies: Animated graph
- Devices: Browse + filter (working)
- Events: Real-time + historical
- Logs: Aggregated display (working)
- Sports: Live games + historical stats
- Data Sources: Status monitoring (working)
- Analytics: Real metrics + charts
- Alerts: Active alerts management
- Configuration: Service config (working)

✅ **No console errors during normal operation**

✅ **Performance targets met:**
- Dashboard load: <2s
- Historical queries: <200ms
- WebSocket latency: <100ms
- Tab switching: <500ms

---

## 📊 Impact Assessment

### Business Impact
- **User Experience:** Major improvement - all advertised features will work
- **Demo/Presentation:** Dashboard ready for demos (currently embarrassing)
- **Feature Completeness:** 100% vs current ~33%
- **Technical Debt:** Eliminates Epic 12/13 completion gaps

### Technical Impact
- **Architecture:** Validates Epic 13 separation-of-concerns
- **Performance:** Historical queries faster than real-time polling
- **Scalability:** Enables independent scaling of data vs monitoring APIs
- **Maintainability:** Clear API boundaries reduce coupling

### Risk Impact
- **Current Risk:** HIGH - Major features advertised but broken
- **Post-Epic 21:** LOW - All features functional and tested

---

## 🚀 Implementation Timeline

### Week 1: Critical Deployment
- **Day 1:** Story 21.0 - Deploy data-api (2 hours)
- **Day 1-2:** Story 21.1 - Fix WebSocket (1 day)
- **Day 2-3:** Story 21.6 - Update OverviewTab (1 day)
- **Day 3-5:** Story 21.3 - Events historical (2 days)

### Week 2: Feature Integration
- **Day 1-2:** Story 21.4 - Analytics real data (2 days)
- **Day 3-4:** Story 21.5 - Alerts functionality (2 days)
- **Day 5:** Testing and fixes

### Week 3: Sports Completion
- **Day 1-5:** Story 21.2 - Sports tab full implementation (5 days)

### Week 4: Polish & QA
- **Day 1-2:** Integration testing
- **Day 3:** Performance testing
- **Day 4:** E2E testing (Playwright)
- **Day 5:** Documentation + deployment

**Total Duration:** 3-4 weeks

---

## 💰 Cost-Benefit Analysis

### Costs
- **Development Time:** ~3-4 weeks (1 full-stack developer)
- **Testing Time:** ~1 week (QA)
- **Risk:** Low (all backend APIs exist and work)

### Benefits
- **Feature Completeness:** 67% increase (4/12 → 12/12 tabs functional)
- **User Satisfaction:** High (all promised features delivered)
- **Technical Debt:** Eliminated (Epics 12 & 13 truly complete)
- **Demo-Ready:** Dashboard suitable for customer demos
- **Maintenance:** Reduced confusion from "complete" but broken features

### ROI
**High** - Relatively small investment (4-5 weeks total) to complete promised functionality and eliminate technical debt from 2 major epics.

---

## 🎯 Recommendations

### Immediate Actions (This Week)
1. **Deploy data-api service** (Story 21.0)
   - Estimated: 1-2 hours
   - Impact: Unblocks all other work
   - Risk: Very low (service tested in isolation)

2. **Fix WebSocket connection** (Story 21.1)
   - Estimated: 1 day
   - Impact: Restores real-time features
   - Risk: Low (well-understood change)

3. **Update Overview health** (Story 21.6)
   - Estimated: 1 day
   - Impact: Improves primary monitoring view
   - Risk: Very low (enhancement only)

### Short-Term (Next 2 Weeks)
- Complete Stories 21.3, 21.4, 21.5
- Get all feature tabs functional
- Achieve ~80% feature completion

### Medium-Term (Weeks 3-4)
- Complete Story 21.2 (Sports integration)
- Full E2E testing
- Documentation updates
- Achieve 100% feature completion

### Long-Term (Post-Epic 21)
- Monitor performance metrics
- Gather user feedback
- Plan future dashboard enhancements
- Consider mobile app based on completed APIs

---

## 📝 Key Takeaways

1. **Critical Gap Identified:** data-api service not deployed despite being fully built
2. **Epic 13 Incomplete:** Code complete but deployment skipped
3. **Epic 12 Half-Done:** Backend excellent, frontend integration missing
4. **Quick Win Available:** Story 21.0 (2 hours) unblocks everything
5. **Reasonable Scope:** 3-4 weeks to full completion
6. **High ROI:** Small investment, major feature delivery

---

## 🎬 Next Steps

### For Product Owner
1. Review and approve Epic 21 scope
2. Prioritize Story 21.0 for immediate execution
3. Allocate resources (1 full-stack dev, 1 QA)
4. Set success metrics and acceptance criteria

### For Development Team
1. Review Epic 21 stories
2. Estimate effort for each story
3. Execute Story 21.0 deployment (start immediately)
4. Plan sprint allocation for remaining stories

### For QA Team
1. Review test requirements in Epic 21
2. Prepare test environments
3. Create E2E test scenarios for new features
4. Plan performance testing approach

---

**Analysis Completed:** 2025-10-13  
**Reviewed By:** BMad Master Agent  
**Epic Document:** [epic-21-dashboard-api-integration-fix.md](../docs/stories/epic-21-dashboard-api-integration-fix.md)  
**Deployment Checklist:** [EPIC_21_DATA_API_DEPLOYMENT_CHECKLIST.md](EPIC_21_DATA_API_DEPLOYMENT_CHECKLIST.md)

