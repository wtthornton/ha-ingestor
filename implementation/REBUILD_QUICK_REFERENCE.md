# System Rebuild - Quick Reference
**Generated:** October 14, 2025  
**For:** Complete homeiq system rebuild

---

## ⚡ Quick Commands

### Complete Teardown & Rebuild (One-Command)
```bash
# ⚠️ WARNING: This removes ALL containers and images
# Preserves data volumes by default

cd ~/homeiq

# 1. Stop and remove everything
docker-compose down --timeout 30
docker ps -a --filter "name=homeiq" -q | xargs -r docker rm -f
docker images --filter=reference='*homeiq*' -q | xargs -r docker rmi -f
docker network rm homeiq-network 2>/dev/null || true
docker builder prune -a -f

# 2. Build and deploy fresh
docker-compose build --no-cache --parallel
docker-compose up -d

# 3. Wait and verify
sleep 30
docker-compose ps
curl http://localhost:3000
```

---

## 🎯 Critical Issues to Fix FIRST

### 1. Add data-api to Production Compose
```bash
# docker-compose.prod.yml is missing data-api service
# Copy service definition from docker-compose.yml
# Or use main compose for production deployment
```

### 2. Fix admin-api Dependencies
```bash
# Edit docker-compose.yml line 182-188
# Add data-api to admin-api depends_on section

depends_on:
  influxdb:
    condition: service_healthy
  websocket-ingestion:
    condition: service_healthy
  enrichment-pipeline:
    condition: service_healthy
  data-api:                    # ← ADD THIS
    condition: service_healthy  # ← ADD THIS
```

### 3. Create Root .dockerignore
```bash
cat > .dockerignore << 'EOF'
.git/
docs/
implementation/
tests/
*.md
!README.md
.env*
!.env.example
node_modules/
__pycache__/
*.log
EOF
```

---

## 📋 Phase Summary

| Phase | Duration | Key Actions |
|-------|----------|-------------|
| **1. Backup** | 5-10 min | Backup InfluxDB, SQLite, .env files |
| **2. Teardown** | 5 min | Stop services, remove containers/images |
| **3. Rebuild** | 15-20 min | Build images from scratch |
| **4. Deploy** | 5 min | Start all services |
| **5. Validate** | 10 min | Test all endpoints and functionality |
| **Total** | **40-50 min** | Complete rebuild cycle |

---

## 🚦 Status Indicators

### All Services Healthy ✅
```bash
$ docker-compose ps
NAME                            STATUS                  PORTS
homeiq-admin               Up (healthy)            0.0.0.0:8003->8004/tcp
homeiq-air-quality         Up (healthy)            0.0.0.0:8012->8012/tcp
homeiq-calendar            Up (healthy)            0.0.0.0:8013->8013/tcp
homeiq-carbon-intensity    Up (healthy)            0.0.0.0:8010->8010/tcp
homeiq-dashboard           Up (healthy)            0.0.0.0:3000->80/tcp
homeiq-data-api            Up (healthy)            0.0.0.0:8006->8006/tcp
homeiq-data-retention      Up (healthy)            0.0.0.0:8080->8080/tcp
homeiq-electricity-pricing Up (healthy)            0.0.0.0:8011->8011/tcp
homeiq-enrichment          Up (healthy)            0.0.0.0:8002->8002/tcp
homeiq-influxdb            Up (healthy)            0.0.0.0:8086->8086/tcp
homeiq-log-aggregator      Up (healthy)            0.0.0.0:8015->8015/tcp
homeiq-smart-meter         Up (healthy)            0.0.0.0:8014->8014/tcp
homeiq-sports-data         Up (healthy)            0.0.0.0:8005->8005/tcp
homeiq-websocket           Up (healthy)            0.0.0.0:8001->8001/tcp
```

### Quick Health Check ✅
```bash
#!/bin/bash
# Save as: check-health.sh

endpoints=(
    "http://localhost:8086/health:InfluxDB"
    "http://localhost:8001/health:WebSocket"
    "http://localhost:8002/health:Enrichment"
    "http://localhost:8003/api/v1/health:Admin-API"
    "http://localhost:8006/health:Data-API"
    "http://localhost:8080/health:Data-Retention"
    "http://localhost:8005/health:Sports-Data"
    "http://localhost:8015/health:Log-Aggregator"
    "http://localhost:3000:Dashboard"
)

for endpoint in "${endpoints[@]}"; do
    url="${endpoint%:*}"
    name="${endpoint#*:}"
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✅ $name"
    else
        echo "❌ $name"
    fi
done
```

---

## 🔧 Common Issues Quick Fix

### Service Won't Start
```bash
# Check logs
docker-compose logs <service-name> --tail=50

# Common fixes:
# 1. Missing env var → Check .env file
# 2. Port conflict → Change port in docker-compose.yml
# 3. Dependency not ready → Wait longer or restart dependency
```

### Dashboard 502 Error
```bash
# Check admin-api is running
docker-compose ps admin-api

# If not healthy:
docker-compose restart admin-api

# Wait for health
watch -n 1 'docker-compose ps admin-api'
```

### HA Connection Failed
```bash
# Test HA connectivity
curl ${HOME_ASSISTANT_URL}

# Check token
curl -H "Authorization: Bearer ${HOME_ASSISTANT_TOKEN}" \
     ${HOME_ASSISTANT_URL}/api/

# If fails:
# 1. Generate new token in HA
# 2. Update .env: HOME_ASSISTANT_TOKEN=new_token
# 3. Restart: docker-compose restart websocket-ingestion
```

### No Data in InfluxDB
```bash
# Check HA connection (see above)

# Check enrichment pipeline
docker-compose logs enrichment-pipeline | grep -i error

# Check bucket exists
docker exec homeiq-influxdb influx bucket list

# Trigger test event in HA (toggle light)
# Check for data:
docker exec homeiq-influxdb influx query \
  'from(bucket:"home_assistant_events") |> range(start: -5m) |> limit(n:10)'
```

---

## 📊 Verification Checklist

### Quick Validation (2 minutes)
```bash
# 1. All services healthy
docker-compose ps | grep -c "Up (healthy)"
# Should show 13+

# 2. Dashboard accessible
curl -I http://localhost:3000
# Should show "HTTP/1.1 200 OK"

# 3. API responding
curl http://localhost:8003/api/v1/health | jq .status
# Should show "healthy"

# 4. HA connected
docker-compose logs websocket-ingestion | grep -i "connected"
# Should show "Connected to Home Assistant"
```

### Full Validation (5 minutes)
- [ ] Run: `./scripts/test-services.sh`
- [ ] Open: `http://localhost:3000` in browser
- [ ] Check: All 12 dashboard tabs load
- [ ] Verify: No console errors (F12)
- [ ] Test: API endpoints respond
- [ ] Confirm: HA events flowing

---

## 🎯 Success Criteria

✅ **System is healthy when:**
1. `docker-compose ps` shows all services "Up (healthy)"
2. Dashboard loads at `http://localhost:3000`
3. WebSocket logs show "Connected to Home Assistant"
4. All health endpoints return 200 OK
5. No errors in service logs
6. Memory usage < 70% of allocated
7. CPU usage stable < 50%

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `implementation/COMPLETE_SYSTEM_REBUILD_PLAN.md` | Full detailed plan (100+ pages) |
| `docker-compose.yml` | Main service definitions |
| `docker-compose.prod.yml` | Production configuration (needs updates) |
| `.env` | Environment configuration |
| `infrastructure/env.example` | Configuration template |
| `scripts/deploy.sh` | Automated deployment script |

---

## 🆘 Emergency Rollback

```bash
# If rebuild fails and you need to go back:

# 1. Stop everything
docker-compose down

# 2. Restore from backup
cd ~/homeiq-backup-YYYYMMDD
cp docker-compose.yml.backup ~/homeiq/docker-compose.yml
cp env.backup ~/homeiq/.env

# 3. Restore InfluxDB data
docker-compose up -d influxdb
docker cp ./influxdb-backup homeiq-influxdb:/tmp/backup
docker exec homeiq-influxdb influx restore /tmp/backup

# 4. Restore SQLite
docker-compose up -d data-api
docker cp ./metadata.db.backup homeiq-data-api:/app/data/metadata.db

# 5. Start all services
docker-compose up -d

# 6. Verify
docker-compose ps
curl http://localhost:3000
```

---

## 📞 Support Resources

- **Full Rebuild Plan:** `implementation/COMPLETE_SYSTEM_REBUILD_PLAN.md`
- **Deployment Guide:** `docs/DEPLOYMENT_GUIDE.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING_GUIDE.md`
- **API Docs:** `docs/API_DOCUMENTATION.md`
- **Architecture:** `docs/architecture/`

---

## ⏱️ Estimated Timeline

```
00:00 - Start backup                     ━━━━━━━━━━ (10 min)
00:10 - Begin teardown                   ━━━━━ (5 min)
00:15 - Start rebuild                    ━━━━━━━━━━━━━━━━━━━━ (20 min)
00:35 - Deploy services                  ━━━━━ (5 min)
00:40 - Validate deployment              ━━━━━━━━━━ (10 min)
00:50 - COMPLETE ✅
```

**Total Time:** ~50 minutes (may vary based on system)

---

**Next Steps:**
1. Read full plan: `implementation/COMPLETE_SYSTEM_REBUILD_PLAN.md`
2. Fix critical issues (see above)
3. Create backup
4. Execute rebuild
5. Validate system
6. Celebrate success! 🎉

