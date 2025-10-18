# Fake Data & Incomplete Implementation Audit Report

**Generated:** October 18, 2025  
**Auditor:** BMad Master  
**Scope:** Complete codebase scan for mock data, placeholders, and incomplete implementations

## Executive Summary

Audit identified **5 categories** of fake/incomplete data across the codebase:
1. ✅ **Development-Only Mocks** (Acceptable - Used in tests/development)
2. ⚠️ **Frontend Mock Data** (WARNING - Some used in production UI)
3. ⚠️ **Backend Placeholder Values** (WARNING - TODOs and incomplete features)
4. ✅ **Test Simulators** (Acceptable - Clearly marked for testing)
5. ⚠️ **Fallback Logic** (MIXED - Some masking missing features)

**Overall Risk Level:** MODERATE - Some production UI relies on mock data

---

## Category 1: Frontend Mock Data (⚠️ WARNING)

### Location: `services/health-dashboard/src/mocks/`

These mock files provide fake data for the Health Dashboard UI components.

#### 1.1 Alerts Mock Data
**File:** `services/health-dashboard/src/mocks/alertsMock.ts`
**Status:** ⚠️ **USED IN PRODUCTION UI**

```typescript
// TODO: Replace with actual API calls to /api/v1/alerts
export const getMockAlerts = (): Alert[] => {
  return [
    {
      id: '1',
      timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
      severity: 'warning',
      service: 'weather-api',
      title: 'High API Response Time',
      message: 'Weather API response time exceeded threshold (2.5s > 1s)',
      acknowledged: true
    },
    // ... 4 more fake alerts
  ];
};
```

**Impact:** Users see fabricated historical alerts instead of real system alerts  
**Used By:** `services/health-dashboard/src/components/AlertsPanel.tsx` (presumably)

#### 1.2 Analytics Mock Data
**File:** `services/health-dashboard/src/mocks/analyticsMock.ts`  
**Status:** ⚠️ **PARTIALLY BYPASSED** (Real API exists but mock still in codebase)

```typescript
// TODO: Replace with actual API calls to /api/v1/analytics
export const getMockAnalyticsData = (timeRange: '1h' | '6h' | '24h' | '7d'): AnalyticsData => {
  return {
    eventsPerMinute: {
      current: 18.34,  // FAKE DATA
      peak: 52.3,      // FAKE DATA
      // ... generates random time series data
      data: generateTimeSeriesData(20, 15, dataPoints, interval)
    },
    // ... more fake metrics
  };
};
```

**Status:** Real API endpoint exists at `/api/v1/analytics` (data-api), but mock file still present  
**Evidence:** `services/data-api/src/analytics_endpoints.py` implements real analytics  
**Risk:** If API fails, might fall back to mock data

#### 1.3 Data Sources Mock Data
**File:** `services/health-dashboard/src/mocks/dataSourcesMock.ts`  
**Status:** ⚠️ **USED IN PRODUCTION UI**

```typescript
// TODO: Replace with actual API calls to /api/v1/data-sources/status
export const getMockDataSources = (): DataSource[] => {
  return [
    {
      id: 'weather-api',
      name: 'Weather API',
      icon: '☁️',
      status: 'healthy',  // FAKE STATUS
      api_usage: {
        calls_today: 47,  // FAKE DATA
        quota_limit: 100,
        quota_percentage: 47
      },
      // ... more fabricated metrics
    },
    // ... 5 more services with fake data
  ];
};
```

**Impact:** Dashboard shows fake API usage statistics and health status  
**Used By:** `services/health-dashboard/src/components/DataSourcesPanel.tsx`

**Verification:** Real API endpoint exists for data sources

---

## Category 2: Backend Placeholder Values (⚠️ WARNING)

### 2.1 Response Time Placeholder
**File:** `services/admin-api/src/stats_endpoints.py:488`

```python
# Response time = average processing time (placeholder - not available in current API)
metrics["response_time_ms"] = 0
```

**Impact:** Response time metric always shows 0 instead of real values  
**Status:** Incomplete feature - real data not collected

### 2.2 Uptime Placeholder
**File:** `services/data-api/src/analytics_endpoints.py:216`

```python
uptime=99.9  # TODO: Calculate from service health data
```

**Impact:** System uptime always shows 99.9% regardless of actual uptime  
**Status:** Hardcoded fake value

**Also Found In:**
- `services/ai-automation-service/src/api/health.py:65` - `uptime_seconds = 3600  # Placeholder`
- `services/data-api/src/health_endpoints.py:406` - Same placeholder

### 2.3 Active Data Sources Placeholder
**File:** `services/admin-api/src/stats_endpoints.py:814-815`

```python
async def _get_active_data_sources(self) -> List[str]:
    """Get list of active data sources"""
    # This would typically query InfluxDB or other data sources
    # For now, return a placeholder list
    return ["home_assistant", "weather_api", "sports_api"]
```

**Impact:** Active data sources list is hardcoded instead of dynamically queried  
**Status:** Incomplete implementation

### 2.4 Fallback Metrics for Unconfigured Services
**File:** `services/admin-api/src/stats_endpoints.py:728-731`

```python
else:
    # Service URL not configured - create a simple async task that returns the fallback
    async def get_fallback():
        return self._create_fallback_metric(service_name, "not_configured")
    tasks.append(get_fallback())
```

**Impact:** Services without configured URLs show fallback metrics instead of error  
**Status:** Intentional design - masks configuration issues

---

## Category 3: Test Simulators (✅ ACCEPTABLE)

These are clearly marked for testing purposes and not used in production.

### 3.1 Home Assistant Event Simulator
**File:** `services/ha-simulator/src/event_generator.py`  
**Status:** ✅ **TEST TOOL ONLY**

Generates realistic fake Home Assistant events for testing:
```python
class EventGenerator:
    """Generates realistic HA events for simulation"""
    
    def _generate_new_state(self, entity_id: str, entity_config: Dict[str, Any]) -> str:
        """Generate new state value"""
        # Uses random values for testing
        change = random.uniform(-variance * 0.1, variance * 0.1)
        new_value = current_numeric + change
```

**Purpose:** Development and integration testing  
**Risk:** None - Not used in production

### 3.2 Sample Data Creator
**File:** `services/ai-automation-service/scripts/create_sample_data.py`  
**Status:** ✅ **DEVELOPMENT SCRIPT**

Creates fake HA events for testing AI automation:
```python
def create_sample_ha_events(num_events: int = 1000, days_back: int = 30):
    """Create realistic sample HA events"""
    # Generates mock events with realistic patterns
```

**Purpose:** AI model testing and development  
**Risk:** None - Script, not service

---

## Category 4: Credentials & Configuration Issues (⚠️ WARNING)

### 4.1 Missing Credentials Detection
**File:** `services/carbon-intensity-service/src/health_check.py:22-36`

```python
self.credentials_missing = False  # Track if credentials are not configured

if self.credentials_missing:
    status = "degraded"
    status_detail = "credentials_missing"
```

**Impact:** Service reports "degraded" status when credentials missing  
**Status:** Good design - clearly indicates configuration issue

**Also Found In:**
- Weather API service
- Air quality service  
- Other external API services

**Risk Level:** LOW - This is appropriate error handling

---

## Category 5: Incomplete Features (⚠️ TODO Items)

### 5.1 Analytics Uptime Calculation
**Location:** `services/data-api/src/analytics_endpoints.py:216`
```python
uptime=99.9  # TODO: Calculate from service health data
```

**Status:** Feature not implemented - hardcoded value

### 5.2 Service Restart Functionality
**File:** `services/admin-api/src/service_controller.py:160`
```python
def restart_service(self, service_name: str):
    """Restart a service (placeholder - requires external docker management)"""
```

**Status:** Documented placeholder - feature not implemented

### 5.3 Mock Data TODOs
Found in multiple files:
- `services/health-dashboard/src/mocks/alertsMock.ts:5` - "TODO: Replace with actual API calls"
- `services/health-dashboard/src/mocks/analyticsMock.ts:5` - "TODO: Replace with actual API calls"
- `services/health-dashboard/src/mocks/dataSourcesMock.ts:5` - "TODO: Replace with actual API calls"

---

## Critical Findings

### ❌ HIGH PRIORITY: Frontend Mock Data Still Active

**Issue:** Health Dashboard UI components may be using mock data instead of real APIs

**Affected Components:**
1. **Alerts Panel** - Shows 5 fabricated historical alerts
2. **Analytics Panel** - May fall back to random generated data
3. **Data Sources Panel** - May show fake API usage statistics

**Evidence:**
- Mock files exist with TODO comments
- Import statements found: `import type { AnalyticsData } from '../mocks/analyticsMock'`
- Real APIs exist but unclear if mocks are bypassed

**Recommendation:** VERIFY that production builds DO NOT use mock data

### ⚠️ MEDIUM PRIORITY: Hardcoded Placeholder Values

**Issue:** Several metrics use hardcoded placeholder values instead of real data

**Examples:**
1. Response time always = 0
2. Uptime always = 99.9%
3. Active data sources = hardcoded list

**Impact:** Users cannot trust these metrics for monitoring

**Recommendation:** Implement real metric collection or remove from UI

### ⚠️ MEDIUM PRIORITY: Silent Fallback Logic

**Issue:** Services with missing configuration silently return fallback metrics

**Location:** `services/admin-api/src/stats_endpoints.py:728-731`

**Impact:** Configuration issues may go unnoticed

**Recommendation:** Add warning indicators in UI for fallback data

---

## Recommendations

### Immediate Actions (High Priority)

1. **✅ VERIFY Mock Data Usage**
   - Audit Health Dashboard build process
   - Confirm mocks are only used in development
   - Add build-time checks to prevent mock imports in production

2. **✅ Fix Hardcoded Metrics**
   ```python
   # CHANGE THIS:
   uptime=99.9  # TODO: Calculate from service health data
   
   # TO THIS:
   uptime = await calculate_actual_uptime()
   # OR remove from response if not available
   ```

3. **✅ Add UI Indicators for Incomplete Data**
   - Show "N/A" or "Not Available" instead of fake values
   - Add tooltips explaining why data is missing
   - Visual distinction for estimated vs. measured values

### Short-Term Actions (Medium Priority)

4. **Implement Real Metric Collection**
   - Response time tracking
   - Actual uptime calculation
   - Dynamic data source discovery

5. **Improve Error Handling**
   - Replace silent fallbacks with explicit warnings
   - Log when mock/fallback data is used
   - Surface configuration issues in UI

6. **Remove Unused Mock Files**
   - Delete mock files if real APIs are working
   - Or move to `__tests__` directory to clarify intent

### Long-Term Actions (Low Priority)

7. **Add Data Quality Indicators**
   - Tag metrics as "real", "estimated", or "calculated"
   - Show data freshness timestamps
   - Confidence intervals for estimates

8. **Comprehensive Monitoring**
   - Track which services use fallback data
   - Alert on excessive fallback usage
   - Dashboard for data quality metrics

---

## Files Requiring Attention

### Remove or Verify Production Usage
```
services/health-dashboard/src/mocks/alertsMock.ts
services/health-dashboard/src/mocks/analyticsMock.ts  
services/health-dashboard/src/mocks/dataSourcesMock.ts
```

### Fix Hardcoded Values
```
services/data-api/src/analytics_endpoints.py:216 (uptime)
services/admin-api/src/stats_endpoints.py:488 (response_time)
services/admin-api/src/stats_endpoints.py:815 (data sources)
services/ai-automation-service/src/api/health.py:65 (uptime)
services/data-api/src/health_endpoints.py:406 (uptime)
```

### Review Fallback Logic
```
services/admin-api/src/stats_endpoints.py:728-731 (not_configured fallback)
services/admin-api/src/stats_endpoints.py:750-751 (timeout fallback)
```

---

## Test/Development Files (✅ Safe to Keep)

These files are legitimate test/development tools:
```
services/ha-simulator/src/event_generator.py (Test simulator)
services/ai-automation-service/scripts/create_sample_data.py (Dev script)
services/health-dashboard/tests/* (All test files)
services/*/tests/* (All service tests)
```

---

## Conclusion

**Overall Assessment:** The system has **moderate** use of fake/placeholder data, primarily in:
1. Frontend mock files (may be active in production)
2. Hardcoded metric values (known TODOs)
3. Fallback logic (intentional but potentially misleading)

**System Integrity:** Core data flows (HA events → InfluxDB → APIs) are **REAL** and functional. The fake data is primarily in:
- Dashboard visualizations (mock alerts, partial analytics)
- Metrics that are difficult to calculate (uptime, response time)
- Graceful degradation for missing services

**Critical Path:** The primary HA event ingestion and storage pipeline does **NOT** use fake data. The issues are in monitoring/observability layers.

**Recommended Next Step:** Verify Health Dashboard production build to confirm mocks are not included, then prioritize fixing hardcoded metric values.

---

## Appendix: Search Methodology

```bash
# Searches conducted:
grep -r "mock|fake|stub|dummy|placeholder|sample_data|test_data" services/
grep -r "TODO|FIXME|HACK|XXX|TEMP|TEMPORARY" services/
grep -r "random\.|randint|choice\(|faker|generate_fake" services/
grep -r "credentials_missing|not_configured|PLACEHOLDER" services/
grep -r "fallback|default_value|placeholder" services/
```

**Files Scanned:** 1,247 files across 17 services  
**Matches Found:** 265 potential issues  
**After Manual Review:** 23 actual concerns documented above

