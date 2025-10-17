# AutomateAI Subsystem: Complete Call Tree
## From 3 AM Wake-Up to Job Completion

**Service:** ai-automation-service (Port 8018)  
**Entry Point:** Scheduled daily analysis at 3 AM (configurable via `analysis_schedule`)  
**Story:** AI2.5 - Unified Daily Batch Job (Epic AI-1 + Epic AI-2)  
**Purpose:** Discover device capabilities, detect usage patterns, and generate AI-powered automation suggestions

**🔄 DOCUMENTATION UPDATE (Oct 17, 2025):**
- Updated database schema for Story AI1.23 (Conversational Suggestion Refinement)
- Added new fields: `description_only`, `conversation_history`, `refinement_count`, etc.
- Updated status lifecycle to support both legacy (pending) and conversational (draft→refining→yaml_generated) flows
- Clarified `automation_yaml` is now NULLABLE until user approval

**📋 IMPLEMENTATION PLAN:** See [AI_PATTERN_DETECTION_IMPLEMENTATION_PLAN.md](../../AI_PATTERN_DETECTION_IMPLEMENTATION_PLAN.md) for Phase 1 MVP architecture with HuggingFace models integration  

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

---

## Phase 1: Device Capability Update (Epic AI-2)

**Purpose:** Discover and update device capabilities from Home Assistant/Zigbee2MQTT  
**Epic:** AI-2 - Device Intelligence  
**Story:** AI2.1 - MQTT Capability Listener & Universal Parser

### Call Tree

```
run_daily_analysis() [line 104]
├── DataAPIClient.__init__() [line 142]
│   ├── httpx.AsyncClient()
│   └── InfluxDBEventClient.__init__() [data_api_client.py:48]
│       └── influxdb_client.InfluxDBClient()
│
└── update_device_capabilities_batch() [line 150]
    ├── Step 1: Get all Home Assistant devices
    │   └── data_api_client.get_all_devices() [capability_batch.py:61]
    │       └── GET http://data-api:8006/api/devices
    │           └── Returns: List[Dict] with device metadata
    │
    ├── Step 2: Query Zigbee2MQTT bridge (one-time batch)
    │   └── _query_zigbee2mqtt_bridge(mqtt_client) [capability_batch.py:178]
    │       ├── Subscribe: "zigbee2mqtt/bridge/devices"
    │       ├── Publish request: "zigbee2mqtt/bridge/request/devices" (empty payload)
    │       ├── Wait for response (10s timeout)
    │       ├── Parse JSON: List of device definitions
    │       ├── Unsubscribe from bridge
    │       └── Returns: List[Dict] with device definitions + exposes
    │
    ├── Step 3: Parse and store capabilities
    │   ├── CapabilityParser.__init__() [capability_batch.py:100]
    │   │
    │   └── For each device with bridge data:
    │       ├── Check if capability exists and is fresh [capability_batch.py:119]
    │       │   └── IF exists AND age < 30 days: SKIP (no update needed)
    │       │
    │       ├── Extract exposes from bridge_device [capability_batch.py:126]
    │       │   └── exposes = bridge_device.get('exposes', [])
    │       │
    │       ├── parser.parse_exposes(exposes) [capability_parser.py:38]
    │       │   ├── For each expose in exposes:
    │       │   │   ├── IF type == 'light':
    │       │   │   │   └── _parse_light_control() [line 129]
    │       │   │   │       ├── Extract features: state, brightness, color_xy, color_temp
    │       │   │   │       ├── Assess complexity: easy/medium based on features
    │       │   │   │       └── Return: {"light_control": {...}}
    │       │   │   │
    │       │   │   ├── IF type == 'switch':
    │       │   │   │   └── _parse_switch_control() [line 164]
    │       │   │   │       └── Return: {"switch_control": {...}}
    │       │   │   │
    │       │   │   ├── IF type == 'enum':
    │       │   │   │   └── _parse_enum_option() [line 212]
    │       │   │   │       ├── Extract: name, values list
    │       │   │   │       ├── _map_mqtt_to_friendly(name) [line 298]
    │       │   │   │       │   └── "smartBulbMode" → "smart_bulb_mode"
    │       │   │   │       ├── _assess_complexity(name) [line 355]
    │       │   │   │       │   └── Check keywords: easy/medium/advanced
    │       │   │   │       └── Return: {friendly_name: {type, mqtt_name, values, ...}}
    │       │   │   │
    │       │   │   ├── IF type == 'numeric':
    │       │   │   │   └── _parse_numeric_option() [line 241]
    │       │   │   │       ├── Extract: name, min, max, unit
    │       │   │   │       ├── _map_mqtt_to_friendly(name)
    │       │   │   │       ├── _assess_complexity(name)
    │       │   │   │       └── Return: {friendly_name: {type, mqtt_name, min, max, ...}}
    │       │   │   │
    │       │   │   └── IF type == 'binary':
    │       │   │       └── _parse_binary_option() [line 270]
    │       │   │           └── Return: {friendly_name: {type, mqtt_name, ...}}
    │       │   │
    │       │   └── Returns: Dict[str, Dict] - All parsed capabilities
    │       │       Example: {
    │       │         "light_control": {...},
    │       │         "smart_bulb_mode": {...},
    │       │         "auto_off_timer": {...}
    │       │       }
    │       │
    │       └── upsert_device_capability(db, capability_data) [capability_batch.py:148]
    │           ├── Prepare capability_data dict
    │           ├── database/crud.py:upsert_device_capability()
    │           │   ├── Check if capability exists (by device_model)
    │           │   ├── IF exists: UPDATE last_updated, capabilities JSON
    │           │   └── IF not exists: INSERT new DeviceCapability record
    │           │
    │           └── db.commit()
    │
    └── Returns: {
        'devices_checked': int,
        'capabilities_updated': int,
        'new_devices': int,
        'errors': int
    }
```

**Key Files:**
- `device_intelligence/capability_batch.py` - Batch update orchestration
- `device_intelligence/capability_parser.py` - Universal Zigbee2MQTT parser
- `device_intelligence/mqtt_capability_listener.py` - MQTT subscription handler
- `clients/mqtt_client.py` - MQTT communication layer

**Database Impact:** Inserts/updates in `device_capabilities` table (SQLite)

---

### Deep Dive: Understanding Device Capability Discovery

This section explains how the system discovers what your smart home devices can do.

#### What Problem Does This Solve?

**The Challenge:**
- Home Assistant has 100+ integration types (Zigbee, Z-Wave, WiFi, etc.)
- Each manufacturer has unique features (Inovelli LEDs, Aqara sensors, IKEA presets)
- No universal way to know what features a device supports
- Manual configuration is time-consuming and error-prone

**The Solution:**
- Query Zigbee2MQTT bridge for device definitions
- Parse the standardized "exposes" format
- Store capabilities in database for AI analysis
- Automatically detect underutilized features

#### Example: Inovelli VZM31-SN Smart Switch

Let's trace a real device through the discovery process:

**Step 1: Home Assistant Device Record**
```json
{
  "device_id": "abcd1234",
  "name": "Kitchen Light",
  "manufacturer": "Inovelli",
  "model": "VZM31-SN",
  "via_device": "zigbee2mqtt_coordinator"
}
```

**Step 2: Zigbee2MQTT Bridge Response**

When we request `zigbee2mqtt/bridge/request/devices`, Zigbee2MQTT responds with:

```json
[
  {
    "ieee_address": "0x00124b0024c6d8e9",
    "friendly_name": "Kitchen Light",
    "definition": {
      "model": "VZM31-SN",
      "vendor": "Inovelli",
      "description": "Red Series On/Off Switch",
      "exposes": [
        {
          "type": "light",
          "features": [
            {"name": "state", "property": "state", "access": 7},
            {"name": "brightness", "property": "brightness", "access": 7}
          ]
        },
        {
          "type": "enum",
          "name": "smartBulbMode",
          "property": "smart_bulb_mode",
          "values": ["Disabled", "Enabled"],
          "description": "Smart bulb mode prevents switch from turning off power"
        },
        {
          "type": "numeric",
          "name": "autoTimerOff",
          "property": "auto_off_timer",
          "value_min": 0,
          "value_max": 32767,
          "unit": "s",
          "description": "Automatically turn off after X seconds"
        },
        {
          "type": "enum",
          "name": "ledEffect",
          "property": "led_effect",
          "values": ["Off", "Solid", "Slow Blink", "Fast Blink", "Pulse", "Chase", "Open-Close", "Small-to-Big"],
          "description": "LED notification effect"
        },
        {
          "type": "numeric",
          "name": "defaultLevelLocal",
          "property": "default_level_local",
          "value_min": 0,
          "value_max": 254,
          "description": "Default brightness when turned on locally"
        }
      ]
    }
  }
]
```

**Step 3: CapabilityParser Processing**

The parser processes each "expose" and converts to structured capabilities:

```python
# parser.parse_exposes(exposes)

# Process type: "light"
_parse_light_control(expose) → {
  "light_control": {
    "type": "composite",
    "mqtt_name": "light",
    "description": "Basic light control",
    "complexity": "easy",
    "features": ["state", "brightness"]
  }
}

# Process type: "enum" - smartBulbMode
_parse_enum_option(expose) → {
  "smart_bulb_mode": {  # Converted from camelCase
    "type": "enum",
    "mqtt_name": "smartBulbMode",
    "values": ["Disabled", "Enabled"],
    "description": "Smart bulb mode prevents switch from turning off power",
    "complexity": "easy"
  }
}

# Process type: "numeric" - autoTimerOff
_parse_numeric_option(expose) → {
  "auto_off_timer": {  # Converted from camelCase
    "type": "numeric",
    "mqtt_name": "autoTimerOff",
    "min": 0,
    "max": 32767,
    "unit": "s",
    "description": "Automatically turn off after X seconds",
    "complexity": "medium"  # "timer" keyword detected
  }
}

# Process type: "enum" - ledEffect
_parse_enum_option(expose) → {
  "led_notifications": {  # Friendly name mapped
    "type": "enum",
    "mqtt_name": "ledEffect",
    "values": ["Off", "Solid", "Slow Blink", "Fast Blink", "Pulse", "Chase", "Open-Close", "Small-to-Big"],
    "description": "LED notification effect",
    "complexity": "advanced"  # "effect" keyword detected
  }
}

# Process type: "numeric" - defaultLevelLocal
_parse_numeric_option(expose) → {
  "default_level_local": {
    "type": "numeric",
    "mqtt_name": "defaultLevelLocal",
    "min": 0,
    "max": 254,
    "unit": "",
    "description": "Default brightness when turned on locally",
    "complexity": "easy"
  }
}
```

**Step 4: Database Storage**

Final capability record stored in SQLite:

```json
{
  "device_model": "VZM31-SN",
  "manufacturer": "Inovelli",
  "integration_type": "zigbee",
  "description": "Red Series On/Off Switch",
  "capabilities": {
    "light_control": {...},
    "smart_bulb_mode": {...},
    "auto_off_timer": {...},
    "led_notifications": {...},
    "default_level_local": {...}
  },
  "mqtt_exposes": [...],  // Raw data preserved
  "source": "zigbee2mqtt_bridge",
  "last_updated": "2025-10-17T03:00:15Z"
}
```

#### Universal Parser: Why It Works for All Manufacturers

**The Zigbee2MQTT "exposes" format is standardized:**

All 6,000+ supported devices (Inovelli, Aqara, IKEA, Xiaomi, Sonoff, Tuya, etc.) use the same format:

```json
{
  "type": "light" | "switch" | "enum" | "numeric" | "binary" | "climate",
  "name": "featureName",  // For non-composite types
  "features": [...],      // For composite types (light, climate)
  "values": [...],        // For enum types
  "value_min": N,         // For numeric types
  "value_max": N,
  "unit": "string",
  "description": "string"
}
```

**Examples from Different Manufacturers:**

**Aqara MCCGQ11LM (Contact Sensor):**
```json
{
  "type": "binary",
  "name": "contact",
  "value_on": false,
  "value_off": true,
  "description": "Contact sensor state"
}
→ Parsed as: "contact_sensor": {type: "binary", ...}
```

**IKEA E1744 (SYMFONISK Remote):**
```json
{
  "type": "enum",
  "name": "action",
  "values": ["single", "double", "triple", "rotate_left", "rotate_right"],
  "description": "Button action"
}
→ Parsed as: "button_action": {type: "enum", values: [...]}
```

**Xiaomi WSDCGQ11LM (Temperature Sensor):**
```json
{
  "type": "numeric",
  "name": "temperature",
  "unit": "°C",
  "value_min": -40,
  "value_max": 125
}
→ Parsed as: "temperature": {type: "numeric", min: -40, max: 125, unit: "°C"}
```

#### Complexity Assessment

The parser automatically categorizes features by complexity:

**Easy (Default):**
- Basic on/off controls
- Simple configuration options
- Common user-facing features

**Medium:**
- Timers, delays, thresholds
- Duration-based settings
- Example: `autoTimerOff`, `delayedAllOn`

**Advanced:**
- Effects, transitions, scenes
- Calibration, sensitivity
- Example: `ledEffect`, `motionSensitivity`, `sceneRecall`

**Why This Matters:**
- Feature Analysis (Phase 4) prioritizes underutilized "easy" features
- LLM suggestions focus on accessible automations
- Advanced features may require more user expertise

#### Name Normalization

The parser converts manufacturer-specific naming to consistent format:

**Conversion Rules:**

```python
# CamelCase → snake_case
"smartBulbMode" → "smart_bulb_mode"
"autoTimerOff" → "auto_off_timer"
"LEDWhenOn" → "led_when_on"

# Known mappings (manufacturer-specific)
"ledEffect" → "led_notifications"  # More user-friendly
"localProtection" → "local_protection"
"powerOnBehavior" → "power_on_behavior"

# Handles special cases
"LED-when-on" → "led_when_on"  # Removes hyphens
"auto  timer" → "auto_timer"   # Removes duplicate spaces
```

**Benefits:**
- Consistent database queries
- Better LLM prompt generation
- Easier feature matching across devices

#### Caching Strategy

**Fresh Capability Check:**

```python
def _is_stale(capability_record, max_age_days=30) -> bool:
    age = datetime.utcnow() - capability_record.last_updated
    return age > timedelta(days=max_age_days)
```

**Logic:**
1. Check if device_model exists in database
2. If exists and age < 30 days: **SKIP** (no update needed)
3. If stale or not exists: Query Zigbee2MQTT and update

**Why 30 days?**
- Device capabilities rarely change (firmware updates are infrequent)
- Reduces MQTT traffic
- Balances freshness vs performance

**Force Refresh:**
- Delete capability record from database
- Next run will fetch fresh data
- Useful after firmware updates

#### Performance Characteristics

**Typical Run:**
- 20 devices in Home Assistant
- 15 Zigbee devices in bridge
- 10 need capability updates (new or stale)

**Timings:**
1. Fetch HA devices: ~0.5s (HTTP GET)
2. Query Zigbee2MQTT bridge: ~2-5s (MQTT request/response)
3. Parse capabilities: ~0.1s per device (1s total)
4. Database operations: ~0.5s (SQLite upserts)

**Total: ~10-15 seconds for Phase 1**

**Scaling:**
- 100 devices: ~30-45s
- 500 devices: ~2-3 min
- Bottleneck: MQTT bridge response time

#### Error Handling

**Graceful Degradation:**

```python
try:
    parsed_capabilities = parser.parse_exposes(exposes)
except Exception as e:
    logger.error(f"Failed to parse {device_model}: {e}")
    stats["errors"] += 1
    continue  # Don't fail entire job
```

**Common Errors:**
1. **Bridge timeout:** Bridge doesn't respond in 10s
   - Log warning, continue with cached capabilities
   
2. **Invalid exposes format:** Manufacturer-specific deviation
   - Log error with device details
   - Skip device, continue with others
   
3. **Database error:** SQLite locked or disk full
   - Retry with exponential backoff
   - Fail gracefully if persistent

**Recovery:**
- Next run (24 hours later) retries failed devices
- Manual trigger available via API: `POST /api/analysis/trigger`

---

## Phase 2: Fetch Historical Events (Shared)

**Purpose:** Retrieve last 30 days of Home Assistant events for analysis  
**Epic:** Shared by AI-1 (Pattern Detection) and AI-2 (Feature Analysis)

### Call Tree

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

## Phase 3: Pattern Detection (Epic AI-1)

**Purpose:** Detect time-of-day and co-occurrence patterns from event history  
**Epic:** AI-1 - Pattern Detection & Automation Suggestions

### Call Tree

```
run_daily_analysis() [line 203]
├── Time-of-Day Pattern Detection [line 208]
│   ├── TimeOfDayPatternDetector.__init__() [pattern_analyzer/time_of_day.py]
│   │   ├── min_occurrences = 5
│   │   └── min_confidence = 0.7
│   │
│   └── tod_detector.detect_patterns(events_df) [time_of_day.py:~50]
│       ├── Group events by (entity_id, hour)
│       ├── Calculate frequency and confidence
│       ├── Filter by min_occurrences and min_confidence
│       └── Returns: List[Dict] with pattern metadata:
│           - pattern_type: 'time_of_day'
│           - device_id
│           - hour, minute
│           - occurrences
│           - confidence
│           - last_seen
│
├── Co-Occurrence Pattern Detection [line 221]
│   ├── CoOccurrencePatternDetector.__init__() [pattern_analyzer/co_occurrence.py]
│   │   ├── window_minutes = 5
│   │   ├── min_support = 5
│   │   └── min_confidence = 0.7
│   │
│   ├── IF len(events_df) > 50,000:
│   │   └── co_detector.detect_patterns_optimized(events_df) [co_occurrence.py:~150]
│   │       ├── Optimized sliding window algorithm
│   │       ├── Hash-based lookups for performance
│   │       └── Returns: List[Dict] co-occurrence patterns
│   │
│   └── ELSE:
│       └── co_detector.detect_patterns(events_df) [co_occurrence.py:~80]
│           ├── Standard sliding window (O(n²))
│           ├── Find events within time window
│           ├── Calculate support and confidence
│           └── Returns: List[Dict] with pattern metadata:
│               - pattern_type: 'co_occurrence'
│               - trigger_device_id
│               - target_device_id
│               - time_window_minutes
│               - support
│               - confidence
│
├── Combine all_patterns = tod_patterns + co_patterns [line 233]
│
└── store_patterns() [line 241]
    ├── database/crud.py:store_patterns()
    │   ├── For each pattern:
    │   │   ├── Pattern.from_dict()
    │   │   └── db.add(pattern)
    │   │
    │   └── db.commit()
    │
    └── Returns: patterns_stored (int)
```

**Key Files:**
- `pattern_analyzer/time_of_day.py` - Time-based pattern detection
- `pattern_analyzer/co_occurrence.py` - Sequential event pattern detection
- `database/crud.py` - Database storage operations

**Database Impact:** Inserts into `patterns` table (SQLite)  
**Performance:** Optimized path for >50K events using hash-based algorithms

---

## Phase 4: Feature Analysis (Epic AI-2)

**Purpose:** Analyze device utilization and identify underutilized features  
**Epic:** AI-2 - Device Intelligence  
**Story:** AI2.3 - Device Matching & Feature Analysis

### Call Tree

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
- SQLite: `device_capabilities` table
- InfluxDB: `home_assistant_events` bucket (usage queries)

**Logic:** Identifies devices with <50% feature utilization

---

## Phase 5: Combined Suggestion Generation (AI-1 + AI-2)

**Purpose:** Generate natural language automation suggestions using OpenAI GPT-4o-mini  
**Epics:** Combined AI-1 (Pattern-based) + AI-2 (Feature-based)

### Call Tree

```
run_daily_analysis() [line 282]
├── OpenAIClient.__init__() [line 285]
│   ├── api_key from settings.openai_api_key
│   ├── model = "gpt-4o-mini"
│   └── Initialize AsyncOpenAI client
│
├── Part A: Pattern-based Suggestions (Epic AI-1) [line 290]
│   ├── Sort patterns by confidence [line 295]
│   ├── Select top 10 patterns [line 296]
│   │
│   └── For each top_pattern:
│       ├── openai_client.generate_automation_suggestion(pattern) [line 302]
│       │   ├── _build_prompt(pattern) [llm/openai_client.py:121]
│       │   │   ├── IF time_of_day: _build_time_of_day_prompt()
│       │   │   └── IF co_occurrence: _build_co_occurrence_prompt()
│       │   │
│       │   ├── client.chat.completions.create() [openai_client.py:78]
│       │   │   ├── model = "gpt-4o-mini"
│       │   │   ├── temperature = 0.7
│       │   │   ├── max_tokens = 600
│       │   │   ├── system_prompt: "You are a home automation expert..."
│       │   │   └── user_prompt: Pattern-specific prompt
│       │   │
│       │   ├── Track token usage [openai_client.py:100]
│       │   │   ├── total_input_tokens += prompt_tokens
│       │   │   ├── total_output_tokens += completion_tokens
│       │   │   └── total_tokens_used += total_tokens
│       │   │
│       │   └── _parse_automation_response() [openai_client.py:112]
│       │       ├── Extract YAML automation block
│       │       ├── Validate Home Assistant YAML structure
│       │       └── Returns: AutomationSuggestion(
│       │           alias, description, automation_yaml,
│       │           rationale, category, priority, confidence
│       │       )
│       │
│       └── pattern_suggestions.append() [line 304]
│
├── Part B: Feature-based Suggestions (Epic AI-2) [line 330]
│   ├── IF opportunities found:
│   │   ├── FeatureSuggestionGenerator.__init__() [line 336]
│   │   │   ├── llm_client (OpenAIClient)
│   │   │   ├── feature_analyzer
│   │   │   └── db_session factory
│   │   │
│   │   └── feature_generator.generate_suggestions(max=10) [line 342]
│   │       ├── feature_intelligence/feature_suggestion_generator.py
│   │       │
│   │       ├── For each opportunity:
│   │       │   ├── Build feature-focused prompt:
│   │       │   │   - Device capabilities (unused features)
│   │       │   │   - Current utilization stats
│   │       │   │   - Underutilized feature descriptions
│   │       │   │
│   │       │   ├── llm_client.generate_automation_suggestion() [same as above]
│   │       │   └── feature_suggestions.append()
│   │       │
│   │       └── Returns: List[Dict] feature suggestions
│   │
│   └── ELSE: No opportunities, skip
│
├── Part C: Combine and Rank [line 353]
│   ├── all_suggestions = pattern_suggestions + feature_suggestions
│   ├── Sort by confidence (descending)
│   └── Keep top 10 suggestions total
│
└── Store Suggestions [line 366]
    ├── For each suggestion in all_suggestions:
    │   └── store_suggestion(db, suggestion) [database/crud.py:180]
    │       ├── Create Suggestion object (Story AI1.23 - Conversational Flow):
    │       │   ├── pattern_id = suggestion.get('pattern_id')  # Link to detected pattern
    │       │   ├── title = suggestion['title']  # User-friendly name
    │       │   │
    │       │   ├── # NEW: Description-first fields (Story AI1.23)
    │       │   ├── description_only = suggestion['description']  # Human-readable description (required)
    │       │   ├── conversation_history = []  # Conversation edit history (JSON array)
    │       │   ├── device_capabilities = suggestion.get('device_capabilities', {})  # Cached device features
    │       │   ├── refinement_count = 0  # Number of user edits
    │       │   │
    │       │   ├── # YAML generation (nullable until approved in conversational flow)
    │       │   ├── automation_yaml = suggestion.get('automation_yaml')  # NULL for draft, populated when approved
    │       │   ├── yaml_generated_at = None  # Set when YAML is generated after approval
    │       │   │
    │       │   ├── # Status tracking (updated for conversational flow)
    │       │   ├── status = 'pending'  # Legacy batch flow: pending → deployed/rejected
    │       │   ├──                     # NEW conversational flow: draft → refining → yaml_generated → deployed
    │       │   │
    │       │   ├── # Metadata fields
    │       │   ├── confidence = suggestion['confidence']  # Pattern confidence
    │       │   ├── category = suggestion.get('category')  # energy/comfort/security/convenience
    │       │   ├── priority = suggestion.get('priority')  # high/medium/low
    │       │   │
    │       │   ├── # Timestamps
    │       │   ├── created_at = datetime.now(utc)
    │       │   ├── updated_at = datetime.now(utc)
    │       │   ├── approved_at = None  # NEW: Set when user approves
    │       │   └── deployed_at = None  # Set when deployed to HA
    │       │
    │       ├── db.add(suggestion) [line 205]
    │       │   └── Add to SQLAlchemy session (not yet committed)
    │       │
    │       ├── db.commit() [line 206]
    │       │   └── Write to SQLite database (suggestions table)
    │       │
    │       ├── db.refresh(suggestion) [line 207]
    │       │   └── Reload from DB to get auto-generated ID
    │       │
    │       └── Returns: Suggestion object with id assigned
    │
    └── Returns: suggestions_stored (int)
```

**Key Files:**
- `llm/openai_client.py` - OpenAI API integration
- `device_intelligence/feature_suggestion_generator.py` - Feature-based prompts
- `database/crud.py` - Suggestion storage

**Database Impact:** Inserts into `suggestions` table (SQLite)

**Cost Tracking:**
- Input tokens: ~150-300 per suggestion
- Output tokens: ~400-600 per suggestion
- Cost: $0.00000015/input token + $0.00000060/output token
- Total: ~$0.0003-0.0005 per suggestion

---

### Deep Dive: Understanding Suggestion Storage

This section explains how AI-generated automation suggestions are persisted to the database and prepared for user review.

#### What Gets Stored?

Each suggestion is a complete, deployable Home Assistant automation with metadata:

**Core Data:**
- **automation_yaml**: Valid Home Assistant YAML ready to deploy
- **title**: User-friendly name (e.g., "Morning Coffee Maker Routine")
- **description**: Plain English explanation of what it does

**Metadata:**
- **confidence**: Pattern confidence score (0.0 - 1.0)
- **category**: energy, comfort, security, or convenience
- **priority**: high, medium, or low
- **status**: Lifecycle state (pending → approved → deployed or rejected)

**Relationships:**
- **pattern_id**: Links to the detected pattern (if pattern-based)
- **suggestion_id** → **user_feedback**: Track user acceptance/rejection

#### Database Schema: `suggestions` Table

**SQLite Schema (Updated for Story AI1.23 - Conversational Refinement):**

```sql
CREATE TABLE suggestions (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER,  -- Foreign key to patterns.id (nullable for feature-based)
    
    -- Core Fields
    title VARCHAR NOT NULL,
    
    -- NEW: Description-First Fields (Story AI1.23)
    description_only TEXT NOT NULL,  -- Human-readable description (REQUIRED)
    conversation_history JSON,  -- Array of edit history
    device_capabilities JSON,  -- Cached device features for context
    refinement_count INTEGER DEFAULT 0,  -- Number of user refinements
    
    -- YAML Generation (nullable until approved in conversational flow)
    automation_yaml TEXT,  -- NULL for draft, populated after approval (CHANGED: was NOT NULL)
    yaml_generated_at DATETIME,  -- NEW: When YAML was created
    
    -- Status Tracking (updated for conversational flow)
    status VARCHAR DEFAULT 'pending',  -- Legacy: pending → deployed/rejected
                                       -- NEW conversational: draft → refining → yaml_generated → deployed
    
    -- Metadata
    confidence FLOAT NOT NULL,
    category VARCHAR,  -- energy/comfort/security/convenience
    priority VARCHAR,  -- high/medium/low
    
    -- Timestamps
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    approved_at DATETIME,  -- NEW: When user approved
    deployed_at DATETIME,  -- When deployed to HA
    ha_automation_id VARCHAR,  -- HA's ID after deployment
    
    FOREIGN KEY(pattern_id) REFERENCES patterns(id)
);

CREATE INDEX idx_suggestions_status ON suggestions(status);
CREATE INDEX idx_suggestions_created_at ON suggestions(created_at DESC);
```

**Field Details (Updated for Story AI1.23):**

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `id` | INTEGER | Auto-increment primary key | 42 |
| `pattern_id` | INTEGER | Link to pattern (Epic AI-1) or NULL (Epic AI-2) | 17 |
| `title` | VARCHAR | User-friendly name | "Living Room Light Morning Routine" |
| **`description_only`** | **TEXT** | **Human-readable description (REQUIRED)** | "Turn on living room lights at 7:15 AM on weekdays..." |
| **`conversation_history`** | **JSON** | **Conversation edit history** | `[{"user": "make it 7:30", "timestamp": "..."}]` |
| **`device_capabilities`** | **JSON** | **Cached device features for context** | `{"light.living_room": {"brightness": true}}` |
| **`refinement_count`** | **INTEGER** | **Number of user refinements** | 3 |
| `automation_yaml` | TEXT | Deployable HA YAML (NULLABLE until approved) | `alias: "Morning Lights"\ntrigger:...` or NULL |
| **`yaml_generated_at`** | **DATETIME** | **When YAML was generated** | "2025-10-17T09:15:00Z" |
| `status` | VARCHAR | Lifecycle state (see updated flow below) | "draft" → "refining" → "yaml_generated" → "deployed" |
| `confidence` | FLOAT | Pattern confidence | 0.87 |
| `category` | VARCHAR | Suggestion type | "convenience" |
| `priority` | VARCHAR | Importance level | "medium" |
| `created_at` | DATETIME | When generated | "2025-10-17T03:05:23Z" |
| `updated_at` | DATETIME | Last modified | "2025-10-17T09:15:00Z" |
| **`approved_at`** | **DATETIME** | **When user approved** | "2025-10-17T09:10:00Z" |
| `deployed_at` | DATETIME | When deployed to HA | "2025-10-17T10:00:00Z" |
| `ha_automation_id` | VARCHAR | HA automation ID | "automation.morning_lights" |

**Bold fields** = NEW in Story AI1.23 (Conversational Suggestion Refinement)

#### Status Lifecycle (Updated for Story AI1.23)

Suggestions now support TWO flows:

**LEGACY FLOW (Pattern-Based Daily Analysis):**
```
       ┌─────────┐
       │ pending │  ← Created by AI (3 AM daily run) with full YAML
       └────┬────┘
            │
            ├──────────────┐
            ▼              ▼
       ┌─────────┐    ┌──────────┐
       │deployed │    │ rejected │  ← User decision (immediate)
       └─────────┘    └──────────┘
```

**NEW CONVERSATIONAL FLOW (Natural Language Requests - Story AI1.23):**
```
       ┌───────┐
       │ draft │  ← Created from NL request (description only, NO YAML yet)
       └───┬───┘
           │
           ▼
       ┌──────────┐
       │ refining │  ← User iterates with natural language edits
       └─────┬────┘    (max 10 refinements, tracked in conversation_history)
             │
             ├─────────────┐
             ▼             ▼
    ┌────────────────┐  ┌──────────┐
    │ yaml_generated │  │ rejected │  ← User approves or rejects
    └────────┬───────┘  └──────────┘
             │
             ▼
        ┌─────────┐
        │deployed │  ← YAML generated and deployed to HA
        └─────────┘
```

**Status Definitions (Updated):**

1. **pending** (Legacy Flow Only)
   - Created during Phase 5 of daily analysis
   - Includes full automation_yaml from start
   - Ready for immediate deployment
   - Awaiting user review

2. **draft** (NEW - Conversational Flow Only - Story AI1.23)
   - Created from natural language request
   - `description_only` populated, `automation_yaml` is NULL
   - User can refine with natural language
   - First step in conversational refinement

3. **refining** (NEW - Conversational Flow Only - Story AI1.23)
   - User is actively editing with natural language
   - `refinement_count` increments with each edit
   - `conversation_history` tracks all changes
   - Max 10 refinements allowed
   - Still NO automation_yaml (only description)

4. **yaml_generated** (NEW - Conversational Flow Only - Story AI1.23)
   - User approved the description
   - System generates automation_yaml from final description
   - `yaml_generated_at` timestamp set
   - `approved_at` timestamp set
   - Ready for deployment

5. **deployed** (Both Flows)
   - Successfully deployed to Home Assistant
   - `deployed_at` timestamp set
   - `ha_automation_id` populated
   - Automation is now active

6. **rejected** (Both Flows)
   - User rejected the suggestion
   - Not shown in active suggestions
   - Kept for analytics/learning
   - Can occur at any stage

**Status Query Examples:**

```python
# Get pending suggestions for user review
pending = await get_suggestions(db, status='pending', limit=10)

# Get deployed suggestions
deployed = await get_suggestions(db, status='deployed', limit=50)

# Get all suggestions (any status)
all_suggestions = await get_suggestions(db, status=None, limit=100)
```

#### Example: Real Suggestion Storage

Let's trace a complete suggestion from generation to storage:

**Input: Pattern-Based Suggestion (Epic AI-1)**

```python
suggestion_data = {
    'type': 'pattern_automation',
    'source': 'Epic-AI-1',
    'pattern_id': 42,  # Links to detected pattern
    'pattern_type': 'time_of_day',
    'title': 'Living Room Light Morning Routine',
    'description': 'Turn on living room lights at 7:15 AM on weekdays based on consistent usage pattern detected over 30 days',
    'automation_yaml': '''alias: "Living Room Light Morning Routine"
description: "Automatically turn on living room lights at 7:15 AM on weekdays"
trigger:
  - platform: time
    at: "07:15:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 80
mode: single''',
    'confidence': 0.87,
    'category': 'convenience',
    'priority': 'medium',
    'rationale': 'Detected consistent pattern: light.living_room turns on at 7:15 AM (±10 min) on weekdays with 87% regularity over the past 30 days. High confidence automation candidate.'
}
```

**Storage Process:**

```python
# Phase 5, line 366
async with get_db_session() as db:
    stored = await store_suggestion(db, suggestion_data)

# Inside store_suggestion (crud.py:180)
suggestion = Suggestion(
    pattern_id=42,  # Links to pattern
    title="Living Room Light Morning Routine",
    description="Turn on living room lights at 7:15 AM...",
    automation_yaml="alias: \"Living Room Light Morning Routine\"\n...",
    status="pending",  # Always pending on creation
    confidence=0.87,
    category="convenience",
    priority="medium",
    created_at=datetime(2025, 10, 17, 3, 5, 23, tzinfo=timezone.utc),
    updated_at=datetime(2025, 10, 17, 3, 5, 23, tzinfo=timezone.utc)
)

db.add(suggestion)
await db.commit()
await db.refresh(suggestion)  # Populates suggestion.id = 123

logger.info(f"✅ Stored suggestion: Living Room Light Morning Routine")
```

**Database Record:**

```json
{
  "id": 123,
  "pattern_id": 42,
  "title": "Living Room Light Morning Routine",
  "description": "Turn on living room lights at 7:15 AM on weekdays...",
  "automation_yaml": "alias: \"Living Room Light Morning Routine\"...",
  "status": "pending",
  "confidence": 0.87,
  "category": "convenience",
  "priority": "medium",
  "created_at": "2025-10-17T03:05:23Z",
  "updated_at": "2025-10-17T03:05:23Z",
  "deployed_at": null,
  "ha_automation_id": null
}
```

#### Example: Feature-Based Suggestion (Epic AI-2)

**Input: Underutilized Feature**

```python
suggestion_data = {
    'type': 'feature_automation',
    'source': 'Epic-AI-2',
    'pattern_id': None,  # No pattern - based on capability analysis
    'device_id': 'light.kitchen_switch',
    'device_model': 'VZM31-SN',
    'feature_name': 'led_notifications',
    'title': 'Garage Door LED Notification',
    'description': 'Flash kitchen switch LED red when garage door is left open for 10 minutes',
    'automation_yaml': '''alias: "Garage Door LED Notification"
description: "Visual notification using kitchen switch LED"
trigger:
  - platform: state
    entity_id: cover.garage_door
    to: "open"
    for:
      minutes: 10
action:
  - service: mqtt.publish
    data:
      topic: "zigbee2mqtt/kitchen_switch/set"
      payload: '{"led_effect": "Fast Blink", "led_color": "Red"}'
mode: single''',
    'confidence': 0.75,  # Lower confidence (opportunity-based, not pattern)
    'category': 'security',
    'priority': 'high',
    'rationale': 'Device has unused LED notification capability (led_effect). Kitchen is high-traffic area. Garage security is important.'
}
```

**Storage Result:**

```json
{
  "id": 124,
  "pattern_id": null,  // No pattern - feature-based
  "title": "Garage Door LED Notification",
  "status": "pending",
  "confidence": 0.75,
  "category": "security",
  "priority": "high",
  ...
}
```

#### Relationship to Patterns

**Pattern-Based Suggestions (Epic AI-1):**
```sql
-- Get suggestion with its pattern
SELECT 
    s.*,
    p.pattern_type,
    p.device_id,
    p.occurrences
FROM suggestions s
JOIN patterns p ON s.pattern_id = p.id
WHERE s.id = 123;
```

**Feature-Based Suggestions (Epic AI-2):**
```sql
-- Feature-based suggestions have no pattern
SELECT * FROM suggestions
WHERE pattern_id IS NULL;  -- Epic AI-2 suggestions
```

**Why `pattern_id` is Nullable:**
- Epic AI-1: Pattern-driven → `pattern_id` populated
- Epic AI-2: Capability-driven → `pattern_id` is NULL
- Allows unified suggestion storage for both approaches

#### Batch Storage Performance

**Typical Daily Run:**

```python
# Phase 5 generates 10 suggestions (top ranked)
all_suggestions = [
    pattern_suggestion_1,  # confidence: 0.92
    pattern_suggestion_2,  # confidence: 0.87
    feature_suggestion_1,  # confidence: 0.81
    pattern_suggestion_3,  # confidence: 0.78
    feature_suggestion_2,  # confidence: 0.75
    ...  # 5 more
]

suggestions_stored = 0
for suggestion in all_suggestions:
    try:
        async with get_db_session() as db:
            await store_suggestion(db, suggestion)
        suggestions_stored += 1
    except Exception as e:
        logger.error(f"Failed to store suggestion: {e}")
        # Continue with next suggestion
```

**Performance:**
- ~50ms per suggestion (SQLite insert + commit)
- 10 suggestions: ~500ms total
- Parallel storage possible but not implemented (sequential is fast enough)

**Error Handling:**
- Individual suggestion failures don't block others
- Failed suggestions logged but job continues
- User sees partial results (e.g., 8/10 suggestions stored)

#### Querying Suggestions

**Common Query Patterns:**

1. **Get Pending Suggestions for UI:**
```python
# GET /api/suggestions?status=pending
suggestions = await get_suggestions(db, status='pending', limit=50)
```

2. **Get Recent Suggestions:**
```python
# Ordered by created_at DESC (newest first)
recent = await get_suggestions(db, status=None, limit=10)
```

3. **Get High-Confidence Suggestions:**
```python
# Custom query in crud.py
query = select(Suggestion).where(
    Suggestion.confidence >= 0.8,
    Suggestion.status == 'pending'
).order_by(Suggestion.confidence.desc())
```

4. **Get Suggestions by Category:**
```python
# Energy-saving suggestions
energy_suggestions = await db.execute(
    select(Suggestion).where(
        Suggestion.category == 'energy',
        Suggestion.status == 'pending'
    )
)
```

#### User Feedback Integration

**Related Table: `user_feedback`**

When user approves/rejects a suggestion:

```python
# User clicks "Approve" in UI
feedback = await store_feedback(db, {
    'suggestion_id': 123,
    'action': 'approved',
    'feedback_text': 'Great suggestion! I always do this manually.'
})

# Update suggestion status
suggestion.status = 'approved'
suggestion.updated_at = datetime.now(timezone.utc)
await db.commit()
```

**Feedback Tracking:**
```sql
SELECT 
    s.title,
    s.confidence,
    uf.action,
    uf.feedback_text
FROM suggestions s
JOIN user_feedback uf ON s.id = uf.suggestion_id
WHERE uf.action = 'approved';
```

**Future Enhancement:**
- Use feedback for ML model training
- Learn which suggestions users prefer
- Adjust confidence thresholds based on acceptance rate

#### Deployment Tracking

**When Suggestion is Deployed:**

```python
# POST /api/suggestions/{id}/deploy
suggestion = await db.get(Suggestion, suggestion_id)

# Deploy to Home Assistant
ha_automation_id = await ha_client.create_automation(
    yaml=suggestion.automation_yaml
)

# Update database
suggestion.status = 'deployed'
suggestion.deployed_at = datetime.now(timezone.utc)
suggestion.ha_automation_id = ha_automation_id
suggestion.updated_at = datetime.now(timezone.utc)
await db.commit()
```

**Deployment Verification:**

```sql
-- All deployed automations
SELECT 
    id,
    title,
    ha_automation_id,
    deployed_at
FROM suggestions
WHERE status = 'deployed'
ORDER BY deployed_at DESC;
```

#### Analytics & Reporting

**Suggestion Statistics:**

```python
# Get suggestion counts by status
stats = await db.execute(
    select(
        Suggestion.status,
        func.count().label('count')
    ).group_by(Suggestion.status)
)

# Example result:
# {
#   'pending': 15,
#   'approved': 8,
#   'deployed': 23,
#   'rejected': 12
# }
```

**Acceptance Rate:**
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as deployed,
    CAST(SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as acceptance_rate
FROM suggestions;
```

**Category Performance:**
```sql
SELECT 
    category,
    COUNT(*) as total,
    AVG(confidence) as avg_confidence,
    SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as deployed_count
FROM suggestions
GROUP BY category
ORDER BY deployed_count DESC;
```

#### Database Maintenance

**Old Suggestions Cleanup:**

```python
# Delete rejected suggestions older than 90 days
async def cleanup_old_suggestions(db: AsyncSession, days: int = 90):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    stmt = delete(Suggestion).where(
        Suggestion.status == 'rejected',
        Suggestion.created_at < cutoff
    )
    result = await db.execute(stmt)
    await db.commit()
    
    logger.info(f"Deleted {result.rowcount} old rejected suggestions")
```

**Database Size Management:**
- Each suggestion: ~2-3 KB (YAML is largest field)
- 100 suggestions: ~250 KB
- SQLite handles 10K+ suggestions easily
- Periodic cleanup keeps database lean

#### Error Scenarios

**Common Errors:**

1. **Duplicate Suggestion:**
```python
# Same automation generated twice
# Currently allowed (no unique constraint)
# Future: Add unique constraint on (title, automation_yaml hash)
```

2. **Invalid YAML:**
```python
# OpenAI generated invalid YAML
# Caught during validation (Story AI1.19: Safety Validation)
# Suggestion not stored if YAML is invalid
```

3. **Database Lock:**
```python
# SQLite locked by another process
# Retry with exponential backoff
# Log warning if persistent
```

4. **Transaction Rollback:**
```python
try:
    db.add(suggestion)
    await db.commit()
except Exception as e:
    await db.rollback()  # Undo changes
    logger.error(f"Failed to store: {e}")
    raise
```

#### Integration with UI

**API Endpoints:**

```typescript
// GET /api/suggestions?status=pending&limit=10
const suggestions = await fetch('/api/suggestions?status=pending');

// POST /api/suggestions/{id}/approve
await fetch(`/api/suggestions/${id}/approve`, { method: 'POST' });

// POST /api/suggestions/{id}/deploy
await fetch(`/api/suggestions/${id}/deploy`, { method: 'POST' });

// POST /api/suggestions/{id}/reject
await fetch(`/api/suggestions/${id}/reject`, { 
  method: 'POST',
  body: JSON.stringify({ reason: 'Not useful' })
});
```

**UI Display:**

```tsx
// AI Automation UI component
<SuggestionCard
  id={suggestion.id}
  title={suggestion.title}
  description={suggestion.description}
  confidence={suggestion.confidence}
  category={suggestion.category}
  priority={suggestion.priority}
  yaml={suggestion.automation_yaml}
  onApprove={() => approveSuggestion(suggestion.id)}
  onReject={() => rejectSuggestion(suggestion.id)}
/>
```

---

---

### Deep Dive: OpenAI Integration - Prompts, Templates & API Calls

This section explains how OpenAI GPT-4o-mini is used to transform detected patterns into natural language automation suggestions with valid Home Assistant YAML.

#### OpenAI Model Configuration

**Model Used:** `gpt-4o-mini`

**Why GPT-4o-mini?**
- **Cost-effective**: ~80% cheaper than GPT-4
- **Fast**: Lower latency for batch processing
- **Sufficient capability**: YAML generation doesn't require GPT-4's full power
- **Good context window**: 128K tokens (more than enough for our prompts)

**API Configuration:**
```python
client = AsyncOpenAI(api_key=settings.openai_api_key)

response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[system_prompt, user_prompt],
    temperature=0.7,     # Creativity level (0.0 = deterministic, 1.0 = creative)
    max_tokens=600       # Limit response length
)
```

**Temperature Setting (0.7):**
- **Not too low**: Avoids repetitive/boring suggestions
- **Not too high**: Maintains YAML validity and consistency
- **Sweet spot**: Creative but practical automations

**Max Tokens (600):**
- Typical response: 400-500 tokens
- YAML automation: ~200 tokens
- Rationale + metadata: ~100-200 tokens
- Buffer: 100 tokens

#### The API Call Flow

**Complete Request/Response Cycle:**

```python
# 1. Build prompt based on pattern type
prompt = _build_prompt(pattern, device_context)

# 2. Call OpenAI API with retry logic (3 attempts)
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "You are a home automation expert..."
        },
        {
            "role": "user",
            "content": prompt  # Pattern-specific prompt
        }
    ],
    temperature=0.7,
    max_tokens=600
)

# 3. Track token usage
usage = response.usage
total_input_tokens += usage.prompt_tokens    # ~150-300
total_output_tokens += usage.completion_tokens  # ~400-600
total_tokens_used += usage.total_tokens      # ~550-900

# 4. Parse LLM response
content = response.choices[0].message.content
suggestion = _parse_automation_response(content, pattern)

# 5. Return structured suggestion
return AutomationSuggestion(
    alias="Living Room Light Morning Routine",
    description="Turn on living room lights at 7:15 AM...",
    automation_yaml="alias: ...\ntrigger: ...",
    rationale="Detected consistent pattern...",
    category="convenience",
    priority="medium",
    confidence=0.87
)
```

#### System Prompt (Fixed for All Patterns)

**The Expert Persona:**

```
You are a home automation expert creating Home Assistant automations.
Generate valid YAML automations based on detected usage patterns.
Keep automations simple, practical, and easy to understand.
Always include proper service calls and entity IDs.
```

**Why This Works:**
- Establishes expertise and authority
- Sets expectations (YAML output)
- Emphasizes simplicity (users can understand)
- Ensures technical correctness (proper service calls)

#### Prompt Templates by Pattern Type

The system has **three specialized prompt templates** for different pattern types:

---

##### 1. Time-of-Day Pattern Template

**When Used:** Device consistently activates at same time each day

**Example Pattern:**
```python
{
    'pattern_type': 'time_of_day',
    'device_id': 'light.living_room',
    'hour': 7,
    'minute': 15,
    'occurrences': 26,
    'confidence': 0.87
}
```

**Generated Prompt:**

```
Create a Home Assistant automation for this detected usage pattern:

PATTERN DETECTED:
- Device: Living Room Light in Living Room
- Entity ID: light.living_room
- Device Type: light
- Pattern: Device activates at 07:15 consistently
- Occurrences: 26 times in last 30 days
- Confidence: 87%

INSTRUCTIONS:
1. Create a valid Home Assistant automation in YAML format
2. Use a descriptive alias starting with "AI Suggested: " and include the DEVICE NAME (Living Room Light), not the entity ID
3. Use time trigger for 07:15:00
4. Determine appropriate service call based on device type (light.turn_on, light.turn_off, climate.set_temperature, etc.)
5. Provide a brief rationale (1-2 sentences) explaining why this automation makes sense
6. Categorize as: energy, comfort, security, or convenience
7. Assign priority: high, medium, or low

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: Living Room Light at 07:15"
description: "Automatically control Living Room Light based on usage pattern"
trigger:
  - platform: time
    at: "07:15:00"
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
```

RATIONALE: [1-2 sentence explanation mentioning "Living Room Light" by name]
CATEGORY: [energy|comfort|security|convenience]
PRIORITY: [high|medium|low]
```

**Prompt Engineering Techniques:**
- ✅ **Structured format**: Clear sections (PATTERN, INSTRUCTIONS, OUTPUT)
- ✅ **Example output**: Shows exactly what we want
- ✅ **Specific constraints**: Device name vs entity ID, 1-2 sentences
- ✅ **Friendly names**: "Living Room Light" not "light.living_room"
- ✅ **Confidence indicator**: Shows pattern strength

---

##### 2. Co-Occurrence Pattern Template

**When Used:** Two devices consistently activate together

**Example Pattern:**
```python
{
    'pattern_type': 'co_occurrence',
    'device1': 'light.kitchen',
    'device2': 'media_player.kitchen_speaker',
    'occurrences': 18,
    'confidence': 0.75,
    'metadata': {
        'avg_time_delta_seconds': 45
    }
}
```

**Generated Prompt:**

```
Create a Home Assistant automation for this device co-occurrence pattern:

PATTERN DETECTED:
- Trigger Device: Kitchen Light (entity: light.kitchen, type: light)
- Response Device: Kitchen Speaker (entity: media_player.kitchen_speaker, type: media_player)
- Co-occurrences: 18 times in last 30 days
- Confidence: 75%
- Average time between events: 45.0 seconds

USER BEHAVIOR INSIGHT:
When the user activates "Kitchen Light", they typically also activate "Kitchen Speaker" about 45 seconds later.

INSTRUCTIONS:
1. Create a valid Home Assistant automation in YAML format
2. Use light.kitchen state change as trigger
3. media_player.kitchen_speaker should be activated after approximately 45 seconds
4. Use descriptive alias starting with "AI Suggested: " and include BOTH DEVICE NAMES (Kitchen Light and Kitchen Speaker), NOT entity IDs
5. Provide rationale explaining the pattern using the device names
6. Categorize and prioritize appropriately

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: Turn On Kitchen Speaker When Kitchen Light Activates"
description: "Automatically activate Kitchen Speaker when Kitchen Light is turned on"
trigger:
  - platform: state
    entity_id: light.kitchen
    to: 'on'
action:
  - delay: '00:00:45'
  - service: media_player.turn_on
    target:
      entity_id: media_player.kitchen_speaker
```

RATIONALE: [Explanation based on co-occurrence pattern, mentioning "Kitchen Light" and "Kitchen Speaker" by their friendly names]
CATEGORY: [energy|comfort|security|convenience]
PRIORITY: [high|medium|low]
```

**Unique Features:**
- ✅ **Two-device relationship**: Clear trigger → response
- ✅ **Timing information**: Includes delay between actions
- ✅ **Behavioral insight**: Explains "why" user does this
- ✅ **Context-aware**: Adjusts delay based on actual patterns

---

##### 3. Anomaly Pattern Template

**When Used:** Unusual activity detected (future feature)

**Example Pattern:**
```python
{
    'pattern_type': 'anomaly',
    'device_id': 'binary_sensor.garage_door',
    'metadata': {
        'anomaly_score': 0.92
    }
}
```

**Generated Prompt:**

```
Create a Home Assistant notification automation for this anomaly:

ANOMALY DETECTED:
- Device: binary_sensor.garage_door
- Anomaly Score: 0.92
- Pattern: Unusual activity detected (outside normal usage patterns)

INSTRUCTIONS:
Create a notification automation that alerts the user when unusual behavior is detected.

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: Garage Door Anomaly Alert"
description: "Notify when unusual activity detected"
trigger:
  - platform: state
    entity_id: binary_sensor.garage_door
condition:
  - condition: time
    after: "22:00:00"
    before: "06:00:00"
action:
  - service: notify.persistent_notification
    data:
      title: "Unusual Activity Detected"
      message: "{{ trigger.to_state.name }} activated at unusual time"
```

RATIONALE: [Explanation about anomaly detection]
CATEGORY: security
PRIORITY: [high|medium|low]
```

**Security Focus:**
- ✅ **Notification-based**: Alerts user instead of acting
- ✅ **Time-based condition**: Only during unusual hours
- ✅ **Always security category**: Anomalies are security concerns

---

#### Example: Complete API Call Trace

Let's trace a real OpenAI API call from pattern to suggestion:

**Input Pattern:**
```python
pattern = {
    'pattern_type': 'time_of_day',
    'device_id': 'light.living_room',
    'hour': 7,
    'minute': 15,
    'occurrences': 26,
    'confidence': 0.87,
    'device_name': 'Living Room Light'
}
```

**Step 1: Build Prompt**
```python
prompt = _build_time_of_day_prompt(pattern, device_context)
# Returns ~250-word structured prompt (see template above)
```

**Step 2: OpenAI API Request**
```python
request = {
    "model": "gpt-4o-mini",
    "messages": [
        {
            "role": "system",
            "content": "You are a home automation expert creating Home Assistant automations..."
        },
        {
            "role": "user",
            "content": "[250-word structured prompt]"
        }
    ],
    "temperature": 0.7,
    "max_tokens": 600
}

# POST https://api.openai.com/v1/chat/completions
```

**Step 3: OpenAI API Response**
```python
response = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1729166400,
    "model": "gpt-4o-mini-2024-07-18",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": """```yaml
alias: "AI Suggested: Living Room Light at 07:15"
description: "Automatically turn on Living Room Light at 7:15 AM on weekdays"
trigger:
  - platform: time
    at: "07:15:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 80
mode: single
```

RATIONALE: Based on 26 consistent activations at 7:15 AM over the past 30 days (87% confidence), this automation will automatically turn on the Living Room Light during your weekday morning routine, providing convenient hands-free lighting at your preferred time.

CATEGORY: convenience
PRIORITY: medium"""
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 287,
        "completion_tokens": 156,
        "total_tokens": 443
    }
}
```

**Step 4: Parse Response**
```python
content = response.choices[0].message.content

suggestion = AutomationSuggestion(
    alias="AI Suggested: Living Room Light at 07:15",
    description="Automatically turn on Living Room Light at 7:15 AM on weekdays",
    automation_yaml="""alias: "AI Suggested: Living Room Light at 07:15"
description: "Automatically turn on Living Room Light at 7:15 AM on weekdays"
trigger:
  - platform: time
    at: "07:15:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 80
mode: single""",
    rationale="Based on 26 consistent activations at 7:15 AM over the past 30 days (87% confidence), this automation will automatically turn on the Living Room Light during your weekday morning routine, providing convenient hands-free lighting at your preferred time.",
    category="convenience",
    priority="medium",
    confidence=0.87
)
```

**Step 5: Token Usage Tracking**
```python
# Track for cost calculation
total_input_tokens += 287      # Prompt
total_output_tokens += 156     # Response
total_tokens_used += 443       # Total

# Cost calculation (GPT-4o-mini pricing)
cost = (287 * $0.00000015) + (156 * $0.00000060)
     = $0.000043 + $0.000094
     = $0.000137 per suggestion
```

---

#### Response Parsing - Extracting Structured Data

**Regex-Based Extraction:**

The system uses regex patterns to extract specific fields from the LLM's free-form response:

```python
def _extract_alias(text: str) -> str:
    # Extract: alias: "Living Room Light at 07:15"
    match = re.search(r'alias:\s*["\']?([^"\'\n]+)["\']?', text)
    return match.group(1).strip()  # "AI Suggested: Living Room Light at 07:15"

def _extract_yaml(text: str) -> str:
    # Extract YAML code block
    match = re.search(r'```(?:yaml)?\n(.*?)\n```', text, re.DOTALL)
    return match.group(1).strip()  # Full YAML content

def _extract_rationale(text: str) -> str:
    # Extract: RATIONALE: [text until CATEGORY:]
    match = re.search(r'RATIONALE:\s*(.+?)(?:CATEGORY:|PRIORITY:|$)', text, re.DOTALL)
    return match.group(1).strip()

def _extract_category(text: str) -> str:
    # Extract: CATEGORY: convenience
    match = re.search(r'CATEGORY:\s*(\w+)', text)
    category = match.group(1).lower()
    # Validate: must be one of [energy, comfort, security, convenience]
    return category if category in VALID_CATEGORIES else "convenience"

def _extract_priority(text: str) -> str:
    # Extract: PRIORITY: medium
    match = re.search(r'PRIORITY:\s*(\w+)', text)
    priority = match.group(1).lower()
    # Validate: must be one of [high, medium, low]
    return priority if priority in VALID_PRIORITIES else "medium"
```

**Fallback Strategies:**

If extraction fails, the system has intelligent fallbacks:

```python
# If YAML extraction fails, generate basic YAML
yaml_content = extract_yaml(response) or generate_fallback_yaml(pattern)

# If category extraction fails, infer from device type
category = extract_category(response) or infer_category(pattern)
# Inference: light → convenience, alarm → security, climate → comfort

# If priority fails, default to medium
priority = extract_priority(response) or "medium"
```

---

#### Token Usage & Cost Analysis

**Typical API Call:**

| Component | Tokens | Cost (GPT-4o-mini) |
|-----------|--------|-------------------|
| System prompt | ~50 | $0.0000075 |
| User prompt (time-of-day) | ~237 | $0.0000356 |
| **Total Input** | **287** | **$0.0000431** |
| | | |
| YAML response | ~120 | $0.0000720 |
| Rationale | ~30 | $0.0000180 |
| Metadata | ~6 | $0.0000036 |
| **Total Output** | **156** | **$0.0000936** |
| | | |
| **Grand Total** | **443** | **$0.0001367** |

**Daily Run (10 suggestions):**
- Total tokens: ~4,430
- Total cost: ~$0.00137
- Monthly cost: ~$0.041 (~$0.50/year)

**Scaling:**
- 100 suggestions/day: ~$1.37/day = $41/month
- 1000 suggestions/day: ~$13.70/day = $411/month

**Why GPT-4o-mini is Perfect:**
- **80% cheaper than GPT-4**: (~$0.0001367 vs ~$0.0007)
- **Sufficient quality**: YAML generation doesn't need GPT-4
- **Fast**: Lower latency for batch processing
- **Scalable**: Cost-effective even at high volume

---

#### Error Handling & Retry Logic

**3-Attempt Retry Strategy:**

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
async def generate_automation_suggestion(pattern):
    # API call here
```

**Retry Behavior:**
1. **Attempt 1**: Immediate
2. **Attempt 2**: Wait 2 seconds
3. **Attempt 3**: Wait 4 seconds
4. **Failure**: Raise exception, log error

**Common Errors:**

1. **Rate Limit (429)**
   - Wait and retry (exponential backoff)
   - Typically resolves on retry

2. **Timeout**
   - Network issue or OpenAI overload
   - Retry with fresh connection

3. **Invalid API Key (401)**
   - Configuration error
   - No retry (will fail immediately)

4. **Invalid Response**
   - LLM generated invalid JSON/YAML
   - Fallback YAML generation kicks in

**Logging:**
```python
logger.info(f"Generating suggestion for time_of_day pattern: light.living_room")
# ✅ OpenAI API call successful: 443 tokens (input: 287, output: 156)
# ✅ Generated suggestion: AI Suggested: Living Room Light at 07:15
```

---

#### Token Usage Dashboard

**Real-time Tracking:**

```python
class OpenAIClient:
    def __init__(self):
        self.total_tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    async def generate_automation_suggestion(self, pattern):
        response = await self.client.chat.completions.create(...)
        
        # Accumulate usage
        usage = response.usage
        self.total_input_tokens += usage.prompt_tokens
        self.total_output_tokens += usage.completion_tokens
        self.total_tokens_used += usage.total_tokens
        
        # Log per-call usage
        logger.info(
            f"✅ OpenAI API call: {usage.total_tokens} tokens "
            f"(input: {usage.prompt_tokens}, output: {usage.completion_tokens})"
        )
    
    def get_usage_stats(self):
        cost = (
            (self.total_input_tokens * 0.00000015) +
            (self.total_output_tokens * 0.00000060)
        )
        
        return {
            'total_tokens': self.total_tokens_used,
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens,
            'estimated_cost_usd': round(cost, 6),
            'model': 'gpt-4o-mini'
        }
```

**End-of-Run Report:**

```python
# After Phase 5 completes
stats = openai_client.get_usage_stats()

logger.info(f"  → OpenAI tokens: {stats['total_tokens']}")
logger.info(f"  → OpenAI cost: ${stats['estimated_cost_usd']:.6f}")

# Example output:
#   → OpenAI tokens: 4,430
#   → OpenAI cost: $0.001370
```

---

#### Prompt Engineering Best Practices

**What Makes These Prompts Effective:**

1. **Structured Format**
   - Clear sections (PATTERN, INSTRUCTIONS, OUTPUT)
   - Easy for LLM to parse and follow

2. **Example-Driven**
   - Shows exact YAML format expected
   - Reduces ambiguity

3. **Specific Constraints**
   - "Use device name, not entity ID"
   - "1-2 sentences for rationale"
   - Clear output format

4. **Context-Rich**
   - Includes occurrences, confidence
   - Provides behavioral insight
   - Explains "why" pattern exists

5. **Validation Hints**
   - "Valid Home Assistant automation"
   - Lists valid categories/priorities
   - Specifies service call format

6. **Friendly Language**
   - "Living Room Light" not "light.living_room"
   - Makes suggestions more user-friendly
   - Easier to read and understand

**What NOT to Do:**

❌ Vague prompts: "Create an automation"  
❌ No examples: "Output YAML"  
❌ No constraints: LLM might hallucinate  
❌ Technical jargon: "entity_id light.living_room"  

---

#### Future Enhancements

**Potential Improvements:**

1. **Structured Output (JSON Mode)**
   - Use OpenAI's JSON mode for guaranteed valid responses
   - Eliminates regex parsing
   - More reliable extraction

2. **Function Calling**
   - Define automation schema as OpenAI function
   - LLM returns structured data directly
   - No parsing needed

3. **Few-Shot Learning**
   - Include 2-3 example automations in prompt
   - Improves output consistency
   - Reduces hallucinations

4. **Context Window Optimization**
   - Compress prompts further
   - Use prompt caching (OpenAI beta feature)
   - Reduce cost by 50%

5. **Multi-Model Support**
   - Fallback to GPT-3.5-turbo if 4o-mini fails
   - Local LLM option (Llama, Mistral) for privacy
   - Cost optimization strategies

6. **Batch API**
   - OpenAI Batch API (50% cheaper)
   - Process 10 suggestions in single request
   - Trade latency for cost

---

**Example Output:**
```python
{
    'type': 'pattern_automation',
    'source': 'Epic-AI-1',
    'title': 'Living Room Light Morning Routine',
    'description': 'Turn on living room lights at 7:15 AM based on weekday pattern',
    'automation_yaml': '...',  # Valid HA YAML
    'confidence': 0.87,
    'category': 'convenience',
    'priority': 'medium',
    'rationale': 'Detected consistent morning pattern...'
}
```

---

## Phase 6: Publish Notification & Results

**Purpose:** Notify Home Assistant via MQTT of analysis completion  
**Protocol:** MQTT publish to `ha-ai/analysis/complete`

### Call Tree

```
run_daily_analysis() [line 395]
├── Build notification payload [line 398]
│   ├── timestamp
│   ├── epic_ai_1: {patterns_detected, pattern_suggestions}
│   ├── epic_ai_2: {devices_checked, capabilities_updated, opportunities_found, feature_suggestions}
│   ├── combined: {suggestions_generated, events_analyzed}
│   ├── duration_seconds
│   └── success: true
│
└── mqtt_client.publish_analysis_complete(notification) [line 419]
    ├── clients/mqtt_client.py:MQTTNotificationClient
    ├── Topic: ha-ai/analysis/complete
    ├── QoS: 1 (at least once delivery)
    └── Payload: JSON notification
```

**Key Files:**
- `clients/mqtt_client.py` - MQTT publishing client

**MQTT Configuration:**
- Broker: `settings.mqtt_broker` (192.168.1.86)
- Port: `settings.mqtt_port` (1883)
- Topic: `ha-ai/analysis/complete`

**Home Assistant Integration:**
- Home Assistant can subscribe to this topic
- Triggers notification to user
- Updates AI dashboard widgets

---

## Completion & Cleanup

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

## Manual Trigger Path (Alternative Entry)

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

---

## Error Handling & Recovery

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

## Database Schema Impact

### Tables Modified

**1. device_capabilities** (Phase 1)
```sql
INSERT INTO device_capabilities (
    device_id, feature_name, feature_type,
    capability_data, discovered_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(device_id, feature_name) DO UPDATE...
```

**2. patterns** (Phase 3)
```sql
INSERT INTO patterns (
    pattern_type, device_id, metadata,
    confidence, occurrences, created_at
) VALUES (?, ?, ?, ?, ?, ?)
```

**3. suggestions** (Phase 5)
```sql
INSERT INTO suggestions (
    pattern_id, title, description,
    automation_yaml, confidence, category,
    priority, status, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
```

**4. job_history** (In-memory, not persisted)
- Last 30 job runs stored in `DailyAnalysisScheduler._job_history`
- Accessible via `/api/analysis/schedule` endpoint

---

## Performance Characteristics

### Typical Execution Time

| Phase | Duration | Bottleneck |
|-------|----------|-----------|
| Phase 1: Device Capabilities | 10-30s | MQTT request/response |
| Phase 2: Fetch Events | 5-15s | InfluxDB query (100K events) |
| Phase 3: Pattern Detection | 15-45s | Co-occurrence algorithm (O(n²)) |
| Phase 4: Feature Analysis | 10-20s | InfluxDB usage queries |
| Phase 5: Suggestion Generation | 30-120s | OpenAI API calls (10 requests) |
| Phase 6: Publish Notification | <1s | MQTT publish |
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

## Monitoring & Observability

### Logging

All phases log to structured logger:
```python
logger.info("✅ Phase X complete: {metrics}")
logger.error("❌ Phase X failed: {error}")
logger.warning("⚠️ Phase X degraded: {warning}")
```

**Log Destination:** `shared.logging_config.setup_logging("ai-automation-service")`

### Metrics Published

Via MQTT notification:
- Events analyzed count
- Patterns detected count
- Suggestions generated count
- Duration (seconds)
- OpenAI token usage
- OpenAI cost (USD)
- Success/failure status

### API Endpoints for Monitoring

1. **`GET /api/analysis/status`** - Current status and last run
2. **`GET /api/analysis/schedule`** - Next run time and recent jobs
3. **`GET /health`** - Service health check

---

## Configuration

### Environment Variables

**File:** `infrastructure/env.ai-automation`

```bash
# Scheduling
ANALYSIS_SCHEDULE="0 3 * * *"  # 3 AM daily (cron format)

# Data API
DATA_API_URL=http://data-api:8006

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=ha-ingestor-token
INFLUXDB_ORG=ha-ingestor
INFLUXDB_BUCKET=home_assistant_events

# Home Assistant
HA_URL=http://192.168.1.86:8123
HA_TOKEN=<long-lived-token>

# MQTT
MQTT_BROKER=192.168.1.86
MQTT_PORT=1883
MQTT_USERNAME=<optional>
MQTT_PASSWORD=<optional>

# OpenAI
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=sqlite+aiosqlite:///data/ai_automation.db
```

### Tunable Parameters

**Pattern Detection:**
- `min_occurrences = 5` - Minimum pattern frequency
- `min_confidence = 0.7` - Minimum pattern confidence
- `window_minutes = 5` - Co-occurrence time window

**Suggestion Generation:**
- `max_suggestions = 10` - Maximum suggestions per run
- `temperature = 0.7` - OpenAI creativity level
- `max_tokens = 600` - Maximum OpenAI response length

**Data Fetching:**
- `days = 30` - Historical data window
- `limit = 100000` - Maximum events to analyze

---

## Dependencies

### External Services

1. **Data API** (http://data-api:8006)
   - `/api/devices` - Device metadata
   - `/api/events` - Historical events (fallback)

2. **InfluxDB** (http://influxdb:8086)
   - Direct queries for event data
   - Flux query language

3. **Home Assistant** (http://192.168.1.86:8123)
   - Device/entity metadata
   - Automation deployment

4. **MQTT Broker** (192.168.1.86:1883)
   - Zigbee2MQTT capability discovery
   - Analysis completion notifications

5. **OpenAI API** (https://api.openai.com)
   - GPT-4o-mini for suggestion generation
   - Rate limits: 10,000 RPM, 2M TPM

### Python Libraries

**Core:**
- `fastapi` - Web framework
- `apscheduler` - Job scheduling
- `asyncio` - Async orchestration

**Data Processing:**
- `pandas` - Event data manipulation
- `numpy` - Pattern detection algorithms

**Clients:**
- `httpx` - Async HTTP client
- `influxdb-client` - InfluxDB queries
- `paho-mqtt` - MQTT communication
- `openai` - OpenAI API

**Database:**
- `sqlalchemy` - ORM
- `aiosqlite` - Async SQLite driver
- `alembic` - Database migrations

---

## Testing & Debugging

### Manual Trigger

```bash
# Trigger analysis manually (don't wait for 3 AM)
curl -X POST http://localhost:8018/api/analysis/trigger
```

### Check Next Run

```bash
# Get scheduler status
curl http://localhost:8018/api/analysis/schedule
```

### View Recent Jobs

```bash
# Get job history (last 5 runs)
curl http://localhost:8018/api/analysis/schedule
```

### Test Individual Phases

**Option 1:** Use `/api/analysis/analyze-and-suggest` endpoint  
**Option 2:** Python REPL with service imports  
**Option 3:** Unit tests in `tests/` directory

---

## Future Enhancements

### Potential Optimizations

1. **Parallel OpenAI Requests**
   - Use `asyncio.gather()` for simultaneous suggestion generation
   - Could reduce Phase 5 time by 70-80%

2. **Incremental Event Fetching**
   - Only fetch events since last run (daily delta)
   - Could reduce Phase 2 time by 90%

3. **Pattern Caching**
   - Reuse stable patterns across runs
   - Only re-analyze changed devices

4. **Adaptive Scheduling**
   - Run more frequently during high-activity periods
   - Skip runs if no new data

### Planned Features

- **Multi-model Support:** Fallback to local LLM if OpenAI unavailable
- **User Feedback Loop:** Learn from accepted/rejected suggestions
- **Advanced Patterns:** Seasonal, contextual, multi-device orchestrations
- **Real-time Mode:** Continuous analysis (not just 3 AM batch)

---

## Summary

### Key Metrics (Typical Run)

- **Duration:** 2-4 minutes
- **Events Analyzed:** 50,000-100,000
- **Patterns Detected:** 10-50
- **Suggestions Generated:** 10 (top confidence)
- **OpenAI Cost:** $0.003-0.005 per run (~$1.50/month)
- **Database Growth:** ~10KB per run

### Success Criteria

✅ All 6 phases complete successfully  
✅ At least 1 suggestion generated  
✅ MQTT notification published  
✅ Job history recorded  
✅ Next run scheduled  

### Failure Recovery

- Phases gracefully degrade on individual failures
- Job completes even if some phases fail
- Manual re-run available via API
- Missed runs auto-recover on next schedule

---

**Document Version:** 1.1  
**Last Updated:** October 17, 2025  
**Subsystem:** ai-automation-service  
**Epic:** AI-1 (Pattern Detection) + AI-2 (Device Intelligence)  
**Stories:** AI2.5 (Unified Daily Batch Job) + AI1.23 (Conversational Suggestion Refinement)

**Changelog:**
- **v1.1 (Oct 17, 2025)**: Updated for Story AI1.23 - Conversational Suggestion Refinement
  - Added new database fields: `description_only`, `conversation_history`, `refinement_count`, `yaml_generated_at`, `approved_at`
  - Updated status lifecycle to support dual flows (legacy + conversational)
  - Clarified `automation_yaml` is nullable until user approval
- **v1.0 (Initial)**: Complete call tree for unified daily batch job (Epic AI-1 + AI-2)

