# Home Assistant Event Call Tree Analysis
## Complete Data Flow: HA → Database → Dashboard

**Document Version**: 1.0  
**Created**: 2025-10-13  
**Purpose**: Detailed call tree showing complete event flow from Home Assistant through the entire system

---

## 📊 Overview

This document traces the complete journey of a Home Assistant event from its origin through processing, storage, and display on the dashboard. The flow involves multiple services working together in a microservices architecture.

### Architecture Flow Diagram

```
┌─────────────────┐
│ Home Assistant  │ (External System)
└────────┬────────┘
         │ WebSocket Connection (WSS/WS)
         │ Event: state_changed, call_service, etc.
         ▼
┌────────────────────────────────────────────────┐
│ WebSocket Ingestion Service (Port 8001)       │
│ - Connection Management                        │
│ - Event Subscription                           │
│ - Initial Processing                           │
│ - Async Queue Management                       │
│ - Batch Processing                             │
└────────┬───────────────────────────────────────┘
         │
         ├──────────► (Optional) Enrichment Pipeline (Port 8002)
         │            - Data Normalization
         │            - Data Validation
         │            - Quality Metrics
         │
         ▼
┌────────────────────────────────────────────────┐
│ InfluxDB (Port 8086)                          │
│ - Time-Series Database                         │
│ - Measurements: home_assistant_events          │
│ - Retention: 1 year raw, 5 years aggregated   │
└────────┬───────────────────────────────────────┘
         │
         │ Flux Query Language
         │
         ▼
┌────────────────────────────────────────────────┐
│ Admin API Service (Port 8003)                 │
│ - REST API Gateway                             │
│ - Statistics Endpoints                         │
│ - Events Endpoints                             │
│ - WebSocket Streaming                          │
└────────┬───────────────────────────────────────┘
         │
         │ HTTP/REST + WebSocket
         │
         ▼
┌────────────────────────────────────────────────┐
│ Health Dashboard (Port 3000)                  │
│ - React Frontend                               │
│ - Real-time Updates                            │
│ - 12 Tabs with Visualizations                 │
└────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Call Tree

### Phase 1: Event Reception from Home Assistant

#### 1.1 WebSocket Connection Establishment

**File**: `services/websocket-ingestion/src/connection_manager.py`

```python
ConnectionManager.connect()
└─► ConnectionManager._connect_with_retry()
    └─► HomeAssistantWebSocketClient.connect()
        ├─► websocket.connect(url)  # aiohttp WebSocket
        ├─► _authenticate()
        │   ├─► send_message({"type": "auth", "access_token": token})
        │   └─► receive auth_ok/auth_invalid
        └─► _on_connect()
            ├─► _subscribe_to_events()
            │   └─► EventSubscriptionManager.subscribe_to_event("state_changed")
            │       ├─► generate subscription ID (message_id counter)
            │       ├─► send_message({
            │       │     "id": message_id,
            │       │     "type": "subscribe_events",
            │       │     "event_type": "state_changed"
            │       │   })
            │       └─► wait for subscription confirmation
            │
            └─► DiscoveryService.discover_all()
                ├─► discover_devices()
                └─► discover_entities()
```

**Key Data Structures**:
- **Connection URL**: `ws://HA_URL:8123/api/websocket`
- **Auth Token**: Long-lived access token from Home Assistant
- **Subscription Types**: `state_changed`, `call_service`, etc.

---

#### 1.2 Event Message Reception

**File**: `services/websocket-ingestion/src/websocket_client.py`

```python
HomeAssistantWebSocketClient.listen()
└─► async for msg in self.websocket:  # aiohttp WebSocket message loop
    ├─► if msg.type == WSMsgType.TEXT:
    │   ├─► json.loads(msg.data)  # Parse JSON message
    │   └─► if self.on_message:
    │       └─► on_message(data)  # Callback to ConnectionManager
    │
    └─► ConnectionManager._handle_message(message)
        ├─► if message["type"] == "event":
        │   └─► EventSubscriptionManager.handle_event_message(message)
        │       ├─► Extract event data from message["event"]
        │       ├─► Log event reception
        │       └─► Trigger event handlers
        │           └─► for handler in self.event_handlers:
        │               └─► handler(event_data)  # Call to main service
        │
        └─► if message["type"] == "result":
            └─► EventSubscriptionManager.handle_subscription_result(message)
```

**Event Message Structure** (from Home Assistant):
```json
{
  "id": 123,
  "type": "event",
  "event": {
    "event_type": "state_changed",
    "data": {
      "entity_id": "sensor.temperature",
      "old_state": {
        "state": "20.5",
        "attributes": {"unit_of_measurement": "°C"}
      },
      "new_state": {
        "state": "21.0",
        "attributes": {"unit_of_measurement": "°C"}
      }
    },
    "origin": "LOCAL",
    "time_fired": "2025-10-13T10:30:00.123456+00:00",
    "context": {
      "id": "01234567890abcdef",
      "user_id": null
    }
  }
}
```

---

### Phase 2: Event Processing & Queue Management

#### 2.1 Event Handler Callback

**File**: `services/websocket-ingestion/src/main.py`

```python
WebSocketIngestionService.start()
├─► connection_manager.on_message = self._handle_event
│
└─► _handle_event(message)  # Called by WebSocket client
    ├─► if message["type"] == "event":
    │   ├─► event_data = message["event"]
    │   ├─► EventProcessor.validate_event(event_data)
    │   │   ├─► Check required fields (entity_id, event_type, time_fired)
    │   │   ├─► Validate data structure
    │   │   └─► Return bool (valid/invalid)
    │   │
    │   ├─► if valid:
    │   │   ├─► EventProcessor.extract_event_data(event_data)
    │   │   │   ├─► _extract_state_changed_data()
    │   │   │   │   ├─► Parse entity_id → extract domain
    │   │   │   │   ├─► Extract old_state and new_state
    │   │   │   │   ├─► Extract attributes (unit_of_measurement, device_class, etc.)
    │   │   │   │   └─► Extract context (user_id, parent_id)
    │   │   │   │
    │   │   │   └─► Return structured event data
    │   │   │
    │   │   └─► AsyncEventProcessor.process_event(extracted_data)
    │   │       └─► event_queue.put_nowait(event_data)  # Non-blocking queue
    │   │
    │   └─► log event reception statistics
    │
    └─► return processed status
```

**Extracted Event Data Structure**:
```python
{
    "event_type": "state_changed",
    "entity_id": "sensor.temperature",
    "domain": "sensor",
    "time_fired": "2025-10-13T10:30:00.123456+00:00",
    "origin": "LOCAL",
    "context": {
        "id": "01234567890abcdef",
        "user_id": null
    },
    "old_state": {
        "state": "20.5",
        "attributes": {"unit_of_measurement": "°C"},
        "last_changed": "2025-10-13T10:25:00.000000+00:00",
        "last_updated": "2025-10-13T10:25:00.000000+00:00"
    },
    "new_state": {
        "state": "21.0",
        "attributes": {"unit_of_measurement": "°C"},
        "last_changed": "2025-10-13T10:30:00.123456+00:00",
        "last_updated": "2025-10-13T10:30:00.123456+00:00"
    }
}
```

---

#### 2.2 Async Event Processing

**File**: `services/websocket-ingestion/src/async_event_processor.py`

```python
AsyncEventProcessor (Background Workers)
├─► start()
│   └─► for i in range(max_workers):  # Default: 10 workers
│       └─► asyncio.create_task(_worker(f"worker-{i}"))
│
└─► _worker(worker_name)  # Runs continuously
    └─► while self.is_running:
        ├─► event_data = await self.event_queue.get()  # Blocks until event available
        ├─► RateLimiter.acquire()  # Max 1000 events/second
        │
        ├─► for handler in self.event_handlers:
        │   └─► await handler(event_data)
        │       └─► BatchProcessor.add_event(event_data)
        │
        ├─► self.processed_events += 1
        ├─► self.processing_times.append(processing_time)
        └─► self.event_queue.task_done()
```

**Performance Characteristics**:
- **Concurrency**: 10 parallel workers
- **Queue Size**: 10,000 events max
- **Rate Limit**: 1,000 events/second
- **Processing Time**: Tracked for last 1,000 events

---

#### 2.3 Batch Processing

**File**: `services/websocket-ingestion/src/batch_processor.py`

```python
BatchProcessor
├─► add_event(event_data)
│   ├─► async with self.batch_lock:
│   │   ├─► self.current_batch.append(event_data)
│   │   ├─► if len(current_batch) >= batch_size (1000):
│   │   │   └─► _process_batch()
│   │   │
│   │   └─► if batch_timeout (5 seconds) exceeded:
│   │       └─► _process_batch()
│   │
│   └─► return queued status
│
└─► _process_batch()
    ├─► batch_to_process = self.current_batch
    ├─► self.current_batch = []  # Clear for next batch
    │
    ├─► for handler in self.batch_handlers:
    │   └─► await handler(batch_to_process)
    │       └─► InfluxDBBatchWriter.write_batch(events)
    │
    └─► log batch statistics
```

**Batch Configuration**:
- **Batch Size**: 1,000 events
- **Batch Timeout**: 5 seconds
- **Retry Logic**: 3 attempts with exponential backoff

---

### Phase 3: Database Write Operations

#### 3.1 InfluxDB Schema Creation

**File**: `services/websocket-ingestion/src/influxdb_schema.py`

```python
InfluxDBSchema.create_event_point(event_data)
├─► Extract basic fields:
│   ├─► event_type = event_data["event_type"]
│   ├─► entity_id = event_data["entity_id"]
│   ├─► timestamp = parse_timestamp(event_data["time_fired"])
│   └─► domain = entity_id.split(".")[0]
│
├─► Point(measurement="home_assistant_events")
│   ├─► .time(timestamp, WritePrecision.MS)
│   │
│   ├─► _add_event_tags(point, event_data)  # Indexed for fast queries
│   │   ├─► .tag("entity_id", entity_id)
│   │   ├─► .tag("domain", domain)
│   │   ├─► .tag("event_type", event_type)
│   │   ├─► .tag("device_class", attributes.get("device_class"))
│   │   ├─► .tag("area", attributes.get("area"))
│   │   └─► .tag("location", attributes.get("location"))
│   │
│   └─► _add_event_fields(point, event_data)  # Actual data values
│       ├─► .field("state", new_state["state"])
│       ├─► .field("old_state", old_state["state"])
│       ├─► .field("attributes", json.dumps(attributes))
│       ├─► .field("context_id", context["id"])
│       ├─► .field("context_user_id", context["user_id"])
│       ├─► Extract numeric values if applicable:
│       │   ├─► .field("temperature", float(state)) if domain == "sensor"
│       │   ├─► .field("humidity", float(state)) if device_class == "humidity"
│       │   └─► .field("pressure", float(state)) if device_class == "pressure"
│       │
│       └─► return Point object
│
└─► return point
```

**InfluxDB Point Structure**:
```
Measurement: home_assistant_events
Tags (indexed):
  - entity_id: "sensor.temperature"
  - domain: "sensor"
  - event_type: "state_changed"
  - device_class: "temperature"
  - area: "living_room"
Fields (data):
  - state: "21.0"
  - old_state: "20.5"
  - temperature: 21.0 (numeric)
  - attributes: '{"unit_of_measurement":"°C",...}'
  - context_id: "01234567890abcdef"
Timestamp: 2025-10-13T10:30:00.123Z
```

---

#### 3.2 InfluxDB Batch Write

**File**: `services/websocket-ingestion/src/influxdb_batch_writer.py`

```python
InfluxDBBatchWriter.write_batch(events)
├─► for event in events:
│   ├─► point = InfluxDBSchema.create_event_point(event)
│   └─► batch_points.append(point)
│
├─► async with self.batch_lock:
│   ├─► InfluxDBConnectionManager.get_write_api()
│   │   └─► influxdb_client.write_api(
│   │         write_options=WriteOptions(
│   │           batch_size=1000,
│   │           flush_interval=5000
│   │         )
│   │       )
│   │
│   ├─► write_api.write(
│   │     bucket=self.bucket,
│   │     org=self.org,
│   │     record=batch_points,
│   │     write_precision=WritePrecision.MS
│   │   )
│   │
│   ├─► await write_api.flush()  # Ensure data is written
│   │
│   └─► on_success:
│       ├─► self.total_batches_written += 1
│       ├─► self.total_points_written += len(batch_points)
│       └─► log batch statistics
│
└─► on_error:
    ├─► retry with exponential backoff (max 3 attempts)
    ├─► self.total_points_failed += len(batch_points)
    └─► log error details
```

**Write Performance**:
- **Batch Size**: Up to 1,000 points
- **Flush Interval**: 5 seconds
- **Write Precision**: Milliseconds
- **Retry Strategy**: Exponential backoff (1s, 2s, 4s)

---

### Phase 4: Optional Enrichment Pipeline

#### 4.1 Enrichment Service Processing

**File**: `services/enrichment-pipeline/src/main.py`

```python
EnrichmentPipelineService.process_event(event_data)
├─► DataNormalizer.normalize_event(event_data)
│   ├─► DataValidator.validate_event(event_data)
│   │   ├─► Check required fields
│   │   ├─► Validate data types
│   │   ├─► Check value ranges
│   │   └─► Return ValidationResult(is_valid, errors, warnings)
│   │
│   ├─► normalized = event_data.copy()
│   │
│   ├─► _normalize_timestamps(normalized)
│   │   ├─► Convert to ISO 8601 format
│   │   ├─► Ensure UTC timezone
│   │   └─► Add "_normalized" metadata
│   │
│   ├─► _normalize_state_values(normalized)
│   │   ├─► Boolean states: "on" → True, "off" → False
│   │   ├─► Numeric states: "21.5" → 21.5 (float)
│   │   └─► String states: trim whitespace
│   │
│   ├─► _normalize_units(normalized)
│   │   ├─► Temperature: °C → celsius, °F → fahrenheit
│   │   ├─► Pressure: hPa → hectopascal
│   │   └─► Standardize unit names
│   │
│   └─► return normalized event
│
└─► InfluxDBClientWrapper.write_normalized_event(normalized)
    └─► (Similar to Phase 3 write process)
```

**Normalization Benefits**:
- **Consistent Data Types**: String → Numeric/Boolean where applicable
- **Standardized Units**: Unified unit naming conventions
- **Validation**: Early detection of data quality issues
- **Metadata**: Tracking of normalization version and timestamp

---

### Phase 5: Data Retrieval by Admin API

#### 5.1 API Request Handling

**File**: `services/admin-api/src/events_endpoints.py`

```python
EventsEndpoints (FastAPI Router)
├─► @router.get("/events")
│   └─► async def get_recent_events(
│         limit: int = 100,
│         entity_id: Optional[str] = None,
│         event_type: Optional[str] = None,
│         start_time: Optional[datetime] = None,
│         end_time: Optional[datetime] = None
│       )
│       ├─► Build EventFilter object
│       ├─► _get_all_events(filter, limit, offset)
│       │   └─► InfluxDBClientWrapper.query_events(filter)
│       │       ├─► Build Flux query
│       │       │   ```flux
│       │       │   from(bucket: "ha_events")
│       │       │     |> range(start: -1h)
│       │       │     |> filter(fn: (r) => r._measurement == "home_assistant_events")
│       │       │     |> filter(fn: (r) => r.entity_id == "sensor.temperature")
│       │       │     |> sort(columns: ["_time"], desc: true)
│       │       │     |> limit(n: 100)
│       │       │   ```
│       │       │
│       │       ├─► query_api.query(query)
│       │       ├─► Parse FluxTable results
│       │       │   ├─► Extract tags (entity_id, domain, event_type)
│       │       │   ├─► Extract fields (state, attributes)
│       │       │   ├─► Extract timestamp
│       │       │   └─► Construct EventData objects
│       │       │
│       │       └─► return List[EventData]
│       │
│       └─► return JSON response
│
└─► @router.get("/events/stats")
    └─► async def get_events_stats(period: str = "1h")
        └─► InfluxDBClientWrapper.get_event_statistics(period)
            ├─► Query: Count events by domain
            ├─► Query: Count events by type
            ├─► Query: Calculate event rate
            └─► return aggregated statistics
```

**API Response Structure**:
```json
[
  {
    "event_id": "01234567890abcdef",
    "event_type": "state_changed",
    "entity_id": "sensor.temperature",
    "domain": "sensor",
    "timestamp": "2025-10-13T10:30:00.123Z",
    "state": "21.0",
    "old_state": "20.5",
    "attributes": {
      "unit_of_measurement": "°C",
      "device_class": "temperature",
      "friendly_name": "Living Room Temperature"
    },
    "context": {
      "id": "01234567890abcdef",
      "user_id": null
    }
  }
]
```

---

#### 5.2 Statistics Aggregation

**File**: `services/admin-api/src/stats_endpoints.py`

```python
StatsEndpoints
├─► @router.get("/stats")
│   └─► async def get_statistics(period: str = "1h")
│       └─► _get_stats_from_influxdb(period)
│           ├─► get_event_statistics(period)
│           │   ├─► Flux query: Count total events
│           │   ├─► Flux query: Count by domain
│           │   ├─► Flux query: Count by event_type
│           │   └─► Flux query: Calculate percentiles (p50, p95, p99)
│           │
│           ├─► get_error_rate(period)
│           │   └─► Flux query: Error events / Total events
│           │
│           ├─► get_service_metrics(service, period)
│           │   ├─► Flux query: Event processing time
│           │   ├─► Flux query: Queue depth
│           │   └─► Flux query: Throughput rate
│           │
│           └─► Combine all metrics into response
│               └─► return {
│                     "total_events": 12500,
│                     "event_rate": 3.47,  # events/second
│                     "domains": {...},
│                     "error_rate": 0.02,  # 2%
│                     "metrics": {...}
│                   }
│
└─► @router.get("/stats/trends")
    └─► async def get_trends(period: str = "24h")
        └─► Query time-series data with window aggregation
            ├─► Flux query: Window by 5-minute intervals
            └─► Return trend data for charting
```

**Flux Query Example** (Event Count by Domain):
```flux
from(bucket: "ha_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "home_assistant_events")
  |> group(columns: ["domain"])
  |> count()
  |> group()
```

---

### Phase 6: Frontend Data Display

#### 6.1 API Service Layer

**File**: `services/health-dashboard/src/services/api.ts`

```typescript
class ApiService {
  private baseURL = 'http://localhost:8003/api';
  
  async getStatistics(period: string = '1h'): Promise<Statistics> {
    └─► fetch(`${baseURL}/stats?period=${period}`)
        ├─► Add headers: { 'Content-Type': 'application/json' }
        ├─► await response.json()
        ├─► Validate response structure
        └─► return typed Statistics object
  }
  
  async getServicesHealth(): Promise<{ [key: string]: any }> {
    └─► fetch(`${baseURL}/health/services`)
        └─► return health status for all services
  }
  
  async getRecentEvents(options: EventQueryOptions): Promise<Event[]> {
    └─► Build query string with filters
        └─► fetch(`${baseURL}/events?${queryString}`)
            └─► return typed Event[] array
  }
}

export const apiService = new ApiService();
```

---

#### 6.2 React Hooks for Data Fetching

**File**: `services/health-dashboard/src/hooks/useStatistics.ts`

```typescript
export const useStatistics = (period: string, refreshInterval: number = 60000) => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchStatistics = async () => {
    └─► try:
        ├─► setError(null)
        ├─► const statsData = await apiService.getStatistics(period)
        └─► setStatistics(statsData)
        catch:
        └─► setError(error.message)
        finally:
        └─► setLoading(false)
  };
  
  useEffect(() => {
    └─► fetchStatistics()  // Initial fetch
        └─► setInterval(fetchStatistics, refreshInterval)  // Polling
            └─► return cleanup function
  }, [period, refreshInterval]);
  
  return { statistics, loading, error, refresh: fetchStatistics };
};
```

**Hook Usage Pattern**:
```typescript
// In React Component
const { statistics, loading, error } = useStatistics('1h', 60000);

// statistics updates every 60 seconds automatically
// Component re-renders with new data
```

---

#### 6.3 Dashboard Component Rendering

**File**: `services/health-dashboard/src/components/Dashboard.tsx`

```typescript
export const Dashboard: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  
  // Real-time WebSocket connection
  const { connectionState, reconnect } = useRealtimeMetrics({ enabled: true });
  
  return (
    <div className="dashboard">
      <Header>
        ├─► ConnectionStatusIndicator (WebSocket status)
        ├─► ThemeToggle
        └─► TimeRangeSelector
      </Header>
      
      <TabNavigation>
        ├─► Tab: Overview (default)
        ├─► Tab: Custom
        ├─► Tab: Services
        ├─► Tab: Dependencies
        ├─► Tab: Devices
        ├─► Tab: Events ← Shows real-time event stream
        ├─► Tab: Logs
        ├─► Tab: Sports
        ├─► Tab: Data Sources
        ├─► Tab: Analytics
        ├─► Tab: Alerts
        └─► Tab: Configuration
      </TabNavigation>
      
      <TabContent>
        └─► {TabComponent}
            └─► Example: EventsTab
                ├─► const { events, loading } = useEvents(timeRange)
                ├─► useEffect(() => {
                │     // Fetch events on mount and time range change
                │     apiService.getRecentEvents({
                │       limit: 100,
                │       start_time: calculateStartTime(timeRange)
                │     })
                │   })
                │
                └─► return (
                      <EventTable>
                        {events.map(event => (
                          <EventRow key={event.event_id}>
                            ├─► Timestamp: {formatTimestamp(event.timestamp)}
                            ├─► Entity: {event.entity_id}
                            ├─► State: {event.old_state} → {event.state}
                            └─► Attributes: {JSON.stringify(event.attributes)}
                          </EventRow>
                        ))}
                      </EventTable>
                    )
      </TabContent>
    </div>
  );
};
```

---

#### 6.4 Real-time WebSocket Updates

**File**: `services/health-dashboard/src/hooks/useRealtimeMetrics.ts`

```typescript
export const useRealtimeMetrics = ({ enabled }: { enabled: boolean }) => {
  const [connectionState, setConnectionState] = useState<'connected' | 'disconnected'>('disconnected');
  const [realtimeData, setRealtimeData] = useState<any>(null);
  
  useEffect(() => {
    if (!enabled) return;
    
    // WebSocket connection to Admin API
    const ws = new WebSocket('ws://localhost:8003/api/ws/metrics');
    
    ws.onopen = () => {
      └─► setConnectionState('connected')
          └─► console.log('WebSocket connected')
    };
    
    ws.onmessage = (event) => {
      └─► const data = JSON.parse(event.data)
          └─► setRealtimeData(data)  // Triggers re-render
              └─► Update UI components with new data
    };
    
    ws.onerror = (error) => {
      └─► console.error('WebSocket error:', error)
          └─► setConnectionState('disconnected')
    };
    
    ws.onclose = () => {
      └─► setConnectionState('disconnected')
          └─► Attempt reconnection after delay
    };
    
    return () => ws.close();  // Cleanup
  }, [enabled]);
  
  return { connectionState, realtimeData, reconnect: () => { /* ... */ } };
};
```

**WebSocket Message Structure**:
```json
{
  "type": "metrics_update",
  "timestamp": "2025-10-13T10:30:00.123Z",
  "data": {
    "event_count": 12500,
    "event_rate": 3.47,
    "queue_depth": 42,
    "processing_time_ms": 12.5
  }
}
```

---

## 📈 Performance Characteristics

### Event Processing Throughput

| Stage | Component | Throughput | Latency | Bottleneck |
|-------|-----------|------------|---------|------------|
| **Reception** | WebSocket Client | ~10,000 events/sec | <1ms | Network bandwidth |
| **Validation** | Event Processor | ~50,000 events/sec | <0.1ms | CPU-bound |
| **Queue** | Async Queue | ~100,000 events/sec | <0.01ms | Memory-bound |
| **Batch Processing** | Batch Processor | ~20,000 events/sec | ~5ms | Wait for batch |
| **Database Write** | InfluxDB Writer | ~10,000 points/sec | ~50ms | Disk I/O |
| **API Query** | Admin API | ~1,000 queries/sec | ~20ms | InfluxDB query |
| **Dashboard Render** | React Frontend | ~60 FPS | ~16ms | Browser render |

### Memory Usage

| Component | Base Memory | Peak Memory | Notes |
|-----------|------------|-------------|-------|
| WebSocket Ingestion | 50 MB | 200 MB | Event queue size |
| Enrichment Pipeline | 30 MB | 100 MB | Normalization buffers |
| Admin API | 40 MB | 150 MB | Query result caching |
| Health Dashboard | 80 MB | 300 MB | React state + charts |
| InfluxDB | 500 MB | 2 GB | Database cache |

---

## 🔍 Key Data Structures

### Event Data Model (Throughout Pipeline)

```python
# Python (Backend Services)
{
    "event_type": "state_changed",
    "entity_id": "sensor.temperature",
    "domain": "sensor",
    "time_fired": "2025-10-13T10:30:00.123456+00:00",
    "origin": "LOCAL",
    "context": {
        "id": "01234567890abcdef",
        "user_id": None,
        "parent_id": None
    },
    "old_state": {
        "state": "20.5",
        "attributes": {
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "friendly_name": "Living Room Temperature"
        },
        "last_changed": "2025-10-13T10:25:00.000000+00:00",
        "last_updated": "2025-10-13T10:25:00.000000+00:00"
    },
    "new_state": {
        "state": "21.0",
        "attributes": {
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "friendly_name": "Living Room Temperature"
        },
        "last_changed": "2025-10-13T10:30:00.123456+00:00",
        "last_updated": "2025-10-13T10:30:00.123456+00:00"
    }
}
```

```typescript
// TypeScript (Frontend)
interface Event {
  event_id: string;
  event_type: 'state_changed' | 'call_service' | 'automation_triggered';
  entity_id: string;
  domain: string;
  timestamp: string; // ISO 8601
  state: string;
  old_state: string;
  attributes: Record<string, any>;
  context: {
    id: string;
    user_id: string | null;
  };
}
```

---

## 🚀 Optimization Points

### Current Optimizations

1. **Async Processing**: Non-blocking event handling with 10 concurrent workers
2. **Batch Writes**: Accumulate 1,000 events before writing to InfluxDB
3. **Connection Pooling**: Reuse InfluxDB connections across requests
4. **Query Caching**: Cache frequently accessed statistics in Admin API
5. **WebSocket Streaming**: Real-time updates without polling overhead
6. **React Memo**: Prevent unnecessary re-renders in dashboard components

### Potential Future Optimizations

1. **Redis Caching**: Cache hot data paths (last 1000 events, current stats)
2. **GraphQL**: Replace REST API with GraphQL for flexible queries
3. **Server-Sent Events (SSE)**: Alternative to WebSocket for one-way streaming
4. **Time-Series Downsampling**: Pre-aggregate older data for faster queries
5. **CDN for Static Assets**: Offload dashboard static files to CDN
6. **Database Sharding**: Partition InfluxDB by domain or time range

---

## 🛠️ Troubleshooting Guide

### Common Issues & Debugging

#### Issue: Events not appearing in dashboard

**Debug Steps**:
1. Check WebSocket connection: `services/websocket-ingestion/logs`
   - Look for "Connected to Home Assistant" message
   - Verify subscription confirmation

2. Check event processing: Search logs for event_id
   ```bash
   grep "entity_id" services/websocket-ingestion/logs/app.log
   ```

3. Check InfluxDB write: Query InfluxDB directly
   ```flux
   from(bucket: "ha_events")
     |> range(start: -5m)
     |> filter(fn: (r) => r._measurement == "home_assistant_events")
     |> count()
   ```

4. Check Admin API: Test endpoint directly
   ```bash
   curl http://localhost:8003/api/events?limit=10
   ```

5. Check Dashboard: Browser console for API errors
   ```javascript
   // Check Network tab in DevTools
   // Look for failed /api/events requests
   ```

---

#### Issue: High latency (events delayed)

**Debug Steps**:
1. Check queue depth:
   ```python
   # In async_event_processor.py
   logger.info(f"Queue depth: {self.event_queue.qsize()}")
   ```

2. Check batch processing time:
   ```python
   # In batch_processor.py
   logger.info(f"Batch write time: {processing_time_ms}ms")
   ```

3. Check InfluxDB performance:
   ```bash
   # InfluxDB metrics
   curl http://localhost:8086/metrics
   ```

4. Monitor system resources:
   ```bash
   docker stats
   ```

---

#### Issue: Missing data in InfluxDB

**Debug Steps**:
1. Check InfluxDB write errors:
   ```python
   # In influxdb_batch_writer.py
   logger.error(f"Write failed: {e}")
   logger.info(f"Failed points: {self.total_points_failed}")
   ```

2. Verify InfluxDB bucket exists:
   ```bash
   docker exec influxdb influx bucket list
   ```

3. Check retention policy:
   ```bash
   docker exec influxdb influx bucket find --name ha_events
   ```

4. Verify write permissions:
   ```bash
   # Test write with InfluxDB CLI
   docker exec influxdb influx write ...
   ```

---

## 📊 Monitoring & Observability

### Key Metrics to Monitor

1. **Event Processing**
   - Events received per second
   - Events processed per second
   - Events failed per second
   - Queue depth (current/max)
   - Processing latency (p50, p95, p99)

2. **Database Performance**
   - Write throughput (points/sec)
   - Query latency (ms)
   - Failed writes count
   - Disk usage

3. **API Performance**
   - Request rate (requests/sec)
   - Response time (p50, p95, p99)
   - Error rate (%)
   - Active connections

4. **Frontend Performance**
   - Page load time
   - Time to interactive
   - WebSocket connection uptime
   - API call duration

### Logging Standards

All services use structured logging with correlation IDs:

```python
log_with_context(
    logger, "INFO", "Event processed successfully",
    operation="event_processing",
    correlation_id=correlation_id,
    event_type=event_type,
    entity_id=entity_id,
    processing_time_ms=processing_time
)
```

This enables distributed tracing across the entire event flow.

---

## 🎯 Summary

This call tree demonstrates the complete journey of a Home Assistant event:

1. **WebSocket Reception** (~1ms): Event arrives from HA via WebSocket
2. **Validation & Extraction** (~0.1ms): Event data validated and structured
3. **Async Queue** (~0.01ms): Event added to processing queue
4. **Batch Accumulation** (~5s): Events accumulated into batches of 1,000
5. **Database Write** (~50ms): Batch written to InfluxDB time-series database
6. **API Query** (~20ms): Dashboard queries events via REST API
7. **Frontend Render** (~16ms): React components display events with 60 FPS

**Total End-to-End Latency**: ~5-6 seconds (dominated by batching strategy)
**Real-time Updates**: <100ms via WebSocket streaming

The system is designed for high throughput (10,000+ events/sec) with low resource usage through batching, async processing, and efficient data structures.

---

**Document Maintenance**: Update this document when:
- New services are added to the pipeline
- Event processing logic changes
- Database schema is modified
- API endpoints are added/changed
- Performance characteristics change significantly

