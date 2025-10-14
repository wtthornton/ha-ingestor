# UI Events Per Minute Display Fix

## Issue
The Health Dashboard UI was not showing "events per minute" on the Overview tab at http://localhost:3000, even though ingestion was working correctly.

## Root Cause Analysis

### Investigation Steps
1. ✅ Verified API endpoint `/api/v1/stats` is working correctly
   - Returns: `events_per_minute: 17.92` (data is correct)
   
2. ✅ Checked OverviewTab.tsx component logic
   - Component correctly extracts: `websocketMetrics?.events_per_minute`
   - UI structure is correct

3. ✅ Examined useRealtimeMetrics hook
   - **FOUND BUG**: HTTP fallback URL was incorrect

### The Bug
In `services/health-dashboard/src/hooks/useRealtimeMetrics.ts` (line 52):

**Before (INCORRECT):**
```typescript
const HTTP_STATS_URL = '/api/statistics';  // ❌ This endpoint doesn't exist (404)
```

**After (CORRECT):**
```typescript
const HTTP_STATS_URL = '/api/v1/stats';  // ✅ Correct v1 API endpoint
```

### Why This Caused the Issue
1. WebSocket connection may fail or be in fallback mode
2. When using HTTP polling fallback, the hook called `/api/statistics` which returns 404
3. Without valid statistics data, the UI shows 0 or N/A for events per minute

## Fix Applied

### File Modified
- **File:** `services/health-dashboard/src/hooks/useRealtimeMetrics.ts`
- **Lines:** 51-52
- **Changes:**
  ```diff
  - const HTTP_HEALTH_URL = '/api/health';
  - const HTTP_STATS_URL = '/api/statistics';
  + const HTTP_HEALTH_URL = '/api/v1/health';
  + const HTTP_STATS_URL = '/api/v1/stats';
  ```

### Deployment Steps
1. ✅ Fixed the endpoint URL in useRealtimeMetrics.ts
2. ✅ Rebuilt frontend: `npm run build` in services/health-dashboard
3. ✅ Restarted container: `docker-compose restart health-dashboard`

## Verification

### API Endpoints Verified
```bash
# Correct endpoint (works)
GET http://localhost:8003/api/v1/stats?period=1h
Response: 200 OK
{
  "metrics": {
    "websocket-ingestion": {
      "events_per_minute": 17.92,
      ...
    }
  }
}

# Old incorrect endpoint (404)
GET http://localhost:8003/api/statistics
Response: 404 Not Found
```

### Expected Result
After refreshing the browser at http://localhost:3000:
- ✅ Overview tab should display "Events per Minute" with actual values (e.g., 17.92)
- ✅ Ingestion card shows live metrics
- ✅ Processing card shows enrichment metrics
- ✅ Data updates every 30-60 seconds

### Testing Checklist
- [x] API endpoint returns correct data structure
- [x] Frontend code updated with correct endpoint
- [x] Frontend rebuilt successfully
- [x] Container restarted
- [ ] **Manual verification**: Open http://localhost:3000 and check Overview tab shows events/min

## Impact
- **Severity:** Medium (UI display issue, no data loss)
- **Affected Component:** Health Dashboard Overview tab
- **Services Affected:** health-dashboard frontend only
- **Backend:** No changes needed (already working correctly)

## Related Files
- `services/health-dashboard/src/hooks/useRealtimeMetrics.ts` - Fixed HTTP fallback URLs
- `services/health-dashboard/src/components/tabs/OverviewTab.tsx` - Uses the hook (no changes)
- `services/admin-api/src/stats_endpoints.py` - Backend API (already correct)

## Additional Notes
- This fix also corrected the health endpoint from `/api/health` to `/api/v1/health` for consistency
- The WebSocket connection may or may not be working - this fix ensures HTTP fallback works correctly
- Both WebSocket and HTTP polling modes now use the correct v1 API endpoints

## Next Steps
1. **User Action Required:** Refresh browser at http://localhost:3000 to see the fix
2. Consider investigating why WebSocket might be falling back to HTTP (not critical)
3. Monitor dashboard to confirm metrics update correctly

---
**Fixed by:** Dev Agent (James)  
**Date:** 2025-10-13  
**Session:** UI debugging session

