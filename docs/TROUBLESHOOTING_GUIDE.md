# 🔧 Home Assistant Ingestor - Troubleshooting Guide

## 🚨 **Common Issues & Solutions**

### **📋 Recently Fixed Issues (January 2025)**

#### **✅ Data Retention Service API Routes (FIXED)**
**Problem**: 404 errors on `/api/v1/health` and `/api/v1/stats` endpoints
**Status**: ✅ **RESOLVED** - API routes added to service configuration
**Solution**: Added missing API route mappings in `services/data-retention/src/main.py`

#### **✅ Enrichment Pipeline Service API Routes (FIXED)**
**Problem**: 404 errors on `/api/v1/health` and `/api/v1/stats` endpoints  
**Status**: ✅ **RESOLVED** - API routes added and health handler configured
**Solution**: Added API routes and fixed health handler import in `services/enrichment-pipeline/src/main.py`

#### **✅ WebSocket Ingestion Timeout Issues (FIXED)**
**Problem**: Health check endpoints timing out
**Status**: ✅ **RESOLVED** - Connection manager properly configured
**Solution**: Fixed health handler configuration and service initialization

#### **✅ Weather API Authentication (FIXED)**
**Problem**: HTTP 401 authentication errors
**Status**: ✅ **RESOLVED** - Authentication issues resolved
**Solution**: Fixed API key configuration and authentication flow

**Impact**: System success rate improved from 58.3% → 66.7%, all critical issues resolved

### **⚠️ Current Known Issues (January 2025)**

#### **🔴 API Endpoints Returning 404**
**Problem**: Some API endpoints return 404 errors
**Affected Endpoints**:
- `/api/v1/config` - Configuration endpoint
- `/api/v1/events/recent` - Recent events endpoint
- `/api/v1/services` - Services health check endpoint
- `/api/v1/dependencies` - Dependencies health check endpoint

**Status**: ⚠️ **KNOWN ISSUE** - Endpoints not implemented
**Workaround**: Use alternative endpoints or implement missing functionality
**Priority**: Medium - System remains functional without these endpoints

#### **🔴 Smoke Test Unicode Encoding Issues**
**Problem**: Smoke tests fail with Unicode encoding errors in Windows environment
**Error**: `UnicodeEncodeError: 'charmap' codec can't encode characters`
**Status**: ⚠️ **KNOWN ISSUE** - Windows environment compatibility
**Workaround**: Run tests in WSL or Linux environment
**Priority**: Low - Tests pass in Linux environment

#### **🔴 Success Rate Below Target**
**Problem**: Current success rate is 66.7% (8/12 tests passing)
**Target**: 95%+ success rate
**Status**: ⚠️ **KNOWN ISSUE** - System operational but with limitations
**Impact**: System functions but some features may not work as expected
**Priority**: Medium - Address missing endpoints to improve success rate

#### **✅ WSL Port Conflict Resolution (FIXED)**
**Problem**: LocalMCP application appearing on port 8080 instead of HA-Ingestor data retention API
**Status**: ✅ **RESOLVED** - WSL port conflict eliminated
**Root Cause**: WSL relay service (`wslrelay.exe`) was intercepting requests to localhost:8080
**Solution**: Terminated conflicting WSL process and performed full Docker restart
**Files Modified**: None (system-level fix)

### **1. Port Conflict Issues**

#### **Problem**: Wrong application appearing on expected port
**Symptoms:**
- Browser shows unexpected application (e.g., LocalMCP instead of HA-Ingestor API)
- Command line shows correct service but browser shows different content
- Multiple processes listening on the same port

**Diagnosis:**
```bash
# Check what's listening on the port
netstat -ano | findstr :8080

# Check process details
tasklist /FI "PID eq <PID>"

# Test with different methods
curl http://localhost:8080/health
curl http://127.0.0.1:8080/health
```

**Solutions:**

**Option 1: Terminate Conflicting Process**
```bash
# Find the conflicting process
netstat -ano | findstr :8080

# Terminate the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Option 2: Use IPv4 Explicitly**
- Use `http://127.0.0.1:8080` instead of `http://localhost:8080`
- This bypasses IPv6 listeners that might be intercepting requests

**Option 3: Change HA-Ingestor Port**
```bash
# Edit docker-compose.complete.yml
# Change port mapping from 8080:8080 to 8081:8080
# Restart services
docker-compose -f docker-compose.complete.yml down
docker-compose -f docker-compose.complete.yml up -d
```

**Option 4: Full Docker Restart**
```bash
# Stop all services
docker-compose -f docker-compose.complete.yml down

# Clean up any conflicting processes
docker system prune -f

# Restart services
docker-compose -f docker-compose.complete.yml up -d
```

### **2. WebSocket Connection Issues**

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
