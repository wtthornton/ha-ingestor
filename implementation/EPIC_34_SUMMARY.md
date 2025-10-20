# Epic 34: Dashboard Data Integrity Fixes - Quick Reference

**Date**: October 20, 2025  
**Status**: ✅ Ready for Implementation  
**Effort**: 2-3 hours  
**Risk**: Low

## The Problem

Dashboard at http://localhost:3000/ has 3 bugs:
1. Python error breaks all per-API metrics
2. Frontend calls wrong endpoint path
3. Misleading label (says "per minute" but shows "per hour")

## The Fix

**5 lines of code across 3 files:**

### Story 34.1: Fix Python Error + API Path (2 hours)
```python
# Add at line 792 and line 901 in stats_endpoints.py
start_time = datetime.now()
```
```typescript
// Change line 246 in api.ts
'/api/v1/real-time-metrics'  // was: '/api/v1/metrics/realtime'
```

### Story 34.2: Fix Label (30 minutes)
```typescript
// Change lines 331-332 in OverviewTab.tsx
label: 'Events per Hour',  // was: 'Events per Minute'
unit: 'evt/h'  // was: 'evt/min'
```

## What's Broken

- **Dependencies tab**: Shows "No metrics available" (should show 12 services)
- **Per-API metrics**: All return error: "name 'start_time' is not defined"
- **Overview label**: Says "Events per Minute" but shows events per hour

## What Changes

**Only 2 stories** (down from 4):
- ~~Story 34.3~~ - Removed (just testing, not a story)
- ~~Story 34.4~~ - Removed (scope creep, not a dashboard bug)

## Result

**Before:** 12/12 services show "error" ❌  
**After:** 12/12 services show proper metrics ✅  

**Before:** Label says "Events per Minute" (confusing) ⚠️  
**After:** Label says "Events per Hour" (accurate) ✅

## Testing

```bash
# Verify fix worked
curl http://localhost:8003/api/v1/real-time-metrics | jq '.api_metrics[] | select(.status == "error")'
# Expected: empty (no errors)

# Check dashboard
1. Open http://localhost:3000/
2. Dependencies tab: See 12 services ✅
3. Overview tab: See "Events per Hour" label ✅
```

## Epic Document

📄 **Full details**: `docs/prd/epic-34-dashboard-data-integrity-fixes.md`

---

**Status**: 🟢 Ready  
**Priority**: 🔴 High  
**Effort**: ⚡ 2-3 hours  
**Risk**: 🟢 Low

