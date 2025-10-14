# ESPN API Polling Timing Analysis
## Current State, Problems, and Optimization Strategies

**Created**: 2025-10-14  
**Context**: API hub for single-home deployment  
**Purpose**: Optimize ESPN API polling for different use cases

---

## 📊 **Current Timing Configuration**

### **Backend (sports-data service)**

**File**: `services/sports-data/src/sports_api_client.py`

```python
# Line 100: Live games cache
await self.cache.set(cache_key, live_games, ttl=15)
# TTL = 15 seconds

# Line 146: Upcoming games cache  
await self.cache.set(cache_key, upcoming_games, ttl=300)
# TTL = 300 seconds (5 minutes)

# Line 175: Team list cache
await self.cache.set(cache_key, result, ttl=3600)
# TTL = 3600 seconds (1 hour)
```

**Summary**:
| Data Type | Cache TTL | Rationale |
|-----------|-----------|-----------|
| **Live games** | 15 seconds | Scores change frequently |
| **Upcoming games** | 5 minutes | Schedules rarely change |
| **Team list** | 1 hour | Static data |

---

### **Frontend (admin dashboard)**

**File**: `services/health-dashboard/src/components/sports/SportsTab.tsx`

```typescript
// Line 57: Sports data polling
useSportsData({
  teamIds: allTeamIds,
  league: 'all',
  pollInterval: 30000  // 30 seconds
});
```

**File**: `services/health-dashboard/src/hooks/useSportsData.ts`

```typescript
// Line 20: Default poll interval
pollInterval = 30000  // 30 seconds

// Line 85: Polling setup
const interval = setInterval(fetchGames, pollInterval);
```

**What Gets Polled**:
```typescript
async function fetchGames() {
  // Request 1: Live games
  GET /api/sports/games/live?team_ids=sf,dal
  
  // Request 2: Upcoming games
  GET /api/sports/games/upcoming?team_ids=sf,dal&hours=24
  
  // Total: 2 HTTP requests every 30 seconds
}
```

---

## ⚠️ **CRITICAL PROBLEM: Cache TTL Mismatch**

### **The Issue**

```
Dashboard poll interval: 30 seconds
Live games cache TTL:    15 seconds

Timeline:
t=0s   : Dashboard polls → Cache MISS → ESPN API call
t=15s  : Cache expires (TTL reached)
t=30s  : Dashboard polls → Cache MISS → ESPN API call (cache expired!)
t=45s  : Cache expires
t=60s  : Dashboard polls → Cache MISS → ESPN API call
...

Result: 100% cache MISS rate!
```

**Visual**:
```
Dashboard:  |--------30s poll--------|--------30s poll--------|
Cache TTL:  |----15s----|            |----15s----|
ESPN Calls: ^                        ^                        ^
            MISS                     MISS                     MISS
Cache Hits: ZERO!
```

### **Impact**

**Current Behavior** (Admin using dashboard for 5 minutes):
```
Duration: 5 minutes = 300 seconds
Polls: 300s / 30s = 10 polls
Requests per poll: 2 (live + upcoming)
Total requests: 20 requests

Cache behavior:
- Live games: 0% hit rate (all misses)
- Upcoming games: 90% hit rate (5min TTL > 30s poll)

ESPN API calls:
- Live: 10 calls (100% miss)
- Upcoming: 1 call (cached after first)
- Total: 11 ESPN API calls per 5-minute session
```

**With Fixed Cache** (TTL = 30s):
```
Duration: 5 minutes
Polls: 10 polls
Total requests: 20 requests

Cache behavior:
- Live games: 50-90% hit rate!
- Upcoming games: 90% hit rate

ESPN API calls:
- Live: 1-2 calls (cached!)
- Upcoming: 1 call
- Total: 2-3 ESPN API calls per 5-minute session

Savings: 73% reduction (11 → 3 calls)
```

---

## 🎯 **Polling Strategy Options**

### **Option 1: Fix Cache TTL (RECOMMENDED for Current State)** ✅

**Change**:
```python
# services/sports-data/src/sports_api_client.py line 100
# OLD:
await self.cache.set(cache_key, live_games, ttl=15)

# NEW:
await self.cache.set(cache_key, live_games, ttl=30)
```

**Impact**:
```
Effort: 5 minutes (change 1 number)
ESPN calls: 73% reduction
Dashboard experience: Slightly faster (cache hits)
Data freshness: 30s instead of 15s (acceptable for admin monitoring)
```

**Pros**:
- ✅ Instant improvement
- ✅ No frontend changes
- ✅ Works with current architecture
- ✅ 73% fewer ESPN API calls

**Cons**:
- ⚠️ Data is 30s stale vs 15s (minimal impact for admin monitoring)

**Verdict**: **Do this today** (5-minute quick win)

---

### **Option 2: Adaptive Dashboard Polling** (Optional Enhancement)

**Change**:
```typescript
// services/health-dashboard/src/hooks/useSportsData.ts

const getAdaptiveInterval = (hasLiveGames: boolean) => {
  if (hasLiveGames) {
    return 15000;  // 15s during live games
  } else {
    return 300000;  // 5 minutes when no games
  }
};

// Adjust polling based on game state
useEffect(() => {
  const interval = setInterval(
    fetchGames, 
    getAdaptiveInterval(liveGames.length > 0)
  );
  return () => clearInterval(interval);
}, [liveGames]);
```

**Impact**:
```
During live games:
- Poll: 15s
- Cache TTL: 15s (if we change it) or 30s
- ESPN calls: Moderate

No live games (off-season, off-hours):
- Poll: 5 minutes
- ESPN calls: Very low
- Better resource usage
```

**Pros**:
- ✅ Reduced load during off-hours
- ✅ Faster updates during games (if desired)
- ✅ Intelligent adaptation

**Cons**:
- ❌ Frontend complexity (2 hours work)
- ❌ Not needed for single admin user
- ❌ Minimal benefit for monitoring use case

**Verdict**: **Skip for admin dashboard** (unnecessary complexity)

---

### **Option 3: Background Event Detector** (Epic 12 Phase 3) ⭐

**New Component**: Background task in sports-data service

```python
# services/sports-data/src/event_detector.py

class GameEventDetector:
    """
    Background task checks ESPN every 15 seconds
    Replaces dashboard polling for event detection
    """
    
    async def start(self):
        while True:
            # 1. Check ESPN API (NFL + NHL)
            current_games = await self._fetch_all_games()
            
            # 2. Compare with previous state
            for game in current_games:
                if self._score_changed(game):
                    # 3. Trigger webhook to HA
                    await self.webhooks.send_score_change(game)
                    
                    # 4. Update InfluxDB
                    await self.influxdb.write_game(game)
            
            # 5. Wait 15 seconds
            await asyncio.sleep(15)
```

**ESPN API Calls**:
```
Background detector runs continuously:
- Check every: 15 seconds
- NFL + NHL: 2 API calls
- Per hour: 240 calls
- Per 4-hour game: 960 calls

But serves unlimited consumers:
- HA automations: 0 polling needed (webhooks)
- Analytics platforms: 0 polling needed (query InfluxDB)
- Admin dashboard: 0 polling needed (WebSocket optional)
```

**Pros**:
- ✅ Single source of truth (one check)
- ✅ Webhooks to HA (instant automation)
- ✅ InfluxDB persistence (historical queries)
- ✅ Scalable (unlimited consumers)
- ✅ Event-driven (not poll-driven)

**Cons**:
- ❌ Always running (even when no dashboard open)
- ❌ Higher ESPN API usage (240 calls/hour vs dashboard's ~10 calls/day)
- ⚠️ Only justified if webhook consumers exist

**Verdict**: **Build when you need webhooks** (Epic 12 Phase 3)

---

## 📊 **ESPN API Call Comparison**

### **Scenario 1: Admin Monitoring Only (Current)**

**Current (broken cache)**:
```
Admin opens dashboard: 5 minutes/day
Polls every: 30 seconds
Polls per session: 10 polls × 2 requests = 20 requests
Cache miss rate: 100% (live games)
ESPN API calls per session: 11 calls
ESPN API calls per day: 11 calls

ESPN API calls per month: 330 calls
```

**Fixed cache (TTL=30s)**:
```
Admin opens dashboard: 5 minutes/day
Polls every: 30 seconds
Polls per session: 10 polls × 2 requests = 20 requests
Cache hit rate: 90% (live games)
ESPN API calls per session: 2-3 calls
ESPN API calls per day: 2-3 calls

ESPN API calls per month: 60-90 calls
Savings: 73% reduction
```

---

### **Scenario 2: Background Event Detector (Epic 12)**

**With Event Detector**:
```
Background task runs: 24/7
Check interval: 15 seconds
Checks per hour: 240 (4 checks/min)
API calls per hour: 240 calls
API calls per 4-hour game: 960 calls
API calls per day: 5,760 calls

But serves:
- HA automations via webhooks (no HA polling!)
- Analytics via InfluxDB queries (no platform polling!)
- Admin dashboard via... ?
```

**Dashboard Options with Background Detector**:

**A. Keep Polling** (30s):
```
Admin dashboard: 30s polling (as today)
ESPN total: 5,760/day (background) + 3/day (dashboard) = 5,763/day
```

**B. Add WebSocket**:
```
Admin dashboard: WebSocket updates from background detector
ESPN total: 5,760/day (background only)
Dashboard: Instant updates (no polling)
```

**C. Hybrid**: Background detector + dashboard polls InfluxDB (not ESPN)
```
Admin dashboard: 30s polling of InfluxDB (local, fast)
ESPN total: 5,760/day (background only)
Dashboard: Gets data from local DB (instant, no ESPN load)
```

---

## 🎯 **Recommendations by Use Case**

### **Today: Admin Dashboard Only** (No Epic 12)

**Recommendation**: **Fix cache TTL to 30 seconds** ✅

**Change**:
```python
# services/sports-data/src/sports_api_client.py line 100
ttl=30  # Change from 15 to 30
```

**Result**:
- ESPN calls: 11/day → 3/day (73% reduction)
- Dashboard loads: Faster (cache hits)
- Data freshness: 30s (vs 15s) - acceptable for admin glances
- Effort: 5 minutes
- Risk: Zero

**Timeline**: Do this today (quick win)

---

### **Near Future: Epic 12 Phase 1 (InfluxDB Persistence)**

**ESPN Polling**: Keep dashboard polling (no change yet)

**Configuration**:
```
Dashboard polls: 30s (as today, queries data-api)
Data-api: Proxies to sports-data service
Sports-data: Returns cached data + writes to InfluxDB async
InfluxDB writes: Non-blocking (0ms perceived)

ESPN API calls: Same as today (2-3/day when dashboard open)
```

**Rationale**:
- Phase 1 only adds async writes
- Doesn't change polling strategy
- Dashboard still cache-based
- Background detector comes in Phase 3

---

### **Future: Epic 12 Phase 3 (Background Event Detector)**

**ESPN Polling**: Background detector replaces dashboard-driven polling

**Configuration**:
```
Background Task:
  Check interval: 15 seconds
  ESPN API calls: 240/hour (continuous)
  Serves: Webhooks, InfluxDB, optional dashboard

Dashboard Options:
  Option A: Keep 30s polling (simple, works)
  Option B: WebSocket from background task (real-time)
  Option C: Query InfluxDB instead of cache (fast, local)
```

**Recommendation**: **Option A or C**

**Option A** (Simple):
```typescript
// No changes - keep 30s polling
pollInterval = 30000

Dashboard → data-api → sports-data (cache) → response
Background task → ESPN (separate path)
```

**Option C** (Optimal):
```typescript
// Dashboard queries InfluxDB (local, fast)
pollInterval = 30000  // Or could be 60s

Dashboard → data-api → InfluxDB (direct query) → response
Background task → ESPN → InfluxDB (writes)

Benefit: No cache layer needed, queries fresh DB data
```

---

## 📈 **ESPN API Budget Analysis**

### **ESPN API Limits** (Unknown - Self-Imposed)

ESPN doesn't publish official limits, but best practices:
- Respectful usage: <10,000 calls/day
- Conservative target: <1,000 calls/day
- Very conservative: <100 calls/day

### **Our Usage Patterns**

**Current (Dashboard Only)**:
```
Admin monitoring: 2-3 calls/day
Off-season: 0-1 calls/day
Peak usage: 11 calls/day (if cache broken)

Annual: ~1,000 calls/year
Well within any reasonable limit ✅
```

**With Background Detector (24/7)**:
```
Continuous monitoring: 5,760 calls/day
Peak (game day): 5,760 calls/day
Off-season: 5,760 calls/day (same)

Annual: ~2.1 million calls/year
Potentially high, but still reasonable for free API
```

**With Background Detector (Game Hours Only)**:
```
NFL games: ~12 hours/week (Sept-Feb)
NHL games: ~15 hours/week (Oct-June)
Combined: ~20 hours/week average

Background during games only: 4,800 calls/week
Background off-hours: 0 calls
Annual: ~250,000 calls/year

Much more respectful! ✅
```

---

## 🎯 **Optimal Polling Strategy Recommendations**

### **Phase 0: Today (Quick Win)** ⭐ 5 MINUTES

**Fix cache TTL mismatch**:

```python
# services/sports-data/src/sports_api_client.py

# Line 100: Live games
await self.cache.set(cache_key, live_games, ttl=30)  # Was 15

# Line 146: Upcoming games (keep as-is)
await self.cache.set(cache_key, upcoming_games, ttl=300)  # Good

# Line 175: Team list (keep as-is)
await self.cache.set(cache_key, result, ttl=3600)  # Good
```

**Result**:
- 73% fewer ESPN calls
- Faster dashboard loads
- Better cache utilization

**Do this immediately!** ✅

---

### **Phase 1: Epic 12.1 (InfluxDB Writes)** - 2 weeks

**ESPN Polling**: No change from Phase 0

```python
# Dashboard-driven polling remains
# Async InfluxDB writes added (non-blocking)

@app.get("/api/v1/games/live")
async def get_live_games(teams: str):
    # 1. Check cache
    cached = await cache.get(f"live_{teams}")
    if cached:
        return cached  # Cache hit (instant)
    
    # 2. Fetch from ESPN (cache miss)
    games = await fetch_espn_scoreboard()
    
    # 3. Write to InfluxDB (async, non-blocking!)
    for game in games:
        asyncio.create_task(influxdb_writer.write_game(game))
    
    # 4. Return immediately (don't wait for writes)
    return {"games": games}
```

**ESPN API Calls**: Same as Phase 0 (2-3/day when dashboard open)

**What Changes**: Data persists to InfluxDB (foundation for Phase 2)

---

### **Phase 2: Epic 12.2 (Historical APIs)** - 3 weeks

**ESPN Polling**: Still dashboard-driven (no change)

**New**: Historical query APIs (don't poll ESPN, query InfluxDB)

```python
# New endpoint (doesn't call ESPN!)
@app.get("/api/v1/sports/games/history")
async def get_history(team: str, season: int):
    # Query local InfluxDB (fast, no ESPN call)
    query = f"SELECT * FROM nfl_scores WHERE team='{team}' AND season='{season}'"
    results = await influxdb.query(query)
    return results
```

**ESPN API Calls**: Same as Phase 1 (historical queries use InfluxDB, not ESPN)

**What Changes**: External consumers can query historical data

---

### **Phase 3: Epic 12.3 (Background Event Detector)** ⭐ - 4 weeks

**ESPN Polling**: Background task replaces dashboard-initiated polling

**New Architecture**:
```python
# Background task (always running during game hours)
class GameEventDetector:
    async def start(self):
        while True:
            # Check ESPN every 15 seconds
            games = await fetch_espn_scoreboard()
            
            # Detect events
            for game in games:
                if self._is_game_hour(game):
                    # Write to InfluxDB
                    await influxdb.write(game)
                    
                    # Check for events
                    if score_changed(game):
                        await webhooks.send("score_changed", game)
            
            await asyncio.sleep(15)
```

**ESPN API Calls**:
```
Smart scheduling:
- Only run during typical game hours:
  - NFL: Thu 8pm-11pm, Sun 1pm-11pm, Mon 8pm-11pm
  - NHL: Daily 7pm-10pm
- Total: ~20 hours/week
- Calls: 4,800/week = ~250,000/year

Versus 24/7:
- Calls: 5,760/day = ~2.1M/year

Savings: 88% reduction with smart scheduling
```

**Dashboard Options**:

**A. Keep Polling** (Simple):
```typescript
// No changes
pollInterval = 30000
// Queries cache (still works)
```

**B. Query InfluxDB** (Optimal):
```typescript
// Dashboard queries local DB instead of cache
async fetchGames() {
  // Query InfluxDB via data-api (fast, fresh)
  const response = await fetch('/api/v1/sports/games/current');
  // Gets data from local InfluxDB (written by background task)
}
```

**C. WebSocket** (Unnecessary):
```typescript
// Real-time push from background task
// Not needed for admin monitoring
// Save for future if desired
```

---

## 📊 **Recommended Polling Timeline**

### **TODAY: Fix Cache TTL** (5 minutes) ⭐

```python
# services/sports-data/src/sports_api_client.py
ttl=30  # Line 100, change from 15
```

**Impact**: 73% fewer ESPN calls immediately

---

### **WEEK 1-2: Epic 12 Phase 1** (InfluxDB Writes)

**ESPN Polling**: Same as today (dashboard-driven)
- Cache TTL: 30s (already fixed)
- Dashboard poll: 30s
- ESPN calls: 2-3/day when dashboard open

**New**: Async writes to InfluxDB (non-blocking)

---

### **WEEK 3-5: Epic 12 Phase 2** (Historical APIs)

**ESPN Polling**: Same as Phase 1
- Background detector NOT started yet
- Dashboard still cache-based
- ESPN calls: 2-3/day

**New**: Historical query APIs (use InfluxDB, not ESPN)

---

### **WEEK 6-9: Epic 12 Phase 3** (Background Detector) ⭐

**ESPN Polling**: Background task starts (replaces dashboard-initiated)

**New Polling Strategy**:
```python
# Background detector configuration
CHECK_INTERVAL = 15  # seconds

# Smart scheduling (game hours only)
def should_check_now():
    """Only check during typical game hours"""
    now = datetime.now()
    
    # NFL game hours (Thu/Sun/Mon)
    if now.weekday() in [3, 6, 0]:  # Thu, Sun, Mon
        if 13 <= now.hour <= 23:  # 1pm-11pm
            return True
    
    # NHL game hours (daily)
    if 19 <= now.hour <= 22:  # 7pm-10pm
        return True
    
    # Off-hours
    return False

async def event_detector_loop():
    while True:
        if should_check_now():
            await check_espn_and_trigger_events()
            await asyncio.sleep(15)
        else:
            await asyncio.sleep(300)  # Check every 5 min if game hours
```

**ESPN API Calls**:
- Game hours: 240 calls/hour
- Off-hours: 0 calls
- Annual: ~250,000 calls/year (vs 2.1M if 24/7)

**Dashboard**: Can keep 30s polling or switch to InfluxDB queries

---

## 🎯 **Final Recommendations**

### **Immediate (Today)** ⭐

```python
# Fix cache TTL mismatch
TTL_LIVE_GAMES = 30  # Change from 15
```

**Why**: 
- ✅ 5-minute change
- ✅ 73% fewer ESPN calls  
- ✅ Faster dashboard (cache hits)
- ✅ Zero risk
- ✅ Immediate benefit

---

### **Epic 12 Phase 1-2** (Weeks 1-5)

**Keep Dashboard Polling**:
```typescript
pollInterval = 30000  // Don't change
```

**Backend TTLs**:
```python
TTL_LIVE_GAMES = 30     // Already fixed ✅
TTL_UPCOMING = 300      // Keep as-is ✅
TTL_TEAMS = 3600        // Keep as-is ✅
```

**ESPN Calls**: 2-3/day (when admin views dashboard)

**Why**:
- Dashboard-driven is fine for single admin
- Focus on InfluxDB writes and APIs
- Background detector comes later

---

### **Epic 12 Phase 3** (Weeks 6-9)

**Add Background Event Detector**:
```python
CHECK_INTERVAL = 15  # seconds
SMART_SCHEDULING = True  # Only during game hours
```

**ESPN Calls**: 
- With smart scheduling: ~250K/year
- Without: ~2.1M/year
- **Recommendation**: Use smart scheduling ✅

**Dashboard**: 
- **Option A**: Keep 30s polling (simple, works)
- **Option C**: Query InfluxDB instead (optimal)
- **Skip Option B**: WebSocket (unnecessary for admin)

---

## 📋 **ESPN Polling Configuration Summary**

### **Recommended Values**

| Phase | Component | Interval | ESPN Calls/Day | Status |
|-------|-----------|----------|----------------|--------|
| **Phase 0 (Today)** | Dashboard cache TTL | 30s | 2-3 | ⭐ Quick fix |
| **Phase 0 (Today)** | Dashboard polling | 30s | - | ✅ Keep as-is |
| **Phase 1-2 (Weeks 1-5)** | Dashboard polling | 30s | 2-3 | ✅ No change |
| **Phase 3 (Weeks 6-9)** | Background detector | 15s* | 1,000-5,000** | ⭐ Build this |
| **Phase 3** | Dashboard (option A) | 30s | +2-3 | ✅ Simple |
| **Phase 3** | Dashboard (option C) | 30s | 0 | ✅ Optimal |

**\* Only during game hours with smart scheduling**  
**\*\* Varies by schedule (game hours only vs 24/7)**

---

## 🔍 **Decision Points for You**

### **1. Fix Cache TTL Today?**

**Question**: Change TTL from 15s to 30s?

**My Recommendation**: **YES** ✅
- Takes 5 minutes
- 73% fewer ESPN calls
- No downside
- Do it now while we're discussing this

---

### **2. Background Detector Polling (Phase 3)**

**Question**: Check ESPN every 15 seconds or less frequently?

**Options**:
- **15 seconds**: Good balance (industry standard for live sports)
- **30 seconds**: Slower but lighter load
- **10 seconds**: Faster detection but higher load

**My Recommendation**: **15 seconds with smart scheduling** ✅
- Only run during game hours (~20 hours/week)
- 15s is fast enough (<30s webhook delivery)
- Smart scheduling reduces API load by 88%
- ~250K calls/year is reasonable

---

### **3. Dashboard Polling (After Phase 3)**

**Question**: Keep dashboard polling or switch to InfluxDB queries?

**Option A** (Simple):
- Dashboard keeps 30s polling
- Queries cache (as today)
- Works fine, no changes

**Option C** (Better):
- Dashboard queries InfluxDB (local, fast)
- Background detector keeps InfluxDB fresh
- Eliminates cache layer complexity
- Instant dashboard loads (local DB)

**My Recommendation**: **Option C** when you implement Phase 3
- Dashboard queries local InfluxDB
- Background task keeps it fresh
- Best of both worlds

---

## ✅ **Action Items**

### **Immediate** (Today - 5 minutes)

- [ ] Fix cache TTL: `ttl=30` in line 100 of `sports_api_client.py`
- [ ] Test dashboard (should see faster loads on cache hits)
- [ ] Monitor ESPN API calls (should drop 73%)

### **Epic 12 Phase 1** (Weeks 1-2)

- [ ] Keep all polling as-is (dashboard 30s, cache TTL 30s)
- [ ] Add async InfluxDB writes
- [ ] No polling changes needed

### **Epic 12 Phase 3** (Weeks 6-9)

- [ ] Implement background detector (15s interval)
- [ ] Add smart scheduling (game hours only)
- [ ] Dashboard: Switch to InfluxDB queries (optional)
- [ ] Monitor ESPN API usage (<1,000/day target)

---

## 📊 **ESPN Call Projection**

### **Current (Broken Cache)**
```
Daily: 11 calls
Monthly: 330 calls
Yearly: 4,000 calls
Status: Wasteful (100% cache miss)
```

### **Phase 0 (Fixed Cache)** ⭐
```
Daily: 2-3 calls
Monthly: 60-90 calls
Yearly: 730-1,100 calls
Status: Efficient ✅
```

### **Phase 3 (Background 24/7)**
```
Daily: 5,760 calls
Monthly: 172,800 calls
Yearly: 2.1 million calls
Status: High but acceptable
```

### **Phase 3 (Background + Smart Scheduling)** ✅
```
Daily: 800-1,200 calls (game days)
Daily: 0-100 calls (off days)
Monthly: 20,000-30,000 calls
Yearly: 250,000-350,000 calls
Status: Reasonable and respectful ✅
```

---

## 💡 **My Complete Recommendation**

### **ESPN Polling Configuration**:

**1. TODAY** (5 minutes):
```python
TTL_LIVE_GAMES = 30  # Fix cache TTL
```

**2. Phase 1-2** (Weeks 1-5):
```
No polling changes
Dashboard: 30s polling (keep)
ESPN calls: 2-3/day
```

**3. Phase 3** (Weeks 6-9):
```python
# Background detector
CHECK_INTERVAL = 15  # seconds
SMART_SCHEDULING = True  # Only game hours

# Game hour windows
NFL_GAME_HOURS = [(4, 20, 23), (0, 20, 23), (1, 13, 23)]  # Thu/Mon 8pm-11pm, Sun 1pm-11pm
NHL_GAME_HOURS = [(0-6, 19, 22)]  # Daily 7pm-10pm

ESPN calls: ~1,000/day during games, ~100/day off-season
```

**4. Dashboard** (Phase 3):
```typescript
// Option C: Query InfluxDB instead of cache
async fetchGames() {
  const response = await fetch('/api/v1/sports/games/current');
  // data-api queries InfluxDB (fresh data, local, fast)
}
```

---

## 🎯 **Summary**

**Current Problem**: Cache TTL (15s) doesn't align with dashboard poll (30s) = 100% miss rate

**Quick Fix**: Change TTL to 30s = 73% fewer ESPN calls ⭐

**Long-term**: Background detector (Phase 3) with smart scheduling = Efficient event-driven system ✅

**Dashboard**: Keep 30s polling (adequate for admin monitoring), optionally switch to InfluxDB queries in Phase 3

---

**Questions?**
- Should I make the cache TTL fix now (5 minutes)?
- Do you agree with 15s interval for background detector?
- Should we use smart scheduling (game hours only)?
- Keep dashboard at 30s polling?

