# Health Dashboard Fix Plan
**Date:** October 12, 2025  
**Status:** Ready for Implementation  
**Dashboard URL:** http://localhost:3000/

---

## Executive Summary

The Health Dashboard at http://localhost:3000/ is showing most services as unhealthy despite Docker containers reporting healthy status. Root cause analysis identified 4 critical issues:

1. **InfluxDB Field Type Conflict** - Events being dropped due to schema mismatch
2. **Admin API Health Endpoint Mismatch** - Wrong health check URL
3. **Missing Data-Retention Service** - Service referenced but not deployed
4. **WebSocket Authentication Failure** - 403 Forbidden errors on log streaming

---

## Current State Analysis

### What's Working ✅
- Docker containers: All 6 services healthy and running
- WebSocket ingestion: Connected to Home Assistant
- Services responding on correct ports
- Dashboard UI loading correctly

### What's Broken ❌
| Issue | Impact | Severity |
|-------|--------|----------|
| InfluxDB type conflicts | Events dropped, HTTP 500 errors | **CRITICAL** |
| Health endpoint mismatch | False negatives in monitoring | **HIGH** |
| Missing data-retention | Connection timeouts, UI errors | **MEDIUM** |
| WebSocket auth failure | No real-time log streaming | **MEDIUM** |

---

## Detailed Issue Analysis

### Issue 1: InfluxDB Field Type Conflict ⚠️ CRITICAL

**Error Pattern:**
```
field type conflict: input field "attr_azimuth" on measurement "home_assistant_events" 
is type string, already exists as type float dropped=1
```

**Root Cause:**
- Home Assistant is sending `attr_azimuth` with mixed types (float, then string, then float)
- InfluxDB enforces strict field typing - once a field is defined as float, it cannot accept strings
- This causes the enrichment service to fail writing events → HTTP 500 errors → cascading failures

**Impact:**
- Events being dropped silently
- HTTP 500 errors from enrichment-pipeline
- Websocket-ingestion receiving failures
- Dashboard showing 0 events/min

**Best Practice from Context7 KB:**
> "InfluxDB enforces strict schema consistency. Use type coercion and validation BEFORE writing to prevent field type conflicts." - InfluxDB Python Patterns

**Solution Options:**

**Option A: Type Coercion (Recommended)**
```python
# services/enrichment-pipeline/src/data_normalizer.py
def normalize_field_types(data: dict) -> dict:
    """Ensure consistent field types before InfluxDB write"""
    
    # Known numeric fields that may arrive as strings
    numeric_fields = ['attr_azimuth', 'attr_elevation', 'attr_brightness']
    
    for field in numeric_fields:
        if field in data and data[field] is not None:
            try:
                data[field] = float(data[field])
            except (ValueError, TypeError):
                # If conversion fails, remove field rather than cause conflict
                logger.warning(f"Removing non-numeric field {field}: {data[field]}")
                del data[field]
    
    return data
```

**Option B: Separate Measurements (Alternative)**
```python
# Use different measurements for different data types
if isinstance(value, str):
    measurement = f"{measurement_name}_str"
else:
    measurement = f"{measurement_name}_num"
```

**Option C: Schema Migration (Nuclear Option)**
```bash
# Drop and recreate bucket (ONLY if data is disposable)
docker exec -it homeiq-influxdb influx bucket delete --name events
docker exec -it homeiq-influxdb influx bucket create --name events
```

---

### Issue 2: Admin API Health Endpoint Mismatch 🔍 HIGH

**Current State:**
- Dashboard checking: `http://admin-api:8004/health`
- Admin API serving: `http://admin-api:8004/api/health`
- Result: HTTP 404 errors, false negative in monitoring

**Evidence:**
```
docker-compose.yml line 174:
    test: ["CMD", "curl", "-f", "http://localhost:8004/api/health"]

Dashboard checking: GET /health - Status: 404
```

**Solution:**
Update dashboard service configuration to use correct endpoint:

```typescript
// services/health-dashboard/src/services/api.ts
const API_ENDPOINTS = {
  health: '/api/health',        // ✅ Add /api prefix
  stats: '/api/v1/stats',
  services: '/api/v1/services'
}
```

---

### Issue 3: Missing Data-Retention Service 🚫 MEDIUM

**Current State:**
- Dashboard expects service at `http://data-retention:8080`
- Docker container does not exist
- Result: Connection timeout errors

**Evidence:**
```bash
$ docker ps -a --filter "name=data-retention"
# No results
```

**Best Practice from Context7 KB:**
> "Only deploy services that are actively being used. Phantom service references create false alarms and confusion."

**Solution Options:**

**Option A: Remove from Dashboard (Recommended)**
```typescript
// services/health-dashboard/src/config.ts
const CORE_SERVICES = [
  { name: 'websocket-ingestion', port: 8001 },
  { name: 'enrichment-pipeline', port: 8002 },
  // { name: 'data-retention', port: 8080 },  // ❌ Remove until deployed
  { name: 'admin-api', port: 8004 },
  { name: 'health-dashboard', port: 80 },
  { name: 'influxdb', port: 8086 }
]
```

**Option B: Deploy the Service (If Needed)**
```bash
# Only if data retention is actually needed
docker-compose up -d data-retention
```

---

### Issue 4: WebSocket Authentication Failure 🔐 MEDIUM

**Error Pattern:**
```
INFO: ('172.18.0.1', 45750) - "WebSocket /ws/logs" 403
INFO: connection rejected (403 Forbidden)
```

**Root Cause:**
- WebSocket endpoint requires authentication
- Dashboard not sending authentication token
- Admin API rejecting connections

**Best Practice from Context7 KB:**
> "WebSocket authentication should match REST API patterns. Use same token validation for consistency." - FastAPI WebSocket Patterns

**Solution:**
```typescript
// services/health-dashboard/src/services/websocket.ts
class WebSocketService {
  connect() {
    const token = localStorage.getItem('api_token') || 'development-token'
    
    // Add auth to WebSocket connection
    this.ws = new WebSocket(`ws://localhost:8003/ws/logs?token=${token}`)
  }
}
```

```python
# services/admin-api/src/websocket_endpoints.py
@router.websocket("/ws/logs")
async def logs_websocket(
    websocket: WebSocket,
    token: str = Query(None)  # Accept token from query param
):
    # For development, allow without token if ENABLE_AUTH=false
    if not self.auth_manager.enable_auth:
        await websocket.accept()
    elif token and self.auth_manager.validate_token(token):
        await websocket.accept()
    else:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
```

---

## Implementation Plan

### Phase 1: Critical Fixes (Immediate) 🔥

**Task 1.1: Fix InfluxDB Type Conflicts**
- Priority: **CRITICAL**
- Time: 30 minutes
- Files:
  - `services/enrichment-pipeline/src/data_normalizer.py`
  - `services/enrichment-pipeline/src/main.py`

**Steps:**
1. Add type coercion function to data_normalizer.py
2. Call normalization before every InfluxDB write
3. Add comprehensive logging for type conversions
4. Test with real Home Assistant events

**Validation:**
```bash
# Watch for type conflict errors (should be 0)
docker logs homeiq-enrichment --follow | grep "field type conflict"

# Should see events flowing
docker logs homeiq-enrichment --follow | grep "Successfully written"
```

---

**Task 1.2: Fix Admin API Health Endpoint**
- Priority: **HIGH**
- Time: 15 minutes
- Files:
  - `services/health-dashboard/src/config/services.ts`
  - `services/health-dashboard/src/services/api.ts`

**Steps:**
1. Update API endpoint configuration
2. Add /api prefix to all health check URLs
3. Rebuild dashboard container

**Validation:**
```bash
# Test endpoint directly
curl http://localhost:8003/api/health

# Check dashboard logs
docker logs homeiq-dashboard --follow
```

---

### Phase 2: Configuration Cleanup (Quick Wins) ⚡

**Task 2.1: Remove Data-Retention Service**
- Priority: **MEDIUM**
- Time: 10 minutes
- Files:
  - `services/health-dashboard/src/config/services.ts`

**Steps:**
1. Comment out data-retention service from dashboard config
2. Add TODO comment for future implementation
3. Rebuild dashboard

**Validation:**
- Services tab should show 5 services instead of 6
- No more connection timeout errors

---

**Task 2.2: Fix WebSocket Authentication**
- Priority: **MEDIUM**  
- Time: 20 minutes
- Files:
  - `services/admin-api/src/websocket_endpoints.py`
  - `services/health-dashboard/src/services/websocket.ts`

**Steps:**
1. Update WebSocket endpoint to accept development mode
2. Add token parameter to WebSocket connection
3. Test log streaming

**Validation:**
```bash
# Should see WebSocket accepted
docker logs homeiq-admin --follow | grep "WebSocket /ws/logs"

# Check browser console for connection
# Should see: "WebSocket connected to ws://localhost:8003/ws/logs"
```

---

### Phase 3: Verification & Testing ✅

**Task 3.1: End-to-End Verification**
- Priority: **HIGH**
- Time: 15 minutes

**Checklist:**
- [ ] Dashboard shows all services healthy (green)
- [ ] Event metrics showing real numbers (not 0)
- [ ] No InfluxDB type conflict errors in logs
- [ ] WebSocket connection status: Connected
- [ ] Services tab shows 5/5 services healthy
- [ ] Dependencies tab shows data flowing
- [ ] No HTTP 404 or 500 errors in logs

**Verification Commands:**
```bash
# Check all service health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Verify no errors
docker logs homeiq-enrichment --tail 50 | grep -i error
docker logs homeiq-websocket --tail 50 | grep -i error
docker logs homeiq-admin --tail 50 | grep -i error

# Check event flow
curl http://localhost:8003/api/v1/stats?period=1h | jq
```

---

## Best Practices Applied (from Context7 KB)

### 1. InfluxDB Schema Management
✅ **Type Coercion Before Write**
- Normalize data types before InfluxDB operations
- Handle mixed-type fields gracefully
- Log type conversion failures

✅ **Field Validation**
- Validate field types match schema
- Remove fields that can't be coerced
- Prefer dropping fields over causing conflicts

### 2. Service Health Checks
✅ **Consistent Endpoint Patterns**
- Use `/health` for simple checks
- Use `/api/health` for detailed health info
- Document which pattern each service uses

✅ **Only Monitor Deployed Services**
- Remove phantom service references
- Update dashboard when services are added/removed
- Clear documentation of service inventory

### 3. WebSocket Authentication
✅ **Development Mode Support**
- Allow bypass for local development
- Require auth in production
- Log all connection attempts

✅ **Token Management**
- Use query params for WebSocket auth
- Match REST API auth patterns
- Validate tokens on connection

### 4. Error Handling
✅ **Cascading Failure Prevention**
- Services fail gracefully
- Don't propagate upstream errors
- Log errors but continue processing

✅ **Retry Strategies**
- Exponential backoff for transient failures
- Circuit breakers for persistent failures
- Dead letter queues for unprocessable events

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data loss during schema change | LOW | HIGH | Use type coercion, not schema reset |
| Service downtime during updates | LOW | MEDIUM | Rolling restarts, health checks |
| Type coercion introduces bugs | MEDIUM | LOW | Comprehensive logging, validation |
| WebSocket auth breaks existing clients | LOW | LOW | Backward compatible, dev mode |

---

## Rollback Plan

If issues arise during implementation:

1. **InfluxDB Changes:**
   ```bash
   # Revert data_normalizer.py changes
   git checkout HEAD -- services/enrichment-pipeline/src/data_normalizer.py
   docker-compose restart enrichment-pipeline
   ```

2. **Dashboard Changes:**
   ```bash
   # Revert to previous image
   docker-compose down health-dashboard
   git checkout HEAD -- services/health-dashboard/src/config/
   docker-compose up -d health-dashboard
   ```

3. **Full System Rollback:**
   ```bash
   # Restore from backup
   docker-compose down
   git reset --hard <previous-commit>
   docker-compose up -d
   ```

---

## Success Metrics

### Before Fix
- Overall Status: ❌ Unhealthy
- WebSocket Connection: ❌ Disconnected (0 attempts)
- Event Processing: ❌ Unhealthy (0 events/min)
- Database Storage: ❌ Disconnected (0 write errors visible)
- Services: 4/6 Healthy (admin-api 404, data-retention timeout)

### After Fix (Target)
- Overall Status: ✅ Healthy
- WebSocket Connection: ✅ Connected (active)
- Event Processing: ✅ Healthy (>0 events/min)
- Database Storage: ✅ Connected (writes succeeding)
- Services: 5/5 Healthy (data-retention removed)

### KPIs
- InfluxDB write success rate: >99%
- Event processing latency: <100ms p95
- Dashboard load time: <2s
- Health check response time: <500ms
- Zero HTTP 500 errors in logs

---

## Timeline

| Phase | Tasks | Duration | Can Start |
|-------|-------|----------|-----------|
| **Phase 1** | Critical fixes (InfluxDB, Health API) | 45 min | Immediately |
| **Phase 2** | Config cleanup (data-retention, WebSocket) | 30 min | After Phase 1 |
| **Phase 3** | Testing & verification | 15 min | After Phase 2 |
| **TOTAL** | Complete fix implementation | ~90 min | - |

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Create backup** of current state
3. **Execute Phase 1** (critical fixes)
4. **Validate** each fix before proceeding
5. **Document changes** in CHANGELOG.md
6. **Update monitoring** dashboards

---

## References

- Context7 KB: [influxdb-python-patterns.md](docs/kb/context7-cache/influxdb-python-patterns.md)
- Context7 KB: [influxdb-admin-api-query-patterns.md](docs/kb/context7-cache/influxdb-admin-api-query-patterns.md)
- Context7 KB: [fastapi-authentication-jwt.md](docs/kb/context7-cache/fastapi-authentication-jwt.md)
- Tech Stack: [docs/architecture/tech-stack.md](docs/architecture/tech-stack.md)
- Source Tree: [docs/architecture/source-tree.md](docs/architecture/source-tree.md)

---

**Plan Created By:** BMad Master (Context7 KB Integration)  
**Review Status:** Ready for Implementation  
**Estimated Completion:** 90 minutes from start  
**Risk Level:** LOW (all changes reversible, no data loss)

