# Epic 11: NFL & NHL Sports Data Integration - Brownfield Enhancement

## Epic Goal

Enable users to monitor their favorite NFL and NHL teams with real-time game updates, statistics visualization, and smart alerting, integrated seamlessly into the existing HA Ingestor Dashboard with team-specific data fetching to optimize API usage.

## Epic Description

### Existing System Context

- **Current functionality:** HA Ingestor Dashboard monitors Home Assistant events, enriches with weather data, stores in InfluxDB
- **Technology stack:** React 18.2 + TypeScript, Python 3.11 + FastAPI, Docker, InfluxDB 2.7
- **Integration points:** Admin API (port 8004), Health Dashboard (port 3000), Enrichment Pipeline

### Enhancement Details

**What's being added:**
- New Sports Data Service (FastAPI) on port 8005
- Team selection interface in dashboard
- Live game monitoring cards with real-time updates
- Sports tab in dashboard with Recharts visualizations
- API integration with ESPN/NHL Official APIs
- User preferences storage for selected teams

**How it integrates:**
- New microservice follows existing Docker Compose pattern
- Dashboard adds new tab using existing UI patterns
- Uses existing Nginx proxy configuration
- Stores preferences in local storage (Phase 1) or InfluxDB (Phase 2)
- Real-time updates via polling (consistent with existing patterns)

**Success criteria:**
- Users can select 2-5 favorite teams
- Live games display with <15s update latency
- API usage stays under 100 calls/day (free tier)
- No performance degradation to existing features
- Mobile-responsive design matches existing UI

## Stories

### Story 11.1: Sports Data Backend Service
Create FastAPI service for sports data fetching with team-specific filtering, caching, and ESPN/NHL API integration.

**Key Tasks:**
- FastAPI service structure
- ESPN/NHL API clients
- Team-based filtering logic
- Redis/in-memory caching (15s TTL)
- Health check endpoint
- Docker container configuration

### Story 11.2: Team Selection UI & User Preferences
Implement 3-step setup wizard for team selection and preferences management interface.

**Key Tasks:**
- Setup wizard component (3 steps)
- Team grid selection UI
- Search/filter functionality
- Preferences storage (localStorage)
- Empty state handling
- Team management interface

### Story 11.3: Live Games Display & Real-Time Updates
Create live game cards with real-time score updates, animations, and game status indicators.

**Key Tasks:**
- LiveGameCard component with animations
- Real-time polling (30s intervals)
- Score change animations
- Game status indicators
- Sports tab layout
- Mobile-responsive design

### Story 11.4: Statistics Visualization with Recharts
Add Recharts-powered visualizations for game statistics, score timelines, and team comparisons.

**Key Tasks:**
- ScoreTimeline component (LineChart)
- StatsComparison component (BarChart)
- Team performance charts
- Responsive chart containers
- Data transformation for charts
- Interactive tooltips

## Compatibility Requirements

- [x] Existing APIs remain unchanged (new service on separate port)
- [x] Database schema changes are backward compatible (no schema changes)
- [x] UI changes follow existing patterns (Tailwind CSS, React hooks)
- [x] Performance impact is minimal (separate service, cached data)

## Risk Mitigation

**Primary Risk:** API rate limit exhaustion affecting other services

**Mitigation:** 
- Team selection limits data fetching
- Caching with appropriate TTL
- API usage monitoring endpoint
- Warning system when approaching limits

**Rollback Plan:** 
- Stop sports-data Docker container
- Hide Sports tab in UI (feature flag)
- No database changes to rollback
- Existing functionality unaffected

## Definition of Done

- [x] All 4 stories completed with acceptance criteria met
- [x] Existing dashboard functionality verified (no regressions)
- [x] Sports service integrates via Docker Compose
- [x] API usage monitoring in place
- [x] E2E tests for sports features
- [x] Mobile responsive on iOS and Android
- [x] Dark mode support consistent with existing UI
- [x] Documentation updated (API docs, user guide)

## Dependencies

- ESPN API key or NHL Official API access
- Recharts library (add to package.json)
- No architectural changes required

## Estimated Effort

- Story 11.1: 3 days (backend service)
- Story 11.2: 2 days (team selection UI)
- Story 11.3: 3 days (live games display)
- Story 11.4: 2 days (statistics visualization)

**Total:** ~10 days (2 weeks)

---

**Status:** Draft  
**Created:** October 12, 2025  
**Epic Owner:** Product Team  
**Development Lead:** TBD

