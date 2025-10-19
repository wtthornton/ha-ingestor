# System Health Fix Plan - Weather API Configuration

**Date:** October 18, 2025  
**Issue:** 13.3% health score due to 13 unconfigured weather-api services  
**Target:** Bring health score to 90%+ by properly configuring weather services

## Root Cause Analysis

### Problem Identified
The system is detecting **13 instances** of `weather-api` services that are all in `not_configured` status. This is happening because:

1. **Missing Environment Configuration**: The weather-api service requires `WEATHER_API_KEY` but it's not properly configured
2. **Service Detection Logic**: The health monitoring system is detecting multiple weather-api instances that aren't properly initialized
3. **Environment File Missing**: `infrastructure/.env.weather` file doesn't exist (only template exists)

### Current Status
- ✅ Core services working: websocket-ingestion, enrichment-pipeline
- ✅ All 17 Docker containers healthy and running  
- ✅ Home Assistant connection active (192.168.1.86:8123)
- ✅ InfluxDB operational
- ❌ 13 weather-api services showing as `not_configured`
- ❌ Health score: 13.3% (2 active / 15 total)

## Fix Plan - Phase 1: Environment Configuration

### Step 1: Create Weather Environment File (5 minutes)

**Action:** Create proper weather configuration file

```bash
# Create the missing .env.weather file
cp infrastructure/env.weather.template infrastructure/.env.weather
```

**Configure with actual API key:**
```bash
# Edit infrastructure/.env.weather
WEATHER_API_KEY=your_actual_openweathermap_api_key_here
WEATHER_LAT=36.1699
WEATHER_LON=-115.1398
WEATHER_UNITS=metric
WEATHER_CACHE_SECONDS=300
WEATHER_PROVIDER=openweathermap
```

### Step 2: Update Main Environment File (5 minutes)

**Action:** Ensure main environment has weather configuration

```bash
# Edit infrastructure/env.production or create .env file
WEATHER_API_KEY=your_actual_openweathermap_api_key_here
WEATHER_ENRICHMENT_ENABLED=true
ENABLE_WEATHER_API=true
```

### Step 3: Restart Services (2 minutes)

**Action:** Restart services to pick up new configuration

```bash
# Restart weather-related services
docker-compose restart weather-api enrichment-pipeline websocket-ingestion

# Or full restart if needed
docker-compose down && docker-compose up -d
```

## Fix Plan - Phase 2: Service Configuration

### Step 4: Verify Weather API Service (5 minutes)

**Action:** Check if weather-api service is properly defined in docker-compose

**Current Issue:** Weather-api service is defined in `docker-compose.dev.yml` but may not be in production compose file.

**Fix:** Ensure weather-api service is properly defined:

```yaml
# Add to docker-compose.yml if missing
weather-api:
  build:
    context: ./services/weather-api
    dockerfile: Dockerfile
  container_name: ha-ingestor-weather-api
  restart: unless-stopped
  ports:
    - "8007:8007"
  environment:
    - WEATHER_API_KEY=${WEATHER_API_KEY}
    - WEATHER_API_URL=${WEATHER_API_URL:-https://api.openweathermap.org/data/2.5}
    - INFLUXDB_URL=http://influxdb:8086
    - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
    - INFLUXDB_ORG=${INFLUXDB_ORG}
    - INFLUXDB_BUCKET=${INFLUXDB_BUCKET}
  depends_on:
    influxdb:
      condition: service_healthy
  networks:
    - ha-ingestor-network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8007/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 30s
```

### Step 5: Fix Service Detection Logic (10 minutes)

**Action:** Investigate why 13 weather-api instances are detected

**Possible Causes:**
1. Health monitoring system creating multiple instances
2. Service registration happening multiple times
3. Fallback weather services being created

**Investigation Commands:**
```bash
# Check service definitions
docker-compose config | grep -A 20 weather-api

# Check running containers
docker ps | grep weather

# Check service health endpoints
curl http://localhost:3000/api/v1/services | jq '.services[] | select(.service | contains("weather"))'
```

## Fix Plan - Phase 3: Alternative Solutions

### Option A: Enable Weather API (Recommended)

**If you have OpenWeatherMap API key:**
1. Get free API key from: https://openweathermap.org/api
2. Configure in environment files
3. Restart services
4. Expected result: 90%+ health score

### Option B: Disable Weather API Detection

**If you don't need weather functionality:**
1. Set `ENABLE_WEATHER_API=false`
2. Remove weather-api service from docker-compose
3. Update health monitoring to ignore weather services
4. Expected result: 85%+ health score

### Option C: Mock Weather API

**For testing/demo purposes:**
1. Create mock weather service
2. Return static weather data
3. No external API required
4. Expected result: 90%+ health score

## Implementation Timeline

### Immediate (15 minutes)
- [ ] Create `.env.weather` file with API key
- [ ] Update main environment configuration  
- [ ] Restart services
- [ ] Verify health score improvement

### Short-term (30 minutes)
- [ ] Investigate service detection logic
- [ ] Fix docker-compose configuration
- [ ] Test weather API functionality
- [ ] Monitor health score

### Medium-term (1 hour)
- [ ] Implement chosen solution (A, B, or C)
- [ ] Full system testing
- [ ] Documentation update
- [ ] Verify 90%+ health score

## Expected Results

### After Phase 1 (Environment Fix)
- Health score: 40-60% (reduced inactive services)
- Weather-api services properly configured
- Clear error messages instead of "not_configured"

### After Phase 2 (Service Configuration)  
- Health score: 80-90%
- Weather API functional
- All services properly detected

### After Phase 3 (Full Implementation)
- Health score: 90%+
- All services operational
- Clean dashboard metrics

## Verification Commands

```bash
# Check health score
curl http://localhost:3000/api/v1/real-time-metrics | jq '.health_summary'

# Check weather API status
curl http://localhost:8007/health

# Check all services
docker-compose ps

# Check dashboard
# Visit: http://localhost:3000
```

## Rollback Plan

If issues occur:
```bash
# Revert environment changes
git checkout infrastructure/.env.weather

# Restart with original config
docker-compose down && docker-compose up -d

# Check original health score
curl http://localhost:3000/api/v1/real-time-metrics | jq '.health_summary.health_percentage'
```

## Success Criteria

✅ **Primary Goal:** Health score > 85%  
✅ **Secondary Goal:** All services properly configured  
✅ **Tertiary Goal:** Weather API functional (if enabled)  
✅ **Bonus Goal:** Clean dashboard with accurate metrics  

---

**Next Steps:** Execute Phase 1 immediately to see initial improvement, then proceed with Phases 2-3 based on results.
