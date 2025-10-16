# Deployment Guide: Story AI2.5 - Unified Daily Batch Job

**Date:** 2025-10-16  
**Status:** ✅ APPROVED - Ready for Deployment  
**Epic:** AI-2 Device Intelligence System

---

## 🎯 Deployment Summary

**What's Being Deployed:**
- Unified daily batch job combining Epic-AI-1 (Pattern Detection) + Epic-AI-2 (Device Intelligence)
- 6-phase job running at 3 AM daily
- 99% resource reduction vs. real-time architecture

**Impact:**
- ✅ No breaking changes to existing functionality
- ✅ Graceful error handling (phases can fail independently)
- ✅ Same user experience (suggestions at 7 AM)
- ✅ Lower resource usage

---

## 📋 Pre-Deployment Checklist

- [x] Code reviewed and approved
- [x] All tests passing (56/56)
- [x] No linter errors
- [x] Documentation complete
- [ ] Docker image built
- [ ] Integration test passed
- [ ] Backup plan ready
- [ ] Monitoring configured

---

## 🚀 Deployment Steps

### **Step 1: Build Docker Image**

```bash
# Navigate to project root
cd C:\cursor\ha-ingestor

# Build the image
docker-compose build ai-automation-service

# Expected output:
# ✓ Successfully built
# ✓ Successfully tagged ha-ingestor-ai-automation-service:latest
```

**Estimated Time:** 2-3 minutes

---

### **Step 2: Verify Image**

```bash
# Check image exists
docker images | Select-String "ai-automation-service"

# Expected output:
# ha-ingestor-ai-automation-service   latest   [image-id]   [size]
```

---

### **Step 3: Stop Current Service (if running)**

```bash
# Stop the service
docker-compose stop ai-automation-service

# Remove old container
docker-compose rm -f ai-automation-service
```

---

### **Step 4: Start New Service**

```bash
# Start with new image
docker-compose up -d ai-automation-service

# Check status
docker-compose ps ai-automation-service

# Expected output:
# NAME                              STATUS
# ha-ingestor-ai-automation-service Up (healthy)
```

**Estimated Time:** 30 seconds

---

### **Step 5: Verify Health**

```bash
# Check health endpoint
curl http://localhost:8018/health

# Expected output:
# {
#   "status": "healthy",
#   "service": "ai-automation-service",
#   "version": "1.0.0",
#   "device_intelligence": {
#     "capability_listener": "ready",
#     "scheduler": "running"
#   }
# }
```

---

### **Step 6: Trigger Manual Test Run (Optional)**

```bash
# Trigger immediate analysis (don't wait for 3 AM)
curl -X POST http://localhost:8018/api/analysis/trigger

# Expected output:
# {
#   "status": "triggered",
#   "message": "Manual analysis run started in background"
# }
```

**Note:** This runs the full 6-phase job immediately. Watch logs in real-time.

---

### **Step 7: Monitor Logs**

```bash
# Follow logs in real-time
docker-compose logs ai-automation-service --tail=100 --follow

# Look for these indicators:
# ================================================================================
# 🚀 Unified Daily AI Analysis Started (Epic AI-1 + AI-2)
# ================================================================================
# 📡 Phase 1/6: Device Capability Update (Epic AI-2)...
# ✅ Device capabilities updated:
#    - Devices checked: 99
#    - Capabilities updated: 5
# 
# 📊 Phase 2/6: Fetching events (SHARED by AI-1 + AI-2)...
# ✅ Fetched 14523 events
# 
# 🔍 Phase 3/6: Pattern Detection (Epic AI-1)...
# ✅ Total patterns detected: 5
# 
# 🧠 Phase 4/6: Feature Analysis (Epic AI-2)...
# ✅ Feature analysis complete:
#    - Opportunities found: 23
# 
# 💡 Phase 5/6: Combined Suggestion Generation (AI-1 + AI-2)...
# ✅ Combined suggestions: 8 total
#    - Pattern-based (AI-1): 3
#    - Feature-based (AI-2): 5
# 
# 📢 Phase 6/6: Publishing MQTT notification...
# ✅ MQTT notification published
# 
# ================================================================================
# ✅ Unified Daily AI Analysis Complete!
# ================================================================================
#   Duration: 8.3 seconds
```

**Expected Duration:** 7-15 minutes (or faster if limited data)

---

### **Step 8: Verify Results**

```bash
# Check suggestions in database
docker-compose exec ai-automation-service python -c "
from src.database.models import get_db_session
from src.database.crud import get_all_suggestions
import asyncio

async def check():
    async with get_db_session() as db:
        suggestions = await db.execute('SELECT type, title, confidence FROM suggestions ORDER BY created_at DESC LIMIT 10')
        for row in suggestions:
            print(f'{row.type}: {row.title} ({row.confidence:.2f})')

asyncio.run(check())
"

# Expected output:
# pattern_automation: AI Suggested: Turn on bedroom light at 10:30 PM (0.92)
# feature_discovery: Enable LED Notifications on Kitchen Switch (0.88)
# pattern_automation: Motion + light automation (hallway) (0.85)
# feature_discovery: Configure vibration detection on front door (0.82)
# ...
```

---

## ✅ Deployment Validation

### **Success Criteria**

Check all of these:

- [ ] Service started successfully
- [ ] Health endpoint returns "healthy"
- [ ] All 6 phases executed
- [ ] Both pattern and feature suggestions generated
- [ ] Suggestions stored in database
- [ ] MQTT notification published
- [ ] No errors in logs
- [ ] Duration <15 minutes
- [ ] Memory usage <500MB

### **Validation Commands**

```bash
# 1. Service health
curl http://localhost:8018/health | jq '.status'
# Expected: "healthy"

# 2. Check scheduler status
curl http://localhost:8018/api/analysis/status | jq

# 3. Check last run results
docker-compose exec ai-automation-service \
  sqlite3 /app/data/ai_automation.db \
  "SELECT COUNT(*) FROM suggestions WHERE created_at > datetime('now', '-1 day');"
# Expected: >0

# 4. Check memory usage
docker stats ai-automation-service --no-stream
# Expected: <500MB

# 5. Check logs for errors
docker-compose logs ai-automation-service --tail=500 | Select-String -Pattern "ERROR|❌"
# Expected: No critical errors
```

---

## 📊 Monitoring After Deployment

### **What to Monitor**

1. **First Scheduled Run (3 AM next day)**
   - Set alarm for 3:05 AM
   - Check logs: `docker-compose logs ai-automation-service --since 3am`
   - Verify all 6 phases completed

2. **Daily for First Week**
   - Check job completion
   - Verify suggestions generated
   - Monitor resource usage
   - Check for errors

3. **Weekly After First Week**
   - Review suggestion quality
   - Check OpenAI costs
   - Verify user engagement

### **Key Metrics**

| Metric | Target | Alert If |
|--------|--------|----------|
| Job Duration | <15 min | >20 min |
| Memory Usage | <500MB | >600MB |
| OpenAI Cost | <$0.01/run | >$0.05/run |
| Suggestions Generated | 5-10 | <2 or >15 |
| Error Rate | 0% | >5% |

### **Monitoring Commands**

```bash
# Check last run status
curl http://localhost:8018/api/analysis/status

# Check job history
curl http://localhost:8018/api/analysis/history | jq

# Check OpenAI usage
docker-compose exec ai-automation-service \
  sqlite3 /app/data/ai_automation.db \
  "SELECT SUM(openai_tokens), SUM(openai_cost_usd) FROM analysis_runs WHERE created_at > datetime('now', '-7 days');"

# Check suggestion breakdown
docker-compose exec ai-automation-service \
  sqlite3 /app/data/ai_automation.db \
  "SELECT type, COUNT(*) FROM suggestions GROUP BY type;"
```

---

## 🔄 Rollback Plan

If issues occur, here's how to rollback:

### **Option A: Rollback to Previous Image**

```bash
# Stop current service
docker-compose stop ai-automation-service

# Pull previous image (if tagged)
docker pull ha-ingestor-ai-automation-service:[previous-tag]

# Start with previous image
docker-compose up -d ai-automation-service

# Verify
docker-compose logs ai-automation-service --tail=50
```

### **Option B: Disable Device Intelligence**

Epic-AI-1 (Pattern Detection) still works independently:

```bash
# Edit docker-compose.yml to use environment variable
# AI_ENABLE_DEVICE_INTELLIGENCE=false

# Restart service
docker-compose restart ai-automation-service
```

**Note:** This will skip Phases 1 and 4, but Phases 2-3-5-6 (pattern detection) still work.

### **Option C: Emergency Stop**

```bash
# Stop the service completely
docker-compose stop ai-automation-service

# Pattern detection and suggestions temporarily disabled
# No impact on other services (data-api, websocket, etc.)
```

---

## 🐛 Troubleshooting

### **Issue 1: Job Fails at Phase 1**

**Symptoms:**
```
📡 Phase 1/6: Device Capability Update (Epic AI-2)...
⚠️ Device capability update failed: Connection refused
   → Continuing with pattern analysis...
```

**Cause:** Zigbee2MQTT bridge not available

**Impact:** Only pattern suggestions generated (no feature suggestions)

**Fix:**
1. Check MQTT broker: `docker-compose ps mqtt` or check HA MQTT addon
2. Verify MQTT_BROKER environment variable
3. Restart MQTT broker if needed
4. Re-run analysis after MQTT is available

**Workaround:** Pattern suggestions still work, feature suggestions skipped gracefully

---

### **Issue 2: No Suggestions Generated**

**Symptoms:**
```
✅ Combined suggestions: 0 total
   - Pattern-based (AI-1): 0
   - Feature-based (AI-2): 0
```

**Possible Causes:**
- No patterns detected (insufficient data)
- No opportunities found (all devices 100% utilized)
- OpenAI API key invalid

**Diagnosis:**
```bash
# Check patterns
docker-compose exec ai-automation-service \
  sqlite3 /app/data/ai_automation.db \
  "SELECT COUNT(*) FROM patterns WHERE created_at > datetime('now', '-1 day');"

# Check opportunities
docker-compose logs ai-automation-service --tail=200 | Select-String "opportunities found"

# Check OpenAI client
docker-compose logs ai-automation-service --tail=200 | Select-String "OpenAI"
```

**Fix:**
- Wait for more data (30 days of events needed)
- Verify OpenAI API key in environment
- Check device capabilities table populated

---

### **Issue 3: Job Takes >15 Minutes**

**Symptoms:**
```
✅ Unified Daily AI Analysis Complete!
  Duration: 23.5 seconds  ← Too long!
```

**Possible Causes:**
- Large dataset (>100K events)
- Slow InfluxDB query
- Many LLM calls

**Diagnosis:**
```bash
# Check event count
docker-compose logs ai-automation-service --tail=500 | Select-String "Fetched.*events"

# Check phase durations
docker-compose logs ai-automation-service --tail=500 | Select-String "Phase.*✅"
```

**Fix:**
- Optimize InfluxDB query (add indexes)
- Reduce max_suggestions limit (currently 10)
- Increase resources (CPU/memory)

---

### **Issue 4: High Memory Usage**

**Symptoms:**
```
docker stats ai-automation-service
# MEMORY: 850MB ← Too high!
```

**Possible Causes:**
- Large DataFrame in memory (Phase 2)
- Pattern detection holding data
- Memory leak

**Fix:**
```bash
# Restart service
docker-compose restart ai-automation-service

# If persists, check DataFrame size
docker-compose logs ai-automation-service --tail=500 | Select-String "Fetched.*events"

# Consider reducing event query limit (currently 100K)
```

---

## 📞 Support & Escalation

### **Getting Help**

1. **Check Documentation:**
   - `implementation/QUICK_REFERENCE_AI2.md` - Quick debugging
   - `implementation/REVIEW_GUIDE_STORY_AI2-5.md` - Detailed guide

2. **Check Logs:**
   ```bash
   docker-compose logs ai-automation-service --tail=500 > logs.txt
   ```

3. **Check Database:**
   ```bash
   docker-compose exec ai-automation-service \
     sqlite3 /app/data/ai_automation.db .dump > db_dump.sql
   ```

4. **Gather Metrics:**
   ```bash
   docker stats --no-stream > stats.txt
   curl http://localhost:8018/health > health.json
   curl http://localhost:8018/api/analysis/status > status.json
   ```

---

## ✅ Post-Deployment Checklist

After 24 hours:
- [ ] First scheduled run completed (3 AM)
- [ ] Suggestions visible in dashboard
- [ ] No critical errors in logs
- [ ] Resource usage within limits
- [ ] OpenAI costs reasonable

After 1 week:
- [ ] 7 successful runs
- [ ] User feedback collected
- [ ] Suggestion quality verified
- [ ] Performance metrics stable

---

## 🎉 Deployment Complete!

**Next Steps:**
1. Monitor first 3 AM run
2. Collect user feedback
3. Track suggestion adoption
4. Plan Stories 2.6-2.9 (Dashboard + Polish)

**Success! Epic AI-2 is now in production.** 🚀

---

**Deployed by:** _______________  
**Date:** _______________  
**Sign-off:** _______________

