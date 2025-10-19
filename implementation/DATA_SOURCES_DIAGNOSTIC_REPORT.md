# Data Sources Dashboard Diagnostic Report

**Date**: October 15, 2025  
**Issue**: Data Sources Tab shows all services as paused/unavailable despite containers running  
**Investigator**: BMad Master  

---

## Executive Summary

The Data Sources tab is displaying all external data sources (carbon intensity, electricity pricing, air quality, calendar, smart meter) as "unhealthy" or unavailable, even though the Docker containers are running and healthy. The root cause is a **network connectivity issue** where the admin-api service is checking health endpoints on `localhost` instead of using Docker container names.

---

## Investigation Findings

### 1. Container Status ✅
All data source containers are running and healthy:

```
CONTAINER NAME                    STATUS                     PORTS
homeiq-carbon-intensity      Up 2 hours (healthy)       0.0.0.0:8010->8010/tcp
homeiq-electricity-pricing   Up 4 hours (healthy)       0.0.0.0:8011->8011/tcp
homeiq-air-quality           Up 43 minutes (healthy)    0.0.0.0:8012->8012/tcp
homeiq-calendar              Restarting                 
homeiq-smart-meter           Up 3 hours (healthy)       0.0.0.0:8014->8014/tcp
```

**Note**: Calendar service is restarting (separate issue to investigate).

### 2. API Response ❌
The `/api/v1/health/services` endpoint returns:

```json
{
  "carbon-intensity-service": {
    "status": "unhealthy",
    "error_message": "Cannot connect to host localhost:8010 ssl:default [Connection refused]"
  },
  "electricity-pricing-service": {
    "status": "unhealthy",
    "error_message": "Cannot connect to host localhost:8011 ssl:default [Connection refused]"
  },
  ...
}
```

### 3. Root Cause Analysis 🔍

**Location**: `services/admin-api/src/health_endpoints.py` (lines 63-74)

```python
self.service_urls = {
    "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://localhost:8001"),
    "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://localhost:8002"),
    "influxdb": os.getenv("INFLUXDB_URL", "http://localhost:8086"),
    "weather-api": "https://api.openweathermap.org/data/2.5",
    # Data source services - THESE ARE THE PROBLEM
    "carbon-intensity-service": os.getenv("CARBON_INTENSITY_URL", "http://localhost:8010"),
    "electricity-pricing-service": os.getenv("ELECTRICITY_PRICING_URL", "http://localhost:8011"),
    "air-quality-service": os.getenv("AIR_QUALITY_URL", "http://localhost:8012"),
    "calendar-service": os.getenv("CALENDAR_URL", "http://localhost:8013"),
    "smart-meter-service": os.getenv("SMART_METER_URL", "http://localhost:8014")
}
```

**The Issue**:
- The admin-api service runs **inside a Docker container**
- It's trying to connect to `localhost:8010-8014`
- Inside the container, `localhost` refers to the container itself, not the host
- The services are running in **other containers** on the Docker network
- Solution: Use Docker container names (e.g., `http://homeiq-carbon-intensity:8010`)

### 4. Secondary Issues

#### A. Frontend API Path Mismatch
**Location**: `services/health-dashboard/src/services/api.ts` (line 116)

```typescript
const response = await fetch(`${this.baseUrl}/api/v1/health/services`);
```

The frontend is calling `/api/v1/health/services`, but the actual endpoint is `/health/services` (no `/api/v1` prefix from the admin-api perspective).

#### B. Data Structure Mismatch
**Location**: `services/health-dashboard/src/components/DataSourcesPanel.tsx` (line 199)

```typescript
<span>{getStatusIcon(status, source.status_detail, source.credentials_configured)}</span>
```

The frontend expects `status_detail` and `credentials_configured` fields, but the API only returns:
- `name`
- `status`
- `last_check`
- `response_time_ms`
- `error_message`

#### C. Missing Error Handler Reference
**Location**: `services/health-dashboard/src/components/DataSourcesPanel.tsx` (line 119)

```typescript
onClick={fetchDataSources}  // fetchDataSources is not defined in scope
```

This will cause a runtime error when the Retry button is clicked.

---

## Impact Assessment

### User Experience
- ⚠️ **Critical**: Users cannot see actual status of external data sources
- ⚠️ **High**: All data sources appear offline even when functioning
- ⚠️ **Medium**: Error boundary catches frontend crashes, shows generic error
- ⚠️ **Low**: Retry button doesn't work

### System Functionality
- ✅ **No impact on actual data collection** - services are running independently
- ✅ **No impact on data ingestion** - WebSocket and enrichment pipelines functioning
- ❌ **Monitoring and observability compromised** - cannot detect real issues

---

## Recommended Fixes

### Priority 1: Fix Network Connectivity (CRITICAL)

**File**: `services/admin-api/src/health_endpoints.py`

```python
self.service_urls = {
    "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://homeiq-websocket:8001"),
    "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://homeiq-enrichment:8002"),
    "influxdb": os.getenv("INFLUXDB_URL", "http://homeiq-influxdb:8086"),
    "weather-api": "https://api.openweathermap.org/data/2.5",
    # Data source services - FIX: Use Docker container names
    "carbon-intensity-service": os.getenv("CARBON_INTENSITY_URL", "http://homeiq-carbon-intensity:8010"),
    "electricity-pricing-service": os.getenv("ELECTRICITY_PRICING_URL", "http://homeiq-electricity-pricing:8011"),
    "air-quality-service": os.getenv("AIR_QUALITY_URL", "http://homeiq-air-quality:8012"),
    "calendar-service": os.getenv("CALENDAR_URL", "http://homeiq-calendar:8013"),
    "smart-meter-service": os.getenv("SMART_METER_URL", "http://homeiq-smart-meter:8014")
}
```

**Benefits**:
- Services can communicate via Docker network
- Environment variables can still override for custom deployments
- Consistent with websocket-ingestion and enrichment-pipeline patterns

### Priority 2: Fix Frontend API Path (HIGH)

**File**: `services/health-dashboard/src/services/api.ts`

```typescript
async getAllDataSources(): Promise<{...}> {
  try {
    // FIX: Remove /api/v1 prefix - it's not part of the admin-api router
    const response = await fetch(`${this.baseUrl}/health/services`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    ...
  }
}
```

**Alternative**: If nginx routing adds `/api/v1`, verify nginx configuration.

### Priority 3: Enhance API Response (MEDIUM)

**File**: `services/admin-api/src/health_endpoints.py`

Add additional fields to match frontend expectations:

```python
class ServiceHealth(BaseModel):
    """Service health model"""
    name: str
    status: str
    last_check: str
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    # ADD THESE:
    status_detail: Optional[str] = None  # More detailed status info
    credentials_configured: Optional[bool] = None  # Whether API keys are set
    uptime_seconds: Optional[float] = None  # Service uptime
```

### Priority 4: Fix Frontend Error Handler (LOW)

**File**: `services/health-dashboard/src/components/DataSourcesPanel.tsx`

```typescript
// Add refetch prop from hook
const { dataSources, loading, error, refetch } = useDataSources(30000);

// Use correct reference in button
<button
  onClick={refetch}  // FIX: Use refetch instead of fetchDataSources
  className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white transition-colors"
>
  Retry
</button>
```

### Priority 5: Investigate Calendar Service (MEDIUM)

The calendar service is in a restart loop. Check:
1. Container logs: `docker logs homeiq-calendar`
2. Environment variables
3. Dependencies (API keys, credentials)
4. Port conflicts

---

## Testing Plan

### 1. Verify Docker Network Connectivity
```bash
# Test from admin-api container
docker exec homeiq-admin curl http://homeiq-carbon-intensity:8010/health
```

### 2. Verify API Response
```bash
# Should return healthy status for running services
curl http://localhost:8003/health/services | jq
```

### 3. Verify Frontend Display
1. Navigate to dashboard
2. Click "Data Sources" tab
3. Verify services show correct status
4. Verify no TypeErrors in console
5. Test Retry button functionality

### 4. End-to-End Test
1. Stop a service: `docker stop homeiq-carbon-intensity`
2. Verify dashboard shows service as unhealthy
3. Start service: `docker start homeiq-carbon-intensity`
4. Wait 30 seconds (refresh interval)
5. Verify dashboard shows service as healthy

---

## Implementation Order

1. **Immediate** (5 mins): Fix Docker container names in admin-api
2. **Immediate** (5 mins): Fix frontend API path
3. **Quick** (10 mins): Fix frontend error handler reference
4. **Short** (30 mins): Enhance API response fields
5. **Separate** (TBD): Investigate calendar service restart issue

---

## Success Criteria

✅ All running services show "healthy" status in dashboard  
✅ No connection refused errors in API responses  
✅ Frontend displays data without TypeErrors  
✅ Retry button functions correctly  
✅ Status updates automatically every 30 seconds  
✅ Stopped services show "unhealthy" status accurately  

---

## Risk Assessment

**Low Risk**: These are configuration and network routing fixes with no schema changes  
**Rollback**: Simply revert the service URLs to original values  
**Testing**: Can test in isolation without affecting running services  
**Downtime**: Zero - services continue running during fix deployment  

---

## Additional Recommendations

1. **Add health check middleware**: Log all health check requests/responses
2. **Add network diagnostics endpoint**: Test Docker network connectivity
3. **Add service discovery**: Automatically discover services from Docker API
4. **Add credential validation**: Check API key presence before marking as unhealthy
5. **Add status caching**: Reduce load on services by caching health status
6. **Add alert thresholds**: Notify when services are down for > 5 minutes

---

**Status**: Ready for implementation  
**Next Step**: Apply Priority 1 fix to admin-api service URLs

