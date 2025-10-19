# Phase 1: Device Capability Discovery
## Epic AI-2 - Device Intelligence

**Story:** AI2.1 - MQTT Capability Listener & Universal Parser  
**Duration:** 10-30 seconds  
**Database:** SQLite (`device_capabilities` table)  
**Last Updated:** October 17, 2025  
**Last Validated:** October 19, 2025 ✅

**🔗 Navigation:**
- [← Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [← Previous: Main Execution Flow](AI_AUTOMATION_MAIN_FLOW.md)
- [→ Next: Phase 2 - Historical Event Fetching](AI_AUTOMATION_PHASE2_EVENTS.md)

---

## 📋 Overview

**Purpose:** Discover and update device capabilities from Home Assistant/Zigbee2MQTT

Phase 1 discovers what your smart home devices can do by:
1. Fetching device list from Home Assistant
2. Querying Zigbee2MQTT bridge for device definitions
3. Parsing the standardized "exposes" format
4. Storing capabilities in SQLite database for AI analysis
5. Automatically detecting underutilized features

---

## 🔄 Call Tree

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

## 🔬 Deep Dive: Understanding Device Capability Discovery

### What Problem Does This Solve?

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

---

### Example: Inovelli VZM31-SN Smart Switch

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

---

### Universal Parser: Why It Works for All Manufacturers

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

---

### Complexity Assessment

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

---

### Name Normalization

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

---

### Caching Strategy

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

---

### Performance Characteristics

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

---

### Error Handling

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

## 📊 Phase 1 Output

**Returns:**
```python
{
    'devices_checked': 20,
    'capabilities_updated': 10,
    'new_devices': 2,
    'errors': 0
}
```

**Database Updates:**
- 10 records updated in `device_capabilities` table
- 2 new device capability records created
- Raw MQTT exposes preserved for debugging

---

## 🔗 Related Documentation

- [← Main Execution Flow](AI_AUTOMATION_MAIN_FLOW.md)
- [→ Phase 2: Historical Event Fetching](AI_AUTOMATION_PHASE2_EVENTS.md)
- [Phase 4: Feature Analysis](AI_AUTOMATION_PHASE4_FEATURES.md) - Uses capabilities from this phase
- [Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Epic:** AI-2 - Device Intelligence

