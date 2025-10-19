# Mock Data Analysis Report

**Generated:** October 14, 2025  
**Purpose:** Identify all areas where mock data is covering up or replacing real functionality

---

## Executive Summary

This analysis identified **15 critical areas** where mock data is being used instead of real API calls or actual functionality across the homeiq codebase. These mock implementations span frontend components, backend endpoints, and service implementations.

### Priority Classification

- **🔴 Critical** (3): Missing real-time data feeds for core functionality
- **🟡 High** (6): Partially implemented features with fallback mock data
- **🟢 Medium** (6): Placeholder implementations for future enhancements

---

## 1. Frontend Mock Data (Health Dashboard)

### 🔴 CRITICAL: DataSourcesPanel - Complete Mock Implementation

**Location:** `services/health-dashboard/src/components/DataSourcesPanel.tsx`

**Issue:** 
- Line 26: `const mockData = getMockDataSources();`
- The component fetches mock data instead of making real API calls
- TODO comment on line 25: "Replace with actual API call to `/api/v1/data-sources/status`"

**Mock Data:** `services/health-dashboard/src/mocks/dataSourcesMock.ts`
```typescript
export const getMockDataSources = (): DataSource[] => {
  // Returns hardcoded status for:
  // - weather-api (healthy, 47 API calls)
  // - carbon-intensity (degraded, slow response)
  // - air-quality (healthy)
  // - electricity-pricing (healthy)
  // - calendar (unknown)
  // - smart-meter (healthy)
}
```

**Impact:** 
- Dashboard shows fake status for all external data sources
- API usage quotas are fabricated
- Performance metrics are not real
- Cache statistics are meaningless

**Real Implementation Needed:**
- Backend endpoint: `/api/v1/data-sources/status`
- Integration with actual services to report real status
- Actual API call counters and quota tracking
- Real cache hit rates from Redis/memory

---

### 🟡 HIGH: AnalyticsPanel - Partially Mock Data

**Location:** `services/data-api/src/analytics_endpoints.py`

**Issue:**
Lines 266-280 contain mock data generation for 3 out of 4 metrics:

```python
async def query_api_response_time(...):
    # TODO: Implement once we have API response time metrics in InfluxDB
    return generate_mock_series(start_time, interval, num_points, base=50, variance=30)

async def query_database_latency(...):
    # TODO: Implement once we have database latency metrics in InfluxDB
    return generate_mock_series(start_time, interval, num_points, base=15, variance=10)

async def query_error_rate(...):
    # TODO: Implement once we have error tracking in InfluxDB
    return generate_mock_series(start_time, interval, num_points, base=0.5, variance=0.5)
```

**Real Data:** Only `query_events_per_minute()` queries actual InfluxDB data (line 232-262)

**Impact:**
- API response time is fabricated
- Database latency is not real
- Error rates are meaningless
- Only event counts are accurate

**Real Implementation Needed:**
- Store API response times in InfluxDB during actual API calls
- Track database write latency metrics
- Implement error tracking measurement in InfluxDB
- Line 216: Uptime calculation hardcoded to 99.9%

---

### 🟡 HIGH: Mock Alert Data

**Location:** `services/health-dashboard/src/mocks/alertsMock.ts`

**Issue:**
- Mock alert history generator: `getMockAlerts()`
- Returns hardcoded 5 alerts with fabricated timestamps
- TODO comment on line 5: "Replace with actual API calls to `/api/v1/alerts`"

**Note:** The AlertsPanel component (line 23) uses the real `useAlerts` hook and fetches from actual API, so this mock file may be **deprecated/unused**. Verification needed.

---

### 🟢 MEDIUM: MetricsChart Sample Data

**Location:** `services/health-dashboard/src/components/MetricsChart.tsx`

**Issue:**
- Line 46: Comment "Generate sample data if no real metrics available"
- Lines 47-62: `generateTimeSeriesData()` function creates fabricated time series
- Used as fallback when metrics prop is empty

**Impact:** 
- Charts show fake data when metrics aren't available
- Can mislead users about actual system performance

**Real Implementation:**
- Should show "No data available" state instead of fake data
- Or fetch real metrics from `/api/v1/metrics` endpoint

---

## 2. Backend Mock Data (Python Services)

### 🔴 CRITICAL: Docker Service Mock Containers

**Location:** `services/admin-api/src/docker_service.py` (duplicated in `services/data-api/src/docker_service.py`)

**Issue:**
Lines 400-436: `_get_mock_containers()` method

```python
# Mock response when Docker is not available
# Lines 165, 211, 257, 301 all use mock responses
async def _get_mock_containers(self) -> List[ContainerInfo]:
    """Get mock container data when Docker is not available"""
    # Creates fake container status for 13 services
    # Lines 411-420: Hardcoded status assignments
```

**Impact:**
- Docker management appears to work but doesn't actually control containers
- Service status shows fake data when Docker socket unavailable
- Restart operations return placeholder messages (lines 158-178)

**Real Implementation:**
- Requires proper Docker socket access
- Need volume mount: `/var/run/docker.sock:/var/run/docker.sock`
- Service restart/stop/start operations are currently non-functional

---

### 🔴 CRITICAL: Monitoring Realtime Metrics Mock

**Location:** `services/data-api/src/monitoring_endpoints.py` and `services/admin-api/src/monitoring_endpoints.py`

**Issue:**
Lines 98-143: `/metrics/realtime` endpoint

```python
# Line 122: TODO comment
# TODO: Add actual detection logic for sports APIs
# For now, return mock data
active_sources_count = len(active_sources)
```

**Impact:**
- Real-time metrics for animated dependencies visualization are incomplete
- Active data sources detection is not implemented
- Falls back to graceful mock response on errors

---

### 🟡 HIGH: Service Restart Placeholder

**Location:** `services/admin-api/src/service_controller.py` (duplicated in `services/data-api/src/service_controller.py`)

**Issue:**
Lines 158-195: Service restart methods are placeholders

```python
def restart_service(self, service: str) -> Dict[str, any]:
    """Restart a service (placeholder - requires external docker management)"""
    return {
        "success": False,
        "message": "Service restart not available from within container",
        "instruction": f"To restart {service}, run: docker restart..."
    }
```

**Impact:**
- Dashboard restart buttons don't actually work
- Returns instructions for manual Docker commands
- User experience is degraded (appears broken)

---

### 🟡 HIGH: Alerting Service NotImplementedError

**Location:** 
- `services/admin-api/src/alerting_service.py` (line 101)
- `services/data-api/src/alerting_service.py` (line 101)

**Issue:**
```python
class NotificationChannel:
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for an alert."""
        raise NotImplementedError
```

**Impact:**
- Base class raises NotImplementedError
- Subclasses (EmailNotificationChannel, WebhookNotificationChannel, SlackNotificationChannel) do implement it
- This is **architectural**, not a bug - base class is abstract
- **Status:** False positive - this is correct OOP design

---

### 🟢 MEDIUM: Quality Dashboard History Mock

**Location:** `services/enrichment-pipeline/src/quality_dashboard.py`

**Issue:**
Lines 530-560: Mock history data generators

```python
def _get_quality_score_history(self, hours: int) -> List[Dict[str, Any]]:
    """Get quality score history (mock implementation)"""
    return [
        {
            "timestamp": ...,
            "quality_score": 95.0 + (i % 5) - 2.5  # Mock varying scores
        }
        for i in range(hours)
    ]

def _get_error_rate_history(self, hours: int):
    # Mock varying error rates
    
def _get_processing_latency_history(self, hours: int):
    # Mock varying latencies
```

**Impact:**
- Quality metrics dashboard shows fabricated historical trends
- No actual data quality tracking over time

**Real Implementation:**
- Store quality metrics in InfluxDB
- Query historical data from time-series database

---

### 🟢 MEDIUM: Data Retention Mock Implementations

**Location:** `services/data-retention/src/`

**Issue:** Multiple mock implementations when InfluxDB client unavailable:

1. **backup_restore.py** (lines 185-203)
   ```python
   if not self.influxdb_client:
       # Mock implementation for testing
       mock_data = {"events": [...]}
   ```

2. **data_cleanup.py** (lines 183-188, 226-228)
   ```python
   if not self.influxdb_client:
       # Mock implementation for testing
       return mock_records
   ```

3. **data_compression.py** (lines 238-243, 286-287)
   ```python
   if not self.influxdb_client:
       # Mock implementation for testing
       return mock_chunks
   ```

**Impact:**
- Backup/restore operations return fake data when InfluxDB unavailable
- Data cleanup reports false deletion counts
- Data compression doesn't actually compress anything

**Real Implementation:**
- These are intentional fallbacks for testing/development
- Require valid InfluxDB connection in production

---

### 🟢 MEDIUM: Storage Monitor Placeholder

**Location:** `services/data-retention/src/storage_monitor.py`

**Issue:**
Line 186:
```python
return None  # Placeholder
```

**Context:** Within a function that should return storage metrics but returns None instead

---

## 3. Missing API Endpoints

### Backend Endpoints That Don't Exist Yet

1. **`/api/v1/data-sources/status`** 
   - Expected by: DataSourcesPanel
   - Purpose: Real-time status of external data sources
   - Priority: 🔴 Critical

2. **`/api/v1/analytics` (partial)**
   - Exists but returns mostly mock data
   - Needs: Real API response time, DB latency, error rate metrics
   - Priority: 🟡 High

---

## 4. Test Files (Intentional Mocks)

The following files contain mocks but are **legitimate test fixtures**:

- `services/health-dashboard/src/tests/mocks/` - MSW mock server for testing
- `services/**/tests/test_*.py` - pytest mock fixtures
- `services/ha-simulator/` - Intentional simulator for testing

**Status:** ✅ These are correct and expected

---

## 5. Deprecated Mock Files

### Potentially Unused Files

1. **`services/health-dashboard/src/mocks/alertsMock.ts`**
   - AlertsPanel uses real API via `useAlerts` hook
   - May be leftover from early development
   - Recommendation: Verify usage and remove if unused

2. **`services/health-dashboard/src/mocks/analyticsMock.ts`**
   - Type definitions are used, but `getMockAnalyticsData()` may be unused
   - AnalyticsPanel fetches from real `/api/v1/analytics`
   - Recommendation: Keep types, remove mock data generator if unused

---

## 6. Configuration Placeholders

**Location:** 
- `services/data-api/src/config_manager.py`
- `services/admin-api/src/config_manager.py`

**Issue:**
Lines 250-331: Configuration schema with placeholder values

```python
"placeholder": "ws://192.168.1.100:8123/api/websocket"
"placeholder": "Your HA access token"
"placeholder": "Your OpenWeatherMap API key"
```

**Status:** ✅ These are correct - placeholders for UI display, not actual default values

---

## Summary of Findings

### Critical Issues (Need Immediate Attention)

1. **DataSourcesPanel** - Entirely mock, no real API endpoint
2. **Docker Container Management** - Mock containers when Docker unavailable
3. **Analytics Metrics** - 75% of metrics are fabricated

### High Priority Issues

4. **Service Restart Operations** - Placeholder implementations
5. **Real-time Metrics** - Incomplete active source detection
6. **Quality Dashboard** - Mock historical data

### Medium Priority Issues

7. **MetricsChart** - Sample data fallback (should show empty state)
8. **Data Retention** - Mock implementations for testing (acceptable)
9. **Storage Monitor** - Placeholder return value

### False Positives

- **Alerting NotificationChannel** - Abstract base class (correct design)
- **Configuration Placeholders** - UI placeholders (correct)
- **Test Mocks** - Intentional test fixtures (correct)

---

## Recommendations

### Phase 1: Critical Fixes (Immediate)

1. **Implement `/api/v1/data-sources/status` endpoint**
   - Create data source status aggregation service
   - Integrate with actual external services
   - Real API quota tracking

2. **Complete Analytics Metrics Implementation**
   - Store API response times in InfluxDB
   - Track database write latency
   - Implement error rate tracking
   - Calculate real uptime from service health data

3. **Fix Docker Container Management**
   - Ensure Docker socket access in production
   - Remove mock fallback or clearly indicate "unavailable" state
   - Implement actual service restart operations

### Phase 2: High Priority (Next Sprint)

4. **Service Control Improvements**
   - Implement real Docker API integration
   - Add proper error messaging when Docker unavailable
   - Consider external API for container management

5. **Real-time Metrics Enhancement**
   - Implement sports API activity detection
   - Add more data sources to active source tracking

6. **Quality Metrics Storage**
   - Store quality scores in InfluxDB
   - Implement historical trend queries

### Phase 3: Polish (Future)

7. **Remove Deprecated Mock Files**
   - Audit and remove unused mock data files
   - Clean up old development artifacts

8. **Improve Fallback UX**
   - Replace fake data with "No data available" states
   - Add clear indicators when in mock/testing mode

---

## Files Requiring Changes

### Frontend (TypeScript/React)
- `services/health-dashboard/src/components/DataSourcesPanel.tsx` 🔴
- `services/health-dashboard/src/components/MetricsChart.tsx` 🟢
- Remove: `services/health-dashboard/src/mocks/dataSourcesMock.ts` 🔴
- Review: `services/health-dashboard/src/mocks/alertsMock.ts` 🟡
- Review: `services/health-dashboard/src/mocks/analyticsMock.ts` 🟡

### Backend (Python)
- `services/data-api/src/analytics_endpoints.py` 🔴
- `services/admin-api/src/docker_service.py` 🔴
- `services/data-api/src/docker_service.py` 🔴
- `services/admin-api/src/service_controller.py` 🟡
- `services/data-api/src/service_controller.py` 🟡
- `services/data-api/src/monitoring_endpoints.py` 🟡
- `services/admin-api/src/monitoring_endpoints.py` 🟡
- `services/enrichment-pipeline/src/quality_dashboard.py` 🟢
- `services/data-retention/src/backup_restore.py` 🟢
- `services/data-retention/src/data_cleanup.py` 🟢
- `services/data-retention/src/data_compression.py` 🟢
- `services/data-retention/src/storage_monitor.py` 🟢

### New Files Needed
- `services/data-api/src/data_sources_endpoints.py` (new endpoint) 🔴
- Update InfluxDB schema to track API response times 🔴
- Update InfluxDB schema to track database latency 🔴
- Update InfluxDB schema to track error rates 🔴

---

## Testing Requirements

### Before Removing Mock Data

1. **Create Integration Tests**
   - Test actual InfluxDB queries for analytics
   - Test Docker API integration
   - Test data source status aggregation

2. **Create Fallback Tests**
   - Test behavior when InfluxDB unavailable
   - Test behavior when Docker socket unavailable
   - Test graceful degradation

3. **UI Testing**
   - Update E2E tests to expect real data
   - Remove mock data from Playwright tests
   - Test loading and error states

---

## Conclusion

The codebase has **3 critical areas** where mock data is masking missing functionality, primarily around:

1. **External data source status monitoring** - Completely unimplemented
2. **Analytics metrics collection** - 75% incomplete (3 out of 4 metrics are fake)
3. **Docker container management** - Broken when Docker unavailable

The good news is that most of these are well-documented with TODO comments and have clear implementation paths. The infrastructure (endpoints, data models, UI components) is already in place—it just needs to be connected to real data sources.

The medium-priority mock implementations in data-retention services are acceptable fallbacks for testing environments and don't necessarily need to be changed if properly documented.

---

**Next Steps:** Prioritize implementing `/api/v1/data-sources/status` endpoint and completing analytics metrics to unlock full dashboard functionality.

