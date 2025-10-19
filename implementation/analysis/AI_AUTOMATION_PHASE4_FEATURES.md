# Phase 4: Feature Analysis
## Epic AI-2 - Device Intelligence

**Epic:** AI-2 - Device Intelligence  
**Story:** AI2.3 - Device Matching & Feature Analysis  
**Duration:** 10-20 seconds  
**Database:** SQLite (`device_capabilities`) + InfluxDB (usage queries)  
**Last Updated:** October 17, 2025  
**Last Validated:** October 19, 2025 ✅

**🔗 Navigation:**
- [← Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [← Previous: Phase 3 - Pattern Detection](AI_AUTOMATION_PHASE3_PATTERNS.md)
- [→ Next: Phase 5 - OpenAI Suggestion Generation](AI_AUTOMATION_PHASE5_OPENAI.md)

---

## 📋 Overview

**Purpose:** Analyze device utilization and identify underutilized features

Phase 4 discovers optimization opportunities by:
1. Loading device capabilities from Phase 1
2. Querying actual usage from InfluxDB
3. Calculating utilization percentage
4. Identifying devices with <50% feature utilization
5. Creating a list of automation opportunities for Phase 5

---

## 🔄 Call Tree

```
run_daily_analysis() [line 251]
├── FeatureAnalyzer.__init__() [line 254]
│   ├── data_api_client
│   ├── db_session factory
│   └── influxdb_client
│
└── feature_analyzer.analyze_all_devices() [device_intelligence/feature_analyzer.py]
    ├── db.query(DeviceCapability).all() [feature_analyzer.py:~40]
    │   └── Load all devices with capabilities from database
    │
    ├── For each device:
    │   ├── influxdb_client.query_usage() [feature_analyzer.py:~60]
    │   │   ├── Query last 30 days of state changes
    │   │   └── Returns: usage statistics per feature
    │   │
    │   ├── Calculate utilization metrics:
    │   │   ├── feature_count_used / feature_count_total
    │   │   ├── days_active / 30
    │   │   └── event_frequency
    │   │
    │   └── IF utilization < 50%:
    │       └── opportunities.append({
    │           'device_id': str,
    │           'device_name': str,
    │           'capabilities_total': int,
    │           'capabilities_unused': int,
    │           'utilization_pct': float,
    │           'underutilized_features': List[str],
    │           'usage_stats': Dict
    │       })
    │
    └── Returns: {
        'devices_analyzed': int,
        'opportunities': List[Dict],
        'avg_utilization': float,
        'timestamp': str
    }
```

**Key Files:**
- `device_intelligence/feature_analyzer.py` - Utilization analysis engine
- `device_intelligence/capability_parser.py` - Feature capability definitions

**Data Sources:**
- SQLite: `device_capabilities` table (from Phase 1)
- InfluxDB: `home_assistant_events` bucket (usage queries)

**Logic:** Identifies devices with <50% feature utilization

---

## 📊 Utilization Calculation

### Metrics

**Feature Utilization Percentage:**
```python
utilization = (features_used / features_total) * 100
```

**Example:**
```python
device = {
    'device_id': 'light.kitchen_switch',
    'device_model': 'VZM31-SN',
    'capabilities_total': 5,  # light, smart_bulb_mode, auto_timer, led_effect, default_level
    'capabilities_used': 1,   # Only basic light control used
    'utilization_pct': 20.0   # 1/5 = 20%
}
```

**Underutilized Features:**
```python
underutilized = [
    'smart_bulb_mode',   # Never configured
    'auto_off_timer',    # Never used
    'led_notifications', # Never activated
    'default_level_local' # Default value never changed
]
```

---

## 🎯 Example Opportunity

**Input (from Phase 1):**
```json
{
  "device_id": "light.kitchen_switch",
  "device_model": "VZM31-SN",
  "manufacturer": "Inovelli",
  "capabilities": {
    "light_control": {...},        // ✅ USED
    "smart_bulb_mode": {...},      // ❌ UNUSED
    "auto_off_timer": {...},       // ❌ UNUSED
    "led_notifications": {...},    // ❌ UNUSED
    "default_level_local": {...}   // ❌ UNUSED
  }
}
```

**Usage Query (InfluxDB):**
```flux
from(bucket: "home_assistant_events")
  |> range(start: -30d)
  |> filter(fn: (r) => r.entity_id == "light.kitchen_switch")
  |> filter(fn: (r) => r._field == "state" or r._field == "brightness")
  |> count()

// Results: 150 events (all basic light control)
// No events for: smart_bulb_mode, auto_off_timer, led_effect
```

**Calculated Opportunity:**
```python
{
    'device_id': 'light.kitchen_switch',
    'device_name': 'Kitchen Light Switch',
    'device_model': 'VZM31-SN',
    'manufacturer': 'Inovelli',
    'capabilities_total': 5,
    'capabilities_used': 1,
    'capabilities_unused': 4,
    'utilization_pct': 20.0,
    'underutilized_features': [
        {
            'name': 'led_notifications',
            'description': 'LED notification effect',
            'complexity': 'advanced',
            'mqtt_name': 'ledEffect',
            'suggestion': 'Use LED for visual notifications (garage door, security alerts)'
        },
        {
            'name': 'auto_off_timer',
            'description': 'Automatically turn off after X seconds',
            'complexity': 'medium',
            'mqtt_name': 'autoTimerOff',
            'suggestion': 'Set automatic shutoff to save energy'
        }
    ],
    'usage_stats': {
        'total_events_30d': 150,
        'days_active': 28,
        'avg_events_per_day': 5.4
    }
}
```

**This opportunity will be sent to Phase 5 for AI suggestion generation.**

---

## ⚡ Performance Characteristics

**Typical Metrics:**
- **Devices Analyzed:** 20
- **Opportunities Found:** 5-8 devices
- **Average Utilization:** 35-45%
- **Query Time:** 10-20 seconds total

**Per-Device Timing:**
- Load capabilities: ~0.1ms (SQLite)
- Query usage: ~500ms (InfluxDB)
- Calculate metrics: ~10ms
- **Total:** ~510ms per device

**Scaling:**
- 100 devices: ~50s
- 500 devices: ~4 min
- Bottleneck: InfluxDB usage queries

---

## 🎯 Phase 4 Output

**Returns:**
```python
{
    'devices_analyzed': 20,
    'opportunities': [
        {
            'device_id': 'light.kitchen_switch',
            'utilization_pct': 20.0,
            'capabilities_unused': 4,
            'underutilized_features': [...]
        },
        {
            'device_id': 'switch.garage_outlet',
            'utilization_pct': 33.3,
            'capabilities_unused': 2,
            'underutilized_features': [...]
        }
        // ... 3-6 more opportunities
    ],
    'avg_utilization': 38.5,
    'timestamp': '2025-10-17T03:02:45Z'
}
```

**Opportunities sent to Phase 5 for AI suggestion generation.**

---

## ⚠️ Error Handling

**Analysis Errors:**

```python
try:
    opportunities = feature_analyzer.analyze_all_devices()
except Exception as e:
    logger.error(f"Feature analysis failed: {e}")
    opportunities = {'opportunities': []}  # Empty list, don't fail entire job
```

**Per-Device Errors:**

```python
# If individual device fails, continue with others
for device in devices:
    try:
        usage = query_usage(device)
    except Exception as e:
        logger.warning(f"Failed to analyze {device.name}: {e}")
        stats['errors'] += 1
        continue  # Skip this device, analyze others
```

**Graceful Degradation:**
- If feature analysis fails, Phase 5 can still generate pattern-based suggestions (Epic AI-1)
- Job continues even if zero opportunities found
- Next run (24 hours later) will retry

---

## 🔗 Next Steps

**Phase 4 Output Used By:**
- [Phase 5: OpenAI Suggestion Generation](AI_AUTOMATION_PHASE5_OPENAI.md) - Converts opportunities to automations

**Related Phases:**
- [Phase 1: Device Capability Discovery](AI_AUTOMATION_PHASE1_CAPABILITIES.md) - Provides capability data
- [Phase 2: Historical Event Fetching](AI_AUTOMATION_PHASE2_EVENTS.md) - Provides usage data
- [Phase 3: Pattern Detection](AI_AUTOMATION_PHASE3_PATTERNS.md) - Parallel analysis path
- [Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)

---

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Epic:** AI-2 - Device Intelligence

