# Enrichment Pipeline Consolidation Analysis
## Architecture Discussion: Merge vs. Separate Services

**Document Version**: 1.0  
**Created**: 2025-10-13  
**Type**: Architecture Decision Record (ADR)  
**Status**: Discussion  

---

## 🎯 Executive Summary

This document analyzes the architectural trade-offs of **merging the enrichment-pipeline service into websocket-ingestion** versus maintaining them as **separate microservices**.

**Current State**: Two separate services communicating via HTTP  
**Proposed State**: Single consolidated service with inline processing  
**Recommendation**: See "Decision Matrix" section below

---

## 📊 Current Architecture

### Service Separation

```
┌─────────────────────────────────────────┐
│ WebSocket Ingestion Service            │
│ - WebSocket connection to HA            │
│ - Event reception & validation          │
│ - Weather enrichment (inline)           │
│ - Batch processing                      │
│ - Direct InfluxDB write                 │
│ - HTTP POST to enrichment-pipeline      │
└────────────────┬────────────────────────┘
                 │ HTTP (async, non-blocking)
                 ▼
┌─────────────────────────────────────────┐
│ Enrichment Pipeline Service             │
│ - Data normalization                    │
│ - Data validation                       │
│ - Quality metrics collection            │
│ - Quality alerts                        │
│ - Secondary InfluxDB write              │
└─────────────────────────────────────────┘
```

**Communication**: HTTP POST requests (async, fire-and-forget)  
**Failure Mode**: Circuit breaker pattern, continues without enrichment  
**Resource Usage**: 2 separate containers, independent scaling

---

## 🔀 Proposed Architecture

### Consolidated Service

```
┌─────────────────────────────────────────────────────┐
│ WebSocket Ingestion Service (Consolidated)         │
│ ┌─────────────────────────────────────────────────┐ │
│ │ WebSocket Layer                                 │ │
│ │ - Connection to HA                              │ │
│ │ - Event subscription                            │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Processing Pipeline (Sequential)                │ │
│ │ 1. Event validation                             │ │
│ │ 2. Weather enrichment                           │ │
│ │ 3. Data normalization    ← Merged               │ │
│ │ 4. Data validation       ← Merged               │ │
│ │ 5. Quality metrics       ← Merged               │ │
│ │ 6. Batch accumulation                           │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Storage Layer                                   │ │
│ │ - Single InfluxDB write path                    │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Communication**: Internal function calls (no network overhead)  
**Failure Mode**: All-or-nothing (enrichment failures affect ingestion)  
**Resource Usage**: 1 container, simpler deployment

---

## ✅ Pros of Consolidation

### 1. **Performance Improvements**

#### Elimination of Network Overhead
- **Remove HTTP serialization/deserialization**: ~2-5ms saved per event
- **No TCP/IP stack overhead**: ~1-3ms saved per event
- **No circuit breaker checks**: ~0.1ms saved per event
- **Direct memory access**: Zero-copy data transfer between stages

**Estimated Performance Gain**: 3-8ms per event (5-15% improvement)

```python
# Before (HTTP call)
async def _process_batch(batch):
    for event in batch:
        await self.http_client.send_event(event)  # Network call: ~5ms
        
# After (inline call)
async def _process_batch(batch):
    for event in batch:
        normalized = self.normalizer.normalize_event(event)  # Direct call: ~0.1ms
```

#### Reduced Latency
- **Current**: Event → Validate → Queue → Batch → HTTP → Normalize → Validate → DB
- **Proposed**: Event → Validate → Normalize → Validate → Queue → Batch → DB
- **Latency Reduction**: ~5-10ms (HTTP roundtrip eliminated)

---

### 2. **Simplified Architecture**

#### Deployment Complexity
- **Fewer containers**: 11 services instead of 12
- **No HTTP client configuration**: Remove circuit breaker, retry logic
- **Single health check**: One service to monitor instead of two
- **Simplified Docker Compose**: Fewer service definitions, port mappings

```yaml
# Before: 2 services
services:
  websocket-ingestion:
    depends_on: [influxdb, enrichment-pipeline]
    environment:
      - ENRICHMENT_SERVICE_URL=http://enrichment-pipeline:8002
  
  enrichment-pipeline:
    depends_on: [influxdb]

# After: 1 service
services:
  websocket-ingestion:
    depends_on: [influxdb]
```

#### Code Simplicity
- **Remove HTTP client code**: ~300 lines eliminated
- **Remove circuit breaker logic**: ~150 lines eliminated
- **Remove async HTTP handling**: ~100 lines eliminated
- **Direct function calls**: Simpler error handling

---

### 3. **Resource Efficiency**

#### Memory Usage
- **Current**: 
  - websocket-ingestion: ~200 MB peak
  - enrichment-pipeline: ~100 MB peak
  - **Total**: ~300 MB
- **Proposed**: 
  - Consolidated service: ~250 MB peak
  - **Savings**: ~50 MB (17% reduction)

#### CPU Usage
- **Eliminate HTTP processing overhead**: ~5-10% CPU saved
- **No context switching between containers**: Improved CPU cache utilization
- **Shared thread pools**: Better resource utilization

#### Network Bandwidth
- **Current**: ~100 events/sec × 5 KB/event = 500 KB/s internal traffic
- **Proposed**: 0 KB/s internal traffic (in-process communication)

---

### 4. **Operational Simplicity**

#### Monitoring
- **Single service to monitor**: Consolidated metrics, logs
- **Unified health checks**: One endpoint instead of two
- **Simpler alerting**: Fewer alert rules to configure
- **Centralized logging**: All processing in one log stream

#### Debugging
- **Single codebase**: Easier to trace event flow
- **No distributed tracing complexity**: All in-process
- **Single correlation ID**: Simpler tracking
- **Stack traces span entire pipeline**: Better error context

---

### 5. **Transactional Consistency**

#### Atomic Operations
- **Current**: Event written twice to InfluxDB (potential inconsistency)
- **Proposed**: Single write operation (guaranteed consistency)
- **No dual-write problem**: Eliminates race conditions

#### Error Handling
- **Current**: Event may be in DB without enrichment (inconsistent state)
- **Proposed**: Event fully processed or not at all (consistent state)

```python
# Before: Potential inconsistency
await influxdb.write(raw_event)  # Write 1 (always happens)
await http_client.send(event)     # May fail
# enrichment-pipeline writes event again (may or may not happen)

# After: Atomic operation
try:
    normalized = normalizer.normalize(event)
    validated = validator.validate(normalized)
    await influxdb.write(validated)  # Single write
except Exception:
    # Event not written at all - consistent failure
```

---

### 6. **Development Velocity**

#### Faster Development
- **Single repository**: Shared types, no API contract changes
- **Immediate testing**: No need to start two services for testing
- **Single deployment**: Faster CI/CD pipeline
- **Shared dependencies**: No version mismatch issues

#### Easier Refactoring
- **Internal interfaces**: Can change without breaking compatibility
- **Type safety**: Compile-time checks across entire pipeline
- **Shared code**: No duplication of validation logic

---

## ❌ Cons of Consolidation

### 1. **Reduced Scalability**

#### Loss of Independent Scaling

**Current Capability**:
```yaml
# Scale services independently based on load
docker-compose up --scale websocket-ingestion=1 --scale enrichment-pipeline=5
```

**Problem**: Enrichment is CPU-intensive (normalization, validation), WebSocket reception is I/O-intensive

**Scenarios**:
- **High event rate, simple events**: Need more WebSocket capacity, not enrichment
- **Low event rate, complex events**: Need more enrichment capacity, not WebSocket
- **After consolidation**: Must scale entire service (wasteful)

**Impact Analysis**:
- **Current**: Can allocate resources precisely based on bottleneck
- **Proposed**: Over-provision resources for both workload types
- **Cost**: Potentially 20-30% higher resource usage at scale

---

### 2. **Tight Coupling**

#### Single Responsibility Principle Violation

**WebSocket Ingestion Concerns**:
1. WebSocket connection management
2. Event subscription
3. Connection retry logic
4. Health monitoring

**Enrichment Pipeline Concerns**:
1. Data normalization
2. Data validation
3. Quality metrics
4. Quality alerts

**After Consolidation**: One service doing two distinct jobs

#### Change Impact
- **Current**: Change normalization logic → only enrichment-pipeline affected
- **Proposed**: Change normalization logic → entire ingestion service restarts
- **Risk**: Higher blast radius for changes

---

### 3. **Failure Domain Expansion**

#### Blast Radius

**Current**:
```
Enrichment bug → enrichment-pipeline crashes → ingestion continues
                                                events still captured
                                                
Ingestion bug → websocket-ingestion crashes → enrichment idle
                                               no events captured (acceptable)
```

**Proposed**:
```
Enrichment bug → entire service crashes → NO events captured (critical)
                                          HA disconnected
                                          data loss occurs
```

#### Critical Path Addition
- **Current**: Enrichment on non-critical path (optional enhancement)
- **Proposed**: Enrichment on critical path (required for ingestion)
- **Availability Impact**: Potentially lower system availability

**Example Scenario**:
```python
# Normalization bug causes crash
def normalize_event(event):
    # Bug: crashes on unexpected data
    value = float(event['state'])  # TypeError if state is "unavailable"
    
# Current: Only enrichment-pipeline crashes, ingestion continues
# Proposed: Entire ingestion stops, HA events lost
```

---

### 4. **Testing Complexity**

#### Unit Testing Challenges

**Current**:
```python
# Test enrichment in isolation
def test_normalization():
    normalizer = DataNormalizer()
    result = normalizer.normalize_event(sample_event)
    assert result['temperature'] == 21.0
```

**Proposed**:
```python
# Must mock entire WebSocket infrastructure
def test_normalization():
    # Need WebSocket connection, event queue, batch processor...
    service = WebSocketIngestionService()
    await service.start()  # Heavy setup
    # Test normalization
    await service.stop()   # Heavy teardown
```

#### Integration Testing

**Current**: Test services independently
- WebSocket → Mock HTTP client → Verify InfluxDB write
- HTTP endpoint → Enrichment logic → Verify InfluxDB write

**Proposed**: Must test entire pipeline together
- More complex test setup
- Slower test execution
- Harder to isolate failures

---

### 5. **Reusability Loss**

#### Enrichment as a Service

**Current**: Enrichment pipeline can process events from ANY source
```
Home Assistant → WebSocket Ingestion → Enrichment Pipeline
MQTT Broker → MQTT Ingestion → Enrichment Pipeline
REST API → API Gateway → Enrichment Pipeline
```

**Proposed**: Enrichment locked to WebSocket ingestion only
- **Cannot reuse for other data sources**
- **Cannot share enrichment logic across ingestion methods**

#### Multiple Consumers

**Current**: Multiple services can use enrichment
```
┌─────────────────┐
│ WS Ingestion    │──┐
└─────────────────┘  │
                     ├─► Enrichment Pipeline ─► InfluxDB
┌─────────────────┐  │
│ Batch Importer  │──┘
└─────────────────┘
```

**Proposed**: Enrichment logic duplicated or not available
- **Code duplication if needed elsewhere**
- **Maintenance burden increases**

---

### 6. **Language/Technology Lock-in**

#### Current Flexibility

**Current**: Services can use different languages/frameworks
- websocket-ingestion: Python + aiohttp (best for async WebSocket)
- enrichment-pipeline: Could be Go/Rust/Java (best for CPU-intensive processing)

**Proposed**: Must use same language/framework
- **Cannot optimize per-service**: Stuck with Python for CPU-intensive work
- **Performance ceiling**: Python GIL limits parallel normalization

---

### 7. **Resource Isolation Loss**

#### Memory Limits

**Current**:
```yaml
websocket-ingestion:
  deploy:
    resources:
      limits:
        memory: 512M  # Bounded memory for WebSocket
        
enrichment-pipeline:
  deploy:
    resources:
      limits:
        memory: 2G    # More memory for processing
```

**Proposed**: Shared memory pool
- **Memory leak in enrichment affects WebSocket**: Connection drops
- **Cannot set different limits**: One size fits all
- **OOM kills entire service**: Loss of critical ingestion

#### CPU Scheduling

**Current**: Services scheduled independently
- WebSocket can have higher priority (I/O-bound)
- Enrichment can have lower priority (CPU-bound)

**Proposed**: Shared CPU scheduling
- **CPU-intensive normalization blocks WebSocket I/O**
- **Cannot prioritize critical path**

---

### 8. **Deployment Complexity**

#### Version Management

**Current**: Independent versioning
```
websocket-ingestion:1.5.0  ← Can deploy independently
enrichment-pipeline:2.3.1  ← Different version, different cadence
```

**Proposed**: Coupled versioning
- **Must version together**: Slower release cycle
- **Cannot hotfix enrichment only**: Must redeploy everything
- **Rollback complexity**: All-or-nothing rollback

#### Deployment Risk

**Current**: Can deploy enrichment changes with low risk
```bash
# Low risk: Only affects data quality, not ingestion
docker-compose up -d enrichment-pipeline
```

**Proposed**: Every deployment affects critical path
```bash
# High risk: Affects event ingestion
docker-compose up -d websocket-ingestion
# If this fails, HA events are lost
```

---

### 9. **Observability Challenges**

#### Metrics Separation

**Current**: Clear metrics per service
```
# WebSocket metrics
ws_events_received_total
ws_connection_uptime
ws_reconnection_count

# Enrichment metrics
enrich_normalization_duration
enrich_validation_errors
enrich_quality_score
```

**Proposed**: Mixed metrics
- **Harder to identify bottlenecks**: Is CPU from WebSocket or enrichment?
- **Cannot monitor separately**: No isolation
- **Alert fatigue**: Single service, many failure modes

#### Log Correlation

**Current**: Separate log streams
```
[websocket-ingestion] Event received
[enrichment-pipeline] Normalization started
[enrichment-pipeline] Validation failed
```

**Proposed**: Interleaved logs
```
[ingestion] Event received
[ingestion] WebSocket message processed
[ingestion] Normalization started
[ingestion] Queue depth: 5000
[ingestion] Validation failed
[ingestion] Batch written to InfluxDB
```
- **Harder to filter**: All logs mixed together
- **Log volume explosion**: Single service, many concerns

---

## 📊 Decision Matrix

### Quantitative Comparison

| Factor | Current (Separate) | Proposed (Merged) | Winner |
|--------|-------------------|-------------------|--------|
| **Performance** |
| Event Processing Latency | 5-6 seconds | 5-5.5 seconds | Merged (+8%) |
| Network Overhead | 5ms/event | 0ms/event | Merged (100% reduction) |
| CPU Usage | 100% baseline | 90-95% | Merged (5-10% reduction) |
| Memory Usage | 300 MB | 250 MB | Merged (17% reduction) |
| **Scalability** |
| Independent Scaling | ✅ Yes | ❌ No | Separate |
| Scale Efficiency | High | Low | Separate |
| Resource Utilization | 70-80% | 60-70% | Separate |
| **Reliability** |
| Service Availability | 99.5% each | 99.0% combined | Separate |
| Failure Isolation | ✅ Yes | ❌ No | Separate |
| Blast Radius | Small | Large | Separate |
| **Complexity** |
| Deployment Complexity | Medium | Low | Merged |
| Code Complexity | Medium | Low | Merged |
| Testing Complexity | Low | High | Separate |
| **Maintainability** |
| Service Count | 12 | 11 | Merged |
| Lines of Code | 5,000 + 3,000 | 7,500 | Merged (500 lines saved) |
| Debugging Difficulty | Medium | Low | Merged |
| **Flexibility** |
| Reusability | ✅ High | ❌ Low | Separate |
| Technology Choice | ✅ Flexible | ❌ Locked | Separate |
| Version Independence | ✅ Yes | ❌ No | Separate |

---

## 🎯 Recommendation by Scenario

### Scenario 1: Small-Scale Deployment (< 1,000 events/sec)

**Recommendation**: **MERGE** (Consolidated Service)

**Rationale**:
- ✅ Scalability not a concern at this volume
- ✅ Simpler deployment (fewer resources)
- ✅ Lower operational overhead
- ✅ Performance gains more noticeable
- ❌ Failure isolation less critical (can recover quickly)

**Implementation**:
```python
class WebSocketIngestionService:
    def __init__(self):
        self.normalizer = DataNormalizer()
        self.validator = DataValidator()
        self.quality_metrics = QualityMetricsCollector()
    
    async def _process_event(self, event):
        # Inline enrichment
        normalized = self.normalizer.normalize_event(event)
        validated = self.validator.validate_event(normalized)
        self.quality_metrics.record(validated)
        
        await self.influxdb.write(validated)
```

---

### Scenario 2: Medium-Scale Deployment (1,000 - 10,000 events/sec)

**Recommendation**: **HYBRID** (Configurable)

**Rationale**:
- Make enrichment pipeline optional with configuration
- Default to inline for simplicity
- Allow separate service for scaling if needed

**Implementation**:
```python
class WebSocketIngestionService:
    def __init__(self):
        self.enrichment_mode = os.getenv('ENRICHMENT_MODE', 'inline')
        
        if self.enrichment_mode == 'inline':
            self.enricher = InlineEnricher()  # Direct function calls
        elif self.enrichment_mode == 'service':
            self.enricher = RemoteEnricher()  # HTTP calls
    
    async def _process_event(self, event):
        enriched = await self.enricher.enrich(event)
        await self.influxdb.write(enriched)
```

**Configuration**:
```yaml
# docker-compose.yml
websocket-ingestion:
  environment:
    - ENRICHMENT_MODE=inline  # or 'service'
    
# Only needed if ENRICHMENT_MODE=service
enrichment-pipeline:
  profiles: ["scaling"]  # Optional service
```

---

### Scenario 3: Large-Scale Deployment (> 10,000 events/sec)

**Recommendation**: **KEEP SEPARATE** (Current Architecture)

**Rationale**:
- ✅ Independent scaling is critical
- ✅ Failure isolation necessary
- ✅ Can optimize each service differently
- ❌ Network overhead negligible at scale
- ❌ Operational complexity worth the trade-off

**Additional Considerations**:
- Consider adding load balancer for enrichment-pipeline
- Implement async queue (RabbitMQ/Kafka) between services
- Add caching layer for enrichment results

```
┌──────────────┐
│ WS Ingestion │──► RabbitMQ ──► Multiple Enrichment Workers ──► InfluxDB
└──────────────┘                  (Auto-scaled: 1-10 instances)
```

---

### Scenario 4: Development/Testing Environment

**Recommendation**: **MERGE** (Consolidated Service)

**Rationale**:
- ✅ Faster startup (one container)
- ✅ Simpler debugging
- ✅ Lower resource usage
- ✅ Easier to run locally

**Implementation**:
```bash
# docker-compose.dev.yml
services:
  websocket-ingestion:
    build:
      context: .
      dockerfile: Dockerfile.dev
    environment:
      - ENRICHMENT_MODE=inline
    # No enrichment-pipeline service needed
```

---

## 🏗️ Migration Strategy (If Merging)

### Phase 1: Preparation (Week 1)

1. **Create abstraction layer**:
   ```python
   class EnrichmentInterface(ABC):
       @abstractmethod
       async def enrich(self, event) -> dict:
           pass
   
   class InlineEnricher(EnrichmentInterface):
       # Direct function calls
       pass
   
   class HTTPEnricher(EnrichmentInterface):
       # HTTP calls to separate service
       pass
   ```

2. **Add configuration flag**: `ENRICHMENT_MODE=inline|service`

3. **Implement inline enricher**: Copy enrichment logic into websocket-ingestion

4. **Add feature toggle**: Default to `service` mode (no behavior change)

### Phase 2: Testing (Week 2)

1. **Unit tests**: Test inline enricher in isolation
2. **Integration tests**: Test with `ENRICHMENT_MODE=inline`
3. **Performance tests**: Compare inline vs. service mode
4. **Load tests**: Verify throughput with inline enrichment

### Phase 3: Gradual Rollout (Week 3-4)

1. **Deploy to dev**: Enable inline mode in development
2. **Monitor metrics**: CPU, memory, latency, error rates
3. **Deploy to staging**: Enable inline mode in staging
4. **Canary deployment**: 10% of production traffic
5. **Full rollout**: 100% of production traffic

### Phase 4: Cleanup (Week 5)

1. **Remove HTTP client code**
2. **Remove enrichment-pipeline service**
3. **Update documentation**
4. **Archive old service code**

### Rollback Plan

At any point, revert by:
```bash
# Switch back to service mode
export ENRICHMENT_MODE=service

# Restart enrichment-pipeline
docker-compose up -d enrichment-pipeline

# No code changes needed (abstraction layer)
```

---

## 📈 Performance Projections

### Expected Performance Changes After Merge

| Metric | Current | Projected | Change |
|--------|---------|-----------|--------|
| Avg Latency | 5.5s | 5.0s | -9% |
| P95 Latency | 8.0s | 7.5s | -6% |
| P99 Latency | 12.0s | 11.5s | -4% |
| Throughput | 10K events/s | 10.5K events/s | +5% |
| CPU Usage | 100% | 92% | -8% |
| Memory Usage | 300 MB | 250 MB | -17% |
| Network I/O | 500 KB/s | 0 KB/s | -100% |

### Break-Even Analysis

**Cost Savings**:
- Reduced memory: 50 MB × $0.01/MB/month = $0.50/month
- Reduced CPU: 8% × $50/month = $4/month
- Reduced network: Negligible
- **Total Savings**: ~$4.50/month

**Cost Increases**:
- Potential over-provisioning at scale: +20-30% resources
- At 10K events/sec: +$15/month

**Break-Even**: ~5,000 events/sec
- Below: Merged is cheaper
- Above: Separate is cheaper

---

## 🤔 Alternative Architectures

### Option 1: Hybrid - Optional Enrichment

Keep enrichment as optional but make it a library:

```python
# shared/enrichment_lib.py
class EnrichmentLibrary:
    """Shared enrichment logic"""
    pass

# websocket-ingestion
from shared.enrichment_lib import EnrichmentLibrary
enricher = EnrichmentLibrary()
enriched = enricher.normalize(event)

# enrichment-pipeline (if needed for other sources)
from shared.enrichment_lib import EnrichmentLibrary
# Expose via HTTP API
```

**Pros**: Code reuse, optional scaling  
**Cons**: Requires Python for all services

---

### Option 2: Message Queue Pattern

Decouple with asynchronous queue:

```
WS Ingestion → RabbitMQ → Enrichment Workers → InfluxDB
                  ↓
              Direct write (fallback)
```

**Pros**: Complete decoupling, backpressure handling  
**Cons**: Additional component (RabbitMQ), increased complexity

---

### Option 3: Sidecar Pattern

Deploy enrichment as sidecar container:

```yaml
websocket-ingestion:
  sidecars:
    - enrichment-sidecar:
        communication: localhost (fast)
        lifecycle: coupled
        scaling: together
```

**Pros**: Fast communication, logical separation  
**Cons**: Still two containers, complex orchestration

---

## 📝 Final Recommendation

### For Your System (HA Ingestor)

**Recommendation**: **KEEP SEPARATE** but add **INLINE MODE** as option

**Rationale**:
1. **Current scale**: 1-2K events/sec (medium scale)
2. **Growth potential**: May need independent scaling
3. **Failure criticality**: Event loss is unacceptable
4. **Development flexibility**: Want to iterate on enrichment independently

### Implementation Plan

**Short-term** (1-2 weeks):
1. Add `ENRICHMENT_MODE` configuration flag
2. Implement inline enrichment as option
3. Default to separate services (current behavior)

**Medium-term** (1-3 months):
1. Monitor usage patterns (is enrichment CPU-bound?)
2. Collect metrics on scaling needs
3. Test inline mode in development

**Long-term** (3-6 months):
1. Make decision based on actual usage data
2. If inline mode works well, deprecate separate service
3. If scaling issues arise, keep separate and add queue

### Configuration Recommendation

```yaml
# docker-compose.yml
services:
  websocket-ingestion:
    environment:
      # 'inline' = merged, 'service' = separate, 'disabled' = no enrichment
      - ENRICHMENT_MODE=service  # Current default
      
      # Only used if ENRICHMENT_MODE=service
      - ENRICHMENT_SERVICE_URL=http://enrichment-pipeline:8002
      
  enrichment-pipeline:
    # Mark as optional
    profiles: ["full", "production"]
    # Can be disabled in dev with: docker-compose --profile dev up
```

This gives you **flexibility to choose** based on environment and needs without major code changes.

---

## 🎓 Key Takeaways

### When to Merge
- ✅ Small scale (< 1,000 events/sec)
- ✅ Simple deployment preferred
- ✅ Development/testing environments
- ✅ Resource-constrained environments
- ✅ Tight coupling acceptable

### When to Keep Separate
- ✅ Large scale (> 10,000 events/sec)
- ✅ Independent scaling required
- ✅ High availability critical
- ✅ Multiple data sources use enrichment
- ✅ Different teams maintain services

### The Gray Area (1,000 - 10,000 events/sec)
- 🤷 Make it configurable
- 🤷 Monitor and decide based on data
- 🤷 Start simple (merged), split if needed

---

## 📚 References

- Martin Fowler: "Microservices Trade-Offs" - https://martinfowler.com/articles/microservice-trade-offs.html
- AWS: "When to Use Microservices (and When Not To!)" - https://aws.amazon.com/blogs/architecture/
- Google SRE Book: "Simplicity" - https://sre.google/sre-book/simplicity/
- "Monolith First" by Martin Fowler - https://martinfowler.com/bliki/MonolithFirst.html

---

**Document Maintenance**: Update when:
- System scale changes significantly
- New requirements emerge (e.g., multiple data sources)
- Performance characteristics change
- Team structure changes (microservices need separate teams)

