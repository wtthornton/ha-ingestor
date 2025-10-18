# HA Setup & Recommendation Service - Deployment Guide

## 🚀 Quick Deployment (5 Minutes)

**Prerequisites**: ✅ `HA_TOKEN` already configured in `infrastructure/.env.websocket`

### Step 1: Add Service to Docker Compose

Add this to `docker-compose.yml` in the `services:` section:

```yaml
  ha-setup-service:
    build:
      context: .
      dockerfile: services/ha-setup-service/Dockerfile
    container_name: ha-ingestor-setup-service
    restart: unless-stopped
    ports:
      - "8010:8010"
    env_file:
      - infrastructure/.env.websocket  # Uses existing HA_TOKEN ✅
    environment:
      - SERVICE_NAME=ha-setup-service
      - SERVICE_PORT=8010
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - HA_URL=${HA_HTTP_URL:-http://192.168.1.86:8123}
      - DATABASE_URL=sqlite+aiosqlite:///./data/ha-setup.db
      - DATA_API_URL=http://ha-ingestor-data-api:8006
      - ADMIN_API_URL=http://ha-ingestor-admin-api:8003
      - HEALTH_CHECK_INTERVAL=60
      - INTEGRATION_CHECK_INTERVAL=300
    volumes:
      - ha_setup_data:/app/data
      - ha_ingestor_logs:/var/log/ha-ingestor
    depends_on:
      data-api:
        condition: service_healthy
      admin-api:
        condition: service_healthy
    networks:
      - ha-ingestor-network
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8010/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=ha-setup-service,environment=production"
```

Add this to the `volumes:` section:

```yaml
volumes:
  ha_setup_data:
    driver: local
```

### Step 2: Deploy Service

```bash
# Build and start the service
docker-compose up -d ha-setup-service

# Verify it's running
docker ps | grep setup-service

# Check logs
docker logs ha-ingestor-setup-service
```

### Step 3: Verify Deployment

```powershell
# Test health endpoint
Invoke-RestMethod -Uri "http://localhost:8010/health"

# Test environment health
Invoke-RestMethod -Uri "http://localhost:8010/api/health/environment"

# Test integration checks
Invoke-RestMethod -Uri "http://localhost:8010/api/health/integrations"
```

### Step 4: Access Frontend

1. Navigate to `http://localhost:3000`
2. Click on the **Setup** tab
3. View environment health status
4. Monitor integrations
5. See performance metrics

## Features Available

### ✅ Health Monitoring
- Real-time environment health (updated every 60 seconds)
- Health score (0-100) with component breakdown
- Integration status (6 checks)
- Performance metrics tracking
- Issue detection with recommendations

### ✅ Integration Health Checks
1. **HA Authentication** - Token validation
2. **MQTT** - Broker connectivity
3. **Zigbee2MQTT** - Addon status
4. **Device Discovery** - Registry sync
5. **Data API** - Service health
6. **Admin API** - Service health

### ✅ Setup Wizards
- Zigbee2MQTT setup wizard (5 steps)
- MQTT setup wizard (5 steps)
- Session management
- Rollback capabilities
- Progress tracking

### ✅ Performance Optimization
- Performance analysis engine
- Bottleneck identification
- Optimization recommendations
- Impact/effort prioritization

### ✅ Continuous Monitoring
- Background health checks (every 60s)
- Integration checks (every 5 minutes)
- Automatic alerting for critical issues
- Historical trend analysis

## API Endpoints

### Health Monitoring
```http
GET /health                              # Simple health check
GET /api/health/environment              # Comprehensive health
GET /api/health/trends?hours=24          # Health trends
GET /api/health/integrations             # Integration details
```

### Setup Wizards
```http
POST /api/setup/wizard/zigbee2mqtt/start      # Start Z2M wizard
POST /api/setup/wizard/mqtt/start             # Start MQTT wizard
POST /api/setup/wizard/{session_id}/step/{n}  # Execute step
```

### Performance Optimization
```http
GET /api/optimization/analyze                # Performance analysis
GET /api/optimization/recommendations        # Recommendations
```

## Configuration

### Environment Variables (Auto-Configured ✅)

**HA_TOKEN**: Automatically loaded from `infrastructure/.env.websocket`  
**No manual configuration needed!**

Optional overrides:
```bash
HA_URL=http://192.168.1.86:8123
DATABASE_URL=sqlite+aiosqlite:///./data/ha-setup.db
DATA_API_URL=http://ha-ingestor-data-api:8006
ADMIN_API_URL=http://ha-ingestor-admin-api:8003
HEALTH_CHECK_INTERVAL=60          # Health check frequency (seconds)
INTEGRATION_CHECK_INTERVAL=300    # Integration check frequency (seconds)
LOG_LEVEL=INFO
```

## Monitoring

### Check Service Status
```bash
# Service health
curl http://localhost:8010/health

# Environment health
curl http://localhost:8010/api/health/environment

# Logs
docker logs -f ha-ingestor-setup-service
```

### Health Score Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| 80-100 | 🟢 Healthy | Excellent - No action needed |
| 50-79 | 🟡 Warning | Good - Minor issues detected |
| 0-49 | 🔴 Critical | Poor - Immediate attention required |

### Integration Status

| Status | Meaning |
|--------|---------|
| 🟢 Healthy | Fully operational |
| 🟡 Warning | Operational with issues |
| 🔴 Error | Not operational |
| ⚪ Not Configured | Not set up |

## Troubleshooting

### Service Won't Start

```bash
# Check if HA_TOKEN is loaded
docker exec ha-ingestor-setup-service env | grep HA_TOKEN

# Check dependencies
docker ps | grep -E "data-api|admin-api"

# View detailed logs
docker logs ha-ingestor-setup-service
```

### Health Check Returns Errors

```bash
# Verify HA is accessible
curl http://192.168.1.86:8123/api/

# Check network connectivity
docker exec ha-ingestor-setup-service ping -c 3 192.168.1.86

# Restart service
docker restart ha-ingestor-setup-service
```

### Integration Checks Fail

```powershell
# Check MQTT integration in HA
Invoke-RestMethod -Uri "http://192.168.1.86:8123/api/config/config_entries/entry" `
  -Headers @{Authorization="Bearer YOUR_TOKEN"}

# Check Zigbee2MQTT status
Invoke-RestMethod -Uri "http://192.168.1.86:8123/api/states" `
  -Headers @{Authorization="Bearer YOUR_TOKEN"} | 
  ConvertTo-Json | Select-String "zigbee2mqtt"
```

## Performance Tuning

### Adjust Monitoring Intervals

```bash
# Less frequent checks (lower resource usage)
HEALTH_CHECK_INTERVAL=120           # Every 2 minutes
INTEGRATION_CHECK_INTERVAL=600      # Every 10 minutes

# More frequent checks (higher responsiveness)
HEALTH_CHECK_INTERVAL=30            # Every 30 seconds
INTEGRATION_CHECK_INTERVAL=120      # Every 2 minutes
```

### Resource Limits

Current configuration:
- Memory limit: 256M
- Memory reservation: 128M
- Typical usage: ~100MB

Adjust if needed in docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      memory: 512M      # Increase if needed
    reservations:
      memory: 256M
```

## Maintenance

### View Health History

```bash
# Access SQLite database
docker exec -it ha-ingestor-setup-service sqlite3 /app/data/ha-setup.db

# Query health history
SELECT timestamp, health_score, ha_status 
FROM environment_health 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Clear Old Data

```sql
-- Delete health metrics older than 30 days
DELETE FROM environment_health 
WHERE timestamp < datetime('now', '-30 days');

-- Delete integration checks older than 7 days
DELETE FROM integration_health 
WHERE timestamp < datetime('now', '-7 days');
```

## Security

### ✅ Security Features Implemented
- Non-root Docker user
- HA_TOKEN from secure environment file
- No hardcoded secrets
- CORS restricted to localhost:3000, localhost:3001
- Proper exception handling (no data leaks)
- Input validation with Pydantic

### Security Best Practices
- Keep HA_TOKEN secure in `infrastructure/.env.websocket`
- Don't expose port 8010 externally
- Monitor logs for unusual activity
- Keep Docker images updated

## Backup & Recovery

### Backup Database

```bash
# Copy SQLite database
docker cp ha-ingestor-setup-service:/app/data/ha-setup.db ./backup/ha-setup-$(date +%Y%m%d).db
```

### Restore Database

```bash
# Restore from backup
docker cp ./backup/ha-setup-20250118.db ha-ingestor-setup-service:/app/data/ha-setup.db

# Restart service
docker restart ha-ingestor-setup-service
```

## Upgrade Path

### Future Enhancements
- Email/Slack alerting integration
- Advanced trend visualizations
- Additional setup wizards
- Automated optimization execution
- Machine learning for anomaly detection

## Support

### Common Issues

**Q: Health score is 0**  
A: Check if Home Assistant is accessible and HA_TOKEN is valid

**Q: Integrations show "not_configured"**  
A: Follow recommendations in integration check results

**Q: Performance metrics missing**  
A: Ensure performance monitoring is enabled (default: true)

**Q: Continuous monitoring not working**  
A: Check service logs for errors, verify background task started

### Log Levels

```bash
# Debug mode for troubleshooting
LOG_LEVEL=DEBUG

# Production mode
LOG_LEVEL=INFO
```

## Success Metrics

After deployment, you should see:
- ✅ Health score >= 80 (healthy)
- ✅ All integrations showing "healthy" or "warning"
- ✅ Response times < 500ms
- ✅ Continuous monitoring active
- ✅ Health trends populated after 1 hour

## Conclusion

The HA Setup & Recommendation Service is deployed and ready to:
- ✅ Monitor your Home Assistant environment 24/7
- ✅ Detect and alert on critical issues
- ✅ Provide setup assistance for integrations
- ✅ Optimize system performance
- ✅ Track health trends over time

**Status**: ✅ **DEPLOYED AND OPERATIONAL**

---

**Deployment Guide Version**: 1.0  
**Service Version**: 1.0.0  
**Last Updated**: January 18, 2025  
**Port**: 8010  
**Dashboard**: http://localhost:3000 → Setup tab

