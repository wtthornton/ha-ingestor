# HA-Ingestor v0.3.0 - Quick Reference Card

**Enhanced Data Ingestion & Preparation Layer for Home Assistant**

## 🚀 **Current Status**

| Status | Version | Health | Uptime |
|--------|---------|---------|---------|
| ✅ **OPERATIONAL** | **v0.3.0** | ✅ **Healthy** | **Active** |

## 📊 **Quick Health Check**

```bash
# Service status
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Metrics
curl http://localhost:8000/metrics

# Dependencies
curl http://localhost:8000/health/dependencies
```

## 🔧 **Essential Commands**

### **Service Management**
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs ha-ingestor -f

# Restart service
docker-compose restart ha-ingestor

# Rebuild and restart
docker-compose down && docker-compose up -d --build
```

### **Performance Monitoring**
```bash
# Container stats
docker stats ha-ingestor

# Health monitoring
watch -n 5 'curl -s http://localhost:8000/health | jq .'

# Log analysis
docker-compose logs ha-ingestor | grep "ERROR"
docker-compose logs ha-ingestor | grep "Received"
```

## 📈 **Key Metrics**

### **Current Performance**
- **Events Processed**: 10+ per second
- **Success Rate**: 100% (0 failures)
- **Memory Usage**: 49.36MiB (0.31%)
- **CPU Usage**: 0.37%
- **Processing Latency**: < 1 second

### **Health Endpoints**
| Endpoint | Status | Response Time |
|----------|---------|---------------|
| `/` | ✅ Healthy | < 10ms |
| `/health` | ✅ Healthy | < 10ms |
| `/ready` | ✅ Ready | < 10ms |
| `/metrics` | ✅ Active | < 15ms |
| `/dependencies` | ✅ Healthy | < 20ms |

## 🏗️ **Architecture Overview**

```
Home Assistant → MQTT/WebSocket → HA-Ingestor v0.3.0 → InfluxDB
                    ↓                    ↓              ↓
              Event Capture      Enhanced Processing   Storage
                    ↓                    ↓              ↓
              Raw Events        Quality Validation    Analytics
                    ↓                    ↓              ↓
              MQTT/WS          Context Enrichment    Ready Data
```

## ✨ **v0.3.0 Features**

### **Enhanced Data Collection**
- ✅ Multi-domain event capture (sensor, media_player, image, network)
- ✅ Comprehensive device attributes (device_class, state_class, unit_of_measurement)
- ✅ Performance metrics (network speeds, power consumption, lighting)
- ✅ Context tracking (user IDs, correlation IDs, timestamps)

### **Advanced Data Quality**
- ✅ Schema validation with Pydantic
- ✅ Intelligent duplicate detection
- ✅ Comprehensive error handling
- ✅ Data enrichment and metadata

### **Rich Monitoring**
- ✅ 49+ Prometheus metrics
- ✅ Real-time health checks
- ✅ Performance analytics
- ✅ Circuit breaker patterns

## 🔌 **Integration Methods**

### **1. MQTT Events**
```python
# Subscribe to enhanced events
client.subscribe("ha-ingestor/events/#")
client.subscribe("ha-ingestor/enhanced/#")
client.subscribe("ha-ingestor/validated/#")
```

### **2. REST API**
```python
import requests

# Health check
health = requests.get("http://localhost:8000/health").json()

# Service info
info = requests.get("http://localhost:8000/").json()

# Dependencies
deps = requests.get("http://localhost:8000/health/dependencies").json()
```

### **3. InfluxDB Direct**
```python
from influxdb_client import InfluxDBClient

# Query enhanced events
query = '''
from(bucket: "ha_events")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "ha_events")
    |> filter(fn: (r) => r["validation_status"] == "validated")
'''
```

## 📋 **Configuration**

### **Environment Variables**
```bash
# MQTT Configuration
MQTT_BROKER=mosquitto
MQTT_PORT=1883
MQTT_USERNAME=ha_ingestor
MQTT_PASSWORD=your_password

# WebSocket Configuration
WEBSOCKET_URL=ws://homeassistant:8123/api/websocket
WEBSOCKET_EVENTS=state_changed,automation_triggered

# InfluxDB Configuration
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your_token
INFLUXDB_ORG=home_assistant
INFLUXDB_BUCKET=ha_events

# Performance Tuning
BATCH_SIZE=1000
BATCH_TIMEOUT=5.0
MAX_RETRIES=3
CIRCUIT_BREAKER_THRESHOLD=5
```

### **Docker Compose**
```yaml
version: '3.8'
services:
  ha-ingestor:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MQTT_BROKER=mosquitto
      - WEBSOCKET_URL=ws://homeassistant:8123/api/websocket
      - INFLUXDB_URL=http://influxdb:8086
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🧪 **Testing & Validation**

### **Run Tests**
```bash
# All tests
pytest

# Specific test categories
pytest tests/test_enhanced_data_collection.py
pytest tests/test_data_validation.py
pytest tests/test_context_enrichment.py
pytest tests/test_data_export.py
```

### **Test Coverage**
- ✅ **Enhanced Data Collection**: All tests passing
- ✅ **Data Quality & Validation**: All tests passing
- ✅ **Context Enrichment**: All tests passing
- ✅ **Flexible Data Export**: All tests passing

## 🔍 **Troubleshooting**

### **Common Issues**

**Health Check Failing**
```bash
# Check container status
docker-compose ps ha-ingestor

# View logs
docker-compose logs ha-ingestor --tail=50

# Test health endpoint
curl http://localhost:8000/health
```

**Events Not Processing**
```bash
# Check MQTT connection
docker exec ha-ingestor python -c "from ha_ingestor.mqtt.client import MQTTClient; print('MQTT client loaded')"

# Check WebSocket connection
docker exec ha-ingestor python -c "from ha_ingestor.websocket.client import WebSocketClient; print('WebSocket client loaded')"

# Verify subscriptions
docker-compose logs ha-ingestor | grep "subscribed"
```

**Performance Issues**
```bash
# Monitor resources
docker stats ha-ingestor

# Check metrics
curl http://localhost:8000/metrics

# View pipeline stats
docker-compose logs ha-ingestor | grep "Pipeline statistics"
```

### **Log Analysis**
```bash
# Real-time monitoring
docker-compose logs ha-ingestor -f

# Error analysis
docker-compose logs ha-ingestor | grep "ERROR"
docker-compose logs ha-ingestor | grep "WARNING"

# Event processing
docker-compose logs ha-ingestor | grep "Received"
docker-compose logs ha-ingestor | grep "Processed"
```

## 📊 **Data Models**

### **Enhanced Event Structure**
```json
{
  "domain": "sensor",
  "entity_id": "temperature_living_room",
  "timestamp": "2025-08-25T14:30:00Z",
  "event_type": "state_changed",
  "attributes": {
    "device_class": "temperature",
    "state_class": "measurement",
    "unit_of_measurement": "°C"
  },
  "validation_status": "validated",
  "quality_score": 0.95,
  "enrichment_data": {
    "device_metadata": {
      "manufacturer": "Generic",
      "model": "Temperature Sensor"
    }
  }
}
```

### **Quality Metrics**
```python
# Data quality indicators
event.is_high_quality()  # True if validated, score >= 0.8, not duplicate
event.validation_status   # 'validated', 'failed', 'pending'
event.quality_score       # 0.0 to 1.0
event.is_duplicate        # True/False
```

## 🚀 **Performance Optimization**

### **Tuning Recommendations**
- **Batch Size**: Adjust based on event volume (default: 1000)
- **Connection Pooling**: Optimize for concurrent connections
- **Memory Management**: Monitor and adjust based on usage
- **Network Configuration**: Optimize for your topology

### **Scaling Considerations**
- **Horizontal**: Multiple instances with load balancing
- **Vertical**: Increase resources for single instance
- **Database**: InfluxDB retention policies and sharding
- **Network**: Dedicated segments for high throughput

## 📚 **API Reference**

### **Health Endpoints**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/` | Service information |
| `GET` | `/health` | Health status |
| `GET` | `/ready` | Readiness check |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/health/dependencies` | Dependency health |

### **Response Examples**
```json
// Health Check
{
  "status": "healthy",
  "version": "0.3.0",
  "uptime_seconds": 148.99,
  "service": "ha-ingestor"
}

// Dependencies Health
{
  "ready": true,
  "dependencies": {
    "mqtt": {"status": "healthy", "ready": true},
    "websocket": {"status": "healthy", "ready": true},
    "influxdb": {"status": "healthy", "ready": true}
  }
}
```

## 🔄 **Deployment**

### **Quick Deployment**
```bash
# Clone and configure
git clone <repository-url>
cd ha-ingestor
cp env.example .env
# Edit .env with your configuration

# Deploy
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

### **Production Deployment**
```bash
# Use production compose file
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# Monitor logs
docker-compose -f docker-compose.production.yml logs -f
```

## 📞 **Support & Resources**

### **Documentation**
- **README.md**: Complete project documentation
- **CHANGELOG.md**: Version history and changes
- **Integration Guide**: Child projects integration
- **Production Guide**: Deployment and operations

### **Monitoring**
- **Health**: `http://localhost:8000/health`
- **Metrics**: `http://localhost:8000/metrics`
- **Dependencies**: `http://localhost:8000/health/dependencies`

### **Troubleshooting**
- **Logs**: `docker-compose logs ha-ingestor`
- **Status**: `docker-compose ps`
- **Performance**: `docker stats ha-ingestor`

---

## **Quick Status Check**

```bash
# One-liner health check
curl -s http://localhost:8000/health | jq -r '"Status: " + .status + " (v" + .version + ")"'

# One-liner container status
docker-compose ps ha-ingestor --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# One-liner performance check
docker stats ha-ingestor --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

**HA-Ingestor v0.3.0** - Enhanced Data Ingestion & Preparation Layer for Home Assistant

*Built with ❤️ for the Home Assistant community*
