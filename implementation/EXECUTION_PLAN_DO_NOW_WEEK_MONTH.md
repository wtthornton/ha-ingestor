# Execution Plan: DO NOW + DO THIS WEEK + DO THIS MONTH
**Date:** October 19, 2025  
**Status:** IN PROGRESS  
**Context7 Validated:** ✅ Yes

---

## ⚡ DO NOW: Fix Health Checks (10 min) - IN PROGRESS

### Context7 Best Practices Applied
**Source:** `/docker/compose` - Trust Score 9.9
- Use simple, reliable health check commands
- Prefer `curl -f` over Python-based checks
- Set appropriate `start_period` for initialization
- Use consistent intervals (30s standard)

### ✅ COMPLETED FIXES

#### 1. weather-api Health Check ✅
**Issue:** Health check used port 8007 (external) instead of 8001 (internal)  
**Fix Applied:** Changed `http://localhost:8007/health` → `http://localhost:8001/health`  
**File:** `docker-compose.yml` line 829  
**Context7 Validation:** ✅ Curl-based check is recommended pattern  

#### 2. setup-service Health Check ✅
**Issue:** Used `python -c "import requests..."` requiring runtime dependencies  
**Fix Applied:** Changed to `curl -f http://localhost:8020/health`  
**File:** `services/ha-setup-service/docker-compose.service.yml` line 44  
**Context7 Validation:** ✅ Simple curl is more reliable than Python imports  

#### 3. automation-miner Health Check ✅
**Issue:** Used `python -c "import httpx..."` in Dockerfile, missing curl  
**Fix Applied:** 
- Added curl to apt-get install (line 9)
- Changed to `curl -f http://localhost:8019/health`
**File:** `services/automation-miner/Dockerfile` lines 9, 34  
**Context7 Validation:** ✅ Minimal dependencies in health checks  

### 🔄 NEXT STEPS (5 min)
1. Restart affected services
2. Verify all 20 services healthy
3. Monitor health checks for 2 minutes

**Expected Result:** 20/20 services healthy, monitoring trustworthy

---

## 🔥 DO THIS WEEK: Fix Hardcoded Metrics (4 hours)

### Context7 Best Practices Applied
**Source:** `/blueswen/fastapi-observability` - Trust Score 9.8
- Use Prometheus Histogram for request duration
- Implement proper metric collection with labels
- Add exemplars for trace correlation
- Real-time metric calculation, no hardcoding

### Task 1: Replace Hardcoded 99.9% Uptime (1 hour)

#### Current State (WRONG)
```typescript
// OverviewTab.tsx line 418, 431
value: enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB')?.status === 'healthy' ? '99.9' : '0'
```

#### Context7 Recommended Fix
```typescript
// Calculate real uptime from service start time
const calculateUptime = (startTime: Date): number => {
  const now = new Date();
  const uptimeMs = now.getTime() - startTime.getTime();
  const totalMs = uptimeMs; // or system boot time if available
  return (uptimeMs / totalMs) * 100;
};

// Use actual metrics
value: calculateUptime(service.startTime).toFixed(2)
```

**Files to Fix:**
- `services/health-dashboard/src/components/tabs/OverviewTab.tsx` (2 instances)
- `services/health-dashboard/src/mocks/analyticsMock.ts` (mock data for testing)

**Verification:**
- Regression test already exists: `services/data-api/tests/test_analytics_uptime.py:60`

---

### Task 2: Replace Hardcoded 0ms Response Times (2 hours)

#### Current State (WRONG)
```python
# stats_endpoints.py lines 418, 471, 618, 831, 1005
"response_time_ms": 0  # Hardcoded!
"average_response_time": 0  # Hardcoded!
```

#### Context7 Recommended Fix - Use Prometheus Histogram

**Step 1: Add Prometheus instrumentation**
```python
# services/admin-api/src/metrics.py (NEW FILE)
from prometheus_client import Histogram
from opentelemetry import trace

REQUESTS_PROCESSING_TIME = Histogram(
    "admin_api_requests_duration_seconds",
    "Histogram of requests processing time by path",
    ["method", "path", "service"],
)

def track_request_time(method: str, path: str, duration: float):
    """Track request processing time with trace correlation"""
    span = trace.get_current_span()
    trace_id = trace.format_trace_id(span.get_span_context().trace_id)
    
    REQUESTS_PROCESSING_TIME.labels(
        method=method, 
        path=path,
        service="admin-api"
    ).observe(duration, exemplar={'TraceID': trace_id})
```

**Step 2: Update stats_endpoints.py**
```python
# Replace hardcoded values with real metrics
from datetime import datetime
import asyncio

async def get_service_response_time(service_url: str) -> float:
    """Measure actual response time"""
    start = datetime.now()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{service_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                await response.read()
                return (datetime.now() - start).total_seconds() * 1000  # ms
    except Exception as e:
        logger.warning(f"Failed to measure response time for {service_url}: {e}")
        return -1  # Indicate failure
```

**Files to Fix:**
- `services/admin-api/src/stats_endpoints.py` (5 instances)
- `services/data-api/src/metrics_endpoints.py` (potential issues)

**Metrics to Implement:**
- Real-time response time measurement
- Average response time calculation
- 99th percentile response time (P99)
- Response time histograms

**Prometheus Query Example:**
```promql
# 99th percentile request duration
histogram_quantile(0.99, sum(rate(admin_api_requests_duration_seconds_bucket[1m])) by(path, le))
```

---

### Task 3: Test Metrics Across Dashboard (1 hour)

**Testing Checklist:**
- [ ] Overview Tab shows real uptime
- [ ] Overview Tab shows real response times
- [ ] Services Tab displays accurate metrics
- [ ] Analytics Tab calculates correct averages
- [ ] Alerts Tab triggers on real thresholds
- [ ] No hardcoded values remain (grep verification)

**Verification Commands:**
```powershell
# Find remaining hardcoded values
Select-String -Path "services" -Pattern "99\.9|response_time.*=.*0" -Recurse

# Test API response
curl http://localhost:8003/api/v1/stats | jq .
```

**Expected Result:** All dashboard tabs show real, dynamic metrics

---

## 📋 DO THIS MONTH: Strategic Improvements (40 hours)

### Task 1: Consolidate 14 Env Files (12 hours)

#### Current State (CHAOS)
```
infrastructure/env.ai-automation
infrastructure/env.ai-automation.miner
infrastructure/env.ai-automation.template
infrastructure/env.automation-miner
infrastructure/env.calendar.template
infrastructure/env.example
infrastructure/env.influxdb.template
infrastructure/env.production
infrastructure/env.sports.template
infrastructure/env.weather.template
infrastructure/env.websocket.template
infrastructure/.env.influxdb
infrastructure/.env.weather
infrastructure/.env.websocket
```
**Total: 14 files** ❌

#### Target State (CLEAN)
```
.env                          # Main config (auto-generated from .env.template)
.env.template                 # Template with all variables
.env.production              # Production overrides only
```
**Total: 3 files** ✅

#### Implementation Plan

**Phase 1: Analysis (2 hours)**
1. Map all environment variables to services
2. Identify duplicates and conflicts
3. Create consolidated variable map
4. Document required vs optional variables

**Phase 2: Create Unified Template (4 hours)**
```bash
# .env.template structure

# ============================================
# CORE INFRASTRUCTURE
# ============================================
LOG_LEVEL=INFO
LOG_FORMAT=json

# ============================================
# HOME ASSISTANT CONNECTION
# ============================================
HA_HTTP_URL=http://192.168.1.86:8123
HA_WS_URL=ws://192.168.1.86:8123/api/websocket
HA_TOKEN=your_long_lived_access_token_here

# ============================================
# DATABASE CONFIGURATION
# ============================================
# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your_influxdb_token_here
INFLUXDB_ORG=ha-ingestor
INFLUXDB_BUCKET=home_assistant_events

# SQLite
DATABASE_URL=sqlite+aiosqlite:///./data/metadata.db
SQLITE_TIMEOUT=30

# ============================================
# EXTERNAL SERVICES
# ============================================
# Weather
WEATHER_API_KEY=your_openweathermap_key_here
WEATHER_LAT=36.1699
WEATHER_LON=-115.1398

# Sports
DISCOURSE_MIN_LIKES=300

# ============================================
# AI SERVICES
# ============================================
ENABLE_AI_AUTOMATION=true
ENABLE_PATTERN_ENHANCEMENT=false
ENABLE_AUTOMATION_MINER=true

# ============================================
# FEATURE FLAGS
# ============================================
ENABLE_HOME_ASSISTANT=true
WEATHER_ENRICHMENT_ENABLED=true
STORE_DEVICE_HISTORY_IN_INFLUXDB=false
```

**Phase 3: Update docker-compose.yml (4 hours)**
```yaml
services:
  websocket-ingestion:
    env_file:
      - .env  # Single source of truth
    environment:
      # Only overrides or service-specific vars
      - WEBSOCKET_INGESTION_PORT=8001
```

**Phase 4: Migration Script (2 hours)**
```powershell
# scripts/consolidate-env-files.ps1
# 1. Backup existing env files
# 2. Merge all env variables
# 3. Remove duplicates
# 4. Generate .env from template
# 5. Archive old files
# 6. Update docker-compose.yml
```

**Validation:**
- All services start successfully
- No missing environment variables
- Configuration is easier to manage
- Single file to edit for changes

---

### Task 2: Merge Two UIs into Single Dashboard (24 hours)

#### Current State (FRAGMENTED)
```
Port 3000: health-dashboard (12 tabs)
Port 3001: ai-automation-ui (4 tabs: Suggestions, Patterns, Automations, Insights)
```
**Problem:** Users must switch between two apps

#### Target State (UNIFIED)
```
Port 3000: unified-dashboard (16 tabs)
  Overview | Services | Dependencies | Devices | Events | Logs
  Sports | Data Sources | Energy | Analytics | Alerts | Config
  AI Suggestions | AI Patterns | AI Automations | AI Insights
```
**Benefit:** Single interface, better UX

#### Implementation Plan

**Phase 1: Component Migration (12 hours)**
1. Copy AI components to health-dashboard
   - `ai-automation-ui/src/components/` → `health-dashboard/src/components/ai/`
2. Update imports and paths
3. Preserve existing functionality
4. Test each component individually

**Phase 2: Navigation Integration (4 hours)**
1. Add AI tabs to main dashboard
2. Update tab navigation logic
3. Preserve state across tab switches
4. Update routing if needed

**Phase 3: API Integration (4 hours)**
1. Update API calls to use unified service layer
2. Consolidate WebSocket connections
3. Share authentication context
4. Update error handling

**Phase 4: Styling Consistency (2 hours)**
1. Apply TailwindCSS theme consistently
2. Match dark mode behavior
3. Ensure responsive design
4. Test on mobile devices

**Phase 5: Cleanup (2 hours)**
1. Remove ai-automation-ui service from docker-compose.yml
2. Archive old ai-automation-ui directory
3. Update documentation
4. Update README with new URL structure

**Validation:**
- Single dashboard at port 3000
- All 16 tabs functional
- No broken links or missing features
- Performance unchanged or improved

---

### Task 3: Archive 90% of Implementation Docs (4 hours)

#### Current State (ARCHAEOLOGICAL SITE)
```
implementation/*.md - 514 files
```

#### Target State (CLEAN REPO)
```
implementation/
├── CURRENT_STATUS.md         # One file with current state
├── ACTIVE_EPICS.md            # In-progress work
├── RECENT_CHANGES.md          # Last 30 days
└── archive/
    └── 2025-10/               # Dated archive folders
        └── [all old files]
```
**Benefit:** Easy to find current info, history preserved in git

#### Implementation Plan

**Phase 1: Archive Script (2 hours)**
```powershell
# scripts/archive-implementation-docs.ps1

# 1. Create archive directory structure
# 2. Move files older than 30 days
# 3. Group by month/year
# 4. Keep only essential current docs
# 5. Generate index of archived files
# 6. Update .gitignore if needed
```

**Phase 2: Create Summary Documents (1 hour)**
```markdown
# implementation/CURRENT_STATUS.md
- System Health: 20/20 services healthy
- Active Epics: None
- Recent Changes: Health check fixes (Oct 19, 2025)
- Known Issues: None
- Next Priorities: Metrics hardcoding (Epic 24)

# implementation/ACTIVE_EPICS.md
- Epic 24: Monitoring Data Quality (Draft)
- Epic 26: AI E2E Tests (Planned)

# implementation/RECENT_CHANGES.md
- 2025-10-19: Fixed 3 unhealthy health checks
- 2025-10-18: Full system rebuild
- 2025-01-18: Epic 27-30 complete
```

**Phase 3: Documentation (1 hour)**
- Update README with archive location
- Document how to find archived docs
- Create index of key historical documents

**Validation:**
- implementation/ has <10 current files
- All history accessible in archive/
- Easy to find relevant information
- Git history intact

---

## 📊 SUMMARY

| Phase | Tasks | Time | Priority |
|-------|-------|------|----------|
| DO NOW | Fix 3 health checks | 10 min | ⚡ CRITICAL |
| DO THIS WEEK | Fix hardcoded metrics | 4 hours | 🔥 HIGH |
| DO THIS MONTH | Consolidate env files | 12 hours | 🟠 MEDIUM |
| DO THIS MONTH | Merge two UIs | 24 hours | 🟠 MEDIUM |
| DO THIS MONTH | Archive docs | 4 hours | 🟢 LOW |

**Total Time Investment:** ~44 hours  
**Expected Impact:** Production-ready system, easier maintenance, better UX

---

## ✅ SUCCESS CRITERIA

**DO NOW:**
- ✅ 20/20 services show healthy status
- ✅ No false alerts in monitoring
- ✅ Health checks pass consistently

**DO THIS WEEK:**
- ✅ No hardcoded metrics in codebase
- ✅ Real-time uptime calculation
- ✅ Actual response time measurement
- ✅ Prometheus metrics implemented
- ✅ All regression tests pass

**DO THIS MONTH:**
- ✅ 3 env files instead of 14
- ✅ Single unified dashboard
- ✅ <10 current docs in implementation/
- ✅ All features working after consolidation
- ✅ Improved developer experience

---

**Next Action:** Restart weather-api, automation-miner services to verify health check fixes

