# Quick Reference: Epic AI-2 Device Intelligence

**For:** Quick lookup during review or debugging  
**Date:** 2025-10-16

---

## 🗂️ File Structure

```
services/ai-automation-service/
├── src/
│   ├── scheduler/
│   │   └── daily_analysis.py ⭐ MAIN FILE (unified job)
│   ├── device_intelligence/
│   │   ├── __init__.py
│   │   ├── capability_parser.py (Story 2.1)
│   │   ├── mqtt_capability_listener.py (Story 2.1 - legacy)
│   │   ├── capability_batch.py (Story 2.5 - NEW)
│   │   ├── feature_analyzer.py (Story 2.3)
│   │   └── feature_suggestion_generator.py (Story 2.4)
│   └── database/
│       ├── models.py (+ DeviceCapability, DeviceFeatureUsage)
│       └── crud.py (+ upsert_device_capability, etc.)
└── tests/
    ├── test_capability_parser.py
    ├── test_mqtt_capability_listener.py
    ├── test_database_models.py
    ├── test_feature_analyzer.py
    └── test_feature_suggestion_generator.py
```

---

## 📊 Database Schema

### **device_capabilities**
```sql
CREATE TABLE device_capabilities (
    device_model TEXT PRIMARY KEY,        -- e.g., "VZM31-SN"
    manufacturer TEXT NOT NULL,           -- e.g., "Inovelli"
    integration_type TEXT NOT NULL,       -- e.g., "zigbee"
    capabilities JSON NOT NULL,           -- Parsed features
    mqtt_exposes JSON,                    -- Raw Zigbee2MQTT data
    last_updated TIMESTAMP,
    source TEXT DEFAULT 'zigbee2mqtt_bridge'
);
```

### **device_feature_usage**
```sql
CREATE TABLE device_feature_usage (
    device_id TEXT,                       -- e.g., "light.kitchen"
    feature_name TEXT,                    -- e.g., "led_notifications"
    configured BOOLEAN DEFAULT FALSE,
    discovered_date TIMESTAMP,
    last_checked TIMESTAMP,
    PRIMARY KEY (device_id, feature_name)
);
```

---

## 🔄 6-Phase Job Flow

### **Phase 1: Device Capability Update** (Epic AI-2)
- **Function:** `update_device_capabilities_batch()`
- **File:** `capability_batch.py`
- **Duration:** 1-3 min
- **Output:** `{devices_checked, capabilities_updated, new_devices, errors}`

### **Phase 2: Fetch Events** (Shared)
- **Method:** `data_client.fetch_events()`
- **Duration:** 1-2 min
- **Output:** DataFrame with 30 days of events

### **Phase 3: Pattern Detection** (Epic AI-1)
- **Classes:** `TimeOfDayPatternDetector`, `CoOccurrencePatternDetector`
- **Duration:** 2-3 min
- **Output:** List of patterns with confidence scores

### **Phase 4: Feature Analysis** (Epic AI-2)
- **Class:** `FeatureAnalyzer`
- **Method:** `analyze_all_devices()`
- **Duration:** 1-2 min
- **Output:** `{opportunities, devices_analyzed, avg_utilization}`

### **Phase 5: Combined Suggestions** (AI-1 + AI-2)
- **Part A:** Pattern suggestions (Epic AI-1)
- **Part B:** Feature suggestions (Epic AI-2)
- **Part C:** Combine and rank (top 10)
- **Duration:** 2-4 min
- **Output:** List of combined suggestions

### **Phase 6: Publish & Store**
- **Actions:** Store suggestions, publish MQTT notification
- **Duration:** <1 min

---

## 🎯 Key Functions

### **capability_batch.py**
```python
async def update_device_capabilities_batch(
    mqtt_client,
    data_api_client,
    db_session_factory
) -> Dict[str, int]
```

### **feature_analyzer.py**
```python
class FeatureAnalyzer:
    async def analyze_all_devices(self) -> Dict
    async def analyze_device(self, device_id: str) -> Optional[Dict]
```

### **feature_suggestion_generator.py**
```python
class FeatureSuggestionGenerator:
    async def generate_suggestions(self, max_suggestions: int = 10) -> List[Dict]
```

---

## 📝 Suggestion Types

### **Pattern Automation** (Epic AI-1)
```python
{
    'type': 'pattern_automation',
    'source': 'Epic-AI-1',
    'pattern_type': 'time_of_day' | 'co_occurrence' | 'anomaly',
    'title': 'AI Suggested: Turn on bedroom light at 10:30 PM',
    'automation_yaml': '...',
    'confidence': 0.85,
    'category': 'convenience',
    'priority': 'high'
}
```

### **Feature Discovery** (Epic AI-2)
```python
{
    'type': 'feature_discovery',
    'source': 'Epic-AI-2',
    'feature_name': 'led_notifications',
    'title': 'Enable LED Notifications on Kitchen Switch',
    'description': 'Your Inovelli switch supports...',
    'confidence': 0.82,
    'category': 'security',
    'priority': 'high',
    'manufacturer': 'Inovelli',
    'model': 'VZM31-SN',
    'complexity': 'medium',
    'impact': 'high'
}
```

---

## 🔧 Environment Variables

```bash
# Required for Epic AI-2
HA_URL=http://homeassistant:8123
HA_TOKEN=<token>
MQTT_BROKER=homeassistant  # Zigbee2MQTT bridge
MQTT_PORT=1883
OPENAI_API_KEY=<key>
DATA_API_URL=http://data-api:8006
INFLUXDB_URL=http://influxdb:8086
```

---

## 🧪 Testing Commands

```bash
# Run all tests
docker-compose run --rm ai-automation-service pytest -v

# Run specific story tests
docker-compose run --rm ai-automation-service pytest tests/test_feature_analyzer.py -v
docker-compose run --rm ai-automation-service pytest tests/test_feature_suggestion_generator.py -v

# Check linter
docker-compose run --rm ai-automation-service python -m flake8 src/device_intelligence/

# Manual trigger (after service is up)
curl -X POST http://localhost:8018/api/analysis/trigger
```

---

## 📊 Expected Metrics

### **Typical Run**
- Events analyzed: 10,000-20,000
- Patterns detected: 3-8
- Devices checked: 50-150
- Capabilities updated: 2-10 (only new/stale)
- Opportunities found: 15-40
- Total suggestions: 8-10 (mixed)
- Duration: 8-12 minutes
- OpenAI cost: $0.002-$0.004

### **Resource Usage**
- Memory: 200-400MB peak
- CPU: 10-30% during processing
- Network: 5-10MB (InfluxDB query)
- Disk: Minimal (SQLite writes)

---

## ⚠️ Common Issues

### **Issue: No capabilities updated**
- **Cause:** Zigbee2MQTT bridge not responding
- **Fix:** Check MQTT broker availability
- **Impact:** Feature suggestions skipped, pattern suggestions work

### **Issue: No opportunities found**
- **Cause:** All devices at 100% utilization (unlikely) or no capability data
- **Fix:** Check device_capabilities table
- **Impact:** Only pattern suggestions generated

### **Issue: Job takes >15 minutes**
- **Cause:** Large event dataset or slow InfluxDB
- **Fix:** Optimize query, add indexing
- **Impact:** Delayed suggestions (still functional)

---

## 📞 Quick Debugging

### **Check Service Health**
```bash
curl http://localhost:8018/health
```

### **Check Last Run**
```bash
curl http://localhost:8018/api/analysis/status
```

### **View Logs**
```bash
docker-compose logs ai-automation-service --tail=100

# Look for:
# ✅ Phase 1/6 complete
# ✅ Phase 2/6 complete
# ... etc
```

### **Check Database**
```bash
# Check capabilities
sqlite3 data/ai_automation.db "SELECT COUNT(*) FROM device_capabilities;"

# Check suggestions
sqlite3 data/ai_automation.db "SELECT type, title FROM suggestions ORDER BY created_at DESC LIMIT 10;"
```

---

## 🚀 Deployment Commands

```bash
# Build
docker-compose build ai-automation-service

# Deploy
docker-compose up -d ai-automation-service

# Check status
docker-compose ps ai-automation-service

# View logs
docker-compose logs ai-automation-service --tail=100 --follow

# Restart
docker-compose restart ai-automation-service
```

---

## 📚 Document Quick Links

| Document | Purpose |
|----------|---------|
| `STORY_AI2-5_COMPLETE.md` | Implementation summary |
| `REVIEW_GUIDE_STORY_AI2-5.md` | This review guide |
| `REALTIME_VS_BATCH_ANALYSIS.md` | Architecture decision |
| `EPIC_AI1_VS_AI2_SUMMARY.md` | Epic comparison |
| `DATA_INTEGRATION_ANALYSIS.md` | Data source analysis |

---

## 🎯 Success Indicators

✅ All 6 phases execute  
✅ Both suggestion types generated  
✅ Duration <15 minutes  
✅ Memory <500MB  
✅ Cost <$0.01 per run  
✅ No errors in logs  
✅ Suggestions stored in database  
✅ MQTT notification published

