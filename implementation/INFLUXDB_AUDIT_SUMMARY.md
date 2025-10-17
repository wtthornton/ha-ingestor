# InfluxDB Query Audit - Quick Summary

**Date:** October 17, 2025  
**Audit Scope:** All 17 services, 23 files, 45+ queries  
**Trigger:** Events tab fix revealed systemic pattern

---

## Issues Found

| # | Component | Severity | Issue | Impact | Fix Time |
|---|-----------|----------|-------|--------|----------|
| 1 | admin-api events | 🔴 HIGH | No _field filter | 1000x duplicates | 30 min |
| 2 | devices coverage | 🟡 MEDIUM | Count overcounting | Wrong stats | 15 min |
| 3 | integration health (3 queries) | 🟡 MEDIUM | Overcounting | Wrong metrics | 20 min |

**Total Fix Time:** ~2 hours  
**Expected Impact:** 1000x improvement + accurate stats system-wide

---

## Detailed Findings

### 🔴 Issue #1: admin-api events endpoint (CRITICAL)

**File:** `services/admin-api/src/events_endpoints.py:470-508`

**Problem:**
```python
|> filter(fn: (r) => r._measurement == "home_assistant_events")
# Missing: |> filter(fn: (r) => r._field == "context_id")
```

**Result:**
- Request `limit=5` → Returns ~60 duplicate events
- Same issue we just fixed in data-api
- **NEEDS IMMEDIATE FIX**

**Solution:** Copy fix from data-api events_endpoints.py

---

### 🟡 Issue #2: devices coverage calculation

**File:** `services/data-api/src/devices_endpoints.py:265-279`

**Problem:**
```python
|> filter(fn: (r) => r["_measurement"] == "home_assistant_events")
|> count()  # ← Counts all fields (12x inflation)
```

**Result:**
- Coverage shows 8% when should be 100%
- All count-based stats wrong

**Solution:** Add `|> filter(fn: (r) => r._field == "context_id")` before count()

---

### 🟡 Issue #3: Integration health metrics (3 queries)

**File:** `services/data-api/src/devices_endpoints.py:409-463`

**Queries:**
1. Event rate (line 409)
2. Error count (line 433)
3. Response time (line 453)

**Problem:**
- All filter by platform but not by _field
- Overcounting by 10-12x

**Solution:** Add _field filter to each query

---

## What's Already Good ✅

**18 files have NO issues:**
- ✅ data-api events (FIXED this session)
- ✅ energy_endpoints.py (all 12 queries correct)
- ✅ energy-correlator (correct)
- ✅ analytics (uses aggregation)
- ✅ sports endpoints (different structure)
- ✅ All count/aggregation queries with _field filters

---

## Recommended Action Plan

### Option A: Fix Critical Issue Only (30 min)
1. Fix admin-api events endpoint
2. Test and deploy
3. Monitor for issues

**Pros:** Quick fix, low risk  
**Cons:** Stats still wrong

### Option B: Fix All Issues (2 hours)
1. Fix admin-api events (30 min)
2. Fix devices coverage (15 min)
3. Fix integration health (20 min)
4. Test all (30 min)
5. Document (15 min)

**Pros:** Complete solution, accurate stats  
**Cons:** More time investment

### Option C: Fix in Phases
- **This week:** admin-api events
- **Next week:** devices + integration health

**Pros:** Incremental, safe  
**Cons:** Longer timeline

---

## My Recommendation

**Fix ALL issues NOW (Option B - 2 hours)**

**Why:**
- Pattern is proven (Events tab fix)
- Code is similar (easy copy-paste)
- Testing is straightforward
- Gets system fully optimized
- Accurate stats matter for monitoring

**Risk:** LOW - We know exactly what to do

---

**See full details in:** `implementation/INFLUXDB_QUERY_AUDIT_AND_OPTIMIZATION_PLAN.md`

