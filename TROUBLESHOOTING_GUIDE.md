# ha-ingestor Troubleshooting Guide

## 🚨 Common Issues & Solutions

This guide provides AI assistants with quick solutions to common problems encountered in the ha-ingestor project.

## 🔍 Quick Diagnostic Commands

### 1. **Check Service Status**
```bash
# Check if service is running
ps aux | grep ha-ingestor

# Check service logs
tail -f logs/ha-ingestor.log

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

### 2. **Check Dependencies**
```bash
# Check Python version
python --version

# Check Poetry installation
poetry --version

# Check installed packages
poetry show

# Check virtual environment
poetry env info
```

### 3. **Check Network Connectivity**
```bash
# Test Home Assistant connection
python test_connectivity.py

# Test MQTT connection
python test_mqtt.py

# Test InfluxDB connection
python -c "from ha_ingestor.influxdb.writer import InfluxDBWriter; print('InfluxDB connection test')"
```

## 🚨 Issue Categories

### **Category 1: Connection Issues**

#### **Problem: Cannot connect to Home Assistant**
**Symptoms:**
- Connection timeout errors
- Authentication failures
- WebSocket connection refused

**Solutions:**
1. **Check Home Assistant status:**
   ```bash
   curl http://192.168.1.86:8123/api/
   ```

2. **Verify network connectivity:**
   ```bash
   ping 192.168.1.86
   telnet 192.168.1.86 8123
   ```

3. **Check authentication token:**
   - Verify `HA_WEBSOCKET_TOKEN` in environment
   - Ensure token hasn't expired
   - Check token permissions

4. **Check firewall settings:**
   - Ensure port 8123 is accessible
   - Check local firewall rules

#### **Problem: MQTT connection failures**
**Symptoms:**
- MQTT client disconnections
- Connection refused errors
- Authentication failures

**Solutions:**
1. **Check MQTT broker status:**
   ```bash
   # If using Mosquitto
   systemctl status mosquitto
   
   # Check MQTT port
   netstat -tlnp | grep 1883
   ```

2. **Verify MQTT credentials:**
   - Check `MQTT_USERNAME` and `MQTT_PASSWORD`
   - Verify user exists in MQTT broker
   - Check ACL permissions

3. **Test MQTT connection manually:**
   ```bash
   mosquitto_pub -h 192.168.1.86 -t "test/topic" -m "test message"
   ```

#### **Problem: InfluxDB connection issues**
**Symptoms:**
- Database write failures
- Connection timeout errors
- Authentication failures

**Solutions:**
1. **Check InfluxDB status:**
   ```bash
   # If using Docker
   docker ps | grep influxdb
   
   # Check InfluxDB port
   netstat -tlnp | grep 8086
   ```

2. **Verify InfluxDB credentials:**
   - Check `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`
   - Ensure bucket exists and is accessible
   - Verify user permissions

3. **Test InfluxDB connection:**
   ```bash
   curl -G "http://localhost:8086/query" --data-urlencode "q=SHOW DATABASES"
   ```

### **Category 2: Data Processing Issues**

#### **Problem: Events not being processed**
**Symptoms:**
- No data in InfluxDB
- Empty logs
- No metrics being generated

**Solutions:**
1. **Check filter configurations:**
   - Verify filters are enabled
   - Check filter logic
   - Review filter logs

2. **Check transformation pipeline:**
   - Verify transformers are configured
   - Check transformation logic
   - Review error logs

3. **Enable debug logging:**
   ```bash
   LOG_LEVEL=DEBUG poetry run python -m ha_ingestor.main
   ```

#### **Problem: High memory usage**
**Symptoms:**
- Service crashes
- High memory consumption
- Slow performance

**Solutions:**
1. **Check batch sizes:**
   - Reduce `BATCH_SIZE` in configuration
   - Increase `BATCH_TIMEOUT`
   - Monitor memory usage

2. **Review filter efficiency:**
   - Check filter execution times
   - Optimize filter logic
   - Use more efficient filters

3. **Monitor resource usage:**
   ```bash
   # Check memory usage
   ps aux | grep ha-ingestor
   
   # Check system resources
   htop
   free -h
   ```

#### **Problem: Data loss or corruption**
**Symptoms:**
- Missing data points
- Incorrect data values
- Schema mismatches

**Solutions:**
1. **Check data validation:**
   - Verify event models
   - Check data transformation logic
   - Review error logs

2. **Check InfluxDB schema:**
   - Verify measurement names
   - Check tag and field definitions
   - Review retention policies

3. **Enable data validation:**
   ```python
   # In configuration
   data_validation:
     enabled: true
     strict_mode: true
   ```

### **Category 3: Performance Issues**

#### **Problem: Slow event processing**
**Symptoms:**
- High latency
- Event backlog
- Poor throughput

**Solutions:**
1. **Optimize filter performance:**
   - Use more efficient filter algorithms
   - Reduce filter complexity
   - Cache filter results

2. **Check batch processing:**
   - Optimize batch sizes
   - Reduce batch timeouts
   - Use parallel processing

3. **Monitor performance metrics:**
   ```bash
   # Check metrics endpoint
   curl http://localhost:8000/metrics
   
   # Check filter execution times
   grep "filter.*duration" logs/ha-ingestor.log
   ```

#### **Problem: High CPU usage**
**Symptoms:**
- Slow system response
- High CPU consumption
- Service unresponsiveness

**Solutions:**
1. **Profile code performance:**
   ```bash
   # Use Python profiler
   python -m cProfile -o profile.stats ha_ingestor/main.py
   
   # Analyze profile
   python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
   ```

2. **Optimize I/O operations:**
   - Use async I/O consistently
   - Reduce blocking operations
   - Optimize database queries

3. **Check for infinite loops:**
   - Review filter logic
   - Check transformation pipelines
   - Monitor event processing

### **Category 4: Configuration Issues**

#### **Problem: Configuration validation errors**
**Symptoms:**
- Service won't start
- Configuration errors in logs
- Missing environment variables

**Solutions:**
1. **Check environment variables:**
   ```bash
   # List all environment variables
   env | grep -i ha
   env | grep -i mqtt
   env | grep -i influxdb
   ```

2. **Validate configuration file:**
   ```bash
   # Check configuration syntax
   python -c "from ha_ingestor.config import Settings; s = Settings(); print('Config valid')"
   ```

3. **Check required fields:**
   - Verify all required environment variables
   - Check configuration file syntax
   - Review configuration schema

#### **Problem: Missing dependencies**
**Symptoms:**
- Import errors
- Module not found errors
- Service won't start

**Solutions:**
1. **Check Poetry dependencies:**
   ```bash
   # Install dependencies
   poetry install
   
   # Check installed packages
   poetry show
   
   # Update dependencies
   poetry update
   ```

2. **Check Python path:**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"
   
   # Check if package is installed
   python -c "import ha_ingestor; print('Package found')"
   ```

3. **Verify virtual environment:**
   ```bash
   # Activate virtual environment
   poetry shell
   
   # Check Python location
   which python
   ```

### **Category 5: Testing Issues**

#### **Problem: Tests failing**
**Symptoms:**
- Test failures
- Import errors in tests
- Missing test dependencies

**Solutions:**
1. **Install test dependencies:**
   ```bash
   poetry install --with dev
   ```

2. **Run tests with verbose output:**
   ```bash
   poetry run pytest tests/ -v -s
   ```

3. **Check test configuration:**
   - Verify `pytest.ini` settings
   - Check test environment variables
   - Review test fixtures

#### **Problem: Integration test failures**
**Symptoms:**
- External service connection failures
- Timeout errors
- Authentication failures

**Solutions:**
1. **Check external services:**
   - Verify Home Assistant is running
   - Check MQTT broker status
   - Verify InfluxDB availability

2. **Use test doubles:**
   - Mock external services
   - Use test containers
   - Create test fixtures

3. **Check test environment:**
   - Verify test configuration
   - Check test credentials
   - Review test setup

## 🛠️ Debugging Techniques

### **1. Enable Debug Logging**
```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run service with debug logging
poetry run python -m ha_ingestor.main
```

### **2. Use Python Debugger**
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use Python 3.7+ breakpoint()
breakpoint()
```

### **3. Profile Performance**
```bash
# Profile CPU usage
python -m cProfile -o profile.stats ha_ingestor/main.py

# Profile memory usage
python -m memory_profiler ha_ingestor/main.py
```

### **4. Check System Resources**
```bash
# Monitor system resources
htop
iotop
nethogs

# Check disk usage
df -h
du -sh logs/
```

## 📊 Monitoring & Alerting

### **1. Health Check Endpoints**
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed

# Metrics endpoint
curl http://localhost:8000/metrics
```

### **2. Log Analysis**
```bash
# Search for errors
grep -i error logs/ha-ingestor.log

# Search for warnings
grep -i warning logs/ha-ingestor.log

# Search for specific patterns
grep "filter.*duration" logs/ha-ingestor.log
```

### **3. Performance Metrics**
```bash
# Check event processing rate
curl -s http://localhost:8000/metrics | grep events_processed

# Check filter efficiency
curl -s http://localhost:8000/metrics | grep filter_efficiency

# Check processing duration
curl -s http://localhost:8000/metrics | grep processing_duration
```

## 🔧 Maintenance Tasks

### **1. Regular Health Checks**
```bash
# Daily health check
curl http://localhost:8000/health

# Weekly detailed check
curl http://localhost:8000/health/detailed

# Monthly performance review
curl http://localhost:8000/metrics > metrics_$(date +%Y%m).txt
```

### **2. Log Rotation**
```bash
# Check log sizes
du -sh logs/*.log

# Rotate logs if needed
logrotate -f /etc/logrotate.d/ha-ingestor
```

### **3. Database Maintenance**
```bash
# Check InfluxDB status
curl -G "http://localhost:8086/query" --data-urlencode "q=SHOW MEASUREMENTS"

# Check retention policies
curl -G "http://localhost:8086/query" --data-urlencode "q=SHOW RETENTION POLICIES"
```

## 📚 Additional Resources

### **1. Project Documentation**
- `README.md`: Quick start guide
- `DEVELOPMENT.md`: Development setup
- `DEPLOYMENT.md`: Production deployment
- `CONTRIBUTING.md`: Contribution guidelines

### **2. External Resources**
- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- [InfluxDB Documentation](https://docs.influxdata.com/)
- [MQTT Documentation](https://mqtt.org/documentation)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### **3. Community Support**
- [Home Assistant Community](https://community.home-assistant.io/)
- [InfluxDB Community](https://community.influxdata.com/)
- [Python Community](https://www.python.org/community/)

## 🚀 Pro Tips

1. **Always check logs first** - Most issues can be diagnosed from log messages
2. **Use health endpoints** - Regular health checks prevent issues from going unnoticed
3. **Monitor metrics** - Performance metrics help identify bottlenecks early
4. **Test incrementally** - Test small changes before making large modifications
5. **Document changes** - Keep track of configuration changes and their effects
6. **Use version control** - Commit configuration changes to track modifications
7. **Regular backups** - Backup configuration and data regularly
8. **Monitor resources** - Keep an eye on system resource usage
9. **Test in staging** - Test changes in staging environment before production
10. **Stay updated** - Keep dependencies and documentation current
