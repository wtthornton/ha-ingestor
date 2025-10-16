# Epic AI-1 vs. AI-2: What's Built vs. What's Enhanced

**Date:** 2025-10-16  
**Purpose:** Summary of existing ML/Pattern Automation vs. new Device Intelligence features

---

## 🤖 Epic AI-1: Pattern Automation (EXISTING)

### What It Does: **"Watch how you USE devices, suggest automations"**

Analyzes **historical usage patterns** from InfluxDB to create automation suggestions.

---

### Pattern Detection Capabilities (Stories 1.4-1.6)

#### ✅ 1. **Time-of-Day Clustering** (Story 1.4)
**Detects:** Devices used at consistent times

**Algorithm:** KMeans clustering on timestamp features

**Examples:**
```
Pattern Detected:
- light.living_room turns on at 18:30 (95% of days)
→ Suggests: "Turn on living room light at 6:30 PM"

- climate.bedroom sets to 68°F at 22:00 (85% of days)  
→ Suggests: "Set bedroom temperature to 68°F at 10 PM"
```

**Time Scales:**
- ✅ **Daily patterns:** Detects consistent times across days (18:30, 22:00, etc.)
- ⚠️ **Weekly patterns:** NOT YET (would need day-of-week clustering)
- ❌ **Monthly patterns:** NOT IMPLEMENTED
- ❌ **Seasonal patterns:** NOT IMPLEMENTED (future Phase 3+)

---

#### ✅ 2. **Device Co-Occurrence** (Story 1.5)
**Detects:** Devices frequently used together (within 5-minute window)

**Algorithm:** Frequent pattern mining (similar to market basket analysis)

**Examples:**
```
Pattern Detected:
- light.kitchen turns on → light.dining_room turns on (within 2 min)
- Happens 12 times in last 30 days (80% co-occurrence rate)
→ Suggests: "When kitchen light turns on, turn on dining light after 2 minutes"

- switch.coffee_maker turns on → light.kitchen turns on (within 1 min)
→ Suggests: "Turn on kitchen light when coffee maker starts"
```

**Time Scales:**
- ✅ **Daily co-occurrence:** Yes (within 5-minute window)
- ⚠️ **Weekly co-occurrence:** Partial (if pattern repeats weekly)
- ❌ **Seasonal co-occurrence:** NOT IMPLEMENTED

---

#### ✅ 3. **Anomaly Detection** (Story 1.6)
**Detects:** Unusual manual interventions that could be automated

**Algorithm:** Statistical outlier detection (zscore, isolation forest)

**Examples:**
```
Anomaly Detected:
- User manually turns on porch light between 22:00-23:00 on 8 nights
- Outside normal pattern (usually turns on at 19:00)
→ Suggests: "Turn on porch light at 10 PM (late-night arrivals pattern)"

- Heater turned on manually 5 times when temp drops below 60°F
→ Suggests: "Turn on heater when temperature drops below 60°F"
```

**Time Scales:**
- ✅ **Daily anomalies:** Yes (unusual times)
- ⚠️ **Weekly anomalies:** Partial (repeated patterns)
- ❌ **Seasonal anomalies:** NOT IMPLEMENTED

---

### LLM Integration (Stories 1.7-1.8)

#### ✅ OpenAI GPT-4o-mini
**What It Does:**
- Takes detected patterns → Generates natural language suggestions
- Creates valid Home Assistant YAML automations
- Explains rationale for each suggestion
- Categories: energy, comfort, security, convenience
- Priorities: high, medium, low

**Example Flow:**
```
1. Pattern Detected: light.bedroom_lamp at 22:30 (90% confidence)
2. LLM Prompt: "User turns on bedroom lamp at 10:30 PM consistently..."
3. LLM Output:
   alias: "AI Suggested: Bedtime Lighting"
   description: "Turn on bedroom lamp at 10:30 PM"
   trigger:
     - platform: time
       at: "22:30:00"
   action:
     - service: light.turn_on
       target:
         entity_id: light.bedroom_lamp
```

---

### Scheduling (Story 1.9)

#### ✅ Daily Batch Analysis
**When:** 3 AM daily (APScheduler)
**Process:**
1. Query last 30 days from InfluxDB
2. Run pattern detection (5-10 minutes)
3. Generate 5-10 suggestions via LLM
4. Store in SQLite
5. User wakes up to new suggestions

**What Gets Analyzed:**
- ✅ Last 30 days of event data
- ✅ All devices with sufficient activity (5+ events)
- ⚠️ NOT analyzing longer time windows yet

---

### Dashboard (Stories 1.13-1.17)

#### ✅ AI Automation Tabs
1. **Suggestions Tab:** View/approve/reject automation suggestions
2. **Patterns Tab:** Visualize detected patterns (time-of-day, co-occurrence, anomalies)
3. **Current Automations Tab:** See existing HA automations
4. **Insights Dashboard:** Pattern statistics and trends

---

## 🧠 Epic AI-2: Device Intelligence (NEW - Stories 2.1-2.9)

### What It Does: **"Discover what devices CAN do, suggest unused features"**

Analyzes **device capabilities** to find features the user doesn't know about or hasn't configured.

---

### Key Differences from Epic AI-1

| Aspect | Epic AI-1 (Pattern) | Epic AI-2 (Device Intelligence) |
|--------|-------------------|--------------------------------|
| **Data Source** | InfluxDB (historical usage) | Zigbee2MQTT + Device Registry |
| **Focus** | How you USE devices | What devices CAN do |
| **Detection** | Temporal patterns | Feature discovery |
| **Trigger** | Historical events | Device capabilities |
| **Suggestions** | Automation timing | Feature enablement |
| **Example** | "Turn on at 6:30 PM" | "Enable LED notifications" |

---

### Device Intelligence Components (Stories 2.1-2.4)

#### ✅ 1. **MQTT Capability Listener** (Story 2.1)
**What It Does:**
- Subscribes to `zigbee2mqtt/bridge/devices`
- Parses device `exposes` (capabilities)
- Universal parser for all manufacturers (Inovelli, Aqara, IKEA, Xiaomi, etc.)

**Example:**
```json
Device: Inovelli VZM31-SN (Blue Series Switch)
Capabilities Discovered:
- light_control (basic)
- led_notifications (advanced)
- smart_bulb_mode (advanced)
- double_tap_actions (advanced)
- power_monitoring (medium)
```

---

#### ✅ 2. **Capability Database** (Story 2.2)
**Tables:**
- `device_capabilities`: Manufacturer+Model → Feature list
- `device_feature_usage`: Device → Which features configured

**Example:**
```sql
SELECT * FROM device_capabilities WHERE model='VZM31-SN';
→ 15 features (light_control, led_notifications, smart_bulb_mode, ...)

SELECT * FROM device_feature_usage WHERE device_id='light.kitchen';
→ light_control: configured
→ led_notifications: NOT configured ❌
→ smart_bulb_mode: NOT configured ❌
```

---

#### ✅ 3. **Feature Analyzer** (Story 2.3)
**What It Does:**
- Matches HA devices to capability database
- Calculates **utilization score**: configured features / total features
- Identifies **unused features** (high impact + easy to configure)

**Example:**
```
Device: Kitchen Switch (Inovelli VZM31-SN)
Total Capabilities: 15
Configured Features: 3 (20% utilization)
Unused High-Impact Features:
  - LED notifications (high impact, medium complexity)
  - Power monitoring (medium impact, easy complexity)
  - Double-tap actions (medium impact, medium complexity)
```

---

#### ✅ 4. **Feature Suggestion Generator** (Story 2.4)
**What It Does:**
- Takes top unused features from analyzer
- Generates LLM-powered suggestions with configuration steps
- Prioritizes by impact + complexity

**Example Suggestion:**
```
Title: "Enable LED Notifications on Kitchen Switch"
Description: "Your Inovelli switch has a built-in LED bar that can 
             display status information! You can configure it to 
             show different colors based on your home's state - 
             like red when security is armed, or blue when it's 
             raining. Configure in Device Settings → Configure."
Type: feature_discovery
Category: security
Priority: high
Confidence: 0.85
```

---

### Dashboard (Stories 2.6-2.7)

#### ✅ Device Intelligence Tab (NEW)
1. **Utilization Score:** Overall % of features being used
2. **Utilization by Manufacturer:** Bar chart showing which brands underutilized
3. **Top 10 Unused Features:** Quick wins
4. **All Devices Table:** Sortable by utilization %
5. **Recent Configurations:** Timeline of enabled features

---

## 🔗 How Epic AI-1 and AI-2 Work Together (Story 2.5)

### Combined Suggestion Generation

#### **Scenario 1: Time-based Pattern + Unused Feature**
```
AI-1 Detects: Kitchen switch used at 18:30 daily
AI-2 Detects: Kitchen switch has unused LED notifications

Combined Suggestion:
"Turn on kitchen light at 6:30 PM AND set LED to green when light is on"
→ Combines timing automation + feature discovery
```

#### **Scenario 2: Co-occurrence + Power Monitoring**
```
AI-1 Detects: Coffee maker + kitchen light co-occur
AI-2 Detects: Coffee maker has unused power monitoring

Combined Suggestion:
"Turn on kitchen light when coffee maker starts, AND track daily energy usage"
→ Automation + energy awareness
```

---

## 📊 Time Scale Summary: What Gets Analyzed

### Epic AI-1 (Pattern Automation)

| Time Scale | Status | Stories | Example |
|-----------|--------|---------|---------|
| **Hourly** | ❌ No | - | - |
| **Daily** | ✅ YES | 1.4 | "Turn on at 6:30 PM daily" |
| **Weekly** | ⚠️ Partial | - | "Detect weekend vs. weekday patterns" (NOT YET) |
| **Monthly** | ❌ No | - | "First of month patterns" (NOT PLANNED) |
| **Seasonal** | ❌ No | Phase 3+ | "Winter heating patterns" (FUTURE) |
| **Window** | ✅ YES | 1.5 | "5-minute co-occurrence window" |

**Current Limitation:**
- **Analysis Window:** 30 days (rolling)
- **Pattern Frequency:** Daily batch (3 AM)
- **Weekly/Monthly:** Can detect if pattern repeats, but no explicit day-of-week or date-of-month modeling

---

### Epic AI-2 (Device Intelligence)

| Time Scale | Status | Stories | Example |
|-----------|--------|---------|---------|
| **Real-time** | ✅ YES | 2.1 | "MQTT listener discovers new device immediately" |
| **On-demand** | ✅ YES | 2.3 | "Analyze device utilization anytime" |
| **Historical** | ⚠️ Future | 2.5+ | "Track feature adoption over time" |

**No Time Dependency:** Device intelligence is **capability-based**, not time-based.

---

## 🎯 Overlap and Synergy

### What Both Epics Share

1. **LLM Integration:** Both use OpenAI GPT-4o-mini for suggestions
2. **SQLite Storage:** Both store results in ai_automation.db
3. **Health Dashboard:** Both integrate into same UI
4. **Confidence Scoring:** Both rank suggestions by confidence
5. **Category/Priority:** Both use energy/comfort/security/convenience

### What's Different

| Feature | Epic AI-1 | Epic AI-2 |
|---------|----------|----------|
| **Data Source** | InfluxDB events | Zigbee2MQTT capabilities |
| **Analysis Type** | Temporal patterns | Feature discovery |
| **Suggestion Type** | When to automate | What to configure |
| **User Value** | "Save time" | "Discover capabilities" |
| **ML Complexity** | KMeans, anomaly detection | Utilization calculation |
| **Update Frequency** | Daily (3 AM) | Real-time (MQTT) |

---

## 💡 User Experience: How They Work Together

### Week 1: User Installs System
1. **AI-2 (Device Intelligence):**
   - Discovers all device capabilities via MQTT
   - Shows: "You're using 25% of your devices' features"
   - Suggests: "Enable LED notifications on 3 switches"

2. **AI-1 (Pattern Automation):**
   - No suggestions yet (needs 30 days data)

### Week 2-4: Data Collection
1. **AI-1:** Starts detecting patterns
   - "You turn on bedroom light at 10:30 PM consistently"
   - Suggests: "Automate bedtime lighting"

### Month 2+: Full Power
1. **AI-1:** Refines patterns
   - "You turn on lights earlier on weekdays vs. weekends" (if weekly detection added)
   
2. **AI-2:** Tracks feature adoption
   - "You enabled LED notifications! You're now using 40% of features"

3. **Combined (Story 2.5):**
   - "You automate your bedroom lamp at 10:30 PM. Want to add LED notification to show security status?"

---

## 🚀 What's NOT Built Yet

### Epic AI-1 Gaps
- ❌ **Weekly patterns:** Day-of-week clustering
- ❌ **Monthly patterns:** Date-of-month patterns
- ❌ **Seasonal patterns:** Winter/summer adjustments (Phase 3+)
- ❌ **Long-term trends:** 6+ month analysis
- ❌ **Weather correlation:** "Turn on heater when temp drops" (different epic)

### Epic AI-2 Gaps (Stories 2.5-2.9)
- ⚠️ **InfluxDB attribute analysis:** Track feature usage history
- ⚠️ **HA automation analysis:** Check what features used in automations
- ⚠️ **Manual refresh:** Force capability re-discovery
- ⚠️ **Context7 fallback:** Research non-Zigbee devices

---

## 📈 Summary: Multi-Scale Automation

| Scale | Epic AI-1 (Pattern) | Epic AI-2 (Device Intelligence) |
|-------|-------------------|--------------------------------|
| **Real-time** | ❌ | ✅ MQTT discovery |
| **Hourly** | ❌ | ❌ |
| **Daily** | ✅ Time-of-day clustering | ❌ (capability-based) |
| **Weekly** | ⚠️ Can detect repeating patterns | ❌ |
| **Monthly** | ❌ | ❌ |
| **Seasonal** | ❌ (Phase 3+) | ❌ |
| **On-Demand** | ✅ API triggers | ✅ Analyze anytime |

---

## 🎯 Bottom Line

### Epic AI-1: **"You use X at time Y consistently → Automate it"**
- **Time scales:** Daily patterns (30-day window)
- **ML:** KMeans clustering, co-occurrence mining, anomaly detection
- **Output:** 5-10 automation suggestions weekly
- **User value:** Save time, reduce manual actions

### Epic AI-2: **"Your device can do A, B, C but you only use A → Try B and C"**
- **Time scales:** Real-time discovery, on-demand analysis
- **ML:** Utilization calculation, impact assessment
- **Output:** Feature suggestions for top unused capabilities
- **User value:** Discover device features, increase utilization

### Combined: **"Automate X at time Y AND enable feature Z for bonus value"**
- **Synergy:** Pattern automation + feature discovery
- **User value:** Maximum device potential

