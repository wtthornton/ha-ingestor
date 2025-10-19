# 🔄 **Complete Data Flow Call Tree: Home Assistant → GUI**

> **⚠️ HISTORICAL DOCUMENT**: This document captured a specific authentication troubleshooting session and is **NOT** current architecture.
> 
> **For current architecture**, see:
> - [HA_EVENT_CALL_TREE.md](./HA_EVENT_CALL_TREE.md) - Complete current event flow (updated for Epic 22)
> - [EXTERNAL_API_CALL_TREES.md](./EXTERNAL_API_CALL_TREES.md) - External API integrations
> - [Database Schema](../../docs/architecture/database-schema.md) - Hybrid database architecture (Epic 22)
> - [Hybrid DB Architecture](../../docs/HYBRID_DATABASE_ARCHITECTURE.md) - Quick reference
>
> **Status**: This issue was **resolved**. This document is kept for historical reference only.
>
> **Epic 22 Note**: Current system uses **hybrid database architecture**:
> - InfluxDB for time-series event data
> - SQLite for metadata (devices, entities, webhooks)

---

## 🚨 **CRITICAL ISSUE IDENTIFIED: Authentication Failure** (RESOLVED)

The WebSocket service is **failing to authenticate** with Home Assistant, causing the entire data pipeline to be empty.

---

## 📊 **Complete Data Flow Architecture**

### **1. Home Assistant (Data Source)**
```
Home Assistant (http://192.168.1.86:8123)
├── WebSocket API: /api/websocket
├── Events: state_changed, device_registry_updated, etc.
└── Authentication: Bearer Token Required
```

### **2. WebSocket Ingestion Service (Port 8001)**
```
WebSocket Ingestion Service
├── Connection Manager
│   ├── Connects to: ws://192.168.1.86:8123/api/websocket
│   ├── Authentication: Bearer {HOME_ASSISTANT_TOKEN}
│   └── ❌ FAILING: "Invalid access token or password"
├── Event Subscription Manager
│   ├── Subscribes to: state_changed events
│   └── ❌ NO EVENTS: Authentication prevents subscription
├── Event Processor
│   ├── Processes incoming events
│   └── ❌ NO PROCESSING: No events received
├── InfluxDB Batch Writer
│   ├── Writes events to InfluxDB
│   └── ❌ NO WRITES: No events to write
└── Health Endpoint (/health)
    └── Returns: connection_attempts=15, failed_connections=7, error_rate=46.67%
```

### **3. Enrichment Pipeline Service (Port 8002)**
```
Enrichment Pipeline Service
├── HTTP Client
│   ├── Receives events from WebSocket service
│   └── ❌ NO EVENTS: WebSocket service not sending data
├── Data Normalizer
│   ├── Normalizes event data
│   └── ❌ NO NORMALIZATION: No events to process
├── InfluxDB Writer
│   ├── Writes enriched data to InfluxDB
│   └── ❌ NO WRITES: No data to write
└── Stats Endpoint (/api/v1/stats)
    └── Returns: connection_attempts=1039, events_per_minute=0
```

### **4. Databases (Hybrid Architecture - Epic 22)**

**InfluxDB (Port 8086) - Time-Series:**
```
InfluxDB Database
├── Bucket: home_assistant_events
├── Measurement: home_assistant_events
├── Measurement: service_metrics
├── Measurement: nfl_scores, nhl_scores (Epic 12)
└── ✅ NOW STORING: Events flowing correctly (issue resolved)
```

**SQLite (Epic 22) - Metadata:**
```
SQLite Databases
├── data-api/metadata.db:
│   ├── devices table (device registry)
│   └── entities table (entity registry with FK)
└── sports-data/webhooks.db:
    └── webhooks table (game event subscriptions)
```

### **5. Admin API (Port 8003)**
```
Admin API Service
├── Stats Endpoints (/api/stats)
│   ├── Primary: InfluxDB Query
│   │   ├── Query: home_assistant_events measurement
│   │   └── ❌ EMPTY RESULT: No data in InfluxDB
│   └── Fallback: Direct Service Calls
│       ├── WebSocket Service: /health → transformed to stats
│       └── Enrichment Service: /api/v1/stats → direct stats
├── Health Endpoints (/api/health)
│   ├── Checks service dependencies
│   └── Returns: healthy status but 0 events
└── WebSocket Broadcast
    └── Broadcasts updates to dashboard (but no data to broadcast)
```

### **6. Dashboard GUI (Port 3000)**
```
Health Dashboard
├── Overview Tab
│   ├── System Health Cards
│   │   ├── Overall Status: "unhealthy" (0 events)
│   │   ├── WebSocket Connection: "disconnected" (auth failure)
│   │   ├── Event Processing: "unhealthy" (0 events/min)
│   │   └── Database Storage: "connected" (InfluxDB healthy)
│   └── Key Metrics Cards
│       ├── Total Events: 0
│       ├── Events per Minute: 0
│       ├── Error Rate: 46.67%
│       └── Enrichment Pipeline: 1039 attempts
├── Dependencies Tab
│   └── ✅ HEALTHY: All services running, InfluxDB connected
├── Recent Events Tab
│   └── ❌ EMPTY: No events to display
└── Real-time Updates
    ├── WebSocket Connection: ws://localhost:3000/ws
    ├── Proxied to: Admin API WebSocket endpoint
    └── ❌ NO DATA: Nothing to broadcast
```

---

## 🔍 **Root Cause Analysis**

### **Primary Issue: Authentication Failure**
```
Home Assistant Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
├── Token Validation: ❌ FAILING
├── Error: "Invalid access token or password"
├── Connection Attempts: 15
├── Failed Connections: 7
└── Error Rate: 46.67%
```

### **Impact Chain:**
1. **WebSocket Service** → Can't authenticate → No events received
2. **Event Processing** → No events to process → 0 events/minute
3. **InfluxDB** → No data written → Empty database
4. **Admin API** → InfluxDB queries return empty → Falls back to service calls
5. **Dashboard** → Shows accurate but empty data → Appears "broken"

---

## 🎯 **Data Flow Verification**

### **✅ Working Components:**
- InfluxDB connection and health
- Admin API endpoints and fallback mechanism
- Dashboard WebSocket connection and UI rendering
- Service health monitoring
- Error rate calculations

### **❌ Broken Component:**
- **Home Assistant Authentication** → Cascading failure through entire pipeline

---

## 🔧 **Solution Required**

### **Immediate Fix:**
1. **Generate New Home Assistant Token**
   - Go to Home Assistant Profile → Long-Lived Access Tokens
   - Create new token with proper permissions
   - Update `HOME_ASSISTANT_TOKEN` in `.env` file

### **Verification Steps:**
1. Test token: `curl -H "Authorization: Bearer {new_token}" http://192.168.1.86:8123/api/`
2. Restart WebSocket service: `docker restart homeiq-websocket`
3. Monitor logs: `docker logs homeiq-websocket --follow`
4. Verify events: Check dashboard for incoming events

---

## 📈 **Expected Data Flow After Fix**

```
Home Assistant → WebSocket Service → Event Processing → InfluxDB → Admin API → Dashboard
     ✅              ✅                    ✅              ✅          ✅         ✅
```

**Once authentication is fixed, the entire pipeline will flow data correctly and the dashboard will show real-time Home Assistant events.**

