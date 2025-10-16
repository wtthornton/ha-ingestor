# Story AI2.5 Implementation Plan: Unified Daily Batch Job

**Date:** 2025-10-16  
**Story:** AI2.5 - Unified Daily Batch Job (Pattern + Feature Analysis)  
**Status:** In Progress

---

## Implementation Summary

Enhancing the existing `DailyAnalysisScheduler` to include Epic-AI-2 (Device Intelligence) in the unified 3 AM batch job.

**Current State:**
- ✅ Epic-AI-1 pattern detection (time-of-day, co-occurrence)
- ✅ LLM suggestion generation
- ✅ Daily scheduler at 3 AM

**Adding (Story 2.5):**
- 🆕 Device capability update (batch query)
- 🆕 Feature analysis (utilization calculation)
- 🆕 Feature-based suggestions
- 🆕 Combined suggestion ranking

---

## Enhanced Job Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Unified Daily AI Analysis (3 AM)                            │
│                                                              │
│ Phase 1: Device Capability Update (NEW - Epic AI-2)         │
│   - Check HA device registry for new/updated devices        │
│   - Query Zigbee2MQTT bridge (batch)                        │
│   - Update device_capabilities table                        │
│   Duration: 1-3 minutes                                     │
│                                                              │
│ Phase 2: Fetch Events (EXISTING - Epic AI-1, now SHARED)    │
│   - Fetch last 30 days from InfluxDB                        │
│   - Used by BOTH pattern detection AND feature analysis     │
│   Duration: 1-2 minutes                                     │
│                                                              │
│ Phase 3: Pattern Detection (EXISTING - Epic AI-1)           │
│   - Time-of-day clustering                                  │
│   - Co-occurrence detection                                 │
│   Duration: 2-3 minutes                                     │
│                                                              │
│ Phase 4: Feature Analysis (NEW - Epic AI-2)                 │
│   - Match devices to capabilities                           │
│   - Calculate utilization                                   │
│   - Identify unused features                                │
│   Duration: 1-2 minutes                                     │
│                                                              │
│ Phase 5: Combined Suggestion Generation (ENHANCED)          │
│   - Generate pattern suggestions (AI-1)                     │
│   - Generate feature suggestions (AI-2)                     │
│   - Unified ranking                                         │
│   Duration: 2-4 minutes                                     │
│                                                              │
│ Phase 6: Store & Publish (EXISTING, enhanced logging)       │
│   - Store all suggestions                                   │
│   - Publish MQTT notification                               │
│   Duration: <1 minute                                       │
│                                                              │
│ Total Duration: 7-15 minutes                                │
└─────────────────────────────────────────────────────────────┘
```

---

## File Changes Required

### 1. `services/ai-automation-service/src/scheduler/daily_analysis.py`

**Changes:**
- Add device capability update phase (Phase 1)
- Add feature analysis phase (Phase 4)  
- Enhance suggestion generation to include feature suggestions (Phase 5)
- Update logging to show unified stats
- Import new components from Epic AI-2

**New Imports:**
```python
# Epic AI-2 imports (Device Intelligence)
from ..device_intelligence import (
    CapabilityParser,
    FeatureAnalyzer,
    FeatureSuggestionGenerator
)
from ..database.crud import (
    upsert_device_capability,
    get_device_capability,
    initialize_feature_usage
)
```

---

### 2. Create Batch Capability Query Function

**File:** `services/ai-automation-service/src/device_intelligence/capability_batch.py` (NEW)

```python
"""
Batch Device Capability Update
Replaces real-time MQTT listener with daily batch query
Story AI2.5 - Unified Daily Batch Job
"""

async def update_device_capabilities_batch(
    mqtt_client,
    data_api_client,
    db_session
) -> Dict[str, int]:
    """
    Query Zigbee2MQTT bridge for device capabilities (batch).
    
    Returns:
        Dictionary with update statistics
    """
    stats = {
        "devices_checked": 0,
        "capabilities_updated": 0,
        "new_devices": 0
    }
    
    # 1. Get all HA devices
    devices = await data_api_client.get_all_devices()
    stats["devices_checked"] = len(devices)
    
    # 2. Query Zigbee2MQTT bridge (one-time batch query)
    bridge_data = await mqtt_client.query_bridge_devices()
    
    # 3. Parse and store capabilities
    parser = CapabilityParser()
    for device in devices:
        # Check if capability exists
        existing = await get_device_capability(db_session, device['model'])
        
        if not existing or _is_stale(existing):
            # Parse and store
            capabilities = parser.parse_device(device, bridge_data)
            if capabilities:
                await upsert_device_capability(db_session, capabilities)
                stats["capabilities_updated"] += 1
                if not existing:
                    stats["new_devices"] += 1
    
    return stats
```

---

## Code Changes to daily_analysis.py

### Enhanced `run_daily_analysis()` Method

Add these phases to the existing method:

```python
# ================================================================
# Phase 1: Device Capability Update (NEW - Epic AI-2)
# ================================================================
logger.info("📡 Phase 1: Device Capability Update (Epic AI-2)...")

from ..device_intelligence.capability_batch import update_device_capabilities_batch

capability_stats = await update_device_capabilities_batch(
    mqtt_client=self.mqtt_client,
    data_api_client=data_client,
    db_session=get_db_session
)

logger.info(f"✅ Device capabilities updated:")
logger.info(f"   - Devices checked: {capability_stats['devices_checked']}")
logger.info(f"   - Capabilities updated: {capability_stats['capabilities_updated']}")
logger.info(f"   - New devices: {capability_stats['new_devices']}")

job_result['devices_checked'] = capability_stats['devices_checked']
job_result['capabilities_updated'] = capability_stats['capabilities_updated']

# ================================================================
# Phase 2: Fetch Events (EXISTING, now labeled as SHARED)
# ================================================================
logger.info("📊 Phase 2: Fetching events (SHARED by AI-1 + AI-2)...")
# ... existing code ...

# ================================================================
# Phase 3: Pattern Detection (EXISTING - Epic AI-1)
# ================================================================
logger.info("🔍 Phase 3: Pattern Detection (Epic AI-1)...")
# ... existing code ...

# ================================================================
# Phase 4: Feature Analysis (NEW - Epic AI-2)
# ================================================================
logger.info("🧠 Phase 4: Feature Analysis (Epic AI-2)...")

from ..device_intelligence import FeatureAnalyzer

feature_analyzer = FeatureAnalyzer(
    data_api_client=data_client,
    db_session=get_db_session,
    influxdb_client=data_client.influxdb_client
)

analysis_result = await feature_analyzer.analyze_all_devices()
opportunities = analysis_result.get('opportunities', [])

logger.info(f"✅ Feature analysis complete:")
logger.info(f"   - Devices analyzed: {analysis_result.get('devices_analyzed', 0)}")
logger.info(f"   - Opportunities found: {len(opportunities)}")
logger.info(f"   - Average utilization: {analysis_result.get('avg_utilization', 0):.1f}%")

job_result['devices_analyzed'] = analysis_result.get('devices_analyzed', 0)
job_result['opportunities_found'] = len(opportunities)

# ================================================================
# Phase 5: Combined Suggestion Generation (ENHANCED)
# ================================================================
logger.info("💡 Phase 5: Combined Suggestion Generation (AI-1 + AI-2)...")

# Existing pattern suggestions (AI-1)
pattern_suggestions = []
for pattern in top_patterns:
    try:
        suggestion = await openai_client.generate_automation_suggestion(pattern)
        pattern_suggestions.append({
            'type': 'pattern_automation',
            'source': 'Epic-AI-1',
            **suggestion.dict()
        })
    except Exception as e:
        logger.error(f"Pattern suggestion failed: {e}")

logger.info(f"   ✅ Generated {len(pattern_suggestions)} pattern suggestions")

# NEW: Feature suggestions (AI-2)
from ..device_intelligence import FeatureSuggestionGenerator

feature_generator = FeatureSuggestionGenerator(
    llm_client=openai_client,
    feature_analyzer=feature_analyzer,
    db_session=get_db_session
)

feature_suggestions = await feature_generator.generate_suggestions(max_suggestions=10)
logger.info(f"   ✅ Generated {len(feature_suggestions)} feature suggestions")

# Combine and rank suggestions
all_suggestions = pattern_suggestions + feature_suggestions
all_suggestions.sort(key=lambda s: s.get('confidence', 0.5), reverse=True)
all_suggestions = all_suggestions[:10]  # Top 10 total

logger.info(f"✅ Combined suggestions: {len(all_suggestions)} total")
logger.info(f"   - Pattern-based: {len([s for s in all_suggestions if s['type'] == 'pattern_automation'])}")
logger.info(f"   - Feature-based: {len([s for s in all_suggestions if s['type'] == 'feature_discovery'])}")

# Store all suggestions
for suggestion in all_suggestions:
    async with get_db_session() as db:
        await store_suggestion(db, suggestion)

job_result['suggestions_generated'] = len(all_suggestions)
job_result['pattern_suggestions'] = len(pattern_suggestions)
job_result['feature_suggestions'] = len(feature_suggestions)
```

---

## Testing Plan

### 1. Unit Tests

**File:** `services/ai-automation-service/tests/test_unified_batch.py` (NEW)

```python
"""
Unit Tests for Unified Daily Batch Job (Story AI2.5)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from src.scheduler.daily_analysis import DailyAnalysisScheduler


class TestUnifiedDailyBatch:
    """Test unified batch job combining Epic-AI-1 and Epic-AI-2"""
    
    @pytest.mark.asyncio
    async def test_device_capability_update_phase(self):
        """Test Phase 1: Device capability update"""
        # Mock components
        # Test that device capabilities are updated
        pass
    
    @pytest.mark.asyncio
    async def test_feature_analysis_phase(self):
        """Test Phase 4: Feature analysis"""
        # Mock components
        # Test that feature analysis runs
        pass
    
    @pytest.mark.asyncio
    async def test_combined_suggestions(self):
        """Test Phase 5: Combined suggestion generation"""
        # Mock both pattern and feature suggestions
        # Test unified ranking
        # Test balance (mix of both types)
        pass
    
    @pytest.mark.asyncio
    async def test_full_pipeline_integration(self):
        """Test complete unified batch pipeline"""
        # Mock all components
        # Test full execution
        # Verify all phases run in order
        pass
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test that job continues even if one phase fails"""
        # Mock Phase 1 failure
        # Verify Phases 2-6 still execute
        pass
```

### 2. Integration Test

**Manual Test:**
1. Build and deploy updated service
2. Trigger manual analysis run
3. Verify all 6 phases execute
4. Check database for both pattern and feature suggestions
5. Verify MQTT notification includes unified stats

---

## Rollout Plan

### Phase 1: Development & Testing (Current)
- [x] Create implementation plan (this document)
- [ ] Implement `capability_batch.py`
- [ ] Enhance `daily_analysis.py`
- [ ] Write unit tests
- [ ] Test locally

### Phase 2: Docker Testing
- [ ] Build Docker image
- [ ] Test in Docker environment
- [ ] Verify all phases execute correctly
- [ ] Check resource usage

### Phase 3: Documentation
- [ ] Update architecture document
- [ ] Document new job flow
- [ ] Update troubleshooting guide

### Phase 4: Deployment
- [ ] Deploy to production
- [ ] Monitor first run (3 AM)
- [ ] Verify performance (<15 min)
- [ ] Check suggestion quality

---

## Success Criteria

- ✅ All 6 phases execute without errors
- ✅ Both pattern and feature suggestions generated
- ✅ Total job duration <15 minutes
- ✅ Memory usage <500MB
- ✅ Combined suggestions ranked correctly
- ✅ MQTT notification shows unified stats
- ✅ Database contains both suggestion types

---

## Rollback Plan

If unified batch fails:
1. Revert to previous `daily_analysis.py` (pattern detection only)
2. Re-deploy previous Docker image
3. Device Intelligence features will be temporarily disabled
4. Pattern suggestions will continue working

---

## Next Steps

1. ✅ Create this implementation plan
2. ⏩ Implement `capability_batch.py`
3. ⏩ Enhance `daily_analysis.py`
4. ⏩ Write unit tests
5. ⏩ Test in Docker
6. Deploy and monitor

**Estimated Time:** 4-6 hours

