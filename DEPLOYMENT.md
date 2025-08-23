# 🚀 Quick Deployment Guide

This guide will get you up and running with ha-ingestor in **deployment mode** (advanced features disabled) to start ingesting Home Assistant data immediately.

## 🎯 **What You Get (Deployment Mode)**

- ✅ **Core MQTT functionality** - Connects to MQTT broker and listens to topics
- ✅ **Basic topic patterns** - Supports `+` and `#` wildcards
- ✅ **InfluxDB ingestion** - Writes Home Assistant data to InfluxDB
- ✅ **Health monitoring** - Basic metrics and health checks
- ✅ **Production ready** - Conservative performance settings
- ❌ **Advanced features disabled** - Pattern matching, dynamic subscriptions, optimization

## 🚀 **Quick Start (3 Steps)**

### 1. **Setup Environment**
```bash
# Copy deployment configuration
cp deployment.env.example .env

# Edit .env with your actual values
nano .env
```

**Required Configuration:**
```bash
# MQTT Broker
MQTT_BROKER_HOST=your_mqtt_broker_ip
MQTT_BROKER_PORT=1883
MQTT_USERNAME=your_mqtt_username  # if required
MQTT_PASSWORD=your_mqtt_password  # if required

# InfluxDB
INFLUXDB_URL=http://your_influxdb_ip:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_org_name
INFLUXDB_BUCKET=home_assistant
```

### 2. **Run Deployment Script**
```bash
python deploy.py
```

The script will:
- ✅ Validate your configuration
- ✅ Test connections to MQTT and InfluxDB
- ✅ Start the service in deployment mode

### 3. **Verify Data Flow**
```bash
# Check service status
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics

# Check logs
tail -f logs/ha-ingestor.log
```

## 🐳 **Docker Deployment (Recommended)**

### **Option A: Full Stack (MQTT + InfluxDB + ha-ingestor)**
```bash
# Start everything
docker-compose -f docker-compose.deploy.yml up -d

# Check status
docker-compose -f docker-compose.deploy.yml ps

# View logs
docker-compose -f docker-compose.deploy.yml logs -f ha-ingestor
```

### **Option B: Just ha-ingestor (with existing MQTT/InfluxDB)**
```bash
# Build and run only ha-ingestor
docker build -t ha-ingestor .
docker run -d \
  --name ha-ingestor \
  --env-file .env \
  -p 8000:8000 \
  ha-ingestor
```

## 📊 **What Data Gets Ingested**

By default, the service listens to these MQTT topics:
- `homeassistant/+/+/state` - 3-level topics (e.g., `homeassistant/sensor/temperature/state`)
- `homeassistant/+/+/+/state` - 4-level topics (e.g., `homeassistant/sensor/temperature/living_room/state`)

**Example Home Assistant MQTT messages that will be ingested:**
```json
{
  "topic": "homeassistant/sensor/temperature/state",
  "payload": "22.5",
  "timestamp": "2024-12-20T10:30:00Z"
}
```

## 🔧 **Troubleshooting**

### **Connection Issues**
```bash
# Test MQTT connection
mosquitto_pub -h your_mqtt_broker -t "test/topic" -m "test message"

# Test InfluxDB connection
curl -H "Authorization: Token your_token" http://your_influxdb:8086/api/v2/buckets
```

### **Common Issues**
- **MQTT connection failed**: Check broker IP, port, credentials
- **InfluxDB connection failed**: Verify token, org, bucket exist
- **No data flowing**: Check MQTT topics match your Home Assistant setup

### **Enable Debug Logging**
```bash
# In .env file
LOG_LEVEL=DEBUG
```

## 📈 **Next Steps (After Data is Flowing)**

Once you have data flowing, you can:

1. **Enable Advanced Features** (optional):
   ```bash
   MQTT_ENABLE_PATTERN_MATCHING=true
   MQTT_ENABLE_DYNAMIC_SUBSCRIPTIONS=true
   MQTT_ENABLE_TOPIC_OPTIMIZATION=true
   ```

2. **Add Grafana Dashboard**:
   - Access Grafana at `http://localhost:3000` (admin/admin)
   - Add InfluxDB as data source
   - Create dashboards for your Home Assistant data

3. **Customize Topic Patterns**:
   ```bash
   MQTT_TOPICS=homeassistant/+/+/state,homeassistant/+/+/+/state,custom/+/data
   ```

## 🆘 **Need Help?**

- Check the logs: `tail -f logs/ha-ingestor.log`
- Verify configuration: `python deploy.py` (validation step)
- Test connections manually using the troubleshooting commands above

## 🎉 **Success Indicators**

You'll know it's working when you see:
- ✅ "All deployment checks passed!" message
- ✅ "Service starting..." message
- ✅ Data appearing in InfluxDB
- ✅ Health endpoint responding: `curl http://localhost:8000/health`
