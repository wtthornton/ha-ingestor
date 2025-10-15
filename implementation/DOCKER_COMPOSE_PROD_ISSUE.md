# Docker Compose Production Configuration Issue

**Date:** October 14, 2025  
**Issue:** docker-compose.prod.yml missing 8 critical services  
**Severity:** CRITICAL  
**Status:** DOCUMENTED - Awaiting user decision

---

## Issue Summary

The `docker-compose.prod.yml` file is **missing 8 services** that are present in the main `docker-compose.yml`:

### Missing Services
1. **data-api** (port 8006) - ❌ **CRITICAL** - Required for device/entity browsing
2. **log-aggregator** (port 8015) - Log collection
3. **sports-data** (port 8005) - Sports data service
4. **carbon-intensity** (port 8010) - Carbon data service
5. **electricity-pricing** (port 8011) - Pricing data service
6. **air-quality** (port 8012) - Air quality service
7. **calendar** (port 8013) - Calendar integration
8. **smart-meter** (port 8014) - Smart meter service

---

## Impact

### Without data-api Service
- ❌ Dashboard cannot browse devices/entities
- ❌ Device API endpoints non-functional
- ❌ `/api/devices` endpoints return errors
- ❌ Major feature loss in production

### Without Other Services
- ⚠️ Feature loss (sports, external data sources)
- ⚠️ No centralized log aggregation
- ⚠️ Dashboard features incomplete

---

## Recommended Solutions

### Option 1: Use Main Compose for Production (RECOMMENDED)

**Use `docker-compose.yml` for production deployment**

```bash
# Deploy using main compose file
docker-compose -f docker-compose.yml up -d
```

**Pros:**
- ✅ All 13+ services included
- ✅ Tested and working configuration
- ✅ Simpler maintenance (one file)
- ✅ Resource limits defined
- ✅ Health checks on all services

**Cons:**
- ⚠️ Missing some production hardening features
  - No `security_opt: no-new-privileges`
  - No `read_only: true` for read-only services
  - No tmpfs mounts
  - Less aggressive resource limits

**Production Hardening (Optional):**
- Add security_opt to services (see Option 3 below)
- Configure external secrets management
- Set up reverse proxy with SSL/TLS
- Configure automated backups

---

### Option 2: Create Complete Production Compose

**Create new `docker-compose.prod.complete.yml` merging both files**

This would require:
1. Taking all services from `docker-compose.yml`
2. Adding production enhancements from `docker-compose.prod.yml`:
   - security_opt: no-new-privileges
   - read_only: true (where applicable)
   - tmpfs mounts for /tmp
   - Enhanced resource limits
   - CPU limits
3. Testing thoroughly

**Estimated Time:** 2-3 hours (manual merge + testing)

**Risk:** Medium - complex merge, potential for errors

---

### Option 3: Add Production Enhancements to Main Compose

**Enhance `docker-compose.yml` with production features**

Add these to each service in main compose:

```yaml
services:
  service-name:
    # ... existing config ...
    
    # Add production enhancements:
    security_opt:
      - no-new-privileges:true
    
    # For read-only safe services (dashboard, etc):
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
    
    # Enhanced resource limits:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

**Services Safe for read_only: true:**
- health-dashboard (nginx-based)
- websocket-ingestion (if no file writes)
- enrichment-pipeline (if no file writes)

**Services Requiring read_only: false:**
- influxdb (database writes)
- data-api (SQLite writes)
- admin-api (config file writes)
- data-retention (backup writes)

---

## Comparison Table

| Feature | docker-compose.yml | docker-compose.prod.yml |
|---------|-------------------|------------------------|
| **Services** | 13+ ✅ | 5 ❌ |
| **data-api** | ✅ Included | ❌ Missing |
| **sports-data** | ✅ Included | ❌ Missing |
| **External services** | ✅ All 6 | ❌ None |
| **log-aggregator** | ✅ Included | ❌ Missing |
| **Security hardening** | ⚠️ Basic | ✅ Enhanced |
| **Resource limits** | ✅ Memory only | ✅ Memory + CPU |
| **Network config** | ✅ Simple bridge | ✅ Subnet + opts |
| **Read-only FS** | ❌ None | ✅ Some services |
| **tmpfs mounts** | ❌ None | ✅ Configured |

---

## Current State of docker-compose.yml

### ✅ Fixed Issues
- ✅ Added `data-api` dependency to `admin-api` service
- ✅ All services have proper health checks
- ✅ Resource limits defined
- ✅ Logging configured

### Services Included (13+)
1. ✅ influxdb
2. ✅ websocket-ingestion
3. ✅ enrichment-pipeline
4. ✅ admin-api (now with data-api dependency)
5. ✅ data-api
6. ✅ data-retention
7. ✅ health-dashboard
8. ✅ log-aggregator
9. ✅ sports-data
10. ✅ carbon-intensity
11. ✅ electricity-pricing
12. ✅ air-quality
13. ✅ calendar
14. ✅ smart-meter

---

## Immediate Action Required

### For This Rebuild

**RECOMMENDATION:** Use `docker-compose.yml` for deployment

```bash
# Deploy with main compose file
docker-compose -f docker-compose.yml build --no-cache --parallel
docker-compose -f docker-compose.yml up -d

# Verify all services
docker-compose ps
```

**Rationale:**
- ✅ Complete feature set (all 13+ services)
- ✅ Tested configuration
- ✅ data-api service included (critical)
- ✅ Lower risk than untested merge
- ⚠️ Can add production hardening after successful deployment

---

## Future Improvements

### Phase 1: Post-Rebuild (Optional)
Add production enhancements to main compose:
1. Add `security_opt: no-new-privileges` to all services
2. Add `read_only: true` to safe services (dashboard, etc.)
3. Add tmpfs mounts for temp directories
4. Add CPU limits to resource constraints

### Phase 2: Advanced Hardening (Optional)
1. Set up reverse proxy (nginx/Caddy/Traefik)
2. Configure SSL/TLS with Let's Encrypt
3. Implement secrets management (Docker secrets, Vault)
4. Set up external monitoring (Prometheus, Grafana)
5. Configure automated backups to S3

---

## Files Modified

### ✅ Fixed
- `docker-compose.yml` - Added data-api dependency to admin-api
- `.dockerignore` - Created root dockerignore

### ⚠️ Needs Decision
- `docker-compose.prod.yml` - Missing services, incomplete

---

## Decision Required

**Please choose one of the following:**

### A. Use Main Compose (RECOMMENDED)
```bash
# I'll update deployment scripts to use docker-compose.yml
./scripts/deploy.sh  # Will use main compose
```
**Pros:** Immediate, complete, tested  
**Cons:** Missing some hardening features

### B. Merge Files
```bash
# I'll create docker-compose.prod.complete.yml
# Merge all services with production enhancements
# Time: 2-3 hours, requires testing
```
**Pros:** Best of both worlds  
**Cons:** Time-consuming, requires validation

### C. Enhance Main Compose
```bash
# I'll add production features to docker-compose.yml
# Keep as single source of truth
# Time: 1-2 hours
```
**Pros:** Single file, production-ready  
**Cons:** More complex single file

---

## Next Steps

**Waiting for your decision on production compose strategy.**

Once decided, I will:
1. ✅ Implement chosen solution
2. ✅ Update deployment scripts if needed
3. ✅ Document changes
4. ✅ Validate configuration
5. ✅ Update rebuild plan

---

## Related Documents

- Main rebuild plan: `implementation/COMPLETE_SYSTEM_REBUILD_PLAN.md`
- Quick reference: `implementation/REBUILD_QUICK_REFERENCE.md`
- Review summary: `implementation/REBUILD_REVIEW_SUMMARY.md`

---

**Status:** Awaiting user decision on production compose strategy  
**Recommendation:** Option A - Use main compose for now, add hardening later

