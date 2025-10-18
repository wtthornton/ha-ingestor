# Phase 2: Historical Event Fetching
## Shared Data Retrieval for AI-1 and AI-2

**Epic:** Shared by AI-1 (Pattern Detection) and AI-2 (Feature Analysis)  
**Duration:** 5-15 seconds  
**Data Source:** InfluxDB (`home_assistant_events` bucket)  
**Last Updated:** October 17, 2025

**🔗 Navigation:**
- [← Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [← Previous: Phase 1 - Device Capability Discovery](AI_AUTOMATION_PHASE1_CAPABILITIES.md)
- [→ Next: Phase 3 - Pattern Detection](AI_AUTOMATION_PHASE3_PATTERNS.md)

---

## 📋 Overview

**Purpose:** Retrieve last 30 days of Home Assistant events for analysis

Phase 2 fetches historical event data that will be used by:
- **Phase 3:** Pattern Detection (Epic AI-1) - Detects time-of-day and co-occurrence patterns
- **Phase 4:** Feature Analysis (Epic AI-2) - Analyzes device utilization

This is a shared data retrieval phase that supports both AI-1 and AI-2 epics.

---

## 🔄 Call Tree

```
run_daily_analysis() [line 175]
├── DataAPIClient.__init__() [line 177]
│
└── data_client.fetch_events() [line 186]
    ├── start_time = now - 30 days
    ├── limit = 100,000 events
    │
    ├── InfluxDBEventClient.query_events() [data_api_client.py:90]
    │   ├── Build Flux query with filters
    │   ├── influxdb_client.query_api().query_data_frame()
    │   └── Returns: pd.DataFrame with columns:
    │       - timestamp
    │       - entity_id
    │       - event_type
    │       - old_state
    │       - new_state
    │       - attributes (JSON)
    │       - device_id
    │       - tags
    │
    └── Returns: events_df (pandas DataFrame)
```

**Key Files:**
- `clients/data_api_client.py:64` - Main fetch_events method
- `clients/influxdb_client.py` - Direct InfluxDB queries

**Data Source:** InfluxDB bucket `home_assistant_events`  
**Performance:** Optimized with 3-retry exponential backoff

---

## 📊 Flux Query Example

The system queries InfluxDB using Flux query language:

```flux
from(bucket: "home_assistant_events")
  |> range(start: -30d, stop: now())
  |> filter(fn: (r) => r._measurement == "home_assistant_events")
  |> filter(fn: (r) => r.event_type == "state_changed")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> limit(n: 100000)
```

**Query Parameters:**
- **Time Range:** Last 30 days (`-30d` to `now()`)
- **Measurement:** `home_assistant_events`
- **Event Type:** `state_changed` (primary focus)
- **Limit:** 100,000 events maximum

---

## 🔢 Data Structure

**pandas DataFrame Output:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `timestamp` | datetime | Event timestamp | 2025-10-17T07:15:23Z |
| `entity_id` | string | Home Assistant entity | light.living_room |
| `event_type` | string | Event type | state_changed |
| `old_state` | string | Previous state | off |
| `new_state` | string | New state | on |
| `attributes` | JSON | Entity attributes | {"brightness": 80} |
| `device_id` | string | Device identifier | abc123def |
| `tags` | dict | InfluxDB tags | {"domain": "light"} |

**Example Row:**
```python
{
    'timestamp': pd.Timestamp('2025-10-17 07:15:23'),
    'entity_id': 'light.living_room',
    'event_type': 'state_changed',
    'old_state': 'off',
    'new_state': 'on',
    'attributes': '{"brightness": 80, "color_temp": 370}',
    'device_id': 'abc123def456',
    'tags': {'domain': 'light', 'area': 'living_room'}
}
```

---

## ⚡ Performance Characteristics

**Typical Metrics:**
- **Events Fetched:** 50,000-100,000 events
- **Query Time:** 5-15 seconds
- **Memory Usage:** 200-500 MB (pandas DataFrame)
- **Network Bandwidth:** 10-50 MB (depending on event count)

**Optimization:**
- Uses pandas DataFrame for efficient data manipulation
- InfluxDB query optimized with proper indexing (tags)
- 3-retry exponential backoff for resilience

**Scaling:**
- 10,000 events: ~2s
- 50,000 events: ~8s
- 100,000 events: ~15s
- Bottleneck: InfluxDB query execution time

---

## ⚠️ Error Handling

**Retry Strategy:**

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
async def fetch_events():
    # InfluxDB query here
```

**Retry Behavior:**
1. **Attempt 1:** Immediate
2. **Attempt 2:** Wait 2 seconds
3. **Attempt 3:** Wait 4 seconds
4. **Failure:** Raise exception, log error, continue to next phase

**Common Errors:**
1. **InfluxDB timeout:** Query takes too long
   - Retry with exponential backoff
   
2. **Connection error:** InfluxDB unavailable
   - Retry up to 3 times
   - If all fail, log error and skip pattern detection
   
3. **Out of memory:** Too many events
   - Reduce limit or time range
   - Log warning

---

## 🔗 Next Steps

**Phase 2 Output Used By:**
- [Phase 3: Pattern Detection](AI_AUTOMATION_PHASE3_PATTERNS.md) - Analyzes events for patterns
- [Phase 4: Feature Analysis](AI_AUTOMATION_PHASE4_FEATURES.md) - Analyzes device usage

**Related Documentation:**
- [← Phase 1: Device Capability Discovery](AI_AUTOMATION_PHASE1_CAPABILITIES.md)
- [Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [Complete Call Tree](AI_AUTOMATION_CALL_TREE.md)

---

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Epic:** Shared (AI-1 + AI-2)

