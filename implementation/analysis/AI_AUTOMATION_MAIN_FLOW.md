# AutomateAI: Main Execution Flow
## Scheduler Trigger to Job Completion

**Service:** ai-automation-service (Port 8018)  
**Entry Point:** Scheduled daily analysis at 3 AM (configurable via `analysis_schedule`)  
**Story:** AI2.5 - Unified Daily Batch Job (Epic AI-1 + Epic AI-2)  
**Last Updated:** October 17, 2025

**🔗 Navigation:**
- [← Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [→ Next: Phase 1 - Device Capability Discovery](AI_AUTOMATION_PHASE1_CAPABILITIES.md)

---

## 📋 Overview

This document describes the main execution flow for the AutomateAI daily batch job that:
1. **Discovers** what your smart home devices can do (capabilities)
2. **Detects** usage patterns from historical data (time-of-day, co-occurrence)
3. **Analyzes** device utilization (underutilized features)
4. **Generates** AI-powered automation suggestions using OpenAI GPT-4o-mini
5. **Presents** suggestions to users for approval and deployment

### Daily Execution

The system runs automatically at **3:00 AM daily** via APScheduler cron job:
- **Duration:** 2-4 minutes typical
- **Cost:** ~$0.001-0.005 per run (OpenAI)
- **Output:** ~10 automation suggestions

---

## 🕐 3:00 AM - Scheduler Trigger

```
APScheduler (AsyncIOScheduler)
└── CronTrigger.from_crontab("0 3 * * *")
    └── Job: 'daily_pattern_analysis'
        └── Executes: DailyAnalysisScheduler.run_daily_analysis()
```

**Location:** `services/ai-automation-service/src/scheduler/daily_analysis.py:104`  
**Trigger:** APScheduler with cron expression from `settings.analysis_schedule`  
**Initialization:** Scheduler started in `main.py:139` during FastAPI startup event

---

## 📋 Main Execution Flow

### Entry: `DailyAnalysisScheduler.run_daily_analysis()`
**File:** `services/ai-automation-service/src/scheduler/daily_analysis.py:104`

```python
async def run_daily_analysis():
    """
    Unified daily batch job workflow (Story AI2.5):
    
    Phase 1: Device Capability Update (Epic AI-2)
    Phase 2: Fetch Historical Events (Shared by AI-1 + AI-2)
    Phase 3: Pattern Detection (Epic AI-1)
    Phase 4: Feature Analysis (Epic AI-2)
    Phase 5: Combined Suggestion Generation (AI-1 + AI-2)
    Phase 6: Publish Notification & Store Results
    """
```

### Execution Phases Summary

| Phase | Purpose | Duration | Epic | Output |
|-------|---------|----------|------|--------|
| **[Phase 1](AI_AUTOMATION_PHASE1_CAPABILITIES.md)** | Device Capability Discovery | 10-30s | AI-2 | Device capabilities in SQLite |
| **[Phase 2](AI_AUTOMATION_PHASE2_EVENTS.md)** | Fetch Historical Events | 5-15s | Shared | pandas DataFrame with 100K events |
| **[Phase 3](AI_AUTOMATION_PHASE3_PATTERNS.md)** | Pattern Detection | 15-45s | AI-1 | Detected patterns in SQLite |
| **[Phase 4](AI_AUTOMATION_PHASE4_FEATURES.md)** | Feature Analysis | 10-20s | AI-2 | Feature opportunities list |
| **[Phase 5](AI_AUTOMATION_PHASE5_OPENAI.md)** | Suggestion Generation | 30-120s | AI-1+AI-2 | 10 AI-generated suggestions |
| **[Phase 6](AI_AUTOMATION_PHASE6_MQTT.md)** | MQTT Notification | <1s | Shared | MQTT completion message |
| **Total** | **End-to-End** | **70-230s** | **All** | **Complete analysis results** |

---

## 🔄 Completion & Cleanup

### Final Steps

```
run_daily_analysis() [line 431]
├── Calculate duration [line 432]
├── Build job_result summary [line 434]
│   ├── status: 'success'
│   ├── start_time, end_time
│   ├── duration_seconds
│   ├── All phase metrics
│   └── OpenAI token usage and cost
│
├── Log comprehensive summary [line 438]
│   ├── Duration
│   ├── Epic AI-1 metrics
│   ├── Epic AI-2 metrics
│   └── Combined results
│
├── FINALLY block [line 466]
│   ├── self.is_running = False
│   └── _store_job_history(job_result) [line 468]
│       ├── Append to self._job_history
│       ├── Keep last 30 runs in memory
│       └── Used for /api/analysis/schedule endpoint
│
└── RETURN (job complete)
```

**Scheduler State:**
- `is_running` flag reset to `False`
- Next run scheduled automatically by APScheduler
- Next run time: 3:00 AM next day

---

## 🎯 Manual Trigger Path (Alternative Entry)

**HTTP API:** `POST /api/analysis/trigger`  
**File:** `api/analysis_router.py:341`

```
POST /api/analysis/trigger
└── trigger_analysis() [analysis_router.py:342]
    ├── Verify _scheduler is initialized
    ├── Check if not already running
    │
    ├── background_tasks.add_task(_scheduler.trigger_manual_run) [line 365]
    │   └── scheduler.trigger_manual_run() [daily_analysis.py:511]
    │       └── asyncio.create_task(self.run_daily_analysis())
    │           └── [SAME AS SCHEDULED PATH ABOVE]
    │
    └── Return: {
        'success': true,
        'status': 'running_in_background',
        'next_scheduled_run': '2025-10-18T03:00:00Z'
    }
```

**Use Cases:**
- Testing and debugging
- On-demand analysis
- Recovery from missed scheduled runs

**Testing:**
```bash
# Trigger analysis via API (don't wait for 3 AM)
curl -X POST http://localhost:8018/api/analysis/trigger

# Get scheduler status and next run time
curl http://localhost:8018/api/analysis/schedule

# Get analysis results
curl http://localhost:8018/api/analysis/status
```

---

## ⚠️ Error Handling & Recovery

### Per-Phase Error Handling

All phases implement try/except with graceful degradation:

```python
try:
    # Phase execution
    result = await phase_function()
except Exception as e:
    logger.error(f"⚠️ Phase failed: {e}")
    logger.info("   → Continuing with next phase...")
    result = default_fallback_value
```

**Philosophy:** Don't fail entire job due to single phase failure

### Global Error Handler

```
run_daily_analysis() [line 460]
└── EXCEPT Exception as e:
    ├── logger.error(f"❌ Daily analysis job failed: {e}", exc_info=True)
    ├── job_result['status'] = 'failed'
    ├── job_result['error'] = str(e)
    └── Store in job history
```

**Guarantees:**
- Job always completes (success or failed)
- History always recorded
- `is_running` flag always reset
- Next run still scheduled

---

## 📊 Performance Characteristics

### Typical Execution Time

| Phase | Duration | Bottleneck |
|-------|----------|-----------|
| Phase 1: Capabilities | 10-30s | MQTT request/response |
| Phase 2: Events | 5-15s | InfluxDB query (100K events) |
| Phase 3: Patterns | 15-45s | Co-occurrence algorithm (O(n²)) |
| Phase 4: Features | 10-20s | InfluxDB usage queries |
| Phase 5: Suggestions | 30-120s | OpenAI API calls |
| Phase 6: Notification | <1s | MQTT publish |
| **Total** | **70-230s** | **Typically 2-4 minutes** |

### Optimization Strategies

1. **Phase 3:** Uses `detect_patterns_optimized()` for >50K events
2. **Phase 5:** Parallel OpenAI requests possible (currently sequential)
3. **Phase 2:** Could implement incremental fetching (daily delta vs 30-day full)
4. **Database:** Uses SQLite WAL mode for concurrent reads

### Resource Usage

- **Memory:** ~500MB-1GB peak (pandas DataFrames for events)
- **CPU:** Moderate (pattern detection algorithms)
- **Network:** OpenAI API bandwidth (10 requests × ~2KB each)
- **Disk:** Minimal (SQLite database growth ~10KB per run)

---

## 🎯 Success Criteria

A successful daily run produces:
- ✅ Device capabilities updated (0-10 devices)
- ✅ 50,000-100,000 events analyzed
- ✅ 10-50 patterns detected
- ✅ 10 automation suggestions generated
- ✅ All suggestions stored in database
- ✅ MQTT notification published
- ✅ Total cost < $0.01
- ✅ Total duration < 4 minutes

---

## 🔗 Related Documentation

### Phase Documents
- [Phase 1: Device Capability Discovery](AI_AUTOMATION_PHASE1_CAPABILITIES.md)
- [Phase 2: Historical Event Fetching](AI_AUTOMATION_PHASE2_EVENTS.md)
- [Phase 3: Pattern Detection](AI_AUTOMATION_PHASE3_PATTERNS.md)
- [Phase 4: Feature Analysis](AI_AUTOMATION_PHASE4_FEATURES.md)
- [Phase 5: OpenAI Suggestion Generation](AI_AUTOMATION_PHASE5_OPENAI.md)
- [Phase 5b: Suggestion Storage](AI_AUTOMATION_PHASE5B_STORAGE.md)
- [Phase 6: MQTT Notification](AI_AUTOMATION_PHASE6_MQTT.md)

### Architecture
- [Tech Stack](../../docs/architecture/tech-stack.md)
- [Source Tree](../../docs/architecture/source-tree.md)
- [Testing Strategy](../../docs/architecture/testing-strategy.md)

### Implementation Notes
- [Complete Call Tree (All Phases)](AI_AUTOMATION_CALL_TREE.md)
- [Call Tree Index](AI_AUTOMATION_CALL_TREE_INDEX.md)

---

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Subsystem:** ai-automation-service  
**Epic:** AI-1 (Pattern Detection) + AI-2 (Device Intelligence)

