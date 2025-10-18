# Story 24.1: Fix Hardcoded Monitoring Metrics - Created

**Date:** October 18, 2025  
**Epic:** 24 - Monitoring Data Quality & Accuracy  
**Status:** ✅ Story Created, Ready for Implementation

---

## Story Overview

**Goal:** Replace 3 hardcoded placeholder values in monitoring metrics with accurate, calculated values

**Estimated Effort:** 2-3 hours  
**Priority:** High (Data Quality)  
**Complexity:** Low-Medium

---

## What Was Created

### 1. Story Document
**Location:** `docs/stories/story-24.1-fix-hardcoded-monitoring-metrics.md`

**Contents:**
- Complete user story with acceptance criteria
- Detailed task breakdown (5 main tasks, 20+ subtasks)
- Technical approach and implementation guidance
- Testing requirements
- Documentation requirements
- Dev notes with architecture context

### 2. Epic Document
**Location:** `docs/prd/epic-24-monitoring-data-quality.md`

**Contents:**
- Epic goal and business value
- Context from audit findings
- Scope (in/out)
- Technical approach
- Success criteria
- Risk assessment

### 3. Epic List Updated
**Location:** `docs/prd/epic-list.md`

**Changes:**
- Added Epic 24 entry
- Updated epic counts (24 total, 22 complete, 1 in progress)
- Updated last updated date to October 18, 2025

---

## The 3 Issues to Fix

### Issue 1: System Uptime (HARDCODED)
**Current Behavior:**
```python
# services/data-api/src/analytics_endpoints.py:216
uptime=99.9  # TODO: Calculate from service health data
```
**Always returns 99.9%** - Administrator cannot see real uptime

**Fix:**
- Track service start timestamp
- Calculate actual uptime percentage
- Update 3 locations (data-api, admin-api, ai-automation-service)

---

### Issue 2: API Response Time (PLACEHOLDER)
**Current Behavior:**
```python
# services/admin-api/src/stats_endpoints.py:488
metrics["response_time_ms"] = 0  # placeholder - not available in current API
```
**Always returns 0ms** - Metric is meaningless

**Fix Options:**
- **Option A:** Implement timing middleware to measure real response time
- **Option B:** Remove metric if measurement too complex
- Story includes both approaches, dev can choose

---

### Issue 3: Active Data Sources (HARDCODED LIST)
**Current Behavior:**
```python
# services/admin-api/src/stats_endpoints.py:815
return ["home_assistant", "weather_api", "sports_api"]  # Hardcoded
```
**Always returns same 3 sources** - New sources not discovered

**Fix:**
- Query InfluxDB for measurements with recent data
- Return dynamic list based on actual write activity
- Cache results to avoid excessive queries

---

## Task Breakdown

### Task 1: Fix System Uptime Calculation
- Add service start timestamp tracking
- Implement `calculate_uptime()` function
- Update 3 service locations
- **Estimated:** 30-45 minutes

### Task 2: Fix/Remove API Response Time
- Evaluate measurement approach (implement vs remove)
- If implementing: Add timing middleware
- If removing: Update frontend
- **Estimated:** 45-60 minutes

### Task 3: Implement Data Source Discovery
- Create InfluxDB query for active measurements
- Implement `_get_active_data_sources_from_influxdb()`
- Add 5-minute caching
- **Estimated:** 30 minutes

### Task 4: Testing & Validation
- Unit tests for all 3 fixes
- Integration tests
- Manual verification
- **Estimated:** 30-45 minutes

### Task 5: Documentation & Cleanup
- Remove TODO comments
- Update API docs
- Add methodology explanations
- **Estimated:** 15-20 minutes

**Total:** 2.5-3.5 hours

---

## Technical Guidance Provided

The story includes:
- ✅ Exact file locations to modify
- ✅ Code snippets for implementation options
- ✅ InfluxDB query examples
- ✅ Error handling patterns
- ✅ Testing strategy
- ✅ Edge case considerations

**Dev Notes Section:** 600+ lines of implementation guidance including:
- Architecture context
- Technology stack details
- File locations
- Implementation approaches for each fix
- Edge cases & error handling
- Testing standards
- API response structure changes

---

## Success Criteria

**Story is complete when:**
1. ✅ System uptime calculated from service start time
2. ✅ Response time measured OR removed with explanation
3. ✅ Data sources dynamically discovered from InfluxDB
4. ✅ All unit tests passing
5. ✅ Integration tests verify real data
6. ✅ Manual testing confirms accurate values in dashboard
7. ✅ All TODO comments removed
8. ✅ Documentation updated

**Epic is complete when:**
- Data Integrity Score = 100/100 (up from 95/100)
- Zero hardcoded placeholder values in monitoring endpoints
- Administrators can trust system health metrics

---

## Next Steps

### For Implementation:
1. Read story document: `docs/stories/story-24.1-fix-hardcoded-monitoring-metrics.md`
2. Review epic context: `docs/prd/epic-24-monitoring-data-quality.md`
3. Follow task breakdown in story
4. Use dev notes section for implementation guidance
5. Run tests as specified in testing section

### For Project Tracking:
- Story status: Draft → Approved → InProgress → Review → Done
- Update story status in document as work progresses
- Fill in "Dev Agent Record" section during implementation
- Add QA results after testing

---

## Related Documents

**Audit Reports (Source of Issues):**
- `implementation/FAKE_DATA_AUDIT_SUMMARY.md` - Executive summary
- `implementation/analysis/FAKE_DATA_AUDIT_REPORT.md` - Full audit

**Story & Epic:**
- `docs/stories/story-24.1-fix-hardcoded-monitoring-metrics.md` - This story
- `docs/prd/epic-24-monitoring-data-quality.md` - Parent epic
- `docs/prd/epic-list.md` - Updated with Epic 24

---

## Quality Notes

**Story Quality:**
- ✅ Complete acceptance criteria (5 ACs)
- ✅ Detailed task breakdown (5 tasks, 20+ subtasks)
- ✅ Comprehensive dev notes (600+ lines)
- ✅ Testing strategy defined
- ✅ Documentation requirements clear
- ✅ Follows BMAD story template

**Implementation Ready:**
- ✅ Exact file locations provided
- ✅ Code examples included
- ✅ Multiple implementation options
- ✅ Error handling guidance
- ✅ Testing requirements clear
- ✅ Success criteria measurable

---

## Impact

**Before Fix:**
- Data Integrity Score: 95/100
- 3 hardcoded metrics masking system behavior
- Administrators cannot trust monitoring data

**After Fix:**
- Data Integrity Score: 100/100
- All metrics accurate or explicitly "N/A"
- Full transparency in system health monitoring

**Effort:** 2-3 hours  
**Value:** High - Operational confidence in monitoring data

---

**Created By:** BMad Master  
**Source:** Comprehensive fake data audit (October 18, 2025)  
**Ready For:** @dev agent implementation

