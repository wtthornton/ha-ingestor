# Sports API Service - Operations Runbook

Quick reference for common operational tasks.

---

## Common Operations

### Start Service
```bash
docker-compose up sports-api
```

### Stop Service
```bash
docker-compose down sports-api
```

### View Logs
```bash
docker logs ha-sports-api --tail=100 -f
```

### Check Health
```bash
curl http://localhost:8015/health
```

### Get Statistics
```bash
curl http://localhost:8015/api/sports/stats | jq
```

### Clear Cache
```bash
curl -X POST http://localhost:8015/api/sports/cache/clear
```

---

## Troubleshooting

### Service Won't Start

**Check:**
1. API key is set: `echo $API_SPORTS_KEY`
2. Port 8015 available: `netstat -an | grep 8015`
3. InfluxDB running: `docker ps | grep influx`

**Fix:**
```bash
# Restart with fresh logs
docker-compose down sports-api
docker-compose up sports-api
```

### API Errors (503)

**Likely cause:** Missing API key or disabled client

**Check configuration:**
```bash
docker exec ha-sports-api printenv | grep SPORTS
```

### High Memory Usage

**Check:**
```bash
docker stats ha-sports-api
```

**Fix:**
```bash
# Clear cache
curl -X POST http://localhost:8015/api/sports/cache/clear

# Restart if needed
docker-compose restart sports-api
```

### Rate Limit Exceeded

**Check usage:**
```bash
curl http://localhost:8015/api/sports/stats | jq '.stats.rate_limiter'
```

**Solutions:**
- Wait for quota reset
- Adjust cache TTLs (increase)
- Upgrade API plan

---

## Monitoring

### Key Metrics

**Cache Performance:**
```bash
curl http://localhost:8015/api/sports/stats | jq '.stats.cache.hit_rate_percentage'
```
Target: >60%

**Rate Limiting:**
```bash
curl http://localhost:8015/api/sports/stats | jq '.stats.rate_limiter.wait_percentage'
```
Target: <20%

**InfluxDB Writes:**
```bash
curl http://localhost:8015/api/sports/stats | jq '.stats.influxdb.success_rate'
```
Target: >95%

---

## Emergency Procedures

### Service Down

1. Check health: `curl http://localhost:8015/health`
2. Check logs: `docker logs ha-sports-api`
3. Restart: `docker-compose restart sports-api`
4. If fails: Check dependencies (InfluxDB)

### API-SPORTS Outage

- Service will return cached data
- Circuit breaker protects from cascading failures
- Check API-SPORTS status page
- Wait for recovery or use cached data

### Database Issues

- Service continues with degraded functionality
- Data not persisted but API still works
- Check InfluxDB status
- Restart InfluxDB if needed

---

**Keep it simple - most issues resolve with restart!** 🔄

