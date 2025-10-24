# Data Sources Status Fix - Implementation Plan

**Date**: October 15, 2025  
**Epic**: Data Sources Status Dashboard Accuracy  
**Priority**: CRITICAL  
**Estimated Time**: 30 minutes  

---

## Problem Summary

The Data Sources tab displays all external data sources as "unhealthy" with "Connection refused" errors, even though all Docker containers are running and healthy. Root cause: admin-api is checking `localhost` instead of Docker container names.

---

## Implementation Steps

### Step 1: Fix Admin API Service URLs (5 minutes)

**File**: `services/admin-api/src/health_endpoints.py`

**Change lines 63-74** from `localhost` to Docker container names:

```python
self.service_urls = {
    "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://homeiq-websocket:8001"),
    "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://homeiq-enrichment:8002"),
    "influxdb": os.getenv("INFLUXDB_URL", "http://homeiq-influxdb:8086"),
    "weather-api": "https://api.openweathermap.org/data/2.5",
    "carbon-intensity-service": os.getenv("CARBON_INTENSITY_URL", "http://homeiq-carbon-intensity:8010"),
    "electricity-pricing-service": os.getenv("ELECTRICITY_PRICING_URL", "http://homeiq-electricity-pricing:8011"),
    "air-quality-service": os.getenv("AIR_QUALITY_URL", "http://homeiq-air-quality:8012"),
    "calendar-service": os.getenv("CALENDAR_URL", "http://homeiq-calendar:8013"),
    "smart-meter-service": os.getenv("SMART_METER_URL", "http://homeiq-smart-meter:8014")
}
```

**Action**: Restart admin-api service after change
```bash
docker restart homeiq-admin
```

---

### Step 2: Fix Frontend API Path (5 minutes)

**File**: `services/health-dashboard/src/services/api.ts`

**Change line 116** from:
```typescript
const response = await fetch(`${this.baseUrl}/api/v1/health/services`);
```

To:
```typescript
const response = await fetch(`${this.baseUrl}/api/v1/health/services`);
```

**Action**: Rebuild and restart dashboard
```bash
cd services/health-dashboard
npm run build
docker restart homeiq-dashboard
```

---

### Step 3: Fix Frontend Error Handler (5 minutes)

**File**: `services/health-dashboard/src/components/DataSourcesPanel.tsx`

**Change line 119** from:
```typescript
onClick={fetchDataSources}
```

To:
```typescript
onClick={refetch}
```

**Note**: The hook already provides `refetch` - just use the correct reference.

---

### Step 4: Test the Fixes (10 minutes)

#### A. Test API Directly
```bash
# Should show healthy services
curl http://localhost:8003/api/v1/health/services | jq
```

Expected: Carbon Intensity, Electricity Pricing, Air Quality, Smart Meter show "healthy" status.

#### B. Test Dashboard
1. Navigate to http://localhost:3000
2. Click "🌐 Data Sources" tab
3. Verify services show correct status (not all unhealthy)
4. Check browser console for errors

#### C. Test Service Detection
```bash
# Stop a service
docker stop homeiq-carbon-intensity

# Wait 30 seconds, check dashboard shows it as unhealthy

# Start service
docker start homeiq-carbon-intensity

# Wait 30 seconds, check dashboard shows it as healthy
```

---

### Step 5: Optional Enhancements (Future)

#### A. Add Missing API Fields
Enhance `ServiceHealth` model in `health_endpoints.py`:
```python
class ServiceHealth(BaseModel):
    name: str
    status: str
    last_check: str
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    status_detail: Optional[str] = None  # NEW
    credentials_configured: Optional[bool] = None  # NEW
    uptime_seconds: Optional[float] = None  # NEW
    api_usage: Optional[Dict[str, Any]] = None  # NEW
```

#### B. Enhance Health Check Logic
Add credential detection:
```python
# Check if API key is configured
api_key = os.getenv(f"{service_name.upper()}_API_KEY")
if not api_key:
    services_health[service_name] = ServiceHealth(
        name=service_name,
        status="degraded",
        status_detail="credentials_missing",
        credentials_configured=False,
        last_check=datetime.now().isoformat()
    )
```

---

## Validation Checklist

- [ ] Admin API successfully connects to all running services via Docker network
- [ ] Frontend fetches data without 404 errors
- [ ] Data Sources tab displays without TypeErrors
- [ ] Running services show "healthy" status
- [ ] Stopped services show "unhealthy" status
- [ ] Retry button works correctly
- [ ] Status auto-refreshes every 30 seconds
- [ ] Calendar service restart issue documented (separate investigation)

---

## Rollback Plan

If issues arise:

1. **Revert admin-api changes**:
   ```bash
   git checkout services/admin-api/src/health_endpoints.py
   docker restart homeiq-admin
   ```

2. **Revert frontend changes**:
   ```bash
   git checkout services/health-dashboard/src/services/api.ts
   git checkout services/health-dashboard/src/components/DataSourcesPanel.tsx
   cd services/health-dashboard && npm run build
   docker restart homeiq-dashboard
   ```

---

## Known Issues / Follow-up Tasks

1. **Calendar Service Restarting**: Investigate why calendar service is in restart loop
2. **API Path Routing**: Verify nginx routing - frontend expects `/api/v1` prefix
3. **Weather API**: Uses external API - should have separate credential check
4. **Missing Fields**: Frontend expects more fields than API provides (enhancement)

---

## Success Metrics

- **Zero "Connection refused" errors** from admin-api
- **Accurate service status** displayed on dashboard
- **No frontend errors** in browser console
- **Working retry mechanism** for error recovery
- **Automatic status updates** every 30 seconds

---

## Timeline

| Step | Duration | Total Time |
|------|----------|------------|
| 1. Fix admin-api URLs | 5 min | 5 min |
| 2. Fix frontend API path | 5 min | 10 min |
| 3. Fix error handler | 5 min | 15 min |
| 4. Test changes | 10 min | 25 min |
| 5. Document results | 5 min | 30 min |

**Total Estimated Time**: 30 minutes

---

## Dependencies

- Docker network `homeiq-network` (already exists)
- All services must be on the same Docker network
- Container names must match docker-compose.yml
- No external dependencies or schema changes

---

## Next Steps

1. **Apply fixes** (Steps 1-3)
2. **Test thoroughly** (Step 4)
3. **Monitor dashboard** for 5 minutes to verify auto-refresh
4. **Document any issues** found during testing
5. **Create separate ticket** for calendar service investigation

---

**Ready to Implement**: YES ✅  
**Breaking Changes**: NO ❌  
**Requires Restart**: YES (admin-api, dashboard)  
**Risk Level**: LOW 🟢

