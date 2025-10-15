# HA Integration Cards Showing Zero Values - Diagnostic Report

## Date: October 14, 2025

## Issue
The Home Assistant Integration section on the Overview tab shows 0 for all 4 cards:
- Devices: 0
- Entities: 0  
- Integrations: 0
- Health: 0%

## Investigation Findings

### 1. Backend API Status ✅
**Data-API service is running and responding correctly:**

```bash
$ curl http://localhost:8006/api/devices
{"devices":[
  {"device_id":"a0d7b954f1b8c9e2f3a4b5c6d7e8f9a0","name":"Sun","manufacturer":"Home Assistant","model":"Sun",...},
  {"device_id":"b1e8c965f2c9d0e3f4a5b6c7d8e9f0a1","name":"Moon","manufacturer":"Home Assistant","model":"Moon",...},
  {"device_id":"c2f9d076f3d0e1f4a5b6c7d8e9f0a1b2","name":"Person","manufacturer":"Home Assistant","model":"Person",...},
  {"device_id":"d3a0e187f4e1f2a5b6c7d8e9f0a1b2c3","name":"Zone","manufacturer":"Home Assistant","model":"Zone",...},
  {"device_id":"e4b1f298f5f2a3b6c7d8e9f0a1b2c3d4","name":"Weather","manufacturer":"OpenWeatherMap","model":"Weather",...}
],"count":5,"limit":100}

$ curl http://localhost:8006/api/entities
{"entities":[],"count":0,"limit":100}

$ curl http://localhost:8006/api/integrations  
{"integrations":[],"count":0}
```

**Backend Response Summary:**
- ✅ **Devices API:** Returns 5 devices (Sun, Moon, Person, Zone, Weather)
- ✅ **Entities API:** Returns 0 entities (empty but valid response)
- ✅ **Integrations API:** Returns 0 integrations (empty but valid response)

### 2. Docker Logs Analysis
**Data-API logs show:**
- ✅ Health checks: passing regularly
- ✅ API requests: `GET /api/devices HTTP/1.1" 200 OK` (successful)
- ⚠️ **Warning:** Multiple "Error in webhook event detector: InfluxDB client not connected" errors (unrelated to devices API)

### 3. Frontend Code Analysis

**File: `services/health-dashboard/src/hooks/useDevices.ts`**
- Uses `dataApi.getDevices()` to fetch devices
- Expects response format: `{ devices: [], count: number }`
- Sets `devices` state from `response.devices || []`

**File: `services/health-dashboard/src/services/api.ts`**
- `DataApiClient.getDevices()` calls: `${this.baseUrl}/devices`
- `baseUrl` = `DATA_API_BASE_URL` = `/api` (from env)
- **Constructed URL:** `/api/devices` ✅ (correct)

**File: `services/health-dashboard/src/components/tabs/OverviewTab.tsx`**
```typescript
Line 66: const { devices, entities, integrations, loading: devicesLoading } = useDevices();
Line 163: const haIntegration = devices.length > 0 ? calculateHAIntegrationHealth() : null;
Line 414: {haIntegration?.totalDevices || 0}  // Shows 0 when haIntegration is null
```

**Root Cause Logic:**
1. If `devices.length === 0`, then `haIntegration = null`
2. When `haIntegration` is null, all cards show `|| 0` fallback values
3. Therefore, the issue is that `devices` array is empty in the frontend

### 4. nginx Routing ✅
**File: `services/health-dashboard/nginx.conf`**
```nginx
Line 44-51: location /api/devices {
    proxy_pass http://ha-ingestor-data-api:8006/api/devices;
    ...
}
```
✅ Routing is correctly configured

### 5. API Endpoint Implementation ✅
**File: `services/data-api/src/devices_endpoints.py`**
```python
Line 92: @router.get("/api/devices", response_model=DevicesListResponse)
```
✅ Endpoint path matches frontend expectations

## Root Cause Hypothesis

The backend is returning data correctly, but the frontend is not receiving it. Possible causes:

### A. CORS or Network Error (Most Likely)
The browser may be blocking the request or there's a network error that's being silently caught in the try/catch block.

**Evidence Needed:**
- Check browser console for errors
- Check browser Network tab for failed requests
- Check if `/api/devices` request shows in network tab

### B. Proxy Routing Issue
The nginx proxy may not be correctly routing requests from the browser.

**Test:** Check if direct API call works from browser:
```
http://localhost:3000/api/devices
```

### C. Environment Variable Issue
The `VITE_DATA_API_URL` may not be set correctly, causing wrong URL construction.

**File to check:** `services/health-dashboard/.env` or build-time env vars

### D. Response Parsing Error
The frontend may be receiving data but failing to parse it correctly.

## Recommended Next Steps

### Immediate Diagnostics (Run These Now)

1. **Check Browser Console:**
   ```javascript
   // Open browser console (F12) and look for:
   - Red error messages
   - Failed network requests
   - CORS errors
   ```

2. **Check Network Tab:**
   ```
   - Open browser DevTools → Network tab
   - Filter by "XHR" or "Fetch"
   - Look for /api/devices request
   - Check status code and response
   ```

3. **Test Direct API Access:**
   ```bash
   # From browser, navigate to:
   http://localhost:3000/api/devices
   
   # Should return JSON with 5 devices
   ```

4. **Check Frontend Environment Variables:**
   ```bash
   # In health-dashboard container
   docker exec ha-ingestor-dashboard env | grep VITE
   ```

5. **Add Debug Logging:**
   ```typescript
   // In useDevices.ts, line 48, add:
   console.log('Fetching devices from:', dataApi);
   console.log('Response:', response);
   ```

### Verification Commands

```bash
# 1. Verify nginx is routing correctly
curl -v http://localhost:3000/api/devices

# 2. Check data-api directly
curl -v http://localhost:8006/api/devices

# 3. Check from within dashboard container
docker exec ha-ingestor-dashboard wget -O- http://ha-ingestor-data-api:8006/api/devices
```

## ROOT CAUSE IDENTIFIED ✅

**Problem:** nginx DNS cache with stale IP address

### What Happened:
1. nginx cached DNS resolution: `ha-ingestor-data-api` → `172.18.0.9`
2. data-api container was recreated/restarted and got new IP: `172.18.0.8`
3. nginx kept using the old cached IP `172.18.0.9`, causing "Connection refused" (502 errors)
4. Frontend received 502 errors, resulting in empty device/entity/integration arrays
5. OverviewTab displayed 0 for all cards due to empty arrays

### Evidence:
```
nginx error log:
connect() failed (111: Connection refused) while connecting to upstream, 
upstream: "http://172.18.0.9:8006/api/v1/alerts?severity=critical"

docker inspect ha-ingestor-data-api:
"IPAddress": "172.18.0.8"  ← actual IP is different!
```

## SOLUTION APPLIED ✅

**Fix:** Restart nginx container to force DNS re-resolution

```bash
docker restart ha-ingestor-dashboard
```

### Verification:
```bash
# Before restart:
$ curl http://localhost:3000/api/devices
502 Bad Gateway

# After restart:
$ curl http://localhost:3000/api/devices
Status: 200 OK, Content Length: 1078 bytes
{"devices":[...5 devices...], "count":5, "limit":100}

# All endpoints working:
/api/devices      : Status=200 ✅ (5 devices)
/api/entities     : Status=200 ✅ (0 entities - correct)
/api/integrations : Status=200 ✅ (0 integrations - correct)
```

## Expected Dashboard Display (After Page Refresh)

The HA Integration cards should now show:
- **Devices:** 5 ✅ (Sun, Moon, Person, Zone, Weather)
- **Entities:** 0 ✅ (correct - no entities discovered yet)
- **Integrations:** 0 ✅ (correct - no integrations configured yet)
- **Health:** 0% ✅ (correct - 0/0 loaded integrations)

## Prevention for Future

This issue can occur when:
- Docker containers are recreated with `docker-compose up --force-recreate`
- Services restart and get new IP addresses
- nginx starts before dependent services are fully ready

### Recommended Solutions:

1. **Use DNS resolver with TTL (Best Long-term Fix):**
```nginx
# Add to nginx.conf:
resolver 127.0.0.11 valid=10s;  # Docker's internal DNS
set $data_api http://ha-ingestor-data-api:8006;
proxy_pass $data_api/api/devices;
```

2. **Add health check dependency:**
```yaml
# In docker-compose.yml:
health-dashboard:
  depends_on:
    data-api:
      condition: service_healthy
```

3. **Quick manual fix (current approach):**
```bash
# When services get recreated:
docker restart ha-ingestor-dashboard
```

## Related Files
- `services/health-dashboard/src/hooks/useDevices.ts` - Data fetching logic
- `services/health-dashboard/src/services/api.ts` - API client (line 292-300)
- `services/health-dashboard/src/components/tabs/OverviewTab.tsx` - Display logic
- `services/health-dashboard/nginx.conf` - Proxy routing (line 44-69) ⚠️ **Needs resolver directive**
- `services/data-api/src/devices_endpoints.py` - Backend endpoints

