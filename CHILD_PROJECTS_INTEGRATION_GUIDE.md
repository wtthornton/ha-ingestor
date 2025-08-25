# 🔗 Child Projects Integration Guide for HA-Ingestor

**Purpose**: This guide enables other child projects in the ha-cleanup ecosystem to integrate with and utilize HA-Ingestor for Home Assistant data processing and analytics.

## 🎯 **Overview**

HA-Ingestor is now **production-ready** and provides a centralized, type-safe data ingestion and transformation service for Home Assistant data. Other projects can leverage this service for:

- **Real-time data access** from Home Assistant
- **Optimized data storage** in InfluxDB
- **Advanced analytics** and data processing
- **Unified data schema** across projects

## 🚀 **Current Status**

### **Production Deployment**
- ✅ **Status**: Fully operational in production
- ✅ **Version**: v0.2.0 with Type-Safe Migration System
- ✅ **Performance**: Production-optimized configuration
- ✅ **Monitoring**: Comprehensive health and metrics

### **Service Endpoints**
- **Main Service**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **InfluxDB**: http://localhost:8086

## 🔌 **Integration Methods**

### **Method 1: Direct API Integration**

#### **Health Check Integration**
```python
import requests
import json

def check_ha_ingestor_health():
    """Check if HA-Ingestor is operational."""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            health_data = response.json()
            return {
                "status": "operational",
                "service": health_data.get("service"),
                "uptime": health_data.get("uptime_seconds"),
                "version": health_data.get("version")
            }
        else:
            return {"status": "unavailable", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Usage
health = check_ha_ingestor_health()
print(f"HA-Ingestor Status: {health['status']}")
```

#### **Metrics Integration**
```python
import requests
import re

def get_ha_ingestor_metrics():
    """Retrieve HA-Ingestor performance metrics."""
    try:
        response = requests.get("http://localhost:8000/metrics")
        if response.status_code == 200:
            metrics_text = response.text
            
            # Parse key metrics
            metrics = {}
            
            # Service status
            if "ha_ingestor_up 1" in metrics_text:
                metrics["service_status"] = "UP"
            else:
                metrics["service_status"] = "DOWN"
            
            # Event processing
            event_match = re.search(r'ha_ingestor_events_processed_total (\d+)', metrics_text)
            if event_match:
                metrics["events_processed"] = int(event_match.group(1))
            
            # Error rate
            error_match = re.search(r'ha_ingestor_errors_total (\d+)', metrics_text)
            if error_match:
                metrics["errors_total"] = int(error_match.group(1))
            
            return metrics
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# Usage
metrics = get_ha_ingestor_metrics()
print(f"Events Processed: {metrics.get('events_processed', 'Unknown')}")
```

### **Method 2: InfluxDB Direct Access**

#### **Data Query Integration**
```python
from influxdb_client import InfluxDBClient
from influxdb_client.client.flux_table import FluxTable
from typing import List, Dict, Any

class HAIngestorDataClient:
    """Client for accessing HA-Ingestor processed data from InfluxDB."""
    
    def __init__(self, url: str = "http://localhost:8086", 
                 token: str = "Rom24aedslas!@", 
                 org: str = "myorg", 
                 bucket: str = "ha_events"):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.query_api = self.client.query_api()
        self.bucket = bucket
        self.org = org
    
    def get_recent_events(self, minutes: int = 60, entity_id: str = None) -> List[Dict[str, Any]]:
        """Get recent events from HA-Ingestor."""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{minutes}m)
            |> filter(fn: (r) => r["_measurement"] == "ha_entities")
        '''
        
        if entity_id:
            query += f'|> filter(fn: (r) => r["entity_id"] == "{entity_id}")'
        
        query += '''
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"])
        '''
        
        try:
            result = self.query_api.query(query)
            events = []
            
            for table in result:
                for record in table.records:
                    event = {
                        "timestamp": record.get_time(),
                        "entity_id": record.values.get("entity_id"),
                        "domain": record.values.get("domain"),
                        "state": record.values.get("state"),
                        "attributes": record.values.get("attributes", {}),
                        "source": record.values.get("source")
                    }
                    events.append(event)
            
            return events
        except Exception as e:
            print(f"Error querying InfluxDB: {e}")
            return []
    
    def get_entity_history(self, entity_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical data for a specific entity."""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r["_measurement"] == "ha_entities")
            |> filter(fn: (r) => r["entity_id"] == "{entity_id}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"])
        '''
        
        try:
            result = self.query_api.query(query)
            history = []
            
            for table in result:
                for record in table.records:
                    history.append({
                        "timestamp": record.get_time(),
                        "state": record.values.get("state"),
                        "attributes": record.values.get("attributes", {}),
                        "source": record.values.get("source")
                    })
            
            return history
        except Exception as e:
            print(f"Error querying entity history: {e}")
            return []
    
    def close(self):
        """Close the InfluxDB client."""
        self.client.close()

# Usage Example
def example_usage():
    client = HAIngestorDataClient()
    
    # Get recent events
    recent_events = client.get_recent_events(minutes=30)
    print(f"Recent events: {len(recent_events)}")
    
    # Get entity history
    temp_history = client.get_entity_history("sensor.living_room_temperature", hours=6)
    print(f"Temperature history: {len(temp_history)} records")
    
    client.close()

if __name__ == "__main__":
    example_usage()
```

### **Method 3: Docker Compose Integration**

#### **Add HA-Ingestor to Your Project**
```yaml
# In your project's docker-compose.yml
version: '3.8'

services:
  your-service:
    # Your service configuration
    depends_on:
      - ha-ingestor
    environment:
      - HA_INGESTOR_URL=http://ha-ingestor:8000
      - INFLUXDB_URL=http://influxdb:8086

  ha-ingestor:
    image: ha-ingestor-ha-ingestor:latest
    container_name: ha-ingestor
    ports:
      - "8000:8000"
    environment:
      - HA_WS_URL=ws://192.168.1.86:8123/api/websocket
      - HA_WS_TOKEN=${HA_WS_TOKEN}
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - INFLUXDB_ORG=myorg
      - INFLUXDB_BUCKET=ha_events
    depends_on:
      - influxdb
    restart: unless-stopped

  influxdb:
    image: influxdb:2.7
    container_name: influxdb
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword
      - DOCKER_INFLUXDB_INIT_ORG=myorg
      - DOCKER_INFLUXDB_INIT_BUCKET=ha_events
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=${INFLUXDB_TOKEN}
    volumes:
      - influxdb_data:/var/lib/influxdb2
    restart: unless-stopped

volumes:
  influxdb_data:
```

## 📊 **Data Schema & Structure**

### **Measurement: ha_entities**
```json
{
  "measurement": "ha_entities",
  "tags": {
    "domain": "sensor",
    "entity_id": "sensor.living_room_temperature",
    "entity_type": "device",
    "source": "mqtt",
    "event_category": "state_change",
    "entity_group": "living_room"
  },
  "fields": {
    "state": "22.5",
    "state_numeric": 22.5,
    "attributes": "{\"unit_of_measurement\": \"°C\", \"friendly_name\": \"Living Room Temperature\"}",
    "payload_size": 15,
    "topic": "homeassistant/sensor/living_room_temperature/state",
    "processing_timestamp": "2025-08-25T01:33:10.123456Z",
    "original_timestamp": "2025-08-25T01:33:10.000000Z"
  },
  "timestamp": "2025-08-25T01:33:10.000000Z"
}
```

### **Common Query Patterns**
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

## 🔧 **Configuration & Environment Variables**

### **Required Environment Variables**
```bash
# HA-Ingestor Service
HA_INGESTOR_URL=http://localhost:8000
HA_INGESTOR_HEALTH_ENDPOINT=/health
HA_INGESTOR_METRICS_ENDPOINT=/metrics

# InfluxDB Connection
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token_here
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=ha_events

# Home Assistant (if direct access needed)
HA_WS_URL=ws://192.168.1.86:8123/api/websocket
HA_WS_TOKEN=your_long_lived_token_here
```

### **Configuration File Example**
```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class HAIngestorConfig:
    """Configuration for HA-Ingestor integration."""
    
    # Service endpoints
    service_url: str = os.getenv("HA_INGESTOR_URL", "http://localhost:8000")
    health_endpoint: str = os.getenv("HA_INGESTOR_HEALTH_ENDPOINT", "/health")
    metrics_endpoint: str = os.getenv("HA_INGESTOR_METRICS_ENDPOINT", "/metrics")
    
    # InfluxDB
    influxdb_url: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    influxdb_token: str = os.getenv("INFLUXDB_TOKEN", "")
    influxdb_org: str = os.getenv("INFLUXDB_ORG", "myorg")
    influxdb_bucket: str = os.getenv("INFLUXDB_BUCKET", "ha_events")
    
    # Connection settings
    timeout: int = int(os.getenv("HA_INGESTOR_TIMEOUT", "30"))
    retry_attempts: int = int(os.getenv("HA_INGESTOR_RETRY_ATTEMPTS", "3"))
    
    def validate(self) -> bool:
        """Validate configuration."""
        required_fields = [
            self.service_url,
            self.influxdb_token,
            self.influxdb_org,
            self.influxdb_bucket
        ]
        return all(field for field in required_fields)

# Usage
config = HAIngestorConfig()
if not config.validate():
    raise ValueError("Invalid HA-Ingestor configuration")
```

## 🚨 **Error Handling & Resilience**

### **Health Check Integration**
```python
import time
import requests
from typing import Optional

class HAIngestorHealthMonitor:
    """Monitor HA-Ingestor service health."""
    
    def __init__(self, service_url: str, check_interval: int = 30):
        self.service_url = service_url
        self.check_interval = check_interval
        self.last_check = 0
        self.last_status = "unknown"
    
    def is_healthy(self) -> bool:
        """Check if HA-Ingestor is healthy."""
        current_time = time.time()
        
        # Only check if enough time has passed
        if current_time - self.last_check < self.check_interval:
            return self.last_status == "operational"
        
        try:
            response = requests.get(f"{self.service_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.last_status = "operational" if health_data.get("status") == "operational" else "unhealthy"
            else:
                self.last_status = "unhealthy"
        except Exception:
            self.last_status = "unhealthy"
        
        self.last_check = current_time
        return self.last_status == "operational"
    
    def wait_for_healthy(self, timeout: int = 300) -> bool:
        """Wait for HA-Ingestor to become healthy."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_healthy():
                return True
            time.sleep(5)
        
        return False

# Usage
monitor = HAIngestorHealthMonitor("http://localhost:8000")
if monitor.wait_for_healthy(timeout=60):
    print("HA-Ingestor is healthy and ready!")
else:
    print("HA-Ingestor health check failed")
```

## 📈 **Performance & Monitoring**

### **Integration Metrics**
```python
import time
from typing import Dict, Any

class HAIngestorMetrics:
    """Collect and track HA-Ingestor integration metrics."""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0
        self.start_time = time.time()
    
    def record_request(self, response_time: float, success: bool = True):
        """Record a request metric."""
        self.request_count += 1
        self.total_response_time += response_time
        
        if not success:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        uptime = time.time() - self.start_time
        avg_response_time = self.total_response_time / self.request_count if self.request_count > 0 else 0
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate_percent": error_rate,
            "avg_response_time_ms": avg_response_time * 1000,
            "requests_per_second": self.request_count / uptime if uptime > 0 else 0
        }

# Usage
metrics = HAIngestorMetrics()

# Record metrics during operations
start_time = time.time()
try:
    # Your HA-Ingestor operation here
    response_time = time.time() - start_time
    metrics.record_request(response_time, success=True)
except Exception:
    response_time = time.time() - start_time
    metrics.record_request(response_time, success=False)

# Get metrics
current_metrics = metrics.get_metrics()
print(f"Error Rate: {current_metrics['error_rate_percent']:.2f}%")
```

## 🔄 **Migration & Updates**

### **Version Compatibility**
- **Current Version**: v0.2.0
- **API Stability**: Stable (no breaking changes expected)
- **Schema Evolution**: Backward compatible
- **Update Process**: Rolling updates with zero downtime

### **Migration Checklist**
- [ ] **Health Check**: Verify service is operational
- [ ] **Configuration**: Update environment variables
- [ ] **Testing**: Test integration endpoints
- [ ] **Monitoring**: Set up health monitoring
- [ ] **Documentation**: Update project documentation

## 📚 **Resources & Support**

### **Documentation**
- **Production Summary**: `PRODUCTION_DEPLOYMENT_SUMMARY.md`
- **Migration Guide**: `NEXT_STEPS_QUICK_START.md`
- **Performance Guide**: `PERFORMANCE_MONITORING_ALERTING_GUIDE.md`
- **Schema Guide**: `SCHEMA_OPTIMIZATION_GUIDE.md`

### **Support Commands**
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs ha-ingestor

# Restart service
docker-compose -f docker-compose.production.yml restart ha-ingestor

# Check health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics
```

### **Contact & Updates**
- **Status Page**: Check health endpoints for real-time status
- **Logs**: Monitor Docker logs for detailed information
- **Metrics**: Use Prometheus metrics for performance insights

---

## 🎉 **Getting Started**

1. **Verify HA-Ingestor is running**: Check health endpoint
2. **Choose integration method**: API, InfluxDB, or Docker Compose
3. **Configure environment**: Set required environment variables
4. **Test integration**: Use provided examples
5. **Monitor performance**: Set up health checks and metrics
6. **Scale as needed**: Monitor usage and adjust configuration

HA-Ingestor is now your centralized, production-ready data ingestion service for Home Assistant integration across all child projects!
