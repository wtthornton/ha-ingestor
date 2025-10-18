# Phase 6: MQTT Notification
## Job Completion Notification to Home Assistant

**Epic:** Shared (AI-1 + AI-2)  
**Duration:** <1 second  
**Protocol:** MQTT (QoS 1)  
**Last Updated:** October 17, 2025

**🔗 Navigation:**
- [← Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [← Previous: Phase 5b - Suggestion Storage](AI_AUTOMATION_PHASE5B_STORAGE.md)
- [→ Back to: Main Execution Flow](AI_AUTOMATION_MAIN_FLOW.md)

---

## 📋 Overview

**Purpose:** Notify Home Assistant via MQTT of analysis completion

Phase 6 publishes completion metrics to Home Assistant:
1. **Build Notification Payload** - Aggregate all phase metrics
2. **Publish to MQTT** - Send to `ha-ai/analysis/complete` topic
3. **Home Assistant Integration** - HA can trigger notifications/automations

This allows Home Assistant to:
- Display notification to user when analysis completes
- Update AI dashboard widgets with new suggestions
- Trigger automations based on analysis results
- Track job history and success rate

---

## 🔄 Call Tree

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

---

## 📤 Notification Payload

**Complete JSON Structure:**

```json
{
  "timestamp": "2025-10-17T03:04:15Z",
  "success": true,
  "duration_seconds": 245,
  
  "epic_ai_1": {
    "patterns_detected": 23,
    "time_of_day_patterns": 15,
    "co_occurrence_patterns": 8,
    "pattern_suggestions_generated": 6
  },
  
  "epic_ai_2": {
    "devices_checked": 20,
    "capabilities_updated": 10,
    "new_devices": 2,
    "devices_analyzed": 20,
    "opportunities_found": 5,
    "feature_suggestions_generated": 4,
    "avg_utilization_pct": 38.5
  },
  
  "combined": {
    "events_analyzed": 87543,
    "suggestions_generated": 10,
    "suggestions_stored": 10,
    "openai_tokens_used": 4430,
    "openai_cost_usd": 0.00137
  }
}
```

---

## 🔌 MQTT Publishing

**Client Implementation:**

```python
class MQTTNotificationClient:
    def __init__(self, broker: str, port: int):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
    
    async def publish_analysis_complete(self, notification: dict):
        # Connect to broker
        self.client.connect(self.broker, self.port)
        
        # Publish notification
        result = self.client.publish(
            topic="ha-ai/analysis/complete",
            payload=json.dumps(notification),
            qos=1,  # At least once delivery
            retain=False  # Don't retain for future subscribers
        )
        
        # Wait for publish to complete
        result.wait_for_publish()
        
        # Disconnect
        self.client.disconnect()
        
        logger.info(f"✅ Published analysis completion to MQTT")
```

**Quality of Service (QoS 1):**
- **At least once delivery**: Message guaranteed to arrive
- **Broker acknowledges receipt**: Publisher waits for confirmation
- **No duplicates** (unlike QoS 2): Home Assistant may receive once
- **Reliable without overhead**: Good balance for notifications

---

## 🏠 Home Assistant Integration

**Subscription in Home Assistant:**

```yaml
# configuration.yaml
mqtt:
  broker: 192.168.1.86
  port: 1883

# automations.yaml
automation:
  - alias: "AI Analysis Complete Notification"
    trigger:
      - platform: mqtt
        topic: ha-ai/analysis/complete
    action:
      - service: notify.persistent_notification
        data:
          title: "AI Analysis Complete"
          message: >
            Found {{ trigger.payload_json.combined.suggestions_generated }} new automation suggestions!
            Duration: {{ trigger.payload_json.duration_seconds }}s
            Cost: ${{ trigger.payload_json.combined.openai_cost_usd }}
      
      - service: mqtt.publish
        data:
          topic: homeassistant/sensor/ai_suggestions/state
          payload: "{{ trigger.payload_json.combined.suggestions_generated }}"
```

**Use Cases:**
1. **Persistent Notification** - Alert user when analysis completes
2. **Dashboard Widget** - Update sensor with suggestion count
3. **Automation Trigger** - Run other automations after analysis
4. **Logging** - Track analysis history in HA

---

## 📊 Notification Examples

### Success Notification

```json
{
  "timestamp": "2025-10-17T03:04:15Z",
  "success": true,
  "duration_seconds": 245,
  "epic_ai_1": {
    "patterns_detected": 23,
    "pattern_suggestions_generated": 6
  },
  "epic_ai_2": {
    "opportunities_found": 5,
    "feature_suggestions_generated": 4
  },
  "combined": {
    "suggestions_generated": 10,
    "openai_cost_usd": 0.00137
  }
}
```

### Partial Success Notification

```json
{
  "timestamp": "2025-10-17T03:04:15Z",
  "success": true,
  "duration_seconds": 198,
  "epic_ai_1": {
    "patterns_detected": 0,
    "pattern_suggestions_generated": 0,
    "error": "InfluxDB query timeout"
  },
  "epic_ai_2": {
    "opportunities_found": 3,
    "feature_suggestions_generated": 3
  },
  "combined": {
    "suggestions_generated": 3,
    "openai_cost_usd": 0.00041
  }
}
```

### Failure Notification

```json
{
  "timestamp": "2025-10-17T03:01:45Z",
  "success": false,
  "duration_seconds": 105,
  "error": "OpenAI API key invalid",
  "epic_ai_1": {
    "patterns_detected": 12,
    "pattern_suggestions_generated": 0
  },
  "epic_ai_2": {
    "opportunities_found": 4,
    "feature_suggestions_generated": 0
  },
  "combined": {
    "suggestions_generated": 0
  }
}
```

---

## ⚡ Performance

**Typical Metrics:**
- **Publish Time:** <100ms
- **Payload Size:** ~500 bytes
- **Network Overhead:** Minimal
- **Reliability:** 99.9% (QoS 1)

**Bottleneck:** None (MQTT is very fast)

---

## ⚠️ Error Handling

**MQTT Connection Errors:**

```python
try:
    mqtt_client.publish_analysis_complete(notification)
except Exception as e:
    logger.error(f"Failed to publish MQTT notification: {e}")
    # Don't fail entire job - notification is non-critical
    # Analysis results are still stored in database
```

**Common Errors:**
1. **Broker Unavailable**
   - Log warning, continue
   - Analysis results still in database

2. **Publish Timeout**
   - Retry once
   - If still fails, log and continue

3. **Connection Refused**
   - Check broker address/port
   - Verify network connectivity

**Graceful Degradation:**
- MQTT notification is **non-critical**
- Failure doesn't invalidate analysis results
- User can still access suggestions via API/UI
- Next run will publish next notification

---

## 🏁 Phase 6 Output

**Returns:**
```python
{
    'notification_published': True,
    'mqtt_topic': 'ha-ai/analysis/complete',
    'payload_size_bytes': 487
}
```

**MQTT Message Published:**
- Topic: `ha-ai/analysis/complete`
- Payload: Complete analysis metrics (JSON)
- QoS: 1 (at least once delivery)
- Retain: False

---

## 🔗 Home Assistant Sensor Integration

**Create Sensor for Suggestion Count:**

```yaml
# configuration.yaml
mqtt:
  sensor:
    - name: "AI Automation Suggestions"
      state_topic: "ha-ai/analysis/complete"
      value_template: "{{ value_json.combined.suggestions_generated }}"
      unit_of_measurement: "suggestions"
      icon: mdi:robot
      
    - name: "AI Analysis Duration"
      state_topic: "ha-ai/analysis/complete"
      value_template: "{{ value_json.duration_seconds }}"
      unit_of_measurement: "s"
      icon: mdi:timer
      
    - name: "AI Analysis Cost"
      state_topic: "ha-ai/analysis/complete"
      value_template: "{{ value_json.combined.openai_cost_usd }}"
      unit_of_measurement: "USD"
      icon: mdi:currency-usd
```

**Dashboard Card:**

```yaml
# ui-lovelace.yaml
type: entities
title: AI Automation Status
entities:
  - entity: sensor.ai_automation_suggestions
  - entity: sensor.ai_analysis_duration
  - entity: sensor.ai_analysis_cost
```

---

## 🎯 Success Criteria

**Phase 6 Complete When:**
- ✅ Notification payload built successfully
- ✅ MQTT message published
- ✅ Home Assistant receives notification (optional verification)
- ✅ Job metrics logged

**Metrics Included:**
- Total suggestions generated: 10
- OpenAI tokens used: 4,430
- OpenAI cost: $0.00137
- Duration: 245 seconds
- Success status: true

---

## 🔗 Related Documentation

- [← Phase 5b: Suggestion Storage](AI_AUTOMATION_PHASE5B_STORAGE.md)
- [← Main Execution Flow](AI_AUTOMATION_MAIN_FLOW.md) - Job completion and cleanup
- [Phase 1: Device Capability Discovery](AI_AUTOMATION_PHASE1_CAPABILITIES.md) - Uses Zigbee2MQTT
- [Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)

---

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Epic:** Shared (AI-1 + AI-2)

