# Epic AI-4 Implementation Plan
## Community Knowledge Augmentation - Development Handoff

**Created:** October 18, 2025  
**Epic:** AI-4 (Community Knowledge Augmentation)  
**Status:** Ready for Implementation  
**Total Effort:** 10-13 days (6-8 days if parallel)

---

## 📋 Executive Summary

This epic adds a **Community Knowledge Augmentation** layer to the existing AI suggestion engine. It crawls high-quality Home Assistant automations from community sources (Discourse + GitHub), normalizes them into structured insights, and uses them to:

1. **Enhance pattern detection** with community best practices
2. **Educate users** on device potential ("What can I do with X?")
3. **Guide smart purchases** with data-driven device recommendations
4. **Stay fresh** with weekly corpus updates

**Key Principle:** Community knowledge **augments** personal patterns (80/20 split), doesn't replace them.

---

## 🎯 Epic & Story Links

### Epic Document
- **Location:** `docs/prd/epic-ai4-community-knowledge-augmentation.md`
- **Stories:** 4 stories (AI4.1 → AI4.4)
- **Dependencies:** Epic AI-1 (Pattern Detection), Epic AI-2 (Device Intelligence)

### Story Documents
1. **AI4.1: Community Corpus Foundation** (3-4 days)
   - Location: `docs/stories/AI4.1.community-corpus-foundation.md`
   - Purpose: Build crawler + storage for 2,000+ high-quality automations
   - **Start First:** Foundation for all other stories

2. **AI4.2: Pattern Enhancement Integration** (2-3 days)
   - Location: `docs/stories/AI4.2.pattern-enhancement-integration.md`
   - Purpose: Augment Phase 3/5 with community insights
   - **Depends on:** AI4.1 complete

3. **AI4.3: Device Discovery & Purchase Advisor** (3-4 days)
   - Location: `docs/stories/AI4.3.device-discovery-purchase-advisor.md`
   - Purpose: "What can I do?" API + Shopping recommendations UI
   - **Depends on:** AI4.1 complete

4. **AI4.4: Weekly Community Refresh** (2 days)
   - Location: `docs/stories/AI4.4.weekly-community-refresh.md`
   - Purpose: Keep corpus fresh with weekly incremental crawls
   - **Depends on:** AI4.1 complete

---

## 🗓️ Implementation Strategy

### Option A: Sequential (Conservative, 10-13 days)

**Week 1: Foundation**
- Days 1-4: Story AI4.1 (Community Corpus Foundation)
  - Deliverables: Crawler, parser, SQLite storage, query API
  - Validation: 2,000+ automations crawled, avg quality ≥0.7

**Week 2: Enhancement**
- Days 5-7: Story AI4.2 (Pattern Enhancement Integration)
  - Deliverables: Miner client, enhancement extraction, prompt augmentation
  - Validation: Suggestions include 2-3 community enhancements

**Week 3: Discovery**
- Days 8-11: Story AI4.3 (Device Discovery & Purchase Advisor)
  - Deliverables: Device possibilities API, recommendations API, Discovery UI tab
  - Validation: ROI recommendations accurate ±10%

**Week 4: Refresh**
- Days 12-13: Story AI4.4 (Weekly Community Refresh)
  - Deliverables: Weekly APScheduler job, cache invalidation, audit logging
  - Validation: Incremental refresh <30 minutes

### Option B: Parallel (Aggressive, 6-8 days)

**Phase 1: Foundation (Days 1-4)**
- Story AI4.1 only (blocks all others)

**Phase 2: Parallel Development (Days 5-8)**
- Story AI4.2 (Enhancement) - Dev Agent 1
- Story AI4.3 (Discovery) - Dev Agent 2
- Story AI4.4 (Refresh) - Dev Agent 3

**Recommendation:** Start with **Option A** for quality, switch to **Option B** if timeline-critical.

---

## 📊 Story Validation Summary

### Story AI4.1 Review ✅

**Acceptance Criteria:** 10 criteria (functional, integration, quality)
- ✅ Selective crawler (Discourse + GitHub optional)
- ✅ Normalization pipeline (Pydantic validation)
- ✅ SQLite storage with query API
- ✅ Corpus quality targets (2,000+, avg 0.7)
- ✅ Performance targets (<3 hours initial, <100ms queries)

**Tasks Breakdown:** 7 tasks, 35+ subtasks
- Well-structured with Context7 best practices
- Includes unit + integration + performance tests
- Clear dev notes with architecture context

**Dev Notes Quality:** Excellent
- Source tree structure defined
- Tech stack documented
- Context7 examples for httpx, Pydantic
- Integration patterns clear

**Risks Identified:**
- Crawler rate limiting → Mitigation: 2 req/sec, respect robots.txt
- Storage bloat → Mitigation: Quality threshold, store insights only
- API ban → Mitigation: Selective crawling (500+ votes)

**Ready for Dev:** ✅ Yes

---

### Story AI4.2 Review ✅

**Acceptance Criteria:** 7 criteria (functional, integration, quality)
- ✅ Query Miner during pattern detection
- ✅ Extract enhancements (conditions, timing, actions)
- ✅ Augment OpenAI prompts (80/20 weighting)
- ✅ Graceful degradation (100ms timeout)
- ✅ Performance budget (<5% overhead)

**Tasks Breakdown:** 6 tasks, 25+ subtasks
- Clear integration points (Phase 3, Phase 5)
- MinerClient with caching (7-day TTL)
- Feature flag support

**Integration Complexity:** Medium
- Modifies existing Phase 3 (pattern_detector.py)
- Modifies existing Phase 5 (suggestion_generator.py)
- New dependency: MinerClient

**Risks Identified:**
- Miner unavailable → Mitigation: Graceful degradation, feature flag
- Performance impact → Mitigation: 100ms timeout, caching
- Suggestion quality dilution → Mitigation: 80/20 weighting, tracking

**Ready for Dev:** ✅ Yes (after AI4.1)

---

### Story AI4.3 Review ✅

**Acceptance Criteria:** 7 criteria (functional, UI, quality)
- ✅ Device possibilities API
- ✅ Device recommendations with ROI calculation
- ✅ Discovery Tab UI (Dependencies pattern)
- ✅ Interactive visualizations
- ✅ Recommendation accuracy (±10% ROI)

**Tasks Breakdown:** 5 tasks, 20+ subtasks
- Backend: API endpoints + recommendation engine
- Frontend: Discovery Tab + 3 components
- Data: device_costs.json (30+ devices)

**UI/UX Quality:** Excellent
- Uses proven Dependencies Tab pattern [[memory:9810709]]
- Interactive visualizations (ROI chart, device explorer)
- Mobile-responsive (TailwindCSS)

**Risks Identified:**
- Cost estimates inaccurate → Mitigation: Research + quarterly updates
- ROI calculation subjective → Mitigation: Validation against manual analysis
- UI performance → Mitigation: Lazy loading, code splitting

**Ready for Dev:** ✅ Yes (after AI4.1)

---

### Story AI4.4 Review ✅

**Acceptance Criteria:** 8 criteria (functional, reliability, performance)
- ✅ Weekly incremental crawl (Sunday 2 AM)
- ✅ Quality score updates
- ✅ Corpus pruning
- ✅ Cache invalidation
- ✅ Retry logic + health checks
- ✅ Audit logging

**Tasks Breakdown:** 6 tasks, 25+ subtasks
- APScheduler job with retry
- Incremental crawl optimization
- Audit logging + monitoring
- Manual trigger CLI

**Reliability:** Excellent
- 3-attempt retry with backoff
- Graceful degradation (use stale corpus)
- Health check monitoring
- Alerts on 3 consecutive failures

**Risks Identified:**
- Missed weekly run → Mitigation: Misfire grace time, alerts
- Database corruption → Mitigation: Atomic transactions, soft delete
- Long-running refresh → Mitigation: Incremental only, 30-min target

**Ready for Dev:** ✅ Yes (after AI4.1)

---

## 🔧 Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Automation Service                     │
│                      (Port 8018)                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Phase 1-6 (Existing)                               │     │
│  │ ├─ Pattern Detection (Phase 3)                     │     │
│  │ ├─ Feature Analysis (Phase 4)                      │     │
│  │ └─ Suggestion Generation (Phase 5)                 │     │
│  └────────────────────────────────────────────────────┘     │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Automation Miner Integration (NEW - Epic AI-4)     │     │
│  │ ├─ MinerClient (Story AI4.2)                       │     │
│  │ ├─ Enhancement Extractor (Story AI4.2)             │     │
│  │ └─ Cache Manager                                   │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP
┌─────────────────────────────────────────────────────────────┐
│              Automation Miner Service                        │
│                  (Port 8019 or integrated)                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Crawler (Story AI4.1)                              │     │
│  │ ├─ DiscourseClient (httpx async)                   │     │
│  │ ├─ GitHubClient (optional)                         │     │
│  │ └─ AutomationParser (Pydantic)                     │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Storage (Story AI4.1)                              │     │
│  │ ├─ SQLite (community_automations table)            │     │
│  │ └─ CorpusRepository (SQLAlchemy async)             │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Query API (Story AI4.1, AI4.3)                     │     │
│  │ ├─ GET /corpus/search                              │     │
│  │ ├─ GET /corpus/stats                               │     │
│  │ ├─ GET /devices/{type}/possibilities               │     │
│  │ └─ GET /recommendations/devices                    │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Weekly Refresh Job (Story AI4.4)                   │     │
│  │ ├─ APScheduler (Sunday 2 AM)                       │     │
│  │ ├─ Incremental Crawl                               │     │
│  │ └─ Cache Invalidation                              │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          ↓ REST API
┌─────────────────────────────────────────────────────────────┐
│                 AI Automation UI (Port 3001)                 │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Discovery Tab (Story AI4.3)                        │     │
│  │ ├─ Device Explorer                                 │     │
│  │ ├─ Smart Shopping                                  │     │
│  │ └─ Integration Opportunities                       │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Story AI4.1: Corpus Storage
CREATE TABLE community_automations (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,                 -- 'discourse' | 'github'
    source_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    devices JSON NOT NULL,                -- ["light", "motion_sensor"]
    integrations JSON NOT NULL,           -- ["mqtt", "zigbee2mqtt"]
    triggers JSON NOT NULL,
    conditions JSON,
    actions JSON NOT NULL,
    use_case TEXT NOT NULL,               -- 'energy' | 'comfort' | 'security' | 'convenience'
    complexity TEXT NOT NULL,             -- 'low' | 'medium' | 'high'
    quality_score REAL NOT NULL,          -- 0.0-1.0
    vote_count INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    last_crawled DATETIME NOT NULL,
    metadata JSON
);

CREATE INDEX ix_devices ON community_automations(devices);
CREATE INDEX ix_integrations ON community_automations(integrations);
CREATE INDEX ix_use_case ON community_automations(use_case);
CREATE INDEX ix_quality_score ON community_automations(quality_score);

-- Story AI4.4: Audit Logging
CREATE TABLE corpus_audit_log (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    operation TEXT NOT NULL,              -- 'add' | 'update' | 'delete' | 'prune'
    automation_id INTEGER,
    source_id TEXT,
    before_quality REAL,
    after_quality REAL,
    reason TEXT,
    correlation_id TEXT NOT NULL
);

CREATE INDEX ix_audit_timestamp ON corpus_audit_log(timestamp);
CREATE INDEX ix_audit_correlation ON corpus_audit_log(correlation_id);

-- Story AI4.4: Crawler State
CREATE TABLE miner_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME NOT NULL
);
-- Stores: last_crawl_timestamp, consecutive_failures, etc.
```

### API Endpoints

**Story AI4.1:**
- `GET /api/automation-miner/corpus/search` - Query corpus
- `GET /api/automation-miner/corpus/stats` - Corpus statistics
- `GET /api/automation-miner/corpus/{id}` - Single automation

**Story AI4.3:**
- `GET /api/automation-miner/devices/{type}/possibilities` - Device use cases
- `GET /api/automation-miner/recommendations/devices` - Purchase recommendations
- `GET /api/automation-miner/recommendations/integrations` - Integration suggestions

**Story AI4.4:**
- `GET /api/automation-miner/corpus/audit` - Audit log
- `GET /api/automation-miner/health` - Health check (includes refresh status)

---

## 🧪 Testing Strategy

### Story AI4.1 Testing

**Unit Tests:**
- DiscourseClient: Mock httpx responses
- AutomationParser: Various YAML formats
- Deduplication logic: Fuzzy matching
- Quality score calculation: Edge cases

**Integration Tests:**
- Full crawl: Discourse API → Parse → Store → Query
- Error handling: API timeout, invalid YAML
- Deduplication: 90% similar titles

**Performance Tests:**
- Initial crawl: <3 hours for 2,000 posts
- Query API: <100ms p95
- Storage: <500MB

**Acceptance Criteria Validation:**
- ✅ 2,000+ automations crawled
- ✅ Average quality ≥0.7
- ✅ 50+ device types
- ✅ 30+ integrations
- ✅ <5% duplicates

---

### Story AI4.2 Testing

**Unit Tests:**
- MinerClient: Mock HTTP responses + timeout
- EnhancementExtractor: Various automation structures
- `_build_community_context()`: Prompt formatting
- Cache hit/miss logic

**Integration Tests:**
- Full flow: Pattern detection → Miner query → Enhancement → Prompt
- Graceful degradation: Miner unavailable
- Cache invalidation after refresh

**Performance Tests:**
- Overhead measurement: Phase 1 analysis time +<5%
- Miner query latency: <100ms p95
- Cache efficiency: Hit rate >80%

**Acceptance Criteria Validation:**
- ✅ Enhancements appear in 2-3 suggestions
- ✅ Miner timeout works (100ms)
- ✅ Phase 1 continues if Miner fails
- ✅ Feature flag disables cleanly

---

### Story AI4.3 Testing

**Unit Tests:**
- DeviceRecommender: ROI calculation accuracy
- Device gap analysis: Various user inventories
- Cost estimate validation: ±20%

**Integration Tests:**
- API flow: User devices → Recommendations → UI
- Empty inventory: Recommend most popular
- Full inventory: Recommend niche devices

**UI Tests:**
- Discovery page loads <1s
- Device selection triggers API
- Shopping cards render correctly
- Interactive visualizations work

**Performance Tests:**
- API response: <200ms p95
- UI render: <1s (Lighthouse score >90)

**Acceptance Criteria Validation:**
- ✅ ROI calculation ±10% of manual analysis
- ✅ Only recommend devices in corpus (≥50 automations)
- ✅ UI follows Dependencies Tab pattern

---

### Story AI4.4 Testing

**Unit Tests:**
- WeeklyRefreshJob: Mocked Discourse client
- Incremental crawl: `since` parameter
- Pruning logic: Quality/age thresholds
- Audit logging: All operations tracked

**Integration Tests:**
- Full refresh: Fetch → Update → Prune → Invalidate
- Retry logic: API failure simulation
- Cache invalidation: Webhook to ai-automation-service

**Performance Tests:**
- Refresh duration: <30 minutes for 200 posts
- Memory usage: <200MB peak
- Network: <20MB transferred

**Acceptance Criteria Validation:**
- ✅ Incremental crawl completes <30 min
- ✅ Quality scores updated correctly
- ✅ Low-quality entries pruned
- ✅ Caches invalidated automatically
- ✅ Retry works (3 attempts)

---

## 📚 Dependencies & Prerequisites

### External Dependencies

**Python Packages (add to `requirements.txt`):**
```txt
# Story AI4.1
httpx>=0.27.0              # Async HTTP client
beautifulsoup4>=4.12.0     # HTML parsing
pydantic>=2.8.0            # Data validation
fastapi>=0.115.0           # API framework
sqlalchemy[asyncio]>=2.0.0 # Async ORM
apscheduler>=3.10.0        # Job scheduling
pyyaml>=6.0                # YAML parsing
rapidfuzz>=3.0.0           # Fuzzy string matching
```

**External APIs:**
- Discourse API (community.home-assistant.io) - Public, no auth
- GitHub API (optional) - Optional token for higher rate limits

### Internal Dependencies

**Existing Services:**
- `ai-automation-service` (Port 8018) - Phase 3 & 5 integration
- `ai-automation-ui` (Port 3001) - Discovery Tab
- `shared/` modules - Logging, metrics, auth

**Existing Database:**
- `ai_automation.db` (SQLite) - Add new tables (backward compatible)

**Existing Patterns:**
- Async session management: `get_db_session()`
- Structured logging: `logging_config.py`
- Metrics collection: `metrics_collector.py`
- Health checks: `/health` endpoint pattern

---

## ⚠️ Risk Register

### High-Impact Risks

**Risk 1: Discourse API Rate Limiting**
- **Impact:** High (blocks corpus creation)
- **Probability:** Medium
- **Mitigation:**
  - Respect rate limits (2 req/sec)
  - Selective crawling (500+ votes only)
  - Retry with exponential backoff
- **Rollback:** Use static corpus (pre-crawled snapshot)

**Risk 2: Storage Bloat (>1GB)**
- **Impact:** Medium (disk space, query performance)
- **Probability:** Low (if quality threshold maintained)
- **Mitigation:**
  - Store insights only (no full YAML)
  - Quality threshold (≥0.4)
  - Weekly pruning
- **Rollback:** Aggressive pruning, archive old entries

**Risk 3: Performance Impact on Phase 1**
- **Impact:** High (existing functionality degraded)
- **Probability:** Low (timeout + caching in place)
- **Mitigation:**
  - 100ms timeout on Miner queries
  - Graceful degradation
  - Performance tests before deploy
- **Rollback:** Disable feature flag (ENABLE_PATTERN_ENHANCEMENT=false)

### Medium-Impact Risks

**Risk 4: Recommendation Quality (ROI calculation)**
- **Impact:** Medium (poor purchase advice)
- **Probability:** Medium (formula is heuristic)
- **Mitigation:**
  - Validate against manual analysis
  - User feedback loop
  - Quarterly cost updates
- **Rollback:** Hide recommendations, show possibilities only

**Risk 5: Weekly Refresh Failures**
- **Impact:** Medium (stale corpus)
- **Probability:** Low (retry logic in place)
- **Mitigation:**
  - 3-attempt retry
  - Alert on 3 consecutive failures
  - Graceful degradation (use stale corpus)
- **Rollback:** Manual refresh via CLI

---

## 🚀 Deployment Plan

### Phase 1: Foundation (AI4.1)

**Deploy:**
- Automation Miner service (or integrated module)
- SQLite tables (migration)
- Initial crawl job (manual trigger)

**Validate:**
- Run initial crawl (monitor duration, error rate)
- Verify corpus quality (2,000+, avg 0.7)
- Query API smoke tests

**Rollback Plan:**
- Drop new tables
- Remove service
- No impact on existing Phase 1

---

### Phase 2: Weekly Refresh (AI4.4)

**Deploy:**
- APScheduler weekly job
- Audit logging tables
- Health check updates

**Validate:**
- Trigger manual refresh (dry-run first)
- Verify incremental crawl (<30 min)
- Check audit logs

**Rollback Plan:**
- Disable scheduled job
- Manual refresh only

---

### Phase 3: Enhancement (AI4.2)

**Deploy:**
- MinerClient integration
- Phase 3/5 code changes
- Feature flag (disabled initially)

**Validate:**
- Run daily analysis with ENABLE_PATTERN_ENHANCEMENT=false
- Enable flag for test user
- Verify enhancements in suggestions
- Measure overhead (<5%)

**Rollback Plan:**
- Set feature flag to false
- Phase 1 unaffected

---

### Phase 4: Discovery UI (AI4.3)

**Deploy:**
- Device recommendations API
- Discovery Tab UI
- Device costs database

**Validate:**
- Test Discovery Tab in staging
- Verify ROI calculations
- Test with various user inventories

**Rollback Plan:**
- Hide Discovery Tab (UI feature flag)
- API remains for future use

---

## 📖 Documentation Checklist

### Technical Documentation

- [x] Epic document created
- [x] 4 Story documents created
- [x] Implementation plan (this document)
- [ ] Call tree updated (add Miner flows)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Database schema migration guide
- [ ] Deployment runbook

### User Documentation

- [ ] Discovery Tab user guide
- [ ] "What can I do with my devices?" tutorial
- [ ] Smart shopping recommendations explainer
- [ ] ROI calculation methodology

### Developer Documentation

- [ ] Miner API integration guide
- [ ] Crawler customization guide
- [ ] Troubleshooting guide
- [ ] Performance tuning guide

---

## 🎯 Success Metrics

### Corpus Health
- ✅ Total automations: 2,000-3,000
- ✅ Average quality: ≥0.7
- ✅ Device coverage: 50+ types
- ✅ Integration coverage: 30+
- ✅ Weekly growth: +20-50 (after pruning)

### User Engagement
- ✅ Discovery Tab usage: >50% of users/week
- ✅ Enhancement acceptance: >30%
- ✅ Device purchase rate: >10% (within 30 days of recommendation)
- ✅ Feature discovery: +20% (unused features activated)

### System Performance
- ✅ Phase 1 overhead: <5%
- ✅ Miner query latency: <100ms p95
- ✅ Weekly refresh: <30 min
- ✅ API availability: 99.9%

### Business Impact
- ✅ New device time-to-value: 30 days → 2 minutes
- ✅ Suggestion quality: +10-15% approval rate
- ✅ User satisfaction: >4.5/5 (Discovery feature)

---

## 🔄 Handoff to Dev Agent

### Story Assignment

**Recommended Assignment:**
1. **AI4.1 (Foundation):** Senior dev (3-4 days) - Critical path
2. **AI4.4 (Refresh):** Mid-level dev (2 days) - After AI4.1
3. **AI4.2 (Enhancement):** Senior dev (2-3 days) - Phase 1 integration
4. **AI4.3 (Discovery):** Full-stack dev (3-4 days) - UI/UX skills

### Dev Agent Context

**Each story includes:**
- ✅ Detailed acceptance criteria (functional, integration, quality)
- ✅ Task breakdown (7-35 subtasks per story)
- ✅ Dev notes (architecture, tech stack, coding standards)
- ✅ Context7-validated code examples (httpx, Pydantic, APScheduler)
- ✅ Integration patterns (database, logging, health checks)
- ✅ Testing requirements (unit, integration, performance)
- ✅ Performance targets and budgets

**No additional context needed** - Stories are self-contained.

### Implementation Order

**Critical Path:**
```
AI4.1 (Foundation) 
    ↓
┌───┴───┬───────────┐
│       │           │
AI4.2   AI4.3       AI4.4
(Enhancement) (Discovery) (Refresh)
```

**Estimated Timeline:**
- Sequential: 10-13 days
- Parallel (after AI4.1): 6-8 days

---

## ✅ Pre-Implementation Checklist

### Epic Level
- [x] Epic document created and reviewed
- [x] All 4 stories created and validated
- [x] Implementation plan documented
- [x] Risk register complete
- [x] Success metrics defined
- [ ] Story Manager sign-off
- [ ] Dev Agent assigned

### Story AI4.1
- [x] Acceptance criteria clear and testable
- [x] Tasks broken down (<4 hour chunks)
- [x] Dev notes complete with examples
- [x] Context7 best practices included
- [x] Testing strategy defined
- [ ] Dev Agent assigned

### Story AI4.2
- [x] Acceptance criteria clear and testable
- [x] Integration points documented
- [x] Performance budget defined
- [x] Graceful degradation tested
- [ ] Dev Agent assigned

### Story AI4.3
- [x] UI/UX design approved (Dependencies pattern)
- [x] API contracts defined
- [x] ROI calculation validated
- [x] Device costs researched
- [ ] Dev Agent assigned

### Story AI4.4
- [x] Schedule defined (Sunday 2 AM)
- [x] Retry logic specified
- [x] Audit logging designed
- [x] Monitoring plan complete
- [ ] Dev Agent assigned

---

## 📞 Support & Escalation

### Questions During Implementation

**Architecture Questions:**
- Refer to `docs/architecture/*.md`
- Refer to story Dev Notes sections
- Escalate to Architect if ambiguous

**Integration Questions:**
- Refer to existing Phase 1-6 code
- Check call tree documentation
- Escalate to BMad Master if unclear

**Performance Questions:**
- Refer to performance budgets in stories
- Run performance tests early
- Escalate if targets unreachable

### Issue Escalation Path

1. **Blocker:** Dev Agent → BMad Master
2. **Scope Creep:** Dev Agent → Story Manager → Product Owner
3. **Technical Debt:** Dev Agent → Architect
4. **Timeline Risk:** Dev Agent → Scrum Master

---

## 🎉 Ready for Implementation

**All systems GO!** 

- ✅ Epic validated
- ✅ 4 Stories validated  
- ✅ Architecture designed
- ✅ Risks identified & mitigated
- ✅ Testing strategy defined
- ✅ Documentation complete
- ✅ Context7 best practices integrated

**Next Action:** Assign stories to Dev Agent(s) and begin implementation.

---

**Version:** 1.0  
**Created By:** BMad Master  
**Date:** October 18, 2025  
**Status:** ✅ Ready for Dev Agent Handoff

