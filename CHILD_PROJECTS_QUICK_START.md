# 🚀 Quick Start Guide for Child Projects

**HA-Ingestor is NOW LIVE and processing real Home Assistant data!**

## ⚡ **Immediate Access (No Setup Required)**

HA-Ingestor is already running and processing your Home Assistant data. You can start using it **right now**:

### **1. Check if it's working**
```python
import requests

# Quick health check
response = requests.get("http://localhost:8000/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### **2. Get your data**
```python
from influxdb_client import InfluxDBClient

# Connect to HA-Ingestor's processed data
client = InfluxDBClient(
    url="http://localhost:8086",
    token="Rom24aedslas!@",
    org="myorg"
)

# Get recent events
query = '''
from(bucket: "ha_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "ha_entities")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

result = client.query_api().query(query)
print(f"Found {len(result)} data points")
client.close()
```

## 🎯 **What You Get Immediately**

### **Real-Time Data**
- ✅ **Live Home Assistant events** processed in real-time
- ✅ **Optimized schema** for fast queries
- ✅ **Structured data** with proper tags and fields
- ✅ **Historical data** from when HA-Ingestor started

### **Current Data Being Processed**
- **Current sensors**: `sensor.bar_estimated_current`, `sensor.wled_estimated_current`
- **Temperature sensors**: All temperature data automatically optimized
- **State changes**: All entity state changes captured and stored
- **Custom attributes**: All Home Assistant attributes preserved and indexed

## 🔧 **Integration Options**

### **Option 1: Direct InfluxDB Access (Recommended)**
```python
# Your project can directly query the optimized data
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "Rom24aedslas!@"
INFLUXDB_ORG = "myorg"
INFLUXDB_BUCKET = "ha_events"
```

### **Option 2: Health Monitoring**
```python
# Monitor HA-Ingestor health in your app
def check_ha_ingestor():
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# Use in your health checks
if not check_ha_ingestor():
    print("Warning: HA-Ingestor is not available")
```

### **Option 3: Metrics Integration**
```python
# Get performance metrics
def get_processing_stats():
    response = requests.get("http://localhost:8000/metrics")
    # Parse metrics to get processing rates, error counts, etc.
    return response.text
```

## 📊 **Data Schema (Ready to Use)**

### **Measurement**: `ha_entities`
```json
{
  "measurement": "ha_entities",
  "tags": {
    "domain": "sensor",
    "entity_id": "sensor.living_room_temperature",
    "source": "websocket",
    "entity_group": "living_room"
  },
  "fields": {
    "state": "22.5",
    "state_numeric": 22.5,
    "attributes": "{\"unit_of_measurement\": \"°C\"}",
    "payload_size": 15
  },
  "timestamp": "2025-08-25T01:38:29.728852Z"
}
```

### **Common Queries**
```python
# Get all temperature sensors
query = '''
from(bucket: "ha_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "ha_entities")
  |> filter(fn: (r) => r["domain"] == "sensor")
  |> filter(fn: (r) => r["entity_id"] =~ /.*temperature.*/)
'''

# Get entity state changes
query = '''
from(bucket: "ha_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "ha_entities")
  |> filter(fn: (r) => r["_field"] == "state")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''
```

## 🚨 **Error Handling**

### **Service Unavailable**
```python
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code != 200:
        print("HA-Ingestor health check failed")
        # Fall back to direct Home Assistant API or other data source
except requests.exceptions.RequestException:
    print("HA-Ingestor is not accessible")
    # Implement fallback strategy
```

### **Data Not Available**
```python
try:
    # Try to get data from HA-Ingestor
    result = client.query_api().query(query)
    if not result:
        print("No data available from HA-Ingestor")
        # Fall back to direct Home Assistant API
except Exception as e:
    print(f"Error accessing HA-Ingestor data: {e}")
    # Implement fallback strategy
```

## 📈 **Performance Monitoring**

### **Check Processing Status**
```python
# Monitor real-time processing
def get_processing_stats():
    response = requests.get("http://localhost:8000/metrics")
    metrics = response.text
    
    # Parse key metrics
    if "ha_ingestor_events_processed_total" in metrics:
        # Extract processing counts
        pass
    
    return {
        "status": "operational" if "ha_ingestor_up 1" in metrics else "down",
        "events_processed": "extract_from_metrics",
        "error_rate": "calculate_from_metrics"
    }
```

## 🎉 **You're Ready to Go!**

### **What's Already Working**
1. ✅ **HA-Ingestor is processing your Home Assistant data**
2. ✅ **Data is being stored in optimized schema**
3. ✅ **Real-time processing is active**
4. ✅ **Monitoring and alerting is operational**

### **Next Steps**
1. **Test the connection** with the code examples above
2. **Query your data** using the InfluxDB client
3. **Monitor performance** using the metrics endpoint
4. **Scale as needed** - the system is production-ready

### **Support**
- **Health Check**: `http://localhost:8000/health`
- **Metrics**: `http://localhost:8000/metrics`
- **InfluxDB**: `http://localhost:8086`
- **Grafana**: `http://localhost:3000` (for monitoring)

---

**HA-Ingestor is LIVE and processing your data NOW!** 🚀

Start using it immediately - no setup required!
