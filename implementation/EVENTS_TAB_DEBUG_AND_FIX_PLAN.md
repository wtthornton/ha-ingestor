# Events Tab Debug and Fix Plan

**Status:** Research Complete  
**Date:** October 17, 2025  
**Dashboard:** http://localhost:3000/  
**Priority:** HIGH - Real-time event viewing is a core feature

## Executive Summary

The Events tab has **missing functionality** in the real-time stream viewer and potential data display issues. The backend API is working and returning data, but the frontend `EventStreamViewer` component is not implemented (contains a TODO comment).

---

## Research Findings

### ✅ What's Working

1. **Data API Endpoint** - `http://localhost:8006/api/v1/events` is functional
   - Returns JSON array of events
   - Responds to requests successfully
   - Data is flowing from InfluxDB

2. **nginx Routing** - Correctly configured
   - `/api/v1/events` → proxies to `ha-ingestor-data-api:8006`
   - Timeout set to 30s
   - Proper headers configured

3. **EventsTab Component** - Structure is correct
   - Real-Time / Historical toggle buttons exist
   - Historical events fetching implemented
   - Event statistics querying implemented
   - Uses `dataApi.getEvents()` correctly

4. **Backend Events Endpoints** - Fully implemented
   - `/api/v1/events` - List events with filters
   - `/api/v1/events/{id}` - Get single event
   - `/api/v1/events/stats` - Get statistics
   - `/api/v1/events/search` - Search events
   - Support for filtering by entity_id, event_type, time range

### ❌ What's NOT Working

1. **EventStreamViewer Component** - **NOT IMPLEMENTED**
   ```typescript
   // Line 25 in EventStreamViewer.tsx:
   // TODO: Implement HTTP polling for events from /api/v1/events endpoint
   const [events] = useState<Event[]>([]);
   ```
   - Has empty state array
   - No polling logic
   - No API calls
   - Shows "Waiting for events..." forever
   - All the UI is there (filters, controls) but no data

2. **Data Quality Issues**
   - API returns massive amounts of duplicate events
   - `limit` parameter may not be respected correctly
   - Events have null `old_state` and `new_state` values
   - Many events are duplicated 10-20 times

3. **Potential Browser Timeout**
   - Puppeteer times out navigating to dashboard (30s)
   - Likely due to infinite API polling loops (seen in nginx logs)
   - Repeated `/api/v1/alerts?severity=critical` calls

---

## Root Cause Analysis

### Issue #1: EventStreamViewer Not Implemented (PRIMARY ISSUE)

**File:** `services/health-dashboard/src/components/EventStreamViewer.tsx`

**Problem:**
```typescript
export const EventStreamViewer: React.FC<EventStreamViewerProps> = ({ darkMode }) => {
  // TODO: Implement HTTP polling for events from /api/v1/events endpoint
  const [events] = useState<Event[]>([]);  // ← Never populated!
  //...
}
```

**Missing Implementation:**
- No `useEffect` hook to fetch events
- No polling interval (setInterval)
- No API call to `/api/v1/events`
- No error handling
- No loading state

**Expected Behavior:**
1. Poll `/api/v1/events?limit=50` every 2-5 seconds
2. Append new events to the list
3. Respect `isPaused` state to stop/start polling
4. Handle errors gracefully
5. Limit total events in memory (e.g., max 500)

### Issue #2: Data Quality - Duplicate Events

**Evidence:**
```bash
$ curl http://localhost:8006/api/v1/events?limit=3
# Returns 100+ events instead of 3, many duplicates
```

**Root Cause:**
- InfluxDB query in `events_endpoints.py` line 521-596
- Possible issue with query deduplication
- May be querying multiple measurements
- Need to investigate `_get_events_from_influxdb` method

**Fix Location:** `services/data-api/src/events_endpoints.py`

### Issue #3: Frontend useEffect Dependency Warning

**EventsTab.tsx line 30:**
```typescript
useEffect(() => {
  if (showHistorical) {
    fetchHistoricalEvents();
    fetchEventStats();
  }
}, [timeRange, showHistorical]);  // ← Missing dependencies!
```

**Missing dependencies:** `fetchHistoricalEvents`, `fetchEventStats`

**Fix:** Wrap functions in `useCallback` or add to dependency array

---

## Detailed Fix Plan

### Phase 1: Implement EventStreamViewer Polling (HIGH PRIORITY)

**File:** `services/health-dashboard/src/components/EventStreamViewer.tsx`

**Changes Required:**

1. **Add State Management:**
```typescript
const [events, setEvents] = useState<Event[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const [lastEventId, setLastEventId] = useState<string | null>(null);
```

2. **Implement Polling useEffect:**
```typescript
useEffect(() => {
  if (isPaused) return;
  
  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch latest events
      const newEvents = await dataApi.getEvents({ limit: 50 });
      
      // Filter out duplicates and events we already have
      const filtered = newEvents.filter(e => 
        !events.some(existing => existing.id === e.id)
      );
      
      // Prepend new events (newest first)
      setEvents(prev => [...filtered, ...prev].slice(0, 500)); // Keep max 500
      
      if (filtered.length > 0) {
        setLastEventId(filtered[0].id);
      }
    } catch (err) {
      setError(`Failed to fetch events: ${err.message}`);
      console.error('Event fetch error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Initial fetch
  fetchEvents();
  
  // Poll every 3 seconds
  const interval = setInterval(fetchEvents, 3000);
  
  return () => clearInterval(interval);
}, [isPaused, lastEventId]);
```

3. **Add Error Display:**
```typescript
{error && (
  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
    <strong>Error:</strong> {error}
  </div>
)}
```

4. **Add Loading Indicator:**
```typescript
{loading && events.length === 0 && (
  <div className="text-center py-8">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
    <p className="mt-4 text-gray-500">Loading events...</p>
  </div>
)}
```

5. **Fix clearEvents Function:**
```typescript
const clearEvents = () => {
  setEvents([]);
  setLastEventId(null);
};
```

6. **Map API Events to Component Format:**
```typescript
const mapApiEvent = (apiEvent: any): Event => ({
  id: apiEvent.id,
  timestamp: apiEvent.timestamp,
  service: 'home-assistant',  // or parse from event data
  type: apiEvent.event_type,
  severity: inferSeverity(apiEvent),  // infer from event_type
  message: `${apiEvent.entity_id}: ${apiEvent.event_type}`,
  details: apiEvent
});

const inferSeverity = (event: any): 'info' | 'warning' | 'error' | 'debug' => {
  if (event.event_type === 'state_changed') return 'info';
  if (event.event_type === 'call_service') return 'debug';
  if (event.event_type.includes('error')) return 'error';
  if (event.event_type.includes('warn')) return 'warning';
  return 'info';
};
```

**Estimated Time:** 2-3 hours  
**Files Modified:** 1 (`EventStreamViewer.tsx`)  
**Lines Changed:** ~100 lines

---

### Phase 2: Fix Data Quality Issues (MEDIUM PRIORITY)

**File:** `services/data-api/src/events_endpoints.py`

**Changes Required:**

1. **Fix Query Deduplication (Line 521-596):**
```python
async def _get_events_from_influxdb(self, event_filter: EventFilter, limit: int, offset: int) -> List[EventData]:
    """Get events directly from InfluxDB with deduplication"""
    try:
        from influxdb_client import InfluxDBClient
        
        # ... existing setup ...
        
        # Build Flux query with proper deduplication
        query = f'''
        from(bucket: "{influxdb_bucket}")
          |> range(start: -24h)
          |> filter(fn: (r) => r._measurement == "home_assistant_events")
          |> filter(fn: (r) => r._field == "entity_id")  // Use a single field to deduplicate
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> group()
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: {limit})
        '''
        
        # Add offset if needed
        if offset > 0:
            query += f'  |> offset(n: {offset})'
        
        # Execute query...
    except Exception as e:
        logger.error(f"Error querying InfluxDB: {e}")
        return []
```

2. **Add Response Validation:**
```python
# After executing query, deduplicate in Python
seen_ids = set()
unique_events = []
for event in events:
    if event.id not in seen_ids:
        seen_ids.add(event.id)
        unique_events.append(event)

return unique_events[:limit]  # Enforce limit
```

**Estimated Time:** 1-2 hours  
**Files Modified:** 1 (`events_endpoints.py`)  
**Lines Changed:** ~50 lines

---

### Phase 3: Fix EventsTab Dependencies (LOW PRIORITY)

**File:** `services/health-dashboard/src/components/tabs/EventsTab.tsx`

**Changes Required:**

1. **Wrap Functions in useCallback:**
```typescript
const fetchHistoricalEvents = useCallback(async () => {
  try {
    setLoading(true);
    const events = await dataApi.getEvents({ limit: 100 });
    setHistoricalEvents(events || []);
  } catch (error) {
    console.error('Error fetching historical events:', error);
    setHistoricalEvents([]);
  } finally {
    setLoading(false);
  }
}, []);  // No dependencies needed if dataApi is stable

const fetchEventStats = useCallback(async () => {
  try {
    const statsData = await dataApi.getEventsStats(timeRange);
    setStats(statsData);
  } catch (error) {
    console.error('Error fetching event stats:', error);
  }
}, [timeRange]);  // Depends on timeRange
```

2. **Update useEffect:**
```typescript
useEffect(() => {
  if (showHistorical) {
    fetchHistoricalEvents();
    fetchEventStats();
  }
}, [timeRange, showHistorical, fetchHistoricalEvents, fetchEventStats]);
```

**Estimated Time:** 30 minutes  
**Files Modified:** 1 (`EventsTab.tsx`)  
**Lines Changed:** ~20 lines

---

### Phase 4: Add Error Boundaries (LOW PRIORITY)

**File:** `services/health-dashboard/src/components/ErrorBoundary.tsx` (NEW)

**Purpose:** Catch React errors and prevent full dashboard crash

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('EventsTab Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <h2 className="text-red-800 font-semibold">Something went wrong</h2>
          <p className="text-red-600">{this.state.error?.message}</p>
          <button 
            onClick={() => this.setState({ hasError: false })}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Wrap EventsTab:**
```typescript
<ErrorBoundary>
  <EventsTab darkMode={darkMode} />
</ErrorBoundary>
```

**Estimated Time:** 1 hour  
**Files Modified:** 2 (new ErrorBoundary.tsx, update Dashboard.tsx)  
**Lines Changed:** ~80 lines

---

### Phase 5: Testing with Puppeteer

**File:** `tests/visual/test-events-tab.js` (NEW)

**Test Cases:**
1. ✅ Real-time stream displays events
2. ✅ Polling starts automatically
3. ✅ Pause button stops polling
4. ✅ Resume button restarts polling
5. ✅ Auto-scroll works
6. ✅ Filters work (service, severity, search)
7. ✅ Historical mode switches correctly
8. ✅ Event statistics display
9. ✅ No duplicate events in UI
10. ✅ Error handling works

**Script:**
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  // Navigate to dashboard
  await page.goto('http://localhost:3000');
  
  // Click Events tab
  await page.click('button:has-text("Events")');
  await page.waitForTimeout(5000);  // Wait for polling
  
  // Check for events
  const eventCount = await page.$$eval('.event-item', items => items.length);
  console.log(`✅ Found ${eventCount} events`);
  
  // Test pause
  await page.click('button:has-text("Pause")');
  await page.waitForTimeout(3000);
  console.log('✅ Pause button clicked');
  
  // Take screenshot
  await page.screenshot({ path: 'test-results/events-tab-final.png' });
  
  await browser.close();
})();
```

**Estimated Time:** 2 hours  
**Files Created:** 1 (`test-events-tab.js`)  
**Lines:** ~100 lines

---

## Implementation Timeline

| Phase | Task | Priority | Time | Status |
|-------|------|----------|------|--------|
| 1 | Implement EventStreamViewer polling | HIGH | 2-3h | **REQUIRED** |
| 2 | Fix duplicate events in backend | MEDIUM | 1-2h | Recommended |
| 3 | Fix useCallback dependencies | LOW | 30m | Nice-to-have |
| 4 | Add Error Boundaries | LOW | 1h | Nice-to-have |
| 5 | Puppeteer testing | MEDIUM | 2h | Recommended |

**Total Estimated Time:** 6.5-8.5 hours (for all phases)  
**Minimum Required Time:** 2-3 hours (Phase 1 only)

---

## Success Criteria

### Phase 1 Complete When:
- [ ] EventStreamViewer shows real-time events
- [ ] Events update every 3 seconds
- [ ] Pause/Resume controls work
- [ ] Auto-scroll works
- [ ] Clear button empties the list
- [ ] Filters work (service, severity, search)
- [ ] No console errors
- [ ] Events display with correct formatting

### Full Fix Complete When:
- [ ] All Phase 1 criteria met
- [ ] No duplicate events in UI
- [ ] Backend returns correct number of events (respects limit)
- [ ] Historical mode works correctly
- [ ] Event statistics display properly
- [ ] Puppeteer tests pass
- [ ] Dashboard loads within 5 seconds
- [ ] No infinite polling loops

---

## Risk Assessment

### High Risk
- **EventStreamViewer changes** - Core functionality, affects user experience
- **Mitigation:** Test thoroughly with manual checks before automated tests

### Medium Risk  
- **Backend query changes** - Could break other queries
- **Mitigation:** Test /events endpoint separately before deploying

### Low Risk
- **useCallback changes** - Minor React optimization
- **Error boundaries** - Additive feature, doesn't change existing code

---

## Rollback Plan

If EventStreamViewer implementation causes issues:

1. **Quick Rollback:**
```bash
git checkout services/health-dashboard/src/components/EventStreamViewer.tsx
docker-compose restart dashboard
```

2. **Temporary Workaround:**
   - Hide Real-Time tab button
   - Show only Historical Events
   - Add message: "Real-time events coming soon"

3. **Feature Flag:**
```typescript
const ENABLE_REALTIME_STREAM = process.env.REACT_APP_ENABLE_REALTIME === 'true';

{ENABLE_REALTIME_STREAM && <EventStreamViewer darkMode={darkMode} />}
```

---

## Additional Notes

### API Response Format

Current API response (`/api/v1/events`):
```json
[
  {
    "id": "event_1760738766.029175",
    "timestamp": "2025-10-17T22:06:06.029175Z",
    "entity_id": "sun.sun",
    "event_type": "state_changed",
    "old_state": null,
    "new_state": null,
    "attributes": {},
    "tags": {
      "domain": "unknown",
      "device_class": "unknown"
    }
  }
]
```

### Component Dependencies

```
Dashboard
  └─ EventsTab
      ├─ EventStreamViewer (NOT IMPLEMENTED)
      └─ Historical Events (Working)
```

### Related Files

- `services/health-dashboard/src/components/EventStreamViewer.tsx` - Main fix target
- `services/health-dashboard/src/components/tabs/EventsTab.tsx` - Minor fixes
- `services/health-dashboard/src/services/api.ts` - API client (working)
- `services/health-dashboard/nginx.conf` - Routing (working)
- `services/data-api/src/events_endpoints.py` - Backend (needs deduplication)
- `services/data-api/src/main.py` - FastAPI app (working)

---

## Next Steps

1. ✅ **Research Complete** - All issues identified
2. **Implement Phase 1** - EventStreamViewer polling (HIGH PRIORITY)
3. **Test locally** - Manual verification
4. **Fix Phase 2** - Backend deduplication
5. **Add Puppeteer tests** - Automated verification
6. **Deploy to production** - After all tests pass

---

## Questions for Product Owner

1. What's the desired polling interval? (Recommended: 3-5 seconds)
2. Should we limit total events in memory? (Recommended: 500 max)
3. Should we persist paused state? (Between page refreshes)
4. What's priority: Real-time updates vs. server load?
5. Should we add WebSocket support in future?

---

**Report Generated:** October 17, 2025  
**By:** BMad Master Agent  
**Status:** Ready for Implementation

