# Device Display Troubleshooting Knowledge Base

## Issue: Dashboard Showing 0 Devices (502 Bad Gateway)

### Problem Description
Dashboard displays 0 devices despite backend API returning 99 devices correctly. The "Home Assistant Integration" section shows:
- Devices: 0
- Entities: 0  
- Active Services: 10
- System Health: 100%

### Root Cause Analysis
Nginx proxy in dashboard container was trying to connect to an outdated IP address for the data-api service:
- **Trying to connect to**: `172.18.0.13:8006` (stale DNS cache)
- **Actual service location**: `172.18.0.4:8006` (current IP)

This caused 502 Bad Gateway errors in nginx logs.

### Symptoms Checklist
- [ ] Dashboard shows 0 devices/entities
- [ ] API endpoint `http://localhost:3000/api/devices` returns 502 Bad Gateway
- [ ] Direct API call to `http://localhost:8006/api/devices` works fine
- [ ] Nginx logs show: `connect() failed (111: Connection refused) while connecting to upstream`

### Solution Steps
1. **Restart dashboard container** to clear DNS cache:
   ```bash
   docker restart ha-ingestor-dashboard
   ```

2. **Wait 10 seconds** for container to fully start

3. **Verify fix**:
   ```bash
   # Test API endpoint
   curl http://localhost:3000/api/devices
   # Should return JSON with 99 devices
   ```

### Verification Commands
```bash
# Check API endpoint
curl http://localhost:3000/api/devices

# Verify dashboard displays correct device count
# Check nginx logs
docker logs ha-ingestor-dashboard --tail 20
```

### Prevention Measures
- This issue typically occurs after Docker network changes
- Container restarts usually resolve DNS cache issues
- Monitor nginx logs for upstream connection errors
- Consider implementing health checks for upstream services

### Related Files
- `services/health-dashboard/nginx.conf` - Nginx proxy configuration
- `services/health-dashboard/src/hooks/useDevices.ts` - Frontend device fetching
- `services/health-dashboard/src/services/api.ts` - API client configuration

### Context7 Integration
This KB entry is integrated with Context7 for:
- **Search**: `*context7-kb-search "device display 502 gateway"`
- **Analytics**: `*context7-kb-analytics` for usage tracking
- **Status**: `*context7-kb-status` for KB health monitoring

### Date Created
October 17, 2025

### Status
✅ RESOLVED - Dashboard now displays 99 devices correctly

### Tags
- docker
- nginx
- dns-cache
- 502-gateway
- device-display
- troubleshooting
- home-assistant
