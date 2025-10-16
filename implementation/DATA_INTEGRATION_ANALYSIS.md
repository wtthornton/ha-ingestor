# Data Integration Analysis: InfluxDB + SQLite in Feature Suggestions

**Date:** 2025-10-16  
**Epic:** AI-2 Device Intelligence  
**Context:** Ensuring feature suggestions use ALL available data sources

---

## Current Data Sources

### 1. SQLite (via data-api)
**Endpoint:** `GET /api/devices` and `GET /api/devices/{device_id}`

**Returns:**
- ✅ Device metadata: `device_id`, `name`, `manufacturer`, `model`
- ✅ Area/room information: `area_id`
- ✅ Entity count: Number of entities per device
- ✅ Software version: `sw_version`
- ✅ Last seen: `timestamp`

**Usage in Feature Detection:**
- Device matching (Story 2.3): Match HA device → Capability DB by manufacturer+model
- Device metadata for display in suggestions

---

### 2. InfluxDB (via InfluxDBEventClient)
**Client:** `services/ai-automation-service/src/clients/influxdb_client.py`

**Can Query:**
- ✅ Historical state changes (last 30 days)
- ✅ Entity ID and domain (`light.`, `switch.`, etc.)
- ✅ State values (`on`, `off`, brightness values, etc.)
- ✅ Timestamps for pattern analysis
- ✅ Device IDs (from event tags)

**Query Method:**
```python
df = await influxdb_client.fetch_events(
    start_time=datetime.now() - timedelta(days=30),
    entity_id="light.kitchen_switch"
)
# Returns: DataFrame with _time, entity_id, state, domain
```

---

### 3. Device Capability Database (SQLite)
**Table:** `device_capabilities` (Story 2.2)

**Contains:**
- ✅ Manufacturer + Model → Capabilities mapping
- ✅ Feature list with types, complexity, descriptions
- ✅ Populated by MQTT listener from Zigbee2MQTT

---

## Current Feature Detection (Story 2.3)

### ✅ What's Working

**`FeatureAnalyzer._get_configured_features()` (Simplified):**
```python
# CURRENTLY: Basic entity type detection
if entity_id.startswith('light.'):
    configured.append('light_control')
```

**Analysis Flow:**
1. Get device metadata from data-api (SQLite) ✅
2. Get capabilities from capability DB (SQLite) ✅
3. Compare to detect unused features ✅

---

### ⚠️ What's Missing: InfluxDB Historical Analysis

**Current Issue:**
`FeatureAnalyzer` accepts `influxdb_client` parameter but **doesn't use it yet**.

**What Should Be Enhanced:**

```python
async def _get_configured_features(self, device_id: str, device: Dict) -> List[str]:
    """
    CURRENT: Check entity type → assume basic features
    
    SHOULD DO:
    1. Query InfluxDB for entity attribute changes
    2. Check if advanced attributes have been set:
       - led_effect → LED notifications used
       - smartBulbMode → Smart bulb mode configured
       - fan_mode → Fan control used
       - preset_mode → Climate presets configured
    3. Analyze historical usage patterns:
       - Has brightness been adjusted? → dimming used
       - Has color_temp been changed? → color control used
    """
    configured = []
    
    # ENHANCEMENT NEEDED:
    # Query InfluxDB for attribute changes in last 30 days
    events_df = await self.influxdb.fetch_events(
        entity_id=device_id,
        start_time=datetime.now() - timedelta(days=30)
    )
    
    # Analyze what attributes have been used
    if 'brightness' in events_df.columns and events_df['brightness'].notna().any():
        configured.append('dimming')
    
    if 'color_temp' in events_df.columns:
        configured.append('color_temperature')
    
    return configured
```

---

## Data-API Enhancement Needed

### Issue: InfluxDB Only Queries `state` Field

**Current Query (influxdb_client.py:79):**
```flux
from(bucket: "home_assistant_events")
  |> filter(fn: (r) => r["_field"] == "state")  // ❌ Only gets state!
  |> filter(fn: (r) => r["event_type"] == "state_changed")
```

**Should Also Query Attributes:**
```flux
from(bucket: "home_assistant_events")
  |> filter(fn: (r) => r["_field"] == "state" or contains(value: r["_field"], set: ["brightness", "color_temp", "led_effect"]))
```

---

## Recommendations for Story 2.4+

### Priority 1: Add Attribute Query to InfluxDBEventClient

**File:** `services/ai-automation-service/src/clients/influxdb_client.py`

**Add Method:**
```python
async def fetch_entity_attributes(
    self,
    entity_id: str,
    attributes: List[str],
    start_time: Optional[datetime] = None
) -> Dict[str, bool]:
    """
    Check which attributes have been set/changed for an entity.
    
    Returns:
        {"brightness": True, "color_temp": False, "led_effect": True}
    """
    # Query InfluxDB for each attribute field
    # Return True if any non-null values found in time range
```

### Priority 2: Enhance FeatureAnalyzer to Use Historical Data

**File:** `services/ai-automation-service/src/device_intelligence/feature_analyzer.py`

**Update `_get_configured_features()`:**
1. Query InfluxDB for entity attribute history
2. Mark features as "configured" if:
   - Attribute has been written in last 30 days
   - Attribute has non-default value
   - Attribute is present in automations/scripts

### Priority 3: Combine Data Sources in Suggestion Prompt

**File:** `services/ai-automation-service/src/device_intelligence/feature_suggestion_generator.py`

**Enhance Prompt:**
```python
PROMPT:
Device: Kitchen Switch (Inovelli VZM31-SN)
Usage Data (Last 30 days):
  - Total state changes: 145 (from InfluxDB)
  - Brightness adjusted: 23 times (from InfluxDB attributes)
  - Color temp changed: 0 times (from InfluxDB attributes)
  
Unused Features (from Capability DB):
  - LED notifications (never configured)
  - Smart bulb mode (never configured)
  - Double-tap actions (never configured)
```

---

## Current Status: Story 2.4

### ✅ What's Complete
- SQLite device metadata integration
- Device capability database
- Basic feature detection (entity type)
- LLM suggestion generation

### ⚠️ What's Missing
- InfluxDB historical analysis for feature usage
- Entity attribute querying from InfluxDB
- Advanced feature detection (beyond entity type)

### 📊 Data Coverage
| Data Source | Integrated | Used in Suggestions |
|-------------|-----------|---------------------|
| SQLite device metadata | ✅ Yes | ✅ Yes |
| Device capabilities (Zigbee2MQTT) | ✅ Yes | ✅ Yes |
| InfluxDB state changes | ⚠️ Partial | ❌ No |
| InfluxDB attributes | ❌ No | ❌ No |
| HA automations/scripts | ❌ No | ❌ No |

---

## Recommendation

**For Story 2.4 (Current):**
- ✅ Ship with current implementation (SQLite + Capability DB)
- ✅ Add TODO comments for InfluxDB enhancement
- ✅ Document limitation in story completion

**For Story 2.5 (Future Enhancement):**
- Add InfluxDB attribute querying
- Enhance feature detection with historical analysis
- Create "Usage Insights" alongside suggestions:
  - "Your kitchen switch has been turned on 145 times in the last month"
  - "Brightness was adjusted 23 times, but color temperature was never changed"

---

## Conclusion

**Answer to User Question:** 
> "I want to make sure the suggestion engine is combining all data from Influx and SQLite."

**Current Status:**
- ✅ **SQLite metadata**: Fully integrated
- ✅ **Capability database**: Fully integrated
- ⚠️ **InfluxDB state data**: Partially available but not used in feature detection
- ❌ **InfluxDB attributes**: Not queried yet

**Impact:**
- Feature suggestions work with device metadata + capabilities
- BUT: Not yet enhanced with historical usage patterns
- Suggestions are based on "what device CAN do" vs. "what user HAS done"

**Next Step:**
- Complete Story 2.4 with current implementation
- Create Story 2.5 for InfluxDB enhancement
- Add usage insights to make suggestions more intelligent

