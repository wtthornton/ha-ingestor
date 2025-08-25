# Child Projects Quick Start - HA-Ingestor v0.3.0

**Get up and running with HA-Ingestor in under 10 minutes!**

This guide provides a streamlined path for child projects to integrate with HA-Ingestor v0.3.0 and start leveraging enhanced data collection, quality validation, and monitoring capabilities.

## 🚀 **Quick Start (5 minutes)**

### **1. Verify HA-Ingestor is Running**
```bash
# Check if HA-Ingestor is operational
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"0.3.0","uptime_seconds":148.99}
```

### **2. Test Basic Integration**
```python
import requests

def test_ha_ingestor():
    """Quick test of HA-Ingestor integration"""
    try:
        # Health check
        health = requests.get("http://localhost:8000/health").json()
        print(f"✅ HA-Ingestor Status: {health['status']} (v{health['version']})")
        
        # Service info
        info = requests.get("http://localhost:8000/").json()
        print(f"✅ Service: {info['service']}")
        
        # Dependencies
        deps = requests.get("http://localhost:8000/ready").json()
        print(f"✅ Ready: {deps['ready']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return False

# Run test
if test_ha_ingestor():
    print("🎉 Ready to integrate!")
else:
    print("🔧 Check HA-Ingestor deployment")
```

### **3. Start Receiving Enhanced Events**
```python
import paho.mqtt.client as mqtt
import json

class QuickHAIngestorClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def start(self):
        """Start receiving enhanced events"""
        self.client.connect("localhost", 1883)
        self.client.loop_start()
        
    def on_connect(self, client, userdata, flags, rc):
        print("✅ Connected to HA-Ingestor MQTT")
        # Subscribe to enhanced events
        client.subscribe("ha-ingestor/enhanced/#")
        
    def on_message(self, client, userdata, msg):
        try:
            event = json.loads(msg.payload.decode())
            self.process_event(event)
        except Exception as e:
            print(f"Error processing event: {e}")
            
    def process_event(self, event):
        """Process enhanced event with quality validation"""
        if event.get('validation_status') == 'validated':
            print(f"📊 Processing: {event['domain']}.{event['entity_id']}")
            print(f"   Quality Score: {event.get('quality_score', 'N/A')}")
            print(f"   Device: {event.get('attributes', {}).get('device_class', 'Unknown')}")
            
            # Your business logic here
            self.analyze_event(event)
            
    def analyze_event(self, event):
        """Add your custom analysis logic here"""
        # Example: Track temperature sensors
        if event['domain'] == 'sensor' and 'temperature' in event['entity_id']:
            temp = event.get('attributes', {}).get('unit_of_measurement', '')
            print(f"🌡️  Temperature event: {event['entity_id']} - {temp}")
            
        # Example: Track automation triggers
        elif event['domain'] == 'automation':
            print(f"🤖 Automation: {event['entity_id']} - {event['event_type']}")

# Start receiving events
client = QuickHAIngestorClient()
client.start()

print("🎯 Listening for enhanced Home Assistant events...")
print("Press Ctrl+C to stop")

try:
    while True:
        pass
except KeyboardInterrupt:
    print("\n👋 Stopping event listener")
```

## 🔌 **Integration Methods**

### **Method 1: MQTT Events (Recommended for Real-time)**
```python
# Subscribe to enhanced event streams
TOPICS = [
    "ha-ingestor/enhanced/#",      # All enhanced events
    "ha-ingestor/validated/#",     # Quality-validated events
    "ha-ingestor/events/sensor/#", # Sensor-specific events
    "ha-ingestor/events/automation/#" # Automation events
]

# Event structure includes:
# - validation_status: 'validated', 'failed', 'pending'
# - quality_score: 0.0 to 1.0
# - enrichment_data: device metadata, network info
# - context: user IDs, correlation IDs
```

### **Method 2: REST API (Recommended for Status & Metrics)**
```python
import requests

class HAIngestorAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def get_health(self):
        """Quick health check"""
        return requests.get(f"{self.base_url}/health").json()
        
    def get_metrics(self):
        """Get Prometheus metrics"""
        return requests.get(f"{self.base_url}/metrics").text
        
    def get_dependencies(self):
        """Check dependency health"""
        return requests.get(f"{self.base_url}/health/dependencies").json()

# Usage
api = HAIngestorAPI()
health = api.get_health()
print(f"Status: {health['status']} (v{health['version']})")
```

### **Method 3: InfluxDB Direct (Recommended for Analytics)**
```python
from influxdb_client import InfluxDBClient
import pandas as pd

class HAIngestorData:
    def __init__(self):
        self.client = InfluxDBClient(
            url="http://localhost:8086",
            token="your-token-here",
            org="your-org-here"
        )
        
    def get_recent_events(self, hours=1):
        """Get recent validated events"""
        query = f'''
        from(bucket: "ha_events")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r["_measurement"] == "ha_events")
            |> filter(fn: (r) => r["validation_status"] == "validated")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        result = self.client.query_api().query(query)
        return self._to_dataframe(result)
        
    def _to_dataframe(self, result):
        """Convert query result to DataFrame"""
        data = []
        for table in result:
            for record in table.records:
                data.append(record.values)
        return pd.DataFrame(data) if data else pd.DataFrame()

# Usage
data = HAIngestorData()
events = data.get_recent_events(hours=24)
print(f"Retrieved {len(events)} validated events")
```

## 📊 **Enhanced Event Examples**

### **Temperature Sensor Event**
```json
{
  "domain": "sensor",
  "entity_id": "sensor.living_room_temperature",
  "timestamp": "2025-08-25T14:30:00Z",
  "event_type": "state_changed",
  "attributes": {
    "device_class": "temperature",
    "state_class": "measurement",
    "unit_of_measurement": "°C",
    "friendly_name": "Living Room Temperature"
  },
  "validation_status": "validated",
  "quality_score": 0.95,
  "enrichment_data": {
    "device_metadata": {
      "manufacturer": "Generic",
      "model": "Temperature Sensor",
      "sw_version": "1.0.0"
    },
    "network_topology": {
      "ip_address": "192.168.1.100",
      "mac_address": "AA:BB:CC:DD:EE:FF"
    }
  },
  "context": {
    "user_id": "user123",
    "correlation_id": "corr-456",
    "source": "websocket"
  }
}
```

### **Automation Event**
```json
{
  "domain": "automation",
  "entity_id": "automation.morning_routine",
  "timestamp": "2025-08-25T07:00:00Z",
  "event_type": "automation_triggered",
  "attributes": {
    "friendly_name": "Morning Routine",
    "description": "Start morning automation sequence"
  },
  "validation_status": "validated",
  "quality_score": 1.0,
  "enrichment_data": {
    "automation_metadata": {
      "trigger_type": "time",
      "last_triggered": "2025-08-25T07:00:00Z",
      "execution_count": 45
    }
  },
  "context": {
    "user_id": "system",
    "correlation_id": "auto-789",
    "source": "websocket"
  }
}
```

## 🎯 **Common Use Cases**

### **1. Real-time Monitoring Dashboard**
```python
import time
from datetime import datetime

class MonitoringDashboard:
    def __init__(self):
        self.api = HAIngestorAPI()
        self.event_count = 0
        self.last_check = time.time()
        
    def start_monitoring(self):
        """Start real-time monitoring"""
        print("📊 Starting HA-Ingestor monitoring dashboard...")
        
        while True:
            try:
                self.update_dashboard()
                time.sleep(30)  # Update every 30 seconds
                
            except KeyboardInterrupt:
                print("\n👋 Stopping dashboard")
                break
                
    def update_dashboard(self):
        """Update dashboard with current status"""
        # Get health status
        health = self.api.get_health()
        
        # Get metrics
        metrics = self.api.get_metrics()
        
        # Parse key metrics
        events_processed = self._parse_metric(metrics, "ha_ingestor_events_processed_total")
        errors_total = self._parse_metric(metrics, "ha_ingestor_errors_total")
        
        # Display dashboard
        print(f"\n{'='*50}")
        print(f"📊 HA-Ingestor Dashboard - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}")
        print(f"🟢 Status: {health['status']} (v{health['version']})")
        print(f"⏱️  Uptime: {health['uptime_seconds']:.0f} seconds")
        print(f"📈 Events Processed: {events_processed}")
        print(f"❌ Total Errors: {errors_total}")
        print(f"🎯 Success Rate: {self._calculate_success_rate(events_processed, errors_total):.1f}%")
        
    def _parse_metric(self, metrics_text, metric_name):
        """Parse Prometheus metric value"""
        import re
        match = re.search(f'{metric_name} (\\d+)', metrics_text)
        return int(match.group(1)) if match else 0
        
    def _calculate_success_rate(self, total, errors):
        """Calculate success rate percentage"""
        if total == 0:
            return 100.0
        return ((total - errors) / total) * 100

# Start dashboard
dashboard = MonitoringDashboard()
dashboard.start_monitoring()
```

### **2. Data Quality Monitoring**
```python
class DataQualityMonitor:
    def __init__(self):
        self.api = HAIngestorAPI()
        
    def check_quality(self):
        """Check current data quality metrics"""
        try:
            # Get quality metrics
            metrics = self.api.get_metrics()
            
            # Parse quality-related metrics
            total_events = self._parse_metric(metrics, "ha_ingestor_events_processed_total")
            failed_events = self._parse_metric(metrics, "ha_ingestor_events_failed_total")
            duplicate_events = self._parse_metric(metrics, "ha_ingestor_events_deduplicated_total")
            
            # Calculate quality metrics
            success_rate = ((total_events - failed_events) / total_events * 100) if total_events > 0 else 0
            duplicate_rate = (duplicate_events / total_events * 100) if total_events > 0 else 0
            
            # Display quality report
            print(f"\n🔍 Data Quality Report")
            print(f"   Total Events: {total_events}")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Failed Events: {failed_events}")
            print(f"   Duplicate Rate: {duplicate_rate:.1f}%")
            
            # Quality alerts
            if success_rate < 95:
                print("⚠️  Warning: Success rate below 95%")
            if duplicate_rate > 10:
                print("⚠️  Warning: Duplicate rate above 10%")
                
        except Exception as e:
            print(f"❌ Error checking quality: {e}")
            
    def _parse_metric(self, metrics_text, metric_name):
        """Parse Prometheus metric value"""
        import re
        match = re.search(f'{metric_name} (\\d+)', metrics_text)
        return int(match.group(1)) if match else 0

# Check quality
monitor = DataQualityMonitor()
monitor.check_quality()
```

### **3. Event Analytics**
```python
class EventAnalytics:
    def __init__(self):
        self.data = HAIngestorData()
        
    def analyze_events(self, hours=24):
        """Analyze events from the last N hours"""
        print(f"📊 Analyzing events from last {hours} hours...")
        
        # Get events
        events = self.data.get_recent_events(hours=hours)
        
        if events.empty:
            print("No events found")
            return
            
        # Basic statistics
        print(f"📈 Total Events: {len(events)}")
        
        # Domain breakdown
        if 'domain' in events.columns:
            domain_counts = events['domain'].value_counts()
            print(f"\n🏷️  Events by Domain:")
            for domain, count in domain_counts.head(10).items():
                print(f"   {domain}: {count}")
                
        # Quality analysis
        if 'quality_score' in events.columns:
            avg_quality = events['quality_score'].mean()
            print(f"\n🎯 Average Quality Score: {avg_quality:.2f}")
            
        # Time analysis
        if '_time' in events.columns:
            events['_time'] = pd.to_datetime(events['_time'])
            events_per_hour = events.groupby(events['_time'].dt.hour).size()
            print(f"\n⏰ Events per Hour:")
            for hour, count in events_per_hour.items():
                print(f"   {hour:02d}:00 - {count} events")

# Run analytics
analytics = EventAnalytics()
analytics.analyze_events(hours=6)
```

## 🔧 **Configuration Quick Setup**

### **Environment Variables**
```bash
# Add to your .env file
HA_INGESTOR_URL=http://localhost:8000
HA_INGESTOR_MQTT_BROKER=localhost
HA_INGESTOR_MQTT_PORT=1883
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token-here
INFLUXDB_ORG=your-org-here
INFLUXDB_BUCKET=ha_events
```

### **Python Dependencies**
```bash
# Install required packages
pip install requests paho-mqtt influxdb-client pandas

# Or add to requirements.txt
requests>=2.28.0
paho-mqtt>=1.6.1
influxdb-client>=1.36.0
pandas>=1.5.0
```

### **Docker Compose Integration**
```yaml
# Add to your docker-compose.yml
version: '3.8'
services:
  your-service:
    # Your service configuration
    environment:
      - HA_INGESTOR_URL=http://ha-ingestor:8000
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - ha-ingestor
      
  ha-ingestor:
    image: ha-ingestor:latest
    ports:
      - "8000:8000"
    environment:
      - MQTT_BROKER=mosquitto
      - WEBSOCKET_URL=ws://homeassistant:8123/api/websocket
      - INFLUXDB_URL=http://influxdb:8086
```

## 📋 **Quick Start Checklist**

### **Pre-Integration**
- [ ] **HA-Ingestor v0.3.0** deployed and running
- [ ] **Health endpoint** responding at `http://localhost:8000/health`
- [ **Dependencies** showing healthy status
- [ ] **Enhanced features** operational

### **Basic Integration**
- [ ] **Health check** working with your code
- [ ] **Event subscription** configured (MQTT or API)
- [ ] **Event processing** receiving enhanced data
- [ ] **Quality validation** working correctly

### **Advanced Features**
- [ ] **Monitoring dashboard** operational
- [ ] **Data quality** monitoring active
- [ ] **Event analytics** providing insights
- [ ] **Error handling** implemented

## 🚨 **Troubleshooting Quick Fixes**

### **Common Issues & Solutions**

**1. Connection Refused**
```bash
# Check if HA-Ingestor is running
docker-compose ps ha-ingestor

# Check if port 8000 is accessible
curl http://localhost:8000/health
```

**2. MQTT Connection Failed**
```bash
# Check MQTT broker
docker-compose ps mosquitto

# Test MQTT connection
mosquitto_pub -h localhost -t "test/topic" -m "test message"
```

**3. No Events Received**
```bash
# Check HA-Ingestor logs
docker-compose logs ha-ingestor --tail=50

# Verify event subscriptions
docker-compose logs ha-ingestor | grep "subscribed"
```

**4. InfluxDB Connection Failed**
```bash
# Check InfluxDB status
docker-compose ps influxdb

# Test InfluxDB connection
curl http://localhost:8086/health
```

## 🎯 **Next Steps**

### **Immediate (Day 1)**
1. ✅ **Verify integration** is working
2. ✅ **Test event reception** with sample data
3. ✅ **Implement basic processing** logic
4. ✅ **Set up monitoring** and alerts

### **Short-term (Week 1)**
1. **Enhance event processing** with quality validation
2. **Implement error handling** and resilience
3. **Add performance monitoring** and metrics
4. **Create custom analytics** and dashboards

### **Long-term (Month 1)**
1. **Scale integration** to handle increased load
2. **Implement advanced analytics** using enhanced data
3. **Add machine learning** capabilities
4. **Create comprehensive** monitoring and alerting

## 📞 **Getting Help**

### **Quick Support**
- **Health Check**: `curl http://localhost:8000/health`
- **Logs**: `docker-compose logs ha-ingestor`
- **Status**: `docker-compose ps`

### **Documentation**
- **Full Integration Guide**: `CHILD_PROJECTS_INTEGRATION_GUIDE.md`
- **API Reference**: `README.md`
- **Configuration**: `QUICK_REFERENCE_CARD.md`

### **Community**
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Examples**: Real-world integration examples

---

## **🎉 You're Ready!**

**HA-Ingestor v0.3.0 is now integrated and ready to provide enhanced Home Assistant data to your project!**

**Key Benefits You Now Have:**
- ✅ **Real-time enhanced events** with quality validation
- ✅ **Comprehensive monitoring** and health checks
- ✅ **Rich metadata** and context information
- ✅ **Production-ready** data ingestion layer
- ✅ **Scalable architecture** for future growth

**Start building amazing Home Assistant applications with confidence!** 🚀

---

**HA-Ingestor v0.3.0** - Enhanced Data Ingestion & Preparation Layer for Home Assistant

*Built with ❤️ for the Home Assistant community*
