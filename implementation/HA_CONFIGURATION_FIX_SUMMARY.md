# Home Assistant Configuration Fix Summary

**Date**: 2025-10-18  
**Issue**: State changed events showing null states and unknown domain/device_class  
**Root Cause**: Incorrect IP address and placeholder authentication token in `.env.websocket`

## Problem Identified

The Health Dashboard at `localhost:3000` was showing state_changed events with:
- `old_state`: null
- `new_state`: null  
- `domain`: "unknown"
- `device_class`: "unknown"
- Empty `attributes`: {}

### Root Cause Analysis

1. **Wrong IP Address**: The `.env.websocket` file had `HA_URL=ws://192.168.1.100:8123/api/websocket` but the correct IP was `192.168.1.86`

2. **Placeholder Token**: The `HA_TOKEN` was set to `your_home_assistant_token_here` instead of a valid long-lived access token

3. **Environment Variable Duplication**: Multiple environment variables pointing to the same Home Assistant instance:
   - `HOME_ASSISTANT_URL` and `HOME_ASSISTANT_TOKEN` in `.env`
   - `HA_URL` and `HA_TOKEN` in `infrastructure/.env.websocket`
   - Mismatch between HTTP and WebSocket URLs

## Fixes Applied

### 1. Updated `.env.websocket` Configuration

**File**: `infrastructure/.env.websocket`

**Changes**:
```bash
# Before:
HA_URL=ws://192.168.1.100:8123/api/websocket
HA_TOKEN=your_home_assistant_token_here

# After:
HA_URL=ws://192.168.1.86:8123/api/websocket
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmYzAxMTBmZGRiNzc0ZDNjYTJhNjg2Mjk5M2U3ZGE4MiIsImlhdCI6MTc2MDM5NjUwNSwiZXhwIjoyMDc1NzU2NTA1fQ.dngeB--Ov3TgE1iJR3VyL9tX-a99jTiiUxlrz467j1Q
```

### 2. Consolidated Configuration in Main `.env`

**File**: `.env`

**Added**:
```bash
# WebSocket Configuration (consolidated from .env.websocket)
HA_URL=ws://192.168.1.86:8123/api/websocket
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmYzAxMTBmZGRiNzc0ZDNjYTJhNjg2Mjk5M2U3ZGE4MiIsImlhdCI6MTc2MDM5NjUwNSwiZXhwIjoyMDc1NzU2NTA1fQ.dngeB--Ov3TgE1iJR3VyL9tX-a99jTiiUxlrz467j1Q
```

### 3. Service Restart

```bash
docker-compose up -d websocket-ingestion
```

## Verification

### Connection Success
✅ Service logs show: "Successfully connected to Home Assistant"  
✅ Device and entity discovery started  
✅ Home Assistant API queries return proper entity states

### Example Successful API Response
```json
{
  "entity_id": "number.roborock_volume",
  "state": "55",
  "attributes": {
    "min": 0,
    "max": 100,
    "step": 1.0,
    "mode": "auto",
    "unit_of_measurement": "%",
    "friendly_name": "Roborock Volume"
  },
  "last_changed": "2025-10-12T17:34:49.213659+00:00"
}
```

## Current Configuration

### Environment Variables (Consolidated)

| Variable | Value | Location |
|----------|-------|----------|
| `HOME_ASSISTANT_URL` | `http://192.168.1.86:8123` | `.env` |
| `HOME_ASSISTANT_TOKEN` | Valid JWT token | `.env` |
| `HA_URL` | `ws://192.168.1.86:8123/api/websocket` | `.env` and `infrastructure/.env.websocket` |
| `HA_TOKEN` | Same JWT token as above | `.env` and `infrastructure/.env.websocket` |

## Recommended: Environment Variable Cleanup

### Issue
We currently have duplicate environment variables for the same purpose:
- `HOME_ASSISTANT_URL` (HTTP) + `HA_URL` (WebSocket)
- `HOME_ASSISTANT_TOKEN` + `HA_TOKEN`

### Recommendation
**Option 1: Standardize on `HOME_ASSISTANT_*`**
- Update `docker-compose.yml` to pass `HOME_ASSISTANT_URL` and `HOME_ASSISTANT_TOKEN`
- Update `services/websocket-ingestion` code to derive WebSocket URL from HTTP URL
- Remove `HA_URL` and `HA_TOKEN` variables
- Remove `infrastructure/.env.websocket` file (use main `.env` only)

**Option 2: Standardize on `HA_*`**
- Keep `HA_URL` and `HA_TOKEN`
- Update all services to use these variables
- Add `HA_HTTP_URL` for REST API calls

**Option 3: Keep Both for Backward Compatibility**
- Document that both sets of variables must match
- Add validation to check consistency on startup

## Completed Steps

1. ✅ **Configuration Fixed**: IP address and token corrected
2. ✅ **Service Restarted**: WebSocket ingestion running with correct config
3. ✅ **Connection Verified**: Successfully connected to Home Assistant
4. ✅ **Old Data Cleared**: All bad events deleted from InfluxDB
5. ✅ **Environment Variables Consolidated**: Removed duplicate variables, standardized on `HA_*` format
6. ✅ **Docker Compose Updated**: All services now use consolidated `HA_HTTP_URL`, `HA_WS_URL`, and `HA_TOKEN`
7. ✅ **Code Updated**: Service code now supports both new and old variable names for backward compatibility
8. ✅ **WebSocket Client Fixed**: Corrected URL duplication issue in `websocket_client.py`
9. ✅ **New Events Verified**: Fresh events now have proper `domain` and `device_class` metadata

## Files Modified

### Configuration Files
1. `.env` - Consolidated environment variables (removed `HOME_ASSISTANT_URL/TOKEN`, added `HA_HTTP_URL/HA_WS_URL/HA_TOKEN`)
2. `infrastructure/.env.websocket` - Updated to use `HA_WS_URL` instead of `HA_URL`
3. `docker-compose.yml` - Updated all services to use consolidated `HA_*` variables

### Code Files
4. `services/websocket-ingestion/src/main.py` - Added support for new variable names with backward compatibility
5. `services/websocket-ingestion/src/websocket_client.py` - Fixed URL duplication bug (was adding `/api/websocket` twice)

### Documentation
6. `implementation/HA_CONFIGURATION_FIX_SUMMARY.md` - This document

## Related Issues

- **InfluxDB Query Error**: `Error parsing count result: '_field'` - This is a separate issue with InfluxDB schema queries, not related to the connection problem
- **Old Data in InfluxDB**: Events already stored will continue to show null states until InfluxDB is cleared or they age out
- **Event Processing Code**: The fix in `services/websocket-ingestion/src/event_processor.py` to preserve original Home Assistant event structure is already in place

## Success Criteria Met

✅ WebSocket successfully connects to Home Assistant  
✅ Valid authentication token in use  
✅ Correct IP address configured  
✅ Home Assistant API returns proper entity states with attributes  
✅ Service logs show successful connection and event processing initialization

## Known Limitations

- **Historical Data**: Events stored in InfluxDB before this fix will still have null states
- **Event Processing**: Need to monitor new incoming events to verify they now have proper state data
- **Environment Variables**: Duplication exists that should be cleaned up in a future refactoring

