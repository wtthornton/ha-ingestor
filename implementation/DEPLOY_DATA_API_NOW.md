# 🚨 CRITICAL: Deploy Data API Service

**Status:** The data-api service is NOT running  
**Impact:** Dashboard features are broken  
**Time to Fix:** 1-2 hours  
**Risk:** Very Low

---

## Quick Start (5 Minutes)

```bash
# 1. Build the service
docker-compose build data-api

# 2. Start the service
docker-compose up -d data-api

# 3. Verify it's running
docker ps --filter "name=data-api"
# Expected: ha-ingestor-data-api ... Up ... 0.0.0.0:8006->8006/tcp

# 4. Test health
curl http://localhost:8006/health
# Expected: {"status": "healthy", ...}

# 5. Test from dashboard
open http://localhost:3000
# Browser console should show NO connection errors
```

---

## What This Fixes

✅ WebSocket connection errors  
✅ Events tab functionality  
✅ Devices tab queries  
✅ Sports tab data access  
✅ Analytics endpoints  
✅ Alerts endpoints  
✅ All 502/503 Bad Gateway errors

---

## Full Documentation

- **Epic Document:** [docs/stories/epic-21-dashboard-api-integration-fix.md](../docs/stories/epic-21-dashboard-api-integration-fix.md)
- **Deployment Checklist:** [implementation/EPIC_21_DATA_API_DEPLOYMENT_CHECKLIST.md](./EPIC_21_DATA_API_DEPLOYMENT_CHECKLIST.md)
- **Analysis Summary:** [implementation/EPIC_21_ANALYSIS_SUMMARY.md](./EPIC_21_ANALYSIS_SUMMARY.md)

---

**Created:** 2025-10-13  
**Priority:** CRITICAL - Deploy immediately


