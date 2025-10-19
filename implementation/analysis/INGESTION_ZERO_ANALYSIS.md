# Ingestion Zero Events Analysis

**Investigation Date:** October 14, 2025  
**Investigator:** BMad Master  
**System:** HA Ingestor v1.0.0

## Executive Summary

The HA Ingestor system shows **0 events ingested** because the WebSocket connection to Home Assistant at `192.168.1.86:8123` is failing with "Connection Refused" errors, causing the connection manager to stop running.

## Investigation Findings

### 1. Environment Configuration Review

**Configuration File:** `infrastructure/env.example`
- `HOME_ASSISTANT_URL=http://192.168.1.86:8123`
- `HOME_ASSISTANT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (Valid JWT token)

**Active Container Environment:**
```bash
HOME_ASSISTANT_URL=http://192.168.1.86:8123
HOME_ASSISTANT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ENABLE_HOME_ASSISTANT=true
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_BUCKET=ha_events
INFLUXDB_ORG=home-assistant
```

### 2. Docker Container Status

**All Containers Healthy Except:**
- ✅ `homeiq-dashboard` - Up 33 minutes (healthy)
- ✅ `homeiq-data-api` - Up 33 minutes (healthy)
- ⚠️ `homeiq-websocket` - Up 33 minutes (healthy) but **connection manager not running**
- ✅ `homeiq-admin` - Up 33 minutes (healthy)
- ✅ `homeiq-enrichment` - Up 33 minutes (healthy)
- ✅ `homeiq-influxdb` - Up 33 minutes (healthy)
- 🔴 `homeiq-calendar` - **Restarting** (API key issues)
- 🔴 `homeiq-carbon-intensity` - **Restarting** (API key issues)
- 🔴 `homeiq-air-quality` - **Restarting** (API key issues)

### 3. WebSocket Service Logs Analysis

**Error Pattern:** Connection Refused to `192.168.1.86:8123`
```json
{
  "level": "ERROR",
  "message": "Cannot connect to host 192.168.1.86:8123 ssl:default [Connect call failed ('192.168.1.86', 8123)]",
  "exception": "ClientConnectorError",
  "error": "ConnectionRefusedError: [Errno 111] Connect call failed ('192.168.1.86', 8123)"
}
```

**Connection Attempts:**
- Total attempts: 20+
- Successful connections: 0
- Failed connections: 10
- Max reconnection attempts reached: 10
- Status: Connection manager stopped

### 4. Home Assistant Connectivity Test

**HTTP API Test (from host machine):**
```powershell
Status: 200 OK
Response: {"message":"API running."}
```
✅ Home Assistant HTTP API is accessible from the **host machine**

**WebSocket Connection (from Docker container):**
```
Connection Status: FAILED
Error: ConnectionRefusedError: [Errno 111] Connect call failed ('192.168.1.86', 8123)
```
🔴 Home Assistant WebSocket is **NOT accessible from Docker container**

### 5. Service Health Check Results

**WebSocket Ingestion Service Health:**
```json
{
  "status": "unhealthy",
  "reason": "Connection manager not running",
  "connection": {
    "is_running": false,
    "connection_attempts": 20,
    "successful_connections": 0,
    "failed_connections": 10
  },
  "subscription": {
    "is_subscribed": false,
    "total_events_received": 0
  }
}
```

**Admin API Health:**
```json
{
  "status": "healthy",
  "dependencies": [
    {"name": "InfluxDB", "status": "healthy"},
    {"name": "WebSocket Ingestion", "status": "healthy"},
    {"name": "Enrichment Pipeline", "status": "healthy"}
  ]
}
```

Note: Admin API reports WebSocket Ingestion as "healthy" because the health endpoint responds, but the actual connection manager is not running.

### 6. Dashboard State

**Screenshots Captured:**
- `dashboard-current-state.png` - Shows 0 events ingested
- Dashboard loads successfully
- All UI components render correctly
- Connection status indicators show disconnected state

## Root Cause Analysis

### Primary Issue: Network Connectivity

The Docker container running `websocket-ingestion` **cannot reach** Home Assistant at `192.168.1.86:8123` due to one of the following reasons:

1. **Network Routing Issue:**
   - Docker bridge network cannot route to `192.168.1.86`
   - The IP `192.168.1.86` is on the host network, but Docker containers are isolated

2. **Firewall/Security:**
   - Windows Firewall may be blocking incoming connections from Docker network
   - Home Assistant firewall rules may block Docker network IP ranges

3. **Home Assistant Configuration:**
   - Home Assistant may not be configured to accept WebSocket connections from Docker network IPs
   - `trusted_networks` or `http` configuration in Home Assistant may need adjustment

4. **Wrong URL:**
   - The `HOME_ASSISTANT_URL` should use a hostname that's resolvable from inside Docker
   - `192.168.1.86` may be the **host's IP**, but containers need to use `host.docker.internal` or similar

## Recommended Solutions

### Solution 1: Use Docker Host Gateway (RECOMMENDED)

Update the `HOME_ASSISTANT_URL` to use Docker's special hostname:

```bash
HOME_ASSISTANT_URL=http://host.docker.internal:8123
```

This allows Docker containers to access services running on the host machine.

**Implementation:**
1. Create `.env` file in root directory:
   ```bash
   HOME_ASSISTANT_URL=http://host.docker.internal:8123
   HOME_ASSISTANT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. Update `docker-compose.yml` to use the `.env` file:
   ```yaml
   websocket-ingestion:
     environment:
       - HOME_ASSISTANT_URL=${HOME_ASSISTANT_URL}
       - HOME_ASSISTANT_TOKEN=${HOME_ASSISTANT_TOKEN}
   ```

3. Restart the WebSocket service:
   ```bash
   docker-compose restart websocket-ingestion
   ```

### Solution 2: Update docker-compose.yml Network Mode

Add `extra_hosts` to the `websocket-ingestion` service:

```yaml
websocket-ingestion:
  extra_hosts:
    - "homeassistant.local:192.168.1.86"
    - "host.docker.internal:host-gateway"
```

### Solution 3: Home Assistant Network Configuration

Update Home Assistant's `configuration.yaml` to trust the Docker network:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.16.0.0/12
    - 192.168.0.0/16
  cors_allowed_origins:
    - "http://localhost:3000"
```

### Solution 4: Use Nabu Casa URL (If Available)

If Nabu Casa is configured and accessible:

```bash
HOME_ASSISTANT_URL=https://lwzisze94hrpqde9typkwgu5pptxdkoh.ui.nabu.casa
HOME_ASSISTANT_TOKEN=<nabu_casa_token>
```

## Verification Steps

After implementing a solution:

1. **Check WebSocket Service Logs:**
   ```bash
   docker logs homeiq-websocket --tail 50
   ```
   Look for: "WebSocket connection established" and "Successfully authenticated"

2. **Check WebSocket Health:**
   ```bash
   curl http://localhost:8001/health
   ```
   Look for: `"status": "healthy"` and `"is_running": true`

3. **Check Dashboard:**
   - Navigate to http://localhost:3000/
   - Click on "Events" tab
   - Should see events streaming in real-time
   - Ingestion count should increase

4. **Check InfluxDB Data:**
   ```bash
   docker exec homeiq-influxdb influx query 'from(bucket:"ha_events") |> range(start: -1h) |> count()'
   ```

## Additional Issues Found

### Secondary Issues: API Service Containers Restarting

The following services are restarting due to missing API keys:
- `homeiq-calendar` (Google Calendar API)
- `homeiq-carbon-intensity` (WattTime API)
- `homeiq-air-quality` (AirNow API)

**Recommendation:** These are non-critical for core event ingestion. They can be disabled or configured later:
```yaml
# docker-compose.yml - Comment out optional services
# - calendar-service
# - carbon-intensity-service
# - air-quality-service
```

## Impact Assessment

**Current State:**
- ✅ Dashboard: Functional
- ✅ Admin API: Functional
- ✅ Data API: Functional
- ✅ InfluxDB: Functional
- 🔴 **Event Ingestion: 0 events (PRIMARY ISSUE)**
- ⚠️ Weather Enrichment: 0 events processed (depends on ingestion)
- ⚠️ Sports Data: Functional but no HA integration
- 🔴 Optional Services: Restarting (secondary issue)

**Business Impact:**
- No Home Assistant events are being captured
- No historical data is being stored
- Dashboard shows accurate system status but no data
- All infrastructure is healthy except the HA connection

## Next Steps

1. **IMMEDIATE:** Implement Solution 1 (Docker Host Gateway)
2. **VERIFY:** Run verification steps to confirm ingestion
3. **MONITOR:** Watch logs for 5 minutes to ensure stable connection
4. **OPTIONAL:** Configure or disable restarting API services
5. **DOCUMENT:** Update deployment documentation with working configuration

## Files Involved

- `docker-compose.yml` - Main orchestration file
- `infrastructure/env.example` - Environment template
- `services/websocket-ingestion/src/websocket_client.py` - WebSocket client
- `services/websocket-ingestion/src/main.py` - Service entry point

## References

- Docker Documentation: [Networking in Compose](https://docs.docker.com/compose/networking/)
- Home Assistant: [HTTP Integration](https://www.home-assistant.io/integrations/http/)
- WebSocket Logs: See `docker logs homeiq-websocket`

