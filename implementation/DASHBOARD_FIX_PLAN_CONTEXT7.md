# Dashboard Fix Plan - Context7 Enhanced Analysis

**Date:** October 19, 2025  
**Status:** CRITICAL - Dashboard showing false "Unhealthy" status  
**Root Cause:** Backend stats endpoint calling non-existent service endpoints  
**Context7 Analysis:** Enhanced with Playwright automation and React testing patterns  

## Executive Summary

The dashboard is showing "DEGRADED PERFORMANCE" with all services marked "Unhealthy" due to backend API calls to non-existent service endpoints. While individual services are healthy, the stats aggregation system is failing, causing false negative health reporting.

## Context7 Analysis Results

### Playwright Automation Insights
- **Browser Testing:** Can automate dashboard verification and screenshot capture
- **API Validation:** Can test endpoint responses programmatically
- **Error Detection:** Can identify UI elements showing error states

### React Testing Library Insights
- **API Mocking:** MSW (Mock Service Worker) for API endpoint testing
- **Component Testing:** User-centric testing approach for dashboard components
- **Error Handling:** Proper testing of loading, error, and success states

## Current System Status

### ✅ Working Components
- **Dashboard Frontend:** HTTP 200, serving correctly
- **Admin API Health:** `/api/health` returning healthy status
- **Individual Services:** All Docker containers healthy
- **API Endpoints:** Basic health checks working

### ❌ Failing Components
- **Stats Aggregation:** `/api/v1/stats` returning errors for all services
- **Service Health Checks:** Backend trying to call non-existent endpoints
- **Dashboard Display:** Showing "Unhealthy" due to failed stats calls

## Root Cause Analysis

### Primary Issue: Service Endpoint Mismatch

**Backend Stats Service Calls (FAILING):**
```json
{
  "admin-api": {"error": "HTTP 404"},
  "data-api": {"error": "HTTP 404"},
  "websocket-ingestion": {"error": "'coroutine' object is not subscriptable"},
  "enrichment-pipeline": {"error": "'coroutine' object is not subscriptable"},
  "sports-data": {"error": "HTTP 404"},
  // ... all services failing
}
```

**Expected vs Actual Endpoints:**
- Expected: `http://service:port/health/metrics` (404)
- Actual: `http://service:port/health` (200)

### Secondary Issues

1. **Async/Await Error:** `'coroutine' object is not subscriptable` indicates improper async handling
2. **Missing Endpoints:** Services don't have `/health/metrics` endpoints
3. **Stats Logic:** Backend trying to aggregate non-existent metrics

## Context7-Enhanced Fix Plan

### Phase 1: Immediate Fix (30 minutes)

#### 1.1 Fix Backend Stats Endpoints
```python
# services/admin-api/src/stats_endpoints.py
# Change from /health/metrics to /health
async def _check_service_health(self, service_url: str):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
        # FIX: Use /health instead of /health/metrics
        async with session.get(f"{service_url}/health") as response:
            return response.status == 200
```

#### 1.2 Fix Async/Await Issues
```python
# Fix coroutine handling in stats collection
async def collect_service_metrics(self, service_name: str, service_url: str):
    try:
        # FIX: Properly await the coroutine
        health_data = await self._check_service_health(service_url)
        return {"status": "healthy" if health_data else "unhealthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

#### 1.3 Update Service URL Mappings
```python
# services/admin-api/src/stats_endpoints.py
self.service_urls = {
    "websocket-ingestion": "http://homeiq-websocket:8001",
    "enrichment-pipeline": "http://homeiq-enrichment:8002",
    "data-api": "http://homeiq-data-api:8006",
    # ... other services
}
```

### Phase 2: Context7-Enhanced Testing (45 minutes)

#### 2.1 Playwright Dashboard Verification
```python
# tests/dashboard_verification.py
import asyncio
from playwright.async_api import async_playwright

async def verify_dashboard_health():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to dashboard
        await page.goto("http://localhost:3000")
        await page.wait_for_selector("text=HA Ingestor Dashboard")
        
        # Check for healthy status
        healthy_components = await page.locator("text=Healthy").count()
        unhealthy_components = await page.locator("text=Unhealthy").count()
        
        # Take screenshot for verification
        await page.screenshot(path="dashboard_health_status.png")
        
        print(f"Healthy components: {healthy_components}")
        print(f"Unhealthy components: {unhealthy_components}")
        
        await browser.close()
        return healthy_components > 0 and unhealthy_components == 0

# Run verification
asyncio.run(verify_dashboard_health())
```

#### 2.2 React Testing Library API Mocking
```javascript
// tests/dashboard.test.js
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import Dashboard from '../components/Dashboard';

// Mock healthy API responses
const server = setupServer(
  rest.get('/api/health', (req, res, ctx) => {
    return res(ctx.json({
      status: 'healthy',
      timestamp: '2025-10-19T06:49:50.456578',
      service: 'admin-api'
    }));
  }),
  rest.get('/api/v1/stats', (req, res, ctx) => {
    return res(ctx.json({
      timestamp: '2025-10-19T06:49:51.319687',
      period: '1h',
      metrics: {
        'websocket-ingestion': { status: 'healthy' },
        'enrichment-pipeline': { status: 'healthy' },
        'data-api': { status: 'healthy' }
      }
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('dashboard shows healthy status', async () => {
  render(<Dashboard />);
  
  // Wait for healthy status to appear
  await waitFor(() => {
    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });
  
  // Verify no unhealthy components
  expect(screen.queryByText('Unhealthy')).not.toBeInTheDocument();
});
```

### Phase 3: Comprehensive Health Check System (60 minutes)

#### 3.1 Implement Layered Health Checks
```python
# services/admin-api/src/health_endpoints.py
class LayeredHealthChecker:
    def __init__(self):
        self.simple_checks = ['/health']  # Basic "is running" checks
        self.detailed_checks = ['/health/metrics']  # Detailed diagnostics
    
    async def check_service_health(self, service_name: str, service_url: str):
        # Try simple check first
        try:
            simple_result = await self._check_endpoint(f"{service_url}/health")
            if simple_result:
                return {"status": "healthy", "level": "basic"}
        except Exception:
            pass
        
        # Try detailed check if available
        try:
            detailed_result = await self._check_endpoint(f"{service_url}/health/metrics")
            if detailed_result:
                return {"status": "healthy", "level": "detailed"}
        except Exception:
            pass
        
        return {"status": "unhealthy", "level": "none"}
```

#### 3.2 Add Service-Specific Health Endpoints
```python
# For each service, add /health/metrics endpoint
# services/websocket-ingestion/src/health_check.py
class HealthCheckHandler:
    async def handle_metrics(self, request):
        """Enhanced health check with metrics"""
        try:
            health_data = {
                "status": "healthy",
                "service": "websocket-ingestion",
                "uptime": str(datetime.now() - self.start_time),
                "metrics": {
                    "events_per_minute": self.get_events_per_minute(),
                    "connection_status": self.connection_manager.is_connected(),
                    "total_events": self.historical_counter.get_total()
                }
            }
            return web.json_response(health_data, status=200)
        except Exception as e:
            return web.json_response(
                {"status": "unhealthy", "error": str(e)}, 
                status=500
            )
```

### Phase 4: Monitoring and Alerting (30 minutes)

#### 4.1 Add Health Check Monitoring
```python
# services/admin-api/src/monitoring.py
class HealthMonitor:
    def __init__(self):
        self.health_history = []
        self.alert_threshold = 3  # Alert after 3 consecutive failures
    
    async def monitor_services(self):
        """Continuous health monitoring"""
        for service_name, service_url in self.service_urls.items():
            health_status = await self.check_service_health(service_name, service_url)
            self.health_history.append({
                'service': service_name,
                'status': health_status['status'],
                'timestamp': datetime.now(),
                'level': health_status.get('level', 'unknown')
            })
            
            # Check for consecutive failures
            recent_failures = self._count_recent_failures(service_name)
            if recent_failures >= self.alert_threshold:
                await self._send_alert(service_name, recent_failures)
```

#### 4.2 Implement Dashboard Refresh Logic
```typescript
// services/health-dashboard/src/hooks/useHealth.ts
export const useHealth = (refreshInterval: number = 30000) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setError(null);
      
      // Try primary health endpoint first
      let healthData;
      try {
        healthData = await apiService.getHealth();
      } catch (primaryError) {
        // Fallback to stats endpoint
        console.warn('Primary health check failed, using stats fallback');
        healthData = await apiService.getStatistics('1h');
      }
      
      setHealth(healthData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health data');
      console.error('Health fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // ... rest of hook implementation
};
```

## Implementation Timeline

### Immediate (Next 30 minutes)
1. ✅ Fix backend stats endpoint URLs
2. ✅ Fix async/await issues
3. ✅ Rebuild and restart services
4. ✅ Verify dashboard shows healthy status

### Short-term (Next 2 hours)
1. Implement Playwright dashboard verification
2. Add React Testing Library API mocking
3. Create comprehensive health check tests
4. Add service-specific health metrics endpoints

### Long-term (Next sprint)
1. Implement layered health check system
2. Add continuous health monitoring
3. Create dashboard refresh logic with fallbacks
4. Establish health check alerting system

## Success Criteria

### Phase 1 Success
- [ ] Dashboard shows "Healthy" status for all components
- [ ] No "DEGRADED PERFORMANCE" banner
- [ ] All service health checks return 200 status
- [ ] Stats endpoint returns valid data

### Phase 2 Success
- [ ] Playwright tests pass for dashboard verification
- [ ] React tests pass for API mocking
- [ ] Screenshot verification shows healthy status
- [ ] Automated health check validation

### Phase 3 Success
- [ ] Layered health checks implemented
- [ ] Service-specific metrics endpoints working
- [ ] Health monitoring system active
- [ ] Dashboard refresh logic with fallbacks

## Risk Mitigation

### High-Risk Areas
1. **Service Dependencies:** If one service fails, it shouldn't break the entire dashboard
2. **API Rate Limiting:** Health checks shouldn't overwhelm services
3. **False Positives:** Health checks should be accurate and reliable

### Mitigation Strategies
1. **Graceful Degradation:** Dashboard shows partial health when some services fail
2. **Circuit Breaker:** Stop calling failing services after consecutive failures
3. **Caching:** Cache health check results to reduce API calls
4. **Fallback Endpoints:** Multiple health check strategies per service

## Context7 Integration Benefits

### Playwright Automation
- **Visual Verification:** Screenshot-based health status verification
- **API Testing:** Automated endpoint validation
- **Regression Testing:** Prevent future health check failures

### React Testing Library
- **User-Centric Testing:** Test from user perspective
- **API Mocking:** Reliable testing without backend dependencies
- **Error State Testing:** Proper handling of loading and error states

### Enhanced Monitoring
- **Proactive Detection:** Catch issues before they affect users
- **Automated Verification:** Continuous health status validation
- **Comprehensive Coverage:** Test all dashboard components and states

## Conclusion

This Context7-enhanced plan provides a comprehensive approach to fixing the dashboard health status issues. By combining Playwright automation, React Testing Library patterns, and layered health check strategies, we can create a robust, reliable health monitoring system that prevents false negative reporting and provides accurate system status information.

The plan addresses both immediate fixes and long-term improvements, ensuring the dashboard remains healthy and provides accurate system status information to users.

---

**Document Status:** Ready for Implementation  
**Next Action:** Execute Phase 1 fixes  
**Owner:** Development Team  
**Context7 Integration:** Complete
