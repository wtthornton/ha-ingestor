# Epic AI-3: Deployment Guide

**Epic:** AI-3 - Cross-Device Synergy & Contextual Opportunities  
**Date:** October 18, 2025  
**Status:** Ready for Production Deployment

---

## 🚀 Quick Deployment (5 minutes)

### Option 1: Full Rebuild (Recommended for First Deploy)

```powershell
# From project root
docker-compose build --no-cache ai-automation-service ai-automation-ui
docker-compose up -d ai-automation-service ai-automation-ui
```

### Option 2: Incremental Rebuild (Faster for Updates)

```powershell
docker-compose build ai-automation-service ai-automation-ui
docker-compose restart ai-automation-service ai-automation-ui
```

---

## ✅ Verification Steps

### 1. Check Service Health

```powershell
docker-compose ps ai-automation-service ai-automation-ui
```

**Expected:** Both services show "Up" and "(healthy)"

### 2. Verify Backend API

```powershell
# Check synergy stats endpoint
Invoke-RestMethod -Uri "http://localhost:8018/api/synergies/stats" -Method Get

# Check synergy list endpoint
Invoke-RestMethod -Uri "http://localhost:8018/api/synergies?limit=5" -Method Get
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "total_synergies": 0,
    "by_type": {},
    "by_complexity": {},
    "avg_impact_score": 0.0
  }
}
```

**Note:** 0 synergies is normal on first run (batch hasn't run yet)

### 3. Verify Frontend UI

**Browser Check:**
- Navigate to: http://localhost:3001/synergies
- Should see: "Automation Opportunities" page
- Stats cards should display (will show 0 until batch runs)
- No JavaScript console errors

### 4. Verify Daily Batch Integration

**Check Logs:**
```powershell
docker-compose logs ai-automation-service | Select-String "Phase 3c"
```

**Expected:** Should see Phase 3c synergy detection in next batch run

---

## 🧪 Testing the Deployment

### Trigger Manual Analysis

```powershell
# Trigger the batch job manually (don't wait for 3 AM)
Invoke-RestMethod -Uri "http://localhost:8018/api/analysis/trigger" -Method Post
```

### Monitor Logs in Real-Time

```powershell
docker-compose logs -f ai-automation-service
```

**Watch for:**
```
🔗 Phase 3c/7: Synergy Detection (Epic AI-3)...
✅ Device synergy detection complete: X synergies
🌤️ Part B: Weather opportunity detection...
⚡ Part C: Energy opportunity detection...
📅 Part D: Event opportunity detection...
✅ Total synergies (device + weather + energy + events): X
💾 Stored X synergies in database
🔗 Generating synergy-based suggestions...
✅ Synergy suggestion generation complete: X suggestions
```

### Verify Data in UI

1. **Refresh Synergies Page:** http://localhost:3001/synergies
2. **Should now show:**
   - Stats cards populated
   - Synergy cards in grid
   - Filter pills working

3. **Check Suggestions Page:** http://localhost:3001/
4. **Should now show:**
   - Mixed suggestions (pattern + feature + synergy)
   - Synergy suggestions have purple "synergy_device_pair" badge

---

## 🔍 Troubleshooting

### Issue: API Returns 404

**Cause:** Router not registered or container not rebuilt

**Fix:**
```powershell
# Force rebuild without cache
docker-compose build --no-cache ai-automation-service
docker-compose up -d ai-automation-service
```

### Issue: No Synergies Detected

**Possible Causes:**
1. **No compatible device pairs** - Check if you have motion sensors + lights in same area
2. **Existing automations** - Synergies filter out pairs that already have automations
3. **Confidence threshold** - Lower threshold in code if needed

**Debug:**
```powershell
# Check devices in system
Invoke-RestMethod -Uri "http://localhost:8006/api/devices" -Method Get

# Check entities and areas
Invoke-RestMethod -Uri "http://localhost:8006/api/entities" -Method Get
```

### Issue: Frontend Page Not Loading

**Cause:** UI container not rebuilt or routing issue

**Fix:**
```powershell
docker-compose build --no-cache ai-automation-ui
docker-compose up -d ai-automation-ui

# Clear browser cache and refresh
```

### Issue: Database Migration Errors

**Cause:** Migration already applied or database locked

**Fix:**
```powershell
# Check migration status inside container
docker-compose exec ai-automation-service alembic current

# If needed, force migration
docker-compose exec ai-automation-service alembic upgrade head
```

---

## 📊 Expected First Run Results

### Typical Home (50-100 devices)

**Synergies Detected:**
- Device pairs: 3-8 (motion→light, door→lock, etc.)
- Weather: 0-2 (seasonal - depends on forecast)
- Energy: 0-3 (depends on pricing data availability)
- Events: 0-2 (depends on device types)
- **Total:** 3-15 synergies

**Suggestions Generated:**
- Pattern-based: 3-5
- Feature-based: 2-4
- **Synergy-based: 2-5** ← NEW
- **Total:** 8-12 suggestions

**Performance:**
- Batch time: 4-7 minutes (was 3-5 minutes)
- Memory: ~600MB peak (was ~400MB)
- Cost: ~$0.003/run (~$1/year)

---

## 🎯 Success Criteria

### Day 1 (First Batch Run)

- ✅ Phase 3c appears in logs
- ✅ Synergies detected > 0
- ✅ Synergies stored in database
- ✅ Synergy suggestions generated
- ✅ /synergies page loads
- ✅ Stats cards populated
- ✅ No errors in logs

### Week 1 (Production Validation)

- ✅ Daily batch completes successfully (7/7 days)
- ✅ Synergy suggestions in Suggestions Tab
- ✅ Users approve synergy suggestions
- ✅ Cost stays <$0.05/week
- ✅ No performance degradation

---

## 📋 Rollback Plan (If Needed)

### Quick Rollback

```powershell
# Revert to previous Docker images
docker-compose down ai-automation-service ai-automation-ui
git checkout HEAD~1 services/ai-automation-service services/ai-automation-ui
docker-compose build ai-automation-service ai-automation-ui
docker-compose up -d
```

### Database Rollback

```powershell
# Downgrade migration
docker-compose exec ai-automation-service alembic downgrade -1
```

**Note:** Epic AI-3 is backward compatible - rollback shouldn't be necessary.

---

## 🎬 Post-Deployment Monitoring

### Daily Checks (Week 1)

1. **Morning Check (after 3 AM batch):**
   ```powershell
   docker-compose logs ai-automation-service | Select-String "Phase 3c" -Context 5
   ```

2. **Synergy Count:**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:8018/api/synergies/stats"
   ```

3. **User Approval Rate:**
   - Check Suggestions Tab
   - Track which synergy suggestions get approved
   - Monitor for patterns

### Performance Monitoring

**Metrics to Track:**
- Batch completion time (target: <10 minutes)
- Memory usage (target: <1GB peak)
- OpenAI cost (target: <$0.01/day)
- Synergy detection time (target: <2 minutes)

**Commands:**
```powershell
# Check batch duration
docker-compose logs ai-automation-service | Select-String "Analysis complete"

# Check memory
docker stats ai-automation-service --no-stream
```

---

## 🔧 Configuration Options

### Adjust Confidence Thresholds

**File:** `services/ai-automation-service/src/scheduler/daily_analysis.py`

```python
synergy_detector = DeviceSynergyDetector(
    data_api_client=data_client,
    ha_client=None,
    influxdb_client=data_client.influxdb_client,
    min_confidence=0.7,  # ← Adjust this (0.5 = more synergies, 0.9 = fewer but higher quality)
    same_area_required=True  # ← Set False to allow cross-area synergies
)
```

### Adjust Weather Thresholds

**File:** `services/ai-automation-service/src/scheduler/daily_analysis.py`

```python
weather_detector = WeatherOpportunityDetector(
    influxdb_client=data_client.influxdb_client,
    data_api_client=data_client,
    frost_threshold_f=32.0,  # ← Adjust frost temperature
    heat_threshold_f=85.0     # ← Adjust pre-cooling temperature
)
```

**After changes:** Rebuild and restart services

---

## 📚 Additional Resources

**Documentation:**
- Epic summary: `docs/prd/epic-ai3-cross-device-synergy.md`
- Story files: `docs/stories/story-ai3-*.md`
- Implementation summary: `implementation/EPIC_AI3_COMPLETE.md`
- API docs: http://localhost:8018/docs

**Support:**
- Check logs: `docker-compose logs ai-automation-service`
- Health check: http://localhost:8018/health
- API status: http://localhost:8018/docs

---

## 🎊 What to Expect

### First 24 Hours

**Batch runs at 3 AM:**
- Detects device synergies
- Checks weather forecast
- Identifies energy opportunities
- Generates AI suggestions

**You'll see:**
- Synergies appear on /synergies page
- New suggestions in Suggestions Tab
- Mixed suggestion types (pattern + feature + synergy)

### First Week

**System learns your home:**
- More accurate impact scores (usage-based)
- Better area traffic analysis
- Refined opportunity detection

**You provide feedback:**
- Approve valuable synergies
- Reject irrelevant ones
- System improves over time

---

## 💡 Tips for Best Results

1. **Ensure devices have areas assigned** in Home Assistant (bedroom, kitchen, etc.)
2. **Use friendly names** for better AI suggestions
3. **Review synergies daily** for first week to establish patterns
4. **Approve high-impact synergies** first (impact >80%)
5. **Check weather/energy** tabs if those synergies seem off

---

**Deployment support:** Check logs and API endpoints above  
**Questions:** Refer to implementation documentation in `/implementation/`

**Epic AI-3 is production-ready - enjoy the enhanced automation intelligence!** 🎉

