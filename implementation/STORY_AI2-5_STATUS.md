# Story AI2.5 Status: Unified Daily Batch Job

**Date:** 2025-10-16  
**Story:** AI2.5 - Unified Daily Batch Job (Pattern + Feature Analysis)  
**Status:** 🟡 In Progress - 70% Complete

---

## ✅ Completed Tasks

### 1. Planning & Documentation
- [x] Analyzed real-time vs. batch architecture
- [x] Created architectural decision document (`REALTIME_VS_BATCH_ANALYSIS.md`)
- [x] Updated PRD (Story 2.1 and Story 2.5)
- [x] Created Story 2.5 file (`story-ai2-5-unified-daily-batch.md`)
- [x] Created implementation plan (`STORY_AI2-5_IMPLEMENTATION_PLAN.md`)

### 2. Core Components (Stories 2.1-2.4)
- [x] Story 2.1: MQTT Capability Listener & Parser ✅
- [x] Story 2.2: Database Schema ✅
- [x] Story 2.3: Feature Analyzer ✅
- [x] Story 2.4: Feature Suggestion Generator ✅
- [x] All tests passing (14/14 passed for Story 2.4)

### 3. Batch Capability Update
- [x] Created `capability_batch.py` module
- [x] Implemented `update_device_capabilities_batch()` function
- [x] Added batch query logic for Zigbee2MQTT
- [x] Implemented staleness check (30-day refresh)
- [x] Updated module exports

---

## 🟡 In Progress

### 4. Unified Scheduler Enhancement
- [ ] Enhance `daily_analysis.py` with 6-phase unified job
- [ ] Integrate device capability update (Phase 1)
- [ ] Integrate feature analysis (Phase 4)
- [ ] Integrate feature suggestions (Phase 5)
- [ ] Update logging for unified stats
- [ ] Test integration

---

## 📋 Remaining Tasks

### 5. Testing
- [ ] Unit tests for `capability_batch.py`
- [ ] Integration tests for unified batch
- [ ] Docker environment testing
- [ ] Performance validation (<15 min)

### 6. Deployment
- [ ] Build Docker image
- [ ] Deploy to environment
- [ ] Monitor first 3 AM run
- [ ] Verify all phases execute
- [ ] Check suggestion quality

---

## Implementation Summary

### What's Built

```
Story 2.1: Batch Capability Discovery ✅
├── capability_parser.py ✅
├── capability_batch.py ✅ (NEW for batch)
└── mqtt_capability_listener.py ✅ (legacy, will deprecate)

Story 2.2: Database Schema ✅
├── device_capabilities table ✅
├── device_feature_usage table ✅
└── Alembic migration ✅

Story 2.3: Feature Analyzer ✅
├── feature_analyzer.py ✅
└── Tests passing ✅

Story 2.4: Feature Suggestion Generator ✅
├── feature_suggestion_generator.py ✅
└── Tests passing (14/14) ✅

Story 2.5: Unified Batch ⏳ (70% complete)
├── capability_batch.py ✅ (NEW)
├── daily_analysis.py ⏳ (needs enhancement)
└── Tests ⏳ (TODO)
```

---

## Unified Batch Job Architecture

### Phase Flow (3 AM Daily)

```
Phase 1: Device Capability Update (NEW - Epic AI-2) ✅
  ├── Check HA devices
  ├── Query Zigbee2MQTT bridge (batch)
  ├── Parse capabilities
  └── Update database

Phase 2: Fetch Events (EXISTING - Shared) ✅
  ├── Query InfluxDB (last 30 days)
  └── Used by BOTH AI-1 and AI-2

Phase 3: Pattern Detection (EXISTING - Epic AI-1) ✅
  ├── Time-of-day clustering
  ├── Co-occurrence detection
  └── Anomaly detection

Phase 4: Feature Analysis (NEW - Epic AI-2) ⏳
  ├── Match devices to capabilities
  ├── Calculate utilization
  └── Identify unused features

Phase 5: Combined Suggestions (ENHANCED) ⏳
  ├── Generate pattern suggestions (AI-1)
  ├── Generate feature suggestions (AI-2)
  ├── Unified ranking
  └── Store top 10

Phase 6: Publish (EXISTING - Enhanced logging) ⏳
  ├── MQTT notification
  └── Job history
```

---

## Code Changes Needed

### File: `services/ai-automation-service/src/scheduler/daily_analysis.py`

**Add imports:**
```python
# Epic AI-2 imports
from ..device_intelligence import (
    update_device_capabilities_batch,
    FeatureAnalyzer,
    FeatureSuggestionGenerator
)
```

**Add Phase 1:**
```python
# Phase 1: Device Capability Update
logger.info("📡 Phase 1: Device Capability Update (Epic AI-2)...")
capability_stats = await update_device_capabilities_batch(
    mqtt_client=self.mqtt_client,
    data_api_client=data_client,
    db_session_factory=get_db_session
)
logger.info(f"✅ Updated {capability_stats['capabilities_updated']} capabilities")
```

**Add Phase 4:**
```python
# Phase 4: Feature Analysis
logger.info("🧠 Phase 4: Feature Analysis (Epic AI-2)...")
feature_analyzer = FeatureAnalyzer(
    data_api_client=data_client,
    db_session=get_db_session,
    influxdb_client=data_client.influxdb_client
)
analysis = await feature_analyzer.analyze_all_devices()
logger.info(f"✅ Found {len(analysis['opportunities'])} opportunities")
```

**Enhance Phase 5:**
```python
# Phase 5: Combined Suggestions
# ... existing pattern suggestions ...
feature_generator = FeatureSuggestionGenerator(
    llm_client=openai_client,
    feature_analyzer=feature_analyzer,
    db_session=get_db_session
)
feature_suggestions = await feature_generator.generate_suggestions(max_suggestions=10)

# Combine and rank
all_suggestions = pattern_suggestions + feature_suggestions
all_suggestions.sort(key=lambda s: s.get('confidence', 0.5), reverse=True)
all_suggestions = all_suggestions[:10]
```

---

## Testing Strategy

### 1. Unit Tests
- `test_capability_batch.py` - Test batch update logic
- `test_unified_scheduler.py` - Test enhanced scheduler

### 2. Integration Tests
- Full pipeline test (all 6 phases)
- Graceful degradation test (phase failures)
- Performance test (<15 min target)

### 3. Manual Testing
- Build Docker image
- Trigger manual analysis
- Verify database contents
- Check logs for all phases

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| All 6 phases execute | Yes | ⏳ Pending |
| Job duration | <15 min | ⏳ Pending |
| Memory usage | <500MB | ⏳ Pending |
| Both suggestion types | Yes | ⏳ Pending |
| Tests passing | 100% | ⏳ Pending |

---

## Next Steps (Priority Order)

1. **Enhance daily_analysis.py** (2-3 hours)
   - Add Phase 1 (device capability update)
   - Add Phase 4 (feature analysis)
   - Enhance Phase 5 (combined suggestions)
   - Update logging

2. **Write unit tests** (1-2 hours)
   - Test capability_batch.py
   - Test unified scheduler integration
   - Test graceful degradation

3. **Docker testing** (1 hour)
   - Build image
   - Run integration tests
   - Verify performance

4. **Deploy and monitor** (1 hour)
   - Deploy to environment
   - Monitor first run
   - Verify results

**Total Remaining:** ~5-7 hours

---

## Files Created/Modified

### New Files
- ✅ `services/ai-automation-service/src/device_intelligence/capability_batch.py`
- ✅ `docs/stories/story-ai2-5-unified-daily-batch.md`
- ✅ `implementation/REALTIME_VS_BATCH_ANALYSIS.md`
- ✅ `implementation/STORY_AI2-5_IMPLEMENTATION_PLAN.md`
- ✅ `implementation/STORY_AI2-5_STATUS.md` (this file)

### Modified Files
- ✅ `docs/prd.md` (Stories 2.1 and 2.5)
- ✅ `services/ai-automation-service/src/device_intelligence/__init__.py`
- ⏳ `services/ai-automation-service/src/scheduler/daily_analysis.py` (TODO)

### Test Files Needed
- ⏳ `services/ai-automation-service/tests/test_capability_batch.py` (TODO)
- ⏳ `services/ai-automation-service/tests/test_unified_batch.py` (TODO)

---

## Resource Usage Improvement

| Metric | Real-time (Before) | Batch (After) | Improvement |
|--------|-------------------|--------------|-------------|
| Uptime | 730 hrs/month | 2.5 hrs/month | **291x less** |
| MQTT Connection | 24/7 | 5-10 min/day | **99% less** |
| Complexity | High | Low | **Simpler** |
| User Experience | Identical | Identical | **No change** |

---

## Conclusion

**Status:** Story 2.5 is 70% complete. Core components (Stories 2.1-2.4) are fully implemented and tested. The batch capability query module is complete. Remaining work is to integrate everything into the unified scheduler and add comprehensive tests.

**Estimated Completion:** 5-7 hours of additional work.

**Next Action:** Enhance `daily_analysis.py` to include all 6 phases of the unified batch job.

