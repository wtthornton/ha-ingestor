# 🚀 HA-Ingestor Quick Reference Card

**Status**: ✅ **PRODUCTION READY** | **Version**: v0.2.0

## 🔗 **Quick Integration**

### **1. Health Check**
```python
import requests

def is_ha_ingestor_ready():
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# Usage
if is_ha_ingestor_ready():
    print("✅ HA-Ingestor is ready!")
else:
    print("❌ HA-Ingestor is not available")
```

### **2. Get Recent Data**
```python
from influxdb_client import InfluxDBClient

def get_recent_events(minutes=60):
    client = InfluxDBClient(
        url="http://localhost:8086",
        token="Rom24aedslas!@",
        org="myorg"
    )
    
    query = f'''
    from(bucket: "ha_events")
        |> range(start: -{minutes}m)
        |> filter(fn: (r) => r["_measurement"] == "ha_entities")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    
    result = client.query_api().query(query)
    events = []
    
    for table in result:
        for record in table.records:
            events.append({
                "timestamp": record.get_time(),
                "entity_id": record.values.get("entity_id"),
                "state": record.values.get("state"),
                "domain": record.values.get("domain")
            })
    
    client.close()
    return events

# Usage
events = get_recent_events(30)  # Last 30 minutes
print(f"Found {len(events)} events")
```

### **3. Environment Variables**
```bash
# Add to your .env file
HA_INGESTOR_URL=http://localhost:8000
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=Rom24aedslas!@
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=ha_events
```

## 📊 **Data Schema**

### **Measurement**: `ha_entities`
- **Tags**: `domain`, `entity_id`, `source`, `entity_group`
- **Fields**: `state`, `attributes`, `payload_size`, `topic`
- **Timestamp**: Event occurrence time

### **Example Query**
```python
# Get temperature sensors
query = '''
from(bucket: "ha_events")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "ha_entities")
    |> filter(fn: (r) => r["domain"] == "sensor")
    |> filter(fn: (r) => r["entity_id"] =~ /.*temperature.*/)
'''
```

## 🔧 **Service Endpoints**

| Endpoint | URL | Purpose |
|----------|-----|---------|
| **Health** | `http://localhost:8000/health` | Service status |
| **Metrics** | `http://localhost:8000/metrics` | Performance data |
| **InfluxDB** | `http://localhost:8086` | Data access |

## 🚨 **Troubleshooting**

### **Service Not Responding**
```bash
# Check if running
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs ha-ingestor

# Restart service
docker-compose -f docker-compose.production.yml restart ha-ingestor
```

### **Data Not Available**
```bash
# Check InfluxDB
curl http://localhost:8086/health

# Check bucket
curl -H "Authorization: Token Rom24aedslas!@" \
     "http://localhost:8086/api/v2/buckets?org=myorg"
```

## 📚 **Full Documentation**

- **Integration Guide**: `CHILD_PROJECTS_INTEGRATION_GUIDE.md`
- **Production Summary**: `PRODUCTION_DEPLOYMENT_SUMMARY.md`
- **Performance Guide**: `PERFORMANCE_MONITORING_ALERTING_GUIDE.md`

## 🎯 **Quick Start Checklist**

- [ ] **Verify Service**: Check `http://localhost:8000/health`
- [ ] **Test Connection**: Try the health check code above
- [ ] **Get Data**: Use the recent events example
- [ ] **Configure**: Add environment variables to your project
- [ ] **Monitor**: Set up health checks in your application

---

**Need Help?** Check the logs or refer to the full integration guide!
