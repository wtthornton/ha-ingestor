# Polling Analysis: API Hub Context
## Dashboard Polling vs API Consumer Real-Time Needs

**Created**: 2025-10-14  
**Context**: Single-home API data hub (not user-facing app)  
**Key Insight**: Dashboard polling is fine; API consumers need webhooks

---

## 🎯 **Critical Context: System Purpose**

### **This is an API Data Hub, Not a User App**

**Primary Purpose**: Provide APIs to external systems
- Home Assistant automations (webhooks, entity sensors)
- External analytics platforms (historical queries)
- Cloud integrations (mobile apps, voice assistants)

**Secondary Purpose**: Admin monitoring dashboard
- Single home administrator
- Occasional viewing (not continuous)
- System health monitoring

**Implication**: Dashboard UX is NOT the priority! API performance is.

---

## 📊 **Current Polling Architecture**

### **What's Being Polled**

| Component | What | Interval | Why | Consumer Type |
|-----------|------|----------|-----|---------------|
| **Sports Live Games** | ESPN scores | 30s | Live updates | Admin dashboard |
| **Sports Upcoming** | Future games | 30s | Schedule | Admin dashboard |
| **Health Status** | Service health | 30s* | Monitoring | Admin dashboard |
| **Statistics** | Event counts | 30s* | Metrics | Admin dashboard |
| **Alerts** | Active alerts | 60s | Alert status | Admin dashboard |
| **Data Sources** | External APIs | Varies | Status check | Admin dashboard |

**\* Has WebSocket option** for health/stats (Epic 15)

---

## 🏠 **Single-Home Context: Polling is Actually Fine**

### **Why 30-Second Polling Works**

**User Pattern**:
```
Home admin's daily routine:
  09:00 - Opens dashboard, checks overnight events (2 min viewing)
  12:00 - Glances at dashboard while eating lunch (30 sec)
  15:00 - Checks if 49ers game started (10 sec)
  18:00 - Monitors system before evening (1 min)
  22:00 - Final health check before bed (30 sec)

Total dashboard active time: ~5 minutes per day
Total polling overhead: Negligible
```

**Load Analysis**:
```
Single admin user:
- Dashboard open: ~5 minutes/day
- Requests while open: 10 requests/min (2 endpoints × 5 polls/min)
- Total daily requests: ~50 requests
- ESPN API calls (90% cache): ~5 calls/day

Verdict: Polling overhead is trivial for single user
```

### **Dashboard Polling: KEEP AS-IS** ✅

**Current Implementation**:
```typescript
// 30-second polling for admin monitoring
useSportsData({ teamIds, pollInterval: 30000 });
```

**Why This is Correct**:
- 👤 **Single user**: No scaling concerns
- 🔧 **Monitoring tool**: Not watching games live
- 💤 **Dashboard closed**: Most of the time (no load)
- 📊 **30s freshness**: Acceptable for admin glances
- 💰 **API budget**: 5 ESPN calls/day is nothing

**No Changes Needed**: Dashboard polling is perfectly adequate ✅

---

## 🚀 **API Consumers: Real-Time IS Critical**

### **Problem: API Consumers Can't Poll Efficiently**

**Bad Scenario** (if HA had to poll):
```yaml
# ❌ Home Assistant polling our API every 15 seconds
automation:
  trigger:
    platform: time_pattern
    seconds: /15  # Poll every 15 seconds
  action:
    - service: rest_command.check_game_status
      data:
        url: "http://ingestor:8006/api/v1/sports/game-status/sf"
    - condition: template
      value_template: "{{ states('sensor.previous_score') != states('sensor.current_score') }}"
    - service: light.turn_on  # Finally trigger action

Problems:
  1. Polls even when no game active (wasted checks)
  2. Checks score even if unchanged (wasted processing)
  3. 15-second latency (misses quick plays)
  4. HA does work (should be our job)
  5. Can't scale (if 10 automations = 10× polling)
```

**API Calls**: 
- HA polls: 4 checks/minute × 60 min × 4 hours = 960 calls per game
- Our background check: 4 checks/minute = 240 calls per game
- Difference: 4× more load if HA polls

---

### **Good Scenario: Event-Driven Webhooks** (Epic 12)

```yaml
# ✅ We push to HA via webhook
automation:
  trigger:
    platform: webhook
    webhook_id: sports_score_change
  condition:
    - "{{ trigger.json.team == 'sf' }}"
  action:
    - service: light.turn_on  # Instant reaction!

Benefits:
  1. Instant (<15s from ESPN update)
  2. Only triggers on actual score changes
  3. No wasted checks
  4. HA does zero work (we do the monitoring)
  5. Scales perfectly (1 background check serves all automations)
```

**API Calls**:
- Our background check: 240 calls per game (same as before)
- HA polling: 0 calls (we push to HA)
- Result: Much more efficient

---

## 🔄 **Complete Data Flow Comparison**

### **Current: Dashboard Polling Only**

```
ESPN API (public, free)
  ↓ (on-demand, when dashboard requests)
Sports Service (cache 15s)
  ↓ (HTTP proxy)
Data API
  ↓ (HTTP)
Admin Dashboard (polls every 30s when open)
  ↓
Single admin user (views occasionally)
```

**Characteristics**:
- Poll-driven
- Dashboard-initiated
- ~5 ESPN calls/day (when dashboard open)
- Adequate for monitoring use case ✅

---

### **Epic 12: API Hub with Event-Driven**

```
                    ESPN API (public, free)
                      ↓ (15s background check)
              GameEventDetector (always running)
                /             \
               /               \
        InfluxDB           Webhook Manager
       (history)           (push to HA)
          ↓                      ↓
    Historical APIs      Home Assistant
    (on-demand)          (instant events)
          ↓                      ↓
   Analytics              Automations
   Platforms              (lights, scenes)
   
   Optional ↓
   Admin Dashboard (30s polling, monitoring only)
```

**Characteristics**:
- Event-driven for API consumers
- Single ESPN check serves all consumers
- Webhooks push to HA (no HA polling)
- Historical APIs for analytics
- Dashboard still polls (but that's OK - single user)

---

## 📈 **Performance Comparison**

### **Scenario: 4-Hour Football Game**

| Approach | ESPN API Calls | HA Load | Admin Experience | API Consumer Experience |
|----------|----------------|---------|------------------|------------------------|
| **Current (Dashboard Only)** | 5-10 calls | None | 30s updates OK | ❌ No APIs available |
| **HA Polls Our API** | 240 calls | 960 API calls | 30s updates | ⚠️ High load, 15s lag |
| **Epic 12 (Webhooks)** | 240 calls | 0 polling! | 30s updates | ✅ <15s webhooks |

**Winner**: Epic 12 (webhooks) - Single background check, push to all consumers

---

## 💡 **Revised Recommendations**

### **For Admin Dashboard: NO CHANGES NEEDED** ✅

**Current polling is perfect**:
```typescript
pollInterval = 30000  // 30 seconds

Why it's fine:
  ✓ Single admin user (no load)
  ✓ Monitoring tool (occasional viewing)
  ✓ Dashboard closed most of the time
  ✓ 30s freshness adequate for glances
  ✓ ESPN budget trivial (~5 calls/day)
```

**Optional optimization** (low priority):
```python
# Fix cache TTL alignment (5-minute change)
TTL_LIVE_GAMES = 30  # Match poll interval

Benefit: 90% cache hit rate (faster dashboard loads)
Priority: LOW (nice-to-have, not critical)
When: When you have 5 spare minutes
```

**Dashboard WebSocket**: NOT NEEDED
- Single user doesn't justify complexity
- 30s polling works fine for monitoring
- Save WebSocket infrastructure for API consumers

---

### **For API Consumers: WEBHOOKS ARE CRITICAL** ⭐

**This is the actual priority!**

**Implementation**: Epic 12 Phase 3 (Webhooks + Event Detection)

```python
# Background task in sports-data service
class GameEventDetector:
    async def start(self):
        """Monitor ESPN every 15 seconds"""
        while True:
            # 1. Check ESPN API
            current_games = await fetch_from_espn()
            
            # 2. Compare with previous state (from InfluxDB)
            for game in current_games:
                if score_changed(game):
                    # 3. Trigger webhook to HA
                    await webhook_manager.send({
                        "event": "score_changed",
                        "team": "sf",
                        "score": {"home": 17, "away": 10},
                        "score_diff": {"home": 3, "away": 0}
                    })
                    
                    # 4. Update InfluxDB (history)
                    await influxdb.write_game(game)
            
            # 5. Wait 15 seconds
            await asyncio.sleep(15)
```

**Why This Matters**:
1. **HA automations work instantly** (<15s from score change)
2. **HA doesn't poll** (we push to it)
3. **Efficient**: One ESPN check serves unlimited automations
4. **Scalable**: 1 automation or 100 = same backend load
5. **Reliable**: Retry logic, HMAC security

---

## 🎯 **Updated Priority Matrix**

### **Critical Path** (Must Have for API Hub):

| Feature | Purpose | Consumer | Timeline |
|---------|---------|----------|----------|
| **InfluxDB Writes** | Foundation for all APIs | All consumers | Phase 1 (2 weeks) |
| **Webhook System** | HA automation triggers | HA automations | Phase 3 (4 weeks) |
| **Event Detector** | Detect score changes | Webhook system | Phase 3 (4 weeks) |
| **Fast Status API** | HA conditional logic | HA automations | Phase 2 (3 weeks) |
| **Historical APIs** | Season stats, trends | Analytics platforms | Phase 2 (3 weeks) |

### **Nice to Have** (Admin Experience):

| Feature | Purpose | Consumer | Priority |
|---------|---------|----------|----------|
| **Dashboard Charts** | Win/loss visualization | Admin viewing | LOW |
| **Score Timeline** | Game progression | Admin viewing | LOW |
| **Real-Time Dashboard** | Instant score updates | Admin viewing | VERY LOW |
| **Dashboard WebSocket** | Push updates to UI | Admin viewing | NOT NEEDED |

---

## 🔍 **Polling vs Real-Time Decision Matrix**

### **When Polling is OK** ✅

- ✅ Admin monitoring dashboards (single user, occasional viewing)
- ✅ Non-critical status checks (30-60s freshness acceptable)
- ✅ Low-frequency data (updates every few minutes)
- ✅ Single-tenant systems (no scaling concerns)
- ✅ Dashboard closed most of the time

**Use Case**: Admin dashboard for this system ✅

---

### **When Real-Time is Required** ⭐

- ⭐ Automation triggers (must respond instantly)
- ⭐ Event-driven systems (webhooks, not polling)
- ⭐ Multi-consumer scenarios (push to many)
- ⭐ Time-sensitive notifications (<15s latency)
- ⭐ External integrations (can't make them poll us)

**Use Case**: HA automations, external API consumers ⭐

---

## 📋 **Action Items**

### **Immediate: NO CHANGES to Dashboard Polling** ✅

**Leave as-is**:
- 30-second polling interval
- In-memory cache
- Current ESPN API integration

**Rationale**: Works perfectly for single-admin monitoring use case

---

### **Short-Term: Optional Cache Fix** (5 minutes)

**If you have 5 spare minutes**:
```python
# services/sports-data/src/sports_api_client.py line 100
TTL_LIVE_GAMES = 30  # Change from 15 to 30
```

**Benefit**: 90% cache hit rate (faster dashboard loads)  
**Priority**: LOW (nice-to-have, not critical)

---

### **Medium-Term: Epic 12 Phase 3 (Webhooks)** ⭐ CRITICAL

**This is the real priority!**

**Why**: HA automations need event-driven webhooks (primary use case)

**Timeline**: 4 weeks (after Phase 1 & 2 complete)

**Deliverable**: 
- Background event detector (15s ESPN checks)
- Webhook system (HMAC-signed)
- HA automation endpoints (<50ms)
- External integration support

---

## 🔗 **Related Documentation**

- [Sports Data Detailed Review](./SPORTS_DATA_DETAILED_REVIEW.md) - Complete technical analysis
- [Sports API Integration Patterns](../../docs/kb/context7-cache/sports-api-integration-patterns.md) - KB best practices
- [External API Call Trees](./EXTERNAL_API_CALL_TREES.md) - Current data flow

---

## 📝 **Summary**

### **Dashboard Polling** (Current - Keep It)
- ✅ 30-second interval
- ✅ Adequate for single admin user
- ✅ Works with current infrastructure
- ✅ Low priority to optimize
- ✅ No real-time dashboard needed

### **API Consumer Real-Time** (Epic 12 - Build It)
- ⭐ Webhooks for HA automations (CRITICAL)
- ⭐ Event detection background task (CRITICAL)
- ⭐ Fast status APIs for HA conditionals (HIGH)
- ⭐ Historical query APIs for analytics (HIGH)
- ⭐ This is where development effort should focus

---

**Key Takeaway**: Don't spend time optimizing dashboard real-time updates. Focus on webhook system and API endpoints for external consumers (the primary use case).

**Next Steps**: Proceed with Epic 12 Phases 1-3, keep dashboard polling as-is.

