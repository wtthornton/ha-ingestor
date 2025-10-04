# 🔧 Home Assistant Ingestor - Troubleshooting Guide

## 🚨 **Common Issues & Solutions**

### **1. WebSocket Connection Issues**

#### **Problem**: WebSocket connection to Home Assistant fails
**Symptoms:**
- "WebSocket connection failed" errors
- No events being captured
- Service shows as unhealthy

**Solutions:**
```bash
# Check Home Assistant URL
curl -I http://your-ha-instance:8123

# Verify access token
curl -H "Authorization: Bearer <token>" http://your-ha-instance:8123/api/

# Check WebSocket endpoint
curl -H "Authorization: Bearer <token>" http://your-ha-instance:8123/api/websocket

# Restart WebSocket service
docker-compose restart websocket-ingestion
```

**Configuration Check:**
- Verify `HA_URL` is correct (ws://your-ha-instance:8123/api/websocket)
- Ensure `HA_ACCESS_TOKEN` is valid and has proper permissions
- Check Home Assistant is running and accessible

### **2. Weather API Issues**

#### **Problem**: Weather data not being retrieved
**Symptoms:**
- No weather context in events
- Weather API errors in logs
- Missing weather enrichment

**Solutions:**
```bash
# Test weather API key
curl "http://api.openweathermap.org/data/2.5/weather?q=London,GB&appid=<api-key>"

# Check weather service logs
docker-compose logs weather-api

# Restart weather service
docker-compose restart weather-api
```

**Configuration Check:**
- Verify `WEATHER_API_KEY` is valid
- Check `WEATHER_LOCATION` format (City,CountryCode)
- Ensure API key has proper permissions

### **3. InfluxDB Connection Issues**

#### **Problem**: Database connection failures
**Symptoms:**
- "InfluxDB connection failed" errors
- Data not being stored
- Database service unhealthy

**Solutions:**
```bash
# Check InfluxDB status
docker-compose logs influxdb

# Test InfluxDB connection
curl http://localhost:8086/health

# Restart InfluxDB
docker-compose restart influxdb

# Check database configuration
docker-compose exec influxdb influx ping
```

**Configuration Check:**
- Verify `INFLUXDB_URL` is correct
- Check `INFLUXDB_TOKEN` is valid
- Ensure `INFLUXDB_ORG` and `INFLUXDB_BUCKET` exist

### **4. High Memory Usage**

#### **Problem**: Services consuming excessive memory
**Symptoms:**
- High memory usage alerts
- Service restarts due to OOM
- System performance degradation

**Solutions:**
```bash
# Check memory usage
docker stats

# Check service logs for memory issues
docker-compose logs | grep -i memory

# Restart services to free memory
docker-compose restart

# Check for memory leaks
docker-compose exec <service-name> ps aux --sort=-%mem
```

**Configuration:**
- Adjust memory limits in docker-compose.yml
- Review log retention policies
- Optimize data processing intervals

### **5. Storage Space Issues**

#### **Problem**: Disk space running low
**Symptoms:**
- Storage alerts triggered
- Services failing to write data
- System performance issues

**Solutions:**
```bash
# Check disk usage
df -h

# Check Docker volumes
docker system df

# Clean up old logs
curl -X DELETE "http://localhost:8080/api/v1/monitoring/logs/cleanup?days_to_keep=7"

# Clean up old backups
curl -X DELETE "http://localhost:8080/api/v1/backups/cleanup?days_to_keep=7"

# Compress old logs
curl -X POST http://localhost:8080/api/v1/monitoring/logs/compress
```

## 🔍 **Diagnostic Commands**

### **System Health Check**
```bash
# Complete system health check
curl http://localhost:8080/api/v1/health

# Check individual services
docker-compose ps
docker-compose logs --tail=50

# Check resource usage
docker stats --no-stream
```

### **Service-Specific Diagnostics**
```bash
# WebSocket Ingestion
docker-compose logs websocket-ingestion | grep -E "(ERROR|WARNING)"
curl http://localhost:8080/api/v1/health/websocket-ingestion

# Enrichment Pipeline
docker-compose logs enrichment-pipeline | grep -E "(ERROR|WARNING)"
curl http://localhost:8080/api/v1/health/enrichment-pipeline

# Data Retention
docker-compose logs data-retention | grep -E "(ERROR|WARNING)"
curl http://localhost:8080/api/v1/health/data-retention
```

### **Network Diagnostics**
```bash
# Check service connectivity
docker-compose exec websocket-ingestion ping influxdb
docker-compose exec enrichment-pipeline ping admin-api

# Check port accessibility
netstat -tulpn | grep -E "(3000|8080|8086)"

# Test API endpoints
curl -I http://localhost:8080/api/v1/health
curl -I http://localhost:3000
```

## 📊 **Performance Troubleshooting**

### **Slow Performance**
**Symptoms:**
- High response times
- Delayed event processing
- Dashboard loading slowly

**Diagnostics:**
```bash
# Check CPU usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}"

# Check memory usage
docker stats --format "table {{.Container}}\t{{.MemUsage}}"

# Check disk I/O
docker stats --format "table {{.Container}}\t{{.BlockIO}}"

# Check network I/O
docker stats --format "table {{.Container}}\t{{.NetIO}}"
```

**Solutions:**
- Increase resource limits
- Optimize data processing intervals
- Review log retention policies
- Scale services if needed

### **High Error Rates**
**Symptoms:**
- Many error messages in logs
- High error rate alerts
- Service instability

**Diagnostics:**
```bash
# Count errors by service
docker-compose logs | grep ERROR | cut -d' ' -f1 | sort | uniq -c

# Check error patterns
docker-compose logs | grep ERROR | tail -20

# Check alert status
curl http://localhost:8080/api/v1/monitoring/alerts/active
```

## 🔧 **Configuration Issues**

### **Environment Variable Problems**
**Symptoms:**
- Services failing to start
- Configuration errors
- Missing environment variables

**Diagnostics:**
```bash
# Check environment variables
docker-compose config

# Validate configuration
docker-compose config --quiet

# Check service environment
docker-compose exec <service-name> env | grep -E "(HA_|WEATHER_|INFLUXDB_)"
```

### **Authentication Issues**
**Symptoms:**
- API authentication failures
- Access denied errors
- Service communication issues

**Solutions:**
```bash
# Test API authentication
curl -H "Authorization: Bearer <api-key>" http://localhost:8080/api/v1/health

# Check API key configuration
grep API_KEY .env

# Regenerate API key if needed
# Update .env file and restart services
```

## 🚨 **Emergency Procedures**

### **Service Recovery**
```bash
# Stop all services
docker-compose down

# Clean up resources
docker system prune -f

# Restart services
docker-compose up -d

# Verify recovery
docker-compose ps
curl http://localhost:8080/api/v1/health
```

### **Data Recovery**
```bash
# List available backups
curl http://localhost:8080/api/v1/backups

# Restore from latest backup
curl -X POST http://localhost:8080/api/v1/restore \
  -H "Authorization: Bearer <api-key>" \
  -d '{"backup_id": "latest"}'

# Verify data recovery
curl http://localhost:8080/api/v1/events/recent?limit=10
```

### **Complete System Reset**
```bash
# Stop all services
docker-compose down

# Remove all data (CAUTION: This deletes all data)
docker-compose down -v

# Restart with fresh data
docker-compose up -d
```

## 📞 **Getting Help**

### **Log Analysis**
```bash
# Get comprehensive logs
docker-compose logs --tail=1000 > system-logs.txt

# Filter for errors
docker-compose logs | grep -E "(ERROR|CRITICAL)" > errors.txt

# Get service-specific logs
docker-compose logs <service-name> > <service-name>-logs.txt
```

### **System Information**
```bash
# Get system info
docker version
docker-compose version
uname -a

# Get service info
docker-compose ps
docker system info
```

### **Contact Information**
- **Documentation**: Check user manual and API docs
- **Logs**: Review system logs for detailed error information
- **Configuration**: Verify all environment variables are correct
- **Support**: Contact support with system information and logs

---

**🔧 Use this guide to troubleshoot and resolve issues with your Home Assistant Ingestor system!**
