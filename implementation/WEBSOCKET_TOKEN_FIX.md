# WebSocket Connection Fix - Token Issue

**Date:** 2025-10-13  
**Issue:** WebSocket service cannot connect to Home Assistant  
**Root Cause:** Invalid/Revoked Home Assistant access token  
**Status:** ✅ SOLUTION PROVIDED

## Problem Summary

The WebSocket ingestion service is continuously failing to authenticate with Home Assistant, showing:
```
Authentication failed: {'type': 'auth_invalid', 'message': 'Invalid access token or password'}
```

### Investigation Results:

1. ✅ **Environment variables ARE set** in the container:
   - `HOME_ASSISTANT_URL=http://192.168.1.86:8123`
   - `HOME_ASSISTANT_TOKEN=eyJhbGci...` (JWT format)

2. ✅ **Token format is valid** - JWT structure is correct

3. ✅ **Token is NOT expired** - Valid until 2035-08-16

4. ❌ **Token is REJECTED by Home Assistant** - Returns 401 Unauthorized

### Root Cause:

The JWT token in your `.env` file has been **revoked or invalidated** by Home Assistant. This can happen when:
- The token was deleted from Home Assistant's token management
- The token was created for a different HA instance
- The token permissions were changed
- Home Assistant was restored from a backup without tokens

## Solution: Generate New Token

### Option 1: Automated Script (Recommended)

I've created a PowerShell script that will:
- Safely update your token
- Create a backup of your current .env
- Test the new token
- Preserve all other settings

**Run this script:**
```powershell
cd c:\cursor\homeiq
.\scripts\update-ha-token.ps1
```

The script will:
1. Show your current configuration
2. Guide you through creating a new token
3. Update .env with the new token
4. Test the token against Home Assistant
5. Provide next steps

### Option 2: Manual Update

If you prefer to update manually:

#### Step 1: Generate New Token in Home Assistant

1. Open Home Assistant: http://192.168.1.86:8123
2. Click your profile (bottom left corner)
3. Scroll down to **"Long-Lived Access Tokens"**
4. Click **"CREATE TOKEN"**
5. Give it a name: `HA Ingestor`
6. **IMPORTANT:** Copy the token immediately (it's only shown once!)

#### Step 2: Update .env File

```powershell
# Backup current .env
Copy-Item .env .env.backup

# Edit .env file
notepad .env
```

Find the line:
```
HOME_ASSISTANT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Replace with your new token:
```
HOME_ASSISTANT_TOKEN=<your_new_token_here>
```

**IMPORTANT:** Make sure to keep `HOME_ASSISTANT_URL` and all other lines unchanged!

#### Step 3: Test the New Token

```powershell
# Test token with REST API
$token = "<your_new_token>"
$headers = @{ "Authorization" = "Bearer $token" }
Invoke-WebRequest -Uri "http://192.168.1.86:8123/api/" -Headers $headers
```

You should get a 200 OK response with JSON data about your HA instance.

#### Step 4: Restart WebSocket Service

```powershell
docker-compose restart websocket-ingestion
```

#### Step 5: Verify Connection

```powershell
# Watch logs for successful connection
docker logs -f homeiq-websocket

# Look for these messages:
# ✓ "Successfully authenticated with Home Assistant"
# ✓ "Successfully connected to Home Assistant"
```

## Verification Steps

After updating the token and restarting:

### 1. Check WebSocket Connection
```powershell
docker logs --tail 50 homeiq-websocket | Select-String "Connected|authenticated"
```

**Success indicators:**
- ✅ "Successfully authenticated with Home Assistant"
- ✅ "Successfully connected to Home Assistant"  
- ✅ "Subscribing to events"

**Failure indicators:**
- ❌ "Authentication failed"
- ❌ "Connection failed"
- ❌ "Disconnected from Home Assistant"

### 2. Verify Events Are Flowing
```powershell
# Check InfluxDB for recent events
docker exec homeiq-influxdb influx query `
  'from(bucket:"home_assistant_events") |> range(start: -5m) |> count()' `
  --token homeiq-token --org homeiq
```

You should see counts increasing over time as events are ingested.

### 3. Check Enrichment Pipeline
```powershell
docker logs --tail 50 homeiq-enrichment | Select-String "process_event"
```

Should show events being processed in real-time.

## What Gets Preserved

The solution **preserves** all your existing configuration:
- ✅ Home Assistant URL
- ✅ InfluxDB credentials
- ✅ Weather API keys
- ✅ All other environment variables
- ✅ Docker volumes and data

**Only the invalid token is replaced.**

## Troubleshooting

### Issue: "Token still not working after update"

**Check:**
1. Did you copy the FULL token? (No spaces, complete string)
2. Is the token from the correct Home Assistant instance?
3. Try creating a new token with a different name

**Test manually:**
```powershell
$token = "your_token_here"
$headers = @{ "Authorization" = "Bearer $token" }
Invoke-WebRequest -Uri "http://192.168.1.86:8123/api/" -Headers $headers
```

### Issue: "Service still shows disconnected"

**Solutions:**
1. Restart the service: `docker-compose restart websocket-ingestion`
2. Check HA is accessible: `Test-NetConnection 192.168.1.86 -Port 8123`
3. Verify .env file was loaded: `docker exec homeiq-websocket printenv | Select-String HOME_ASSISTANT`

### Issue: "Lost my backup"

**Restore from automatic backup:**
```powershell
# List backups
Get-ChildItem .env.backup.*

# Restore specific backup
Copy-Item .env.backup.YYYYMMDD-HHMMSS .env
```

## Expected Results

After successful token update:

**Before:**
```
⚠️ Status: Disconnected
⚠️ Authentication: Failing
⚠️ Events: Not ingesting from HA
```

**After:**
```
✅ Status: Connected
✅ Authentication: Successful
✅ Events: Flowing to InfluxDB
```

## Files Modified

- **`.env`** - Updated HOME_ASSISTANT_TOKEN value
- **`.env.backup.YYYYMMDD-HHMMSS`** - Automatic backup (created by script)

## Related Documentation

- [Home Assistant Long-Lived Access Tokens](https://www.home-assistant.io/docs/authentication/)
- [InfluxDB Event Write Diagnosis](./analysis/INFLUXDB_EVENT_WRITE_DIAGNOSIS.md)
- [WebSocket Service Documentation](../services/websocket-ingestion/README.md)

## Next Steps After Fix

Once the WebSocket connection is established:

1. **Monitor initial sync:**
   - Watch for events flowing in logs
   - Check InfluxDB data increasing

2. **Verify all entity types:**
   - Sensors, lights, switches
   - Weather data enrichment
   - State changes captured

3. **Check dashboard:**
   - Open http://localhost:3000
   - Verify Events tab shows real-time data
   - Check Services tab shows WebSocket as connected

---

**Need Help?**

If the automated script doesn't work or you encounter issues:
1. Check the backup file was created: `ls .env.backup.*`
2. Review Home Assistant logs: `docker logs homeiq-websocket`
3. Verify Home Assistant is accessible: `curl http://192.168.1.86:8123`

