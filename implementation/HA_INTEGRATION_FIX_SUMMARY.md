# HA Integration Cards Fix - Summary

## Date: October 14, 2025

## Problem 
The Home Assistant Integration section on the Overview tab showed **0 for all 4 cards** (Devices, Entities, Integrations, Health).

## Root Cause ✅
**nginx DNS cache with stale IP address**

nginx in the health-dashboard container had cached an old IP address (`172.18.0.9`) for the `homeiq-data-api` service, but the service was actually running on a different IP (`172.18.0.8`). This caused all API requests to fail with 502 Bad Gateway errors.

## Solution Applied ✅
```bash
docker restart homeiq-dashboard
```

This forced nginx to re-resolve DNS names and get the correct IP addresses.

## Verification ✅
All endpoints are now working correctly:
- `/api/devices` - Returns 200 OK with 5 devices
- `/api/entities` - Returns 200 OK with 0 entities (correct)
- `/api/integrations` - Returns 200 OK with 0 integrations (correct)

## What You Should See Now

**Refresh your browser** at http://localhost:3000/ and the HA Integration cards should display:

| Card | Value | Status |
|------|-------|--------|
| **Devices** | 5 | ✅ Should show 5 devices |
| **Entities** | 0 | ✅ Correct (no entities discovered yet) |
| **Integrations** | 0 | ✅ Correct (no integrations yet) |
| **Health** | 0% | ✅ Correct (0/0 loaded integrations) |

The 5 devices are:
1. Sun (Home Assistant)
2. Moon (Home Assistant)
3. Person (Home Assistant)
4. Zone (Home Assistant)
5. Weather (OpenWeatherMap)

## Why Entities and Integrations Are 0

This is **expected behavior**:

- **Entities = 0:** The system hasn't discovered any entities yet from Home Assistant. Once the websocket connection processes entity state changes, this number will increase.

- **Integrations = 0:** No integration config entries have been stored in InfluxDB yet. These will be populated as the system ingests data from Home Assistant.

- **Health = 0%:** Calculated as (loaded integrations / total integrations). Since both are 0, the percentage is 0%. This will update once integrations are discovered.

## Long-Term Fix Recommended

To prevent this issue from recurring, add a DNS resolver to nginx. I recommend applying this fix:

### Option 1: Add DNS Resolver to nginx.conf (RECOMMENDED)

Edit `services/health-dashboard/nginx.conf` and add resolver directive:

```nginx
http {
    # Add Docker's internal DNS with short TTL
    resolver 127.0.0.11 valid=10s ipv6=off;
    
    # ... rest of config
}
```

Then modify proxy_pass directives to use variables (forces DNS re-resolution):

```nginx
location /api/devices {
    set $data_api homeiq-data-api:8006;
    proxy_pass http://$data_api/api/devices;
    # ... rest of proxy headers
}
```

### Option 2: Add Service Dependencies (EASIER)

Edit `docker-compose.yml` to ensure data-api is fully healthy before dashboard starts:

```yaml
services:
  health-dashboard:
    depends_on:
      data-api:
        condition: service_healthy
      admin-api:
        condition: service_healthy
```

## Quick Manual Fix (If It Happens Again)

If you recreate services or see 0 values again:

```bash
# Restart the dashboard to refresh nginx DNS cache
docker restart homeiq-dashboard

# Wait 5 seconds, then refresh browser
```

## Investigation Details

Full diagnostic report available at:
`implementation/analysis/HA_INTEGRATION_ZERO_VALUES_DIAGNOSIS.md`

## Next Steps

1. ✅ **Immediate:** Refresh your browser - cards should now show correct values
2. ⚠️ **Recommended:** Apply one of the long-term fixes above to prevent recurrence
3. 📊 **Monitor:** Watch the Entities count increase as websocket processes events

## Related Docker Logs

The nginx errors that confirmed the issue:
```
[error] connect() failed (111: Connection refused) while connecting to upstream, 
upstream: "http://172.18.0.9:8006/api/v1/alerts?severity=critical"
```

The successful API response after fix:
```
GET /api/devices HTTP/1.1" 200 OK
Content: {"devices":[...5 devices...], "count":5}
```

