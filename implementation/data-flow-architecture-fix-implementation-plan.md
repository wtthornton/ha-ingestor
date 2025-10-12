# Data Flow Architecture Fix - Implementation Plan

**Project:** HA Ingestor - Admin API InfluxDB Integration  
**Date:** October 12, 2025  
**Status:** Ready for Implementation  
**Est. Duration:** 3-4 weeks  
**Priority:** High

---

## Executive Summary

### Problem
The current architecture has Admin API and Dashboard receiving data directly from the Enrichment Pipeline via HTTP calls, bypassing InfluxDB. This creates scalability issues, prevents historical analysis, and underutilizes the time-series database.

### Solution
Refactor Admin API to query InfluxDB for all statistics and metrics, establishing InfluxDB as the single source of truth for time-series data.

### Expected Benefits
- ✅ Access to historical data and trends
- ✅ Improved performance (database queries vs HTTP calls)
- ✅ Better scalability
- ✅ Reduced service coupling
- ✅ Consistent data across all consumers

---

## Architecture Overview

### Current (Incorrect) Flow
```
Enrichment Pipeline → [HTTP] → Admin API
Enrichment Pipeline → [HTTP] → Dashboard
Enrichment Pipeline → [Write] → InfluxDB (write-only)
```

### Target (Correct) Flow
```
All Services → [Write] → InfluxDB
InfluxDB → [Query] → Admin API
Admin API → [REST] → Dashboard
```

---

## Phase 1: Research & Planning ✅ COMPLETE

### Duration: Week 1 - Day 1-2

#### Tasks Completed
- [x] Research InfluxDB Python client best practices
- [x] Document query patterns for time-series aggregation
- [x] Analyze current data flow
- [x] Create architecture diagrams
- [x] Document findings in Context7 KB

#### Deliverables
- ✅ `docs/kb/context7-cache/influxdb-admin-api-query-patterns.md`
- ✅ `docs/kb/context7-cache/data-flow-architecture-fix-pattern.md`
- ✅ Updated `docs/kb/context7-cache/index.yaml`
- ✅ This implementation plan

---

## Phase 2: Infrastructure Setup

### Duration: Week 1 - Day 3-5

### 2.1 Add InfluxDB Client to Admin API

**File:** `services/admin-api/requirements.txt`

```diff
+ # InfluxDB client
+ influxdb-client==1.38.0
```

**Installation:**
```bash
cd services/admin-api
pip install influxdb-client==1.38.0
pip freeze > requirements-prod.txt
```

### 2.2 Create InfluxDB Client Class

**File:** `services/admin-api/src/influxdb_client.py` (NEW)

Create the `AdminAPIInfluxDBClient` class with:
- Connection management
- Query methods for statistics
- Error handling
- Performance tracking
- Connection health checks

**Reference:** See `docs/kb/context7-cache/influxdb-admin-api-query-patterns.md` for complete implementation.

### 2.3 Update Environment Configuration

**File:** `infrastructure/env.example`

```bash
# InfluxDB Configuration (Add if missing)
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=ha-ingestor
INFLUXDB_BUCKET=home_assistant_events
```

### 2.4 Add Connection Initialization

**File:** `services/admin-api/src/main.py`

```python
# Add startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Admin API service...")
    
    # Initialize InfluxDB connection
    try:
        await admin_api_service.stats_endpoints.initialize_influxdb()
        logger.info("InfluxDB connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize InfluxDB: {e}")
        # Don't fail startup - fallback will handle it

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Admin API service...")
    
    # Close InfluxDB connection
    try:
        await admin_api_service.stats_endpoints.close_influxdb()
    except Exception as e:
        logger.error(f"Error closing InfluxDB: {e}")
```

### Success Criteria
- ✅ InfluxDB client package installed
- ✅ Client class created and tested
- ✅ Connection established successfully
- ✅ Health check passing

---

## Phase 3: Refactor Statistics Endpoints

### Duration: Week 2

### 3.1 Update StatsEndpoints Class

**File:** `services/admin-api/src/stats_endpoints.py`

#### Current Implementation (to replace):
```python
class StatsEndpoints:
    def __init__(self):
        self.router = APIRouter()
        self.service_urls = {
            "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://localhost:8001"),
            "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://localhost:8002")
        }
```

#### New Implementation:
```python
class StatsEndpoints:
    def __init__(self):
        self.router = APIRouter()
        self.influxdb_client = AdminAPIInfluxDBClient()
        self.use_influxdb = os.getenv("USE_INFLUXDB_STATS", "true") == "true"
        
        # Keep old service URLs for fallback
        self.service_urls = {
            "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://localhost:8001"),
            "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://localhost:8002")
        }
        
        self._add_routes()
    
    async def initialize_influxdb(self):
        """Initialize InfluxDB connection"""
        try:
            success = await self.influxdb_client.connect()
            if not success:
                logger.warning("InfluxDB connection failed, will use fallback")
                self.use_influxdb = False
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            self.use_influxdb = False
    
    async def close_influxdb(self):
        """Close InfluxDB connection"""
        await self.influxdb_client.close()
```

### 3.2 Refactor /stats Endpoint

#### Before:
```python
@self.router.get("/stats", response_model=StatisticsResponse)
async def get_statistics(period: str = Query("1h")):
    """Get comprehensive statistics"""
    try:
        if service and service in self.service_urls:
            stats = await self._get_service_stats(service, period)
        else:
            stats = await self._get_all_stats(period)  # HTTP calls to services
        
        return StatisticsResponse(...)
```

#### After:
```python
@self.router.get("/stats", response_model=StatisticsResponse)
async def get_statistics(period: str = Query("1h")):
    """Get comprehensive statistics from InfluxDB"""
    try:
        # Query InfluxDB for all stats
        stats = await self._get_stats_from_influxdb(period)
        
        return StatisticsResponse(
            timestamp=datetime.now(),
            period=period,
            metrics=stats["metrics"],
            trends=stats["trends"],
            alerts=stats["alerts"],
            source="influxdb"
        )
    except Exception as e:
        logger.error(f"Error getting statistics from InfluxDB: {e}")
        
        # Fallback to service calls if InfluxDB fails
        logger.warning("Falling back to direct service calls")
        stats = await self._get_stats_from_services(period)
        stats["source"] = "services-fallback"
        return StatisticsResponse(**stats)
```

### 3.3 Implement InfluxDB Query Methods

Add these new methods to `StatsEndpoints`:

```python
async def _get_stats_from_influxdb(self, period: str) -> Dict[str, Any]:
    """Get all statistics from InfluxDB"""
    
    # Get event statistics
    event_stats = await self.influxdb_client.get_event_statistics(period)
    
    # Get error rate
    error_stats = await self.influxdb_client.get_error_rate(period)
    
    # Get service metrics
    service_stats = await self.influxdb_client.get_all_service_statistics(period)
    
    # Get trends
    trends = await self.influxdb_client.get_event_trends(period, window="5m")
    
    # Get alerts (calculate from metrics)
    alerts = self._calculate_alerts(service_stats, error_stats)
    
    return {
        "metrics": {
            **event_stats,
            **error_stats,
            "services": service_stats["services"]
        },
        "trends": trends["trends"],
        "alerts": alerts
    }

async def _get_stats_from_services(self, period: str) -> Dict[str, Any]:
    """Fallback: Get stats from direct service calls (old method)"""
    # Keep existing implementation as fallback
    return await self._get_all_stats(period)

def _calculate_alerts(self, service_stats: Dict, error_stats: Dict) -> List[Dict]:
    """Calculate alerts from metrics"""
    alerts = []
    
    # High error rate alert
    if error_stats.get("error_rate_percent", 0) > 5:
        alerts.append({
            "level": "error",
            "service": "system",
            "message": f"High error rate: {error_stats['error_rate_percent']}%",
            "timestamp": datetime.now().isoformat()
        })
    
    # Service health alerts
    for service, metrics in service_stats.get("services", {}).items():
        if metrics.get("success_rate", 100) < 95:
            alerts.append({
                "level": "warning",
                "service": service,
                "message": f"Low success rate: {metrics['success_rate']}%",
                "timestamp": datetime.now().isoformat()
            })
    
    return alerts
```

### 3.4 Update Other Statistics Endpoints

Apply similar patterns to:
- `/stats/services` - Query service metrics from InfluxDB
- `/stats/metrics` - Query specific metrics from InfluxDB
- `/stats/performance` - Calculate from InfluxDB data
- `/stats/alerts` - Derive from InfluxDB metrics

### Success Criteria
- ✅ All /stats endpoints use InfluxDB
- ✅ Fallback mechanism working
- ✅ Proper error handling
- ✅ Response format unchanged (backward compatible)

---

## Phase 4: Update Health Endpoints

### Duration: Week 2

### 4.1 Refactor Health Metrics

**File:** `services/admin-api/src/health_endpoints.py`

Update health checks to include InfluxDB metrics:

```python
async def _get_detailed_health(self):
    """Get detailed health status including InfluxDB metrics"""
    
    # Get InfluxDB stats
    try:
        influx_stats = await self.stats_endpoints.influxdb_client.get_event_statistics("5m")
        events_per_minute = influx_stats.get("events_per_minute", 0)
    except Exception as e:
        logger.warning(f"Could not get InfluxDB stats for health: {e}")
        events_per_minute = 0
    
    # Rest of health check implementation...
```

### Success Criteria
- ✅ Health endpoint includes InfluxDB metrics
- ✅ No breaking changes to health response format

---

## Phase 5: Update Dashboard Visualization

### Duration: Week 2

### 5.1 Fix Data Flow Diagram

**File:** `services/health-dashboard/src/components/AnimatedDependencyGraph.tsx`

Update the data flow arrows to show correct architecture:

```typescript
// Current (incorrect) connections:
// Enrichment Pipeline -> Admin API
// Enrichment Pipeline -> Dashboard

// Change to (correct) connections:
// Enrichment Pipeline -> InfluxDB
// InfluxDB -> Admin API
// Admin API -> Dashboard
```

Update the `connections` array:

```typescript
const connections = [
  // ... existing connections ...
  
  // FIX: Remove these incorrect connections
  // { from: "enrichment-pipeline", to: "admin-api", type: "api" },
  // { from: "enrichment-pipeline", to: "dashboard", type: "api" },
  
  // ADD: Correct connections
  { from: "enrichment-pipeline", to: "influxdb", type: "storage", active: true },
  { from: "influxdb", to: "admin-api", type: "query", active: true },
  { from: "admin-api", to: "dashboard", type: "api", active: true },
];
```

### 5.2 Update Flow Legend

Update legend to show query operations:

```typescript
<div className="flex items-center gap-4">
  <div className="flex items-center gap-2">
    <div className="w-8 h-0.5 bg-purple-500"></div>
    <span>Storage (Write)</span>
  </div>
  <div className="flex items-center gap-2">
    <div className="w-8 h-0.5 bg-yellow-500"></div>
    <span>Query (Read)</span>
  </div>
  <div className="flex items-center gap-2">
    <div className="w-8 h-0.5 bg-blue-500"></div>
    <span>WebSocket</span>
  </div>
</div>
```

### Success Criteria
- ✅ Data flow diagram shows correct architecture
- ✅ InfluxDB shown as central data store
- ✅ Admin API shown querying InfluxDB
- ✅ Dashboard shown calling Admin API

---

## Phase 6: Testing

### Duration: Week 3

### 6.1 Unit Tests

**File:** `services/admin-api/tests/test_influxdb_client.py` (NEW)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.influxdb_client import AdminAPIInfluxDBClient

@pytest.mark.asyncio
async def test_connect_success():
    """Test successful InfluxDB connection"""
    client = AdminAPIInfluxDBClient()
    success = await client.connect()
    assert success is True
    assert client.client is not None

@pytest.mark.asyncio
async def test_get_event_statistics():
    """Test event statistics query"""
    client = AdminAPIInfluxDBClient()
    client.query_api = AsyncMock()
    client.query_api.query.return_value = [
        MagicMock(records=[MagicMock(values={"_value": 1000})])
    ]
    
    stats = await client.get_event_statistics("1h")
    
    assert stats["total_events"] == 1000
    assert "events_per_minute" in stats
    assert stats["period"] == "1h"

@pytest.mark.asyncio
async def test_query_error_handling():
    """Test error handling in queries"""
    client = AdminAPIInfluxDBClient()
    client.query_api = AsyncMock()
    client.query_api.query.side_effect = Exception("Connection failed")
    
    with pytest.raises(Exception):
        await client.get_event_statistics("1h")
```

**File:** `services/admin-api/tests/test_stats_endpoints_refactored.py`

```python
@pytest.mark.asyncio
async def test_stats_endpoint_uses_influxdb(test_client, mock_influxdb):
    """Test that stats endpoint queries InfluxDB"""
    
    response = await test_client.get("/api/v1/stats?period=1h")
    
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "influxdb"
    assert "metrics" in data
    assert "trends" in data

@pytest.mark.asyncio
async def test_stats_endpoint_fallback(test_client, broken_influxdb):
    """Test fallback to service calls when InfluxDB fails"""
    
    response = await test_client.get("/api/v1/stats?period=1h")
    
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "services-fallback"
    assert "warning" in data or "fallback" in data["source"]
```

### 6.2 Integration Tests

**File:** `services/admin-api/tests/integration/test_influxdb_integration.py` (NEW)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_data_flow():
    """Test complete flow: Write -> InfluxDB -> Read -> API"""
    
    # 1. Write test metrics to InfluxDB
    influx_writer = InfluxDBClientWrapper(...)
    await influx_writer.connect()
    
    test_point = Point("service_metrics") \
        .tag("service", "test-service") \
        .field("events_processed", 100) \
        .time(datetime.now())
    
    await influx_writer.write_point(test_point)
    
    # 2. Wait for data to be available
    await asyncio.sleep(2)
    
    # 3. Query via Admin API
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8003/api/v1/stats?period=5m")
    
    # 4. Verify data
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "influxdb"
    assert "services" in data["metrics"]
```

### 6.3 Performance Tests

**File:** `services/admin-api/tests/performance/test_query_performance.py` (NEW)

```python
import time
import pytest

@pytest.mark.performance
@pytest.mark.asyncio
async def test_stats_query_performance():
    """Verify queries complete within acceptable time"""
    
    client = AdminAPIInfluxDBClient()
    await client.connect()
    
    # Test multiple time periods
    periods = ["1h", "6h", "24h"]
    
    for period in periods:
        start = time.time()
        stats = await client.get_all_service_statistics(period)
        duration_ms = (time.time() - start) * 1000
        
        assert duration_ms < 200, f"Query for {period} took {duration_ms}ms (limit: 200ms)"
        assert stats is not None
        assert "services" in stats

@pytest.mark.performance
async def test_concurrent_queries():
    """Test performance with concurrent requests"""
    
    client = AdminAPIInfluxDBClient()
    await client.connect()
    
    # Simulate 10 concurrent dashboard loads
    start = time.time()
    tasks = [client.get_event_statistics("1h") for _ in range(10)]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    assert duration < 2.0, f"10 concurrent queries took {duration}s (limit: 2s)"
    assert len(results) == 10
    assert all(r is not None for r in results)
```

### 6.4 Test Execution

```bash
# Run unit tests
cd services/admin-api
pytest tests/test_influxdb_client.py -v
pytest tests/test_stats_endpoints_refactored.py -v

# Run integration tests
pytest tests/integration/ -m integration -v

# Run performance tests
pytest tests/performance/ -m performance -v

# Run full test suite
pytest tests/ -v --cov=src --cov-report=html
```

### Success Criteria
- ✅ All unit tests passing
- ✅ Integration tests passing
- ✅ Performance tests passing (queries < 200ms)
- ✅ Test coverage > 80%
- ✅ No regressions in existing tests

---

## Phase 7: Deployment & Monitoring

### Duration: Week 3-4

### 7.1 Deployment Strategy

#### Step 1: Deploy with Feature Flag (Day 1)
```bash
# Deploy with InfluxDB disabled initially
export USE_INFLUXDB_STATS=false
./scripts/deploy.sh
```

#### Step 2: Enable for Subset (Day 2-3)
```bash
# Enable for 10% of requests
# Implement gradual rollout in load balancer or via % logic in code
export USE_INFLUXDB_STATS=true
export INFLUXDB_ROLLOUT_PERCENT=10
```

#### Step 3: Monitor & Adjust (Day 4-7)
- Monitor error rates
- Check response times
- Compare data accuracy
- Increase to 50%, then 100%

#### Step 4: Full Migration (Week 4)
```bash
# Deploy with InfluxDB fully enabled
export USE_INFLUXDB_STATS=true
./scripts/deploy.sh
```

### 7.2 Monitoring Setup

Add these Prometheus metrics:

```python
from prometheus_client import Counter, Histogram, Gauge

# Query metrics
influxdb_queries_total = Counter(
    'admin_api_influxdb_queries_total',
    'Total InfluxDB queries',
    ['endpoint', 'status']
)

influxdb_query_duration = Histogram(
    'admin_api_influxdb_query_duration_seconds',
    'InfluxDB query duration',
    ['endpoint']
)

influxdb_connection_status = Gauge(
    'admin_api_influxdb_connected',
    'InfluxDB connection status (1=connected, 0=disconnected)'
)

# Update in code
@influxdb_query_duration.time()
async def get_event_statistics(self, period: str):
    try:
        result = await self._execute_query(...)
        influxdb_queries_total.labels(endpoint='event_stats', status='success').inc()
        return result
    except Exception as e:
        influxdb_queries_total.labels(endpoint='event_stats', status='error').inc()
        raise
```

### 7.3 Grafana Dashboard

Create dashboard with:
- InfluxDB query rate
- Query response times (p50, p95, p99)
- Error rates
- Connection status
- Fallback activation count
- Cache hit rates

### 7.4 Alerts

```yaml
groups:
  - name: admin_api_influxdb
    rules:
      - alert: InfluxDBQueryFailures
        expr: rate(admin_api_influxdb_queries_total{status="error"}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Admin API InfluxDB queries failing"
          description: "Error rate: {{ $value }}"
      
      - alert: InfluxDBSlowQueries
        expr: histogram_quantile(0.95, admin_api_influxdb_query_duration_seconds) > 0.5
        for: 5m
        annotations:
          summary: "Admin API queries slow"
          description: "P95 latency: {{ $value }}s"
      
      - alert: InfluxDBConnectionDown
        expr: admin_api_influxdb_connected == 0
        for: 2m
        annotations:
          summary: "Admin API lost InfluxDB connection"
```

### Success Criteria
- ✅ Zero downtime during deployment
- ✅ Error rates unchanged
- ✅ Response times improved
- ✅ Monitoring in place
- ✅ Alerts configured

---

## Phase 8: Documentation & Cleanup

### Duration: Week 4

### 8.1 Update Architecture Documentation

**File:** `docs/architecture.md` or `docs/architecture/data-flow.md`

Update with:
- New data flow diagrams
- InfluxDB query patterns
- Admin API architecture
- Performance characteristics

### 8.2 Update API Documentation

**File:** `services/admin-api/README.md`

Document:
- New InfluxDB dependency
- Environment variables
- Query capabilities
- Fallback behavior

### 8.3 Create Runbooks

**File:** `docs/runbooks/admin-api-influxdb-troubleshooting.md`

Include:
- Common issues and solutions
- How to check InfluxDB connection
- How to enable/disable feature flag
- Rollback procedures

### 8.4 Clean Up Old Code

Remove deprecated code:
- Old direct service HTTP call methods (keep one for fallback)
- Unused imports
- Old tests
- Feature flags (after successful rollout)

### 8.5 Update README Files

Update all relevant READMEs with:
- New architecture
- Setup instructions
- Configuration options

### Success Criteria
- ✅ Documentation updated
- ✅ Runbooks created
- ✅ Old code removed
- ✅ Team trained

---

## Rollback Plan

### Immediate Rollback (< 5 minutes)
```bash
# Disable InfluxDB queries via environment variable
kubectl set env deployment/admin-api USE_INFLUXDB_STATS=false

# Or rollback deployment
kubectl rollout undo deployment/admin-api
```

### Gradual Rollback
```bash
# Reduce rollout percentage
export INFLUXDB_ROLLOUT_PERCENT=0
```

### Emergency Rollback
```bash
# Deploy previous version
git checkout <previous-tag>
./scripts/deploy.sh
```

---

## Risk Assessment

### High Risks
1. **InfluxDB Connection Failures**
   - Mitigation: Fallback to service calls
   - Impact: Medium (degraded functionality)

2. **Query Performance Issues**
   - Mitigation: Query optimization, caching
   - Impact: Medium (slow dashboards)

### Medium Risks
1. **Data Inconsistency**
   - Mitigation: Parallel validation phase
   - Impact: Medium (incorrect metrics)

2. **Missing Metrics**
   - Mitigation: Ensure all services write metrics
   - Impact: Low (partial data)

### Low Risks
1. **Breaking API Changes**
   - Mitigation: Maintain response format
   - Impact: Low (client updates needed)

---

## Success Metrics

### Technical Metrics
- [ ] 100% of stats queries use InfluxDB
- [ ] Query response time < 200ms (p95)
- [ ] Zero downtime during migration
- [ ] Error rate unchanged or improved
- [ ] Test coverage > 80%

### Business Metrics
- [ ] Dashboard load time improved
- [ ] Historical data access enabled
- [ ] Team satisfaction with changes
- [ ] Reduced operational complexity

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| 1. Research & Planning | Week 1 (Day 1-2) | ✅ Complete |
| 2. Infrastructure Setup | Week 1 (Day 3-5) | 🔄 Next |
| 3. Refactor Stats Endpoints | Week 2 | ⏸️ Pending |
| 4. Update Health Endpoints | Week 2 | ⏸️ Pending |
| 5. Update Dashboard Viz | Week 2 | ⏸️ Pending |
| 6. Testing | Week 3 | ⏸️ Pending |
| 7. Deployment & Monitoring | Week 3-4 | ⏸️ Pending |
| 8. Documentation & Cleanup | Week 4 | ⏸️ Pending |

---

## Approval & Sign-off

- [ ] Technical Lead: _______________
- [ ] Architecture Review: _______________
- [ ] Security Review: _______________
- [ ] QA Sign-off: _______________
- [ ] Product Owner: _______________

---

## References

### Knowledge Base
- [InfluxDB Admin API Query Patterns](../docs/kb/context7-cache/influxdb-admin-api-query-patterns.md)
- [Data Flow Architecture Fix Pattern](../docs/kb/context7-cache/data-flow-architecture-fix-pattern.md)
- [InfluxDB Python Patterns](../docs/kb/context7-cache/influxdb-python-patterns.md)

### Code Files
- `services/admin-api/src/stats_endpoints.py`
- `services/admin-api/src/health_endpoints.py`
- `services/enrichment-pipeline/src/influxdb_wrapper.py`
- `services/websocket-ingestion/src/influxdb_wrapper.py`
- `services/health-dashboard/src/components/AnimatedDependencyGraph.tsx`

### External Resources
- [InfluxDB Python Client Documentation](https://github.com/influxdata/influxdb-client-python)
- [InfluxDB Flux Query Language](https://docs.influxdata.com/flux/)

---

**Document Status:** Approved for Implementation  
**Last Updated:** October 12, 2025  
**Next Review:** Upon completion of Phase 2

