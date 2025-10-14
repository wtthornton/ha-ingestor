# Epic 23: Enhanced Event Data Capture - Quick Reference

**Status:** 🚧 **60% COMPLETE** (3 of 5 stories)  
**Last Updated:** January 15, 2025  

---

## ✅ **Completed Features (Ready to Use)**

### 1. Automation Chain Tracing (Story 23.1)

**API Endpoint:**
```bash
GET http://localhost:8003/api/v1/events/automation-trace/{context_id}
```

**Parameters:**
- `max_depth` (optional): Maximum chain depth (default: 10)
- `include_details` (optional): Include full event details (default: true)

**Example:**
```bash
# Trace automation starting from context abc123
curl "http://localhost:8003/api/v1/events/automation-trace/abc123?max_depth=5&include_details=true"
```

**Response:**
```json
[
  {
    "depth": 0,
    "context_id": "abc123",
    "context_parent_id": "automation_xyz",
    "timestamp": "2025-01-15T12:00:00Z",
    "entity_id": "light.living_room",
    "event_type": "state_changed",
    "state": "on",
    "old_state": "off"
  },
  {
    "depth": 1,
    "context_id": "def456",
    "context_parent_id": "abc123",
    "timestamp": "2025-01-15T12:00:01Z",
    "entity_id": "sensor.motion",
    "event_type": "state_changed",
    "state": "detected"
  }
]
```

**Use Cases:**
- 🔍 Debug which automation triggered a state change
- 🔗 Visualize multi-step automation chains
- 🔄 Detect circular automation loops
- 📊 Analyze automation interaction patterns

**InfluxDB Fields:**
- `context_id` - Event context identifier
- `context_parent_id` - Parent context (null for user-initiated)
- `context_user_id` - User who triggered (if applicable)

---

### 2. Time-Based Analytics (Story 23.3)

**New Field:** `duration_in_state_seconds`

**What It Tracks:**
Time elapsed between `old_state.last_changed` and `new_state.last_changed`

**Query Examples:**
```flux
// Average motion detection duration in last 24h
from(bucket: "home_assistant_events")
  |> range(start: -24h)
  |> filter(fn: (r) => r["entity_id"] == "binary_sensor.motion_living_room")
  |> filter(fn: (r) => r["_field"] == "duration_in_state_seconds")
  |> mean()

// Find doors open >30 minutes
from(bucket: "home_assistant_events")
  |> range(start: -7d)
  |> filter(fn: (r) => r["domain"] == "binary_sensor")
  |> filter(fn: (r) => r["device_class"] == "door")
  |> filter(fn: (r) => r["_field"] == "duration_in_state_seconds")
  |> filter(fn: (r) => r["_value"] > 1800)
```

**Use Cases:**
- ⏱️ Motion sensor dwell time (how long was room occupied?)
- 🚪 Door/window open duration (security + energy efficiency)
- 💡 Light on-time analysis
- 📈 State stability detection (identify flapping sensors)

**Validation:**
- Negative durations → Clamped to 0 (with warning log)
- Durations >7 days → Stored but logged as warning
- Missing timestamps → Stored as null

---

### 3. Entity Classification Filtering (Story 23.4)

**API Parameters:**
```bash
GET http://localhost:8003/api/v1/events
  ?entity_category=diagnostic    # Include only diagnostic entities
  ?exclude_category=diagnostic   # Exclude diagnostic entities (cleaner analytics)
```

**Examples:**
```bash
# Get only regular entities (exclude diagnostic noise)
curl "http://localhost:8003/api/v1/events?exclude_category=diagnostic&limit=100"

# Get only diagnostic entities (debugging)
curl "http://localhost:8003/api/v1/events?entity_category=diagnostic&limit=100"

# Get only config entities
curl "http://localhost:8003/api/v1/events?entity_category=config&limit=100"

# Combine filters
curl "http://localhost:8003/api/v1/events?exclude_category=diagnostic&event_type=state_changed&limit=50"
```

**Use Cases:**
- 🧹 Clean analytics (hide diagnostic entities)
- 🔍 Debug mode (show only diagnostic entities)
- ⚙️ Configuration review (show only config entities)
- 📊 Accurate event counts (exclude system entities)

**Entity Categories (HA Standard):**
- `null` - Regular user-facing entities (sensors, lights, switches)
- `diagnostic` - System diagnostic entities (CPU, memory, network stats)
- `config` - Configuration entities (settings, options)

**Coverage:** ~15% of entities have categories (HA limitation)

---

## ⏳ **Remaining Features (Stories 23.2 + 23.5)**

### Story 23.2: Device and Area Linkage
**Status:** PENDING  
**Priority:** HIGH ⭐  
**Estimated:** 1.5 days  

**Will Add:**
- `device_id` tag - Link events to physical devices
- `area_id` tag - Link events to rooms/areas
- API filtering: `?device_id=xxx&area_id=yyy`

**Use Cases:**
- 📍 Energy usage per room
- 🏠 Temperature zones by area
- 🔌 Device-level aggregation ("all sensors on Device X")
- 📊 Spatial analytics and heatmaps

---

### Story 23.5: Device Metadata Enrichment
**Status:** PENDING  
**Priority:** LOW  
**Estimated:** 1 day  

**Will Add:**
- `manufacturer` field - Device manufacturer
- `model` field - Device model number
- `sw_version` field - Firmware version
- Reliability dashboard showing failure rates by manufacturer/model

**Use Cases:**
- 🔧 Identify unreliable manufacturers
- 📱 Track firmware version issues
- ⚠️ Predictive maintenance alerts
- 📊 Device lifecycle management

---

## 🚀 **Deployment Checklist**

### Pre-Deployment
- ✅ Code reviewed and approved
- ✅ Unit tests passing
- ⏳ Integration tests (recommended)
- ⏳ Performance benchmarks (recommended)

### Deployment Steps
```bash
# 1. Pull latest code
git pull origin master

# 2. Restart affected services
docker-compose restart websocket-ingestion enrichment-pipeline data-api

# 3. Verify services healthy
./scripts/test-services.sh

# Or individually:
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### Post-Deployment Validation
```bash
# 1. Test automation trace endpoint
curl "http://localhost:8003/api/v1/events/automation-trace/test-context-id"

# 2. Test entity category filtering
curl "http://localhost:8003/api/v1/events?exclude_category=diagnostic&limit=10"

# 3. Check InfluxDB for new fields
influx query 'from(bucket:"home_assistant_events") 
  |> range(start: -1h) 
  |> filter(fn: (r) => r["_field"] == "context_parent_id" or r["_field"] == "duration_in_state_seconds")
  |> limit(n: 10)'

# 4. Verify no errors in logs
docker-compose logs --tail=100 websocket-ingestion enrichment-pipeline data-api
```

---

## 📊 **Monitoring After Deployment**

### Metrics to Watch (First 24 Hours)

**Performance:**
- Event processing latency (target: <50ms p95)
- InfluxDB write success rate (target: >99%)
- API response times (target: <200ms p95)

**Data Quality:**
- % events with context_parent_id (expect: ~50%)
- % events with duration_in_state (expect: ~99%)
- % events with entity_category (expect: ~15%)
- Duration outliers >7 days (expect: <0.1%)

**Storage:**
- Storage growth rate (expect: ~23% increase)
- Daily storage size (expect: ~31 MB/day)
- InfluxDB disk usage trend

**Errors:**
- Check logs for duration calculation errors
- Check logs for context extraction errors
- Monitor InfluxDB write failures

---

## 🔍 **Troubleshooting Guide**

### Issue: Automation trace returns empty array
**Causes:**
- context_id doesn't exist in database
- No events have that context as parent
- Time range too narrow (default: 30 days)

**Fix:**
- Verify context_id is correct
- Check if automation has actually run
- Extend time range in query if needed

---

### Issue: Duration values seem incorrect
**Causes:**
- Timezone mismatch
- System clock skew
- HA timestamp format changed

**Fix:**
- Check logs for duration calculation warnings
- Verify timestamps in InfluxDB
- Review timezone handling in code

---

### Issue: Entity category filtering not working
**Causes:**
- entity_category not set on entities (HA limitation)
- Tag not indexed in InfluxDB
- Query syntax error

**Fix:**
- Check % of entities with categories in HA
- Verify tag exists in InfluxDB schema
- Review API query logs

---

## 📝 **API Documentation**

### Automation Trace Endpoint

**URL:** `GET /api/v1/events/automation-trace/{context_id}`

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| context_id | string | required | Context ID to trace |
| max_depth | int | 10 | Maximum chain depth |
| include_details | bool | true | Include full event details |

**Response:** Array of events in automation chain

**Status Codes:**
- 200: Success
- 404: Context ID not found
- 500: Server error

---

### Entity Category Filtering

**URL:** `GET /api/v1/events`

**New Parameters:**
| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| entity_category | string | config, diagnostic | Include only this category |
| exclude_category | string | config, diagnostic | Exclude this category |

**Examples:**
```bash
# Hide diagnostic entities (recommended for clean analytics)
?exclude_category=diagnostic

# Show only diagnostic entities (for system monitoring)
?entity_category=diagnostic

# Combine with other filters
?exclude_category=diagnostic&event_type=state_changed&limit=50
```

---

## 📈 **Expected Results After Deployment**

### InfluxDB Data
```
Measurement: home_assistant_events

New Fields Added:
- context_id (field, string)
- context_parent_id (field, string) - ~50% populated
- context_user_id (field, string) - ~30% populated
- duration_in_state_seconds (field, float) - ~99% populated

Existing Tag Enhanced:
- entity_category (tag, string) - ~15% populated
```

### API Behavior
- Automation trace queries work immediately (historical data has context fields)
- Duration fields available for all new events (historical events have null)
- Entity category filtering works for entities with categories assigned

### Dashboard Impact
- Dashboard can now filter diagnostic entities
- Automation debugging UI can be built on trace API
- Duration-based analytics enabled

---

**Quick Start:** See [EPIC_23_FINAL_SESSION_SUMMARY.md](EPIC_23_FINAL_SESSION_SUMMARY.md) for full deployment guide.

