# Child Projects Integration Guide - HA-Ingestor v0.3.0

**Enhanced Data Ingestion & Preparation Layer for Home Assistant**

This guide provides comprehensive instructions for integrating child projects with HA-Ingestor v0.3.0, which now offers enhanced data collection, quality validation, and rich monitoring capabilities.

## 🚀 **What's New in v0.3.0 for Child Projects**

### **Enhanced Data Collection**
- **Multi-domain event capture**: sensor, media_player, image, network, automation
- **Comprehensive device attributes**: device_class, state_class, unit_of_measurement
- **Performance metrics**: Network speeds, power consumption, lighting levels
- **Context tracking**: User IDs, correlation IDs, timestamps, state history

### **Advanced Data Quality & Validation**
- **Schema validation**: Pydantic-based data integrity
- **Duplicate detection**: Intelligent deduplication with configurable thresholds
- **Error handling**: Comprehensive error recovery and logging
- **Data enrichment**: Automatic metadata addition and context preservation

### **Rich Monitoring & Observability**
- **49+ Prometheus metrics** for comprehensive monitoring
- **Real-time health checks** with dependency monitoring
- **Performance analytics** including latency, throughput, and error rates
- **Circuit breaker patterns** for resilience and fault tolerance

## 🏗️ **Integration Architecture**

### **Data Flow Overview**
```
Child Project → HA-Ingestor v0.3.0 → InfluxDB → Analytics/ML Systems
     ↓              ↓                    ↓              ↓
Data Sources   Enhanced Processing   Optimized Storage   Advanced Features
     ↓              ↓                    ↓              ↓
Raw Events    Quality Validation    Schema Optimization   Business Logic
     ↓              ↓                    ↓              ↓
MQTT/WS       Context Enrichment    Performance Metrics   Insights
```

### **Integration Points**
1. **Data Ingestion**: MQTT and WebSocket event streaming
2. **Data Processing**: Enhanced transformation and validation pipeline
3. **Data Storage**: Optimized InfluxDB schema and storage
4. **Data Export**: Multiple export formats and APIs
5. **Monitoring**: Comprehensive health and performance metrics

## 🔌 **Integration Methods**

### **Method 1: Direct MQTT Integration**

#### **Subscribe to Enhanced Events**
```python
import paho.mqtt.client as mqtt
import json

class HAIngestorClient:
    def __init__(self, broker="localhost", port=1883):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port)

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to HA-Ingestor MQTT")
        # Subscribe to enhanced events
        client.subscribe("ha-ingestor/events/#")
        client.subscribe("ha-ingestor/enhanced/#")
        client.subscribe("ha-ingestor/validated/#")

    def on_message(self, client, userdata, msg):
        try:
            event = json.loads(msg.payload.decode())
            self.process_enhanced_event(event)
        except Exception as e:
            print(f"Error processing event: {e}")

    def process_enhanced_event(self, event):
        # Process enhanced event with quality validation
        if event.get('validation_status') == 'validated':
            print(f"Processing validated event: {event['entity_id']}")
            # Your business logic here
            self.analyze_event(event)

    def analyze_event(self, event):
        # Access enhanced data fields
        domain = event.get('domain')
        entity_id = event.get('entity_id')
        attributes = event.get('attributes', {})
        context = event.get('context', {})

        # Enhanced attributes available in v0.3.0
        device_class = attributes.get('device_class')
        state_class = attributes.get('state_class')
        unit_of_measurement = attributes.get('unit_of_measurement')

        # Context information
        user_id = context.get('user_id')
        correlation_id = context.get('correlation_id')

        print(f"Enhanced event: {domain}.{entity_id} - {device_class} - {unit_of_measurement}")

# Usage
client = HAIngestorClient()
client.client.loop_forever()
```

#### **Enhanced Event Structure**
```json
{
  "domain": "sensor",
  "entity_id": "temperature_living_room",
  "timestamp": "2025-08-25T14:30:00Z",
  "event_type": "state_changed",
  "attributes": {
    "device_class": "temperature",
    "state_class": "measurement",
    "unit_of_measurement": "°C",
    "friendly_name": "Living Room Temperature"
  },
  "context": {
    "user_id": "user123",
    "correlation_id": "corr-456",
    "source": "websocket"
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
  }
}
```

### **Method 2: REST API Integration**

#### **Enhanced Health & Status API**
```python
import requests
import json

class HAIngestorAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def get_service_info(self):
        """Get comprehensive service information"""
        response = requests.get(f"{self.base_url}/")
        return response.json()

    def get_health_status(self):
        """Get detailed health status"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

    def get_dependencies_health(self):
        """Get detailed dependency health"""
        response = requests.get(f"{self.base_url}/health/dependencies")
        return response.json()

    def get_metrics(self):
        """Get Prometheus metrics"""
        response = requests.get(f"{self.base_url}/metrics")
        return response.text

    def get_readiness(self):
        """Get service readiness status"""
        response = requests.get(f"{self.base_url}/ready")
        return response.json()

# Usage
api = HAIngestorAPI()

# Check service status
info = api.get_service_info()
print(f"Service: {info['service']}")
print(f"Version: {info['version']}")
print(f"Status: {info['status']}")

# Check health
health = api.get_health_status()
print(f"Health: {health['status']}")
print(f"Uptime: {health['uptime_seconds']} seconds")

# Check dependencies
deps = api.get_dependencies_health()
for dep_name, dep_info in deps['dependencies'].items():
    print(f"{dep_name}: {dep_info['status']} - {dep_info['message']}")
```

### **Method 3: InfluxDB Direct Access**

#### **Enhanced Data Schema Access**
```python
from influxdb_client import InfluxDBClient
from influxdb_client.client.flux_table import FluxTable
import pandas as pd

class HAIngestorDataAccess:
    def __init__(self, url="http://localhost:8086", token="your-token", org="your-org"):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.query_api = self.client.query_api()

    def get_enhanced_events(self, bucket="ha_events", start_time="-1h"):
        """Query enhanced events with quality validation"""
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: {start_time})
            |> filter(fn: (r) => r["_measurement"] == "ha_events")
            |> filter(fn: (r) => r["validation_status"] == "validated")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        result = self.query_api.query(query)
        return self._process_query_result(result)

    def get_quality_metrics(self, bucket="ha_events", start_time="-24h"):
        """Query data quality metrics"""
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: {start_time})
            |> filter(fn: (r) => r["_measurement"] == "data_quality")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        result = self.query_api.query(query)
        return self._process_query_result(result)

    def get_performance_metrics(self, bucket="ha_events", start_time="-1h"):
        """Query performance metrics"""
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: {start_time})
            |> filter(fn: (r) => r["_measurement"] == "performance")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        result = self.query_api.query(result)
        return self._process_query_result(result)

    def _process_query_result(self, result):
        """Convert query result to pandas DataFrame"""
        data = []
        for table in result:
            for record in table.records:
                data.append(record.values)

        if data:
            df = pd.DataFrame(data)
            return df
        return pd.DataFrame()

# Usage
data_access = HAIngestorDataAccess()

# Get validated events
events = data_access.get_enhanced_events()
print(f"Retrieved {len(events)} validated events")

# Get quality metrics
quality = data_access.get_quality_metrics()
print(f"Quality metrics: {quality.columns.tolist()}")

# Get performance metrics
performance = data_access.get_performance_metrics()
print(f"Performance metrics: {performance.columns.tolist()}")
```

## 📊 **Enhanced Data Models**

### **Event Quality Validation**
```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class EnhancedEvent:
    """Enhanced event model with quality validation"""
    domain: str
    entity_id: str
    timestamp: datetime
    event_type: str
    attributes: Dict[str, Any]

    # Enhanced fields in v0.3.0
    validation_status: str  # 'validated', 'failed', 'pending'
    quality_score: float    # 0.0 to 1.0
    enrichment_data: Dict[str, Any]
    context: Dict[str, Any]

    # Quality indicators
    is_duplicate: bool = False
    validation_errors: Optional[list] = None
    processing_latency_ms: Optional[float] = None

    def is_high_quality(self) -> bool:
        """Check if event meets quality standards"""
        return (
            self.validation_status == 'validated' and
            self.quality_score >= 0.8 and
            not self.is_duplicate
        )

    def get_device_info(self) -> Dict[str, Any]:
        """Extract device information from enrichment data"""
        return self.enrichment_data.get('device_metadata', {})

    def get_network_info(self) -> Dict[str, Any]:
        """Extract network topology information"""
        return self.enrichment_data.get('network_topology', {})

# Usage
def process_enhanced_event(event_data: Dict[str, Any]):
    event = EnhancedEvent(**event_data)

    if event.is_high_quality():
        # Process high-quality event
        device_info = event.get_device_info()
        network_info = event.get_network_info()

        print(f"Processing high-quality event from {device_info.get('model', 'Unknown')}")
        print(f"Network location: {network_info.get('ip_address', 'Unknown')}")

        # Your business logic here
        analyze_event_quality(event)
    else:
        # Handle low-quality event
        print(f"Low-quality event: {event.validation_errors}")
```

### **Data Quality Metrics**
```python
@dataclass
class DataQualityMetrics:
    """Data quality metrics for monitoring"""
    total_events: int
    validated_events: int
    failed_events: int
    duplicate_events: int
    average_quality_score: float
    validation_success_rate: float

    @property
    def quality_percentage(self) -> float:
        """Calculate overall quality percentage"""
        if self.total_events == 0:
            return 0.0
        return (self.validated_events / self.total_events) * 100

    def get_quality_summary(self) -> str:
        """Get human-readable quality summary"""
        return (
            f"Quality: {self.quality_percentage:.1f}% "
            f"({self.validated_events}/{self.total_events} events) "
            f"Score: {self.average_quality_score:.2f}"
        )

# Usage
def monitor_data_quality(api: HAIngestorAPI):
    """Monitor data quality in real-time"""
    try:
        # Get quality metrics
        metrics = api.get_metrics()

        # Parse Prometheus metrics for quality data
        quality_data = parse_quality_metrics(metrics)

        # Create quality metrics object
        quality = DataQualityMetrics(**quality_data)

        # Display quality summary
        print(quality.get_quality_summary())

        # Alert if quality drops
        if quality.quality_percentage < 90:
            print("⚠️  Data quality below threshold!")

    except Exception as e:
        print(f"Error monitoring data quality: {e}")
```

## 🔍 **Monitoring & Observability**

### **Real-Time Health Monitoring**
```python
import time
from typing import Dict, Any

class HAIngestorMonitor:
    def __init__(self, api: HAIngestorAPI, check_interval: int = 30):
        self.api = api
        self.check_interval = check_interval
        self.health_history = []

    def start_monitoring(self):
        """Start continuous health monitoring"""
        print("Starting HA-Ingestor health monitoring...")

        while True:
            try:
                health_status = self.check_health()
                self.health_history.append(health_status)

                # Display status
                self.display_health_status(health_status)

                # Check for issues
                self.check_for_issues(health_status)

                # Wait for next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(self.check_interval)

    def check_health(self) -> Dict[str, Any]:
        """Check comprehensive health status"""
        return {
            'timestamp': time.time(),
            'service_info': self.api.get_service_info(),
            'health': self.api.get_health_status(),
            'dependencies': self.api.get_dependencies_health(),
            'readiness': self.api.get_readiness()
        }

    def display_health_status(self, status: Dict[str, Any]):
        """Display current health status"""
        health = status['health']
        deps = status['dependencies']

        print(f"\n[{time.strftime('%H:%M:%S')}] Health Check:")
        print(f"  Service: {health['status']} (v{health['version']})")
        print(f"  Uptime: {health['uptime_seconds']:.0f}s")

        # Display dependency status
        for dep_name, dep_info in deps['dependencies'].items():
            status_icon = "✅" if dep_info['status'] == 'healthy' else "❌"
            print(f"  {dep_name}: {status_icon} {dep_info['status']}")

    def check_for_issues(self, status: Dict[str, Any]):
        """Check for potential issues"""
        health = status['health']
        deps = status['dependencies']

        # Check service health
        if health['status'] != 'healthy':
            print("🚨 Service health issue detected!")

        # Check dependencies
        for dep_name, dep_info in deps['dependencies'].items():
            if dep_info['status'] != 'healthy':
                print(f"🚨 Dependency issue: {dep_name} - {dep_info['message']}")

# Usage
api = HAIngestorAPI()
monitor = HAIngestorMonitor(api, check_interval=30)
monitor.start_monitoring()
```

### **Performance Metrics Dashboard**
```python
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

class PerformanceDashboard:
    def __init__(self, data_access: HAIngestorDataAccess):
        self.data_access = data_access

    def create_performance_chart(self, hours: int = 24):
        """Create performance overview chart"""
        # Get performance data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        performance_data = self.data_access.get_performance_metrics(
            start_time=start_time.isoformat()
        )

        if performance_data.empty:
            print("No performance data available")
            return

        # Create chart
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'HA-Ingestor Performance Overview (Last {hours}h)')

        # Event processing rate
        if 'events_per_second' in performance_data.columns:
            axes[0, 0].plot(performance_data['_time'], performance_data['events_per_second'])
            axes[0, 0].set_title('Events per Second')
            axes[0, 0].set_ylabel('Events/sec')

        # Processing latency
        if 'processing_latency_ms' in performance_data.columns:
            axes[0, 1].plot(performance_data['_time'], performance_data['processing_latency_ms'])
            axes[0, 1].set_title('Processing Latency')
            axes[0, 1].set_ylabel('Latency (ms)')

        # Memory usage
        if 'memory_usage_mb' in performance_data.columns:
            axes[1, 0].plot(performance_data['_time'], performance_data['memory_usage_mb'])
            axes[1, 0].set_title('Memory Usage')
            axes[1, 0].set_ylabel('Memory (MB)')

        # Quality score
        if 'quality_score' in performance_data.columns:
            axes[1, 1].plot(performance_data['_time'], performance_data['quality_score'])
            axes[1, 1].set_title('Data Quality Score')
            axes[1, 1].set_ylabel('Score (0-1)')

        plt.tight_layout()
        plt.show()

# Usage
data_access = HAIngestorDataAccess()
dashboard = PerformanceDashboard(data_access)
dashboard.create_performance_chart(hours=24)
```

## 🚀 **Integration Best Practices**

### **1. Event Quality Validation**
```python
def validate_event_quality(event: Dict[str, Any]) -> bool:
    """Validate event quality before processing"""
    required_fields = ['domain', 'entity_id', 'timestamp', 'event_type']

    # Check required fields
    for field in required_fields:
        if field not in event:
            return False

    # Check validation status
    if event.get('validation_status') != 'validated':
        return False

    # Check quality score
    quality_score = event.get('quality_score', 0)
    if quality_score < 0.8:
        return False

    # Check for duplicates
    if event.get('is_duplicate', False):
        return False

    return True

# Usage in your processing pipeline
def process_events(events: List[Dict[str, Any]]):
    """Process events with quality validation"""
    for event in events:
        if validate_event_quality(event):
            # Process high-quality event
            process_high_quality_event(event)
        else:
            # Handle low-quality event
            handle_low_quality_event(event)
```

### **2. Error Handling & Resilience**
```python
import asyncio
from typing import Optional

class ResilientHAIngestorClient:
    def __init__(self, api: HAIngestorAPI, max_retries: int = 3):
        self.api = api
        self.max_retries = max_retries
        self.circuit_breaker_state = 'CLOSED'
        self.failure_count = 0

    async def get_health_with_retry(self) -> Optional[Dict[str, Any]]:
        """Get health status with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if self.circuit_breaker_state == 'OPEN':
                    # Circuit breaker is open, wait before retry
                    await asyncio.sleep(30)
                    self.circuit_breaker_state = 'HALF_OPEN'

                result = self.api.get_health_status()
                self.failure_count = 0
                self.circuit_breaker_state = 'CLOSED'
                return result

            except Exception as e:
                self.failure_count += 1
                print(f"Health check attempt {attempt + 1} failed: {e}")

                if self.failure_count >= 5:
                    self.circuit_breaker_state = 'OPEN'
                    print("Circuit breaker opened - too many failures")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return None

# Usage
async def monitor_with_resilience():
    api = HAIngestorAPI()
    client = ResilientHAIngestorClient(api)

    while True:
        health = await client.get_health_with_retry()
        if health:
            print(f"Health: {health['status']}")
        else:
            print("Health check failed")

        await asyncio.sleep(30)

# Run monitoring
asyncio.run(monitor_with_resilience())
```

### **3. Configuration Management**
```python
import os
from typing import Dict, Any

class HAIngestorConfig:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'ha_ingestor': {
                'url': os.getenv('HA_INGESTOR_URL', 'http://localhost:8000'),
                'mqtt_broker': os.getenv('HA_INGESTOR_MQTT_BROKER', 'localhost'),
                'mqtt_port': int(os.getenv('HA_INGESTOR_MQTT_PORT', '1883')),
                'influxdb_url': os.getenv('HA_INGESTOR_INFLUXDB_URL', 'http://localhost:8086'),
                'influxdb_token': os.getenv('HA_INGESTOR_INFLUXDB_TOKEN'),
                'influxdb_org': os.getenv('HA_INGESTOR_INFLUXDB_ORG'),
                'influxdb_bucket': os.getenv('HA_INGESTOR_INFLUXDB_BUCKET', 'ha_events')
            },
            'quality': {
                'min_quality_score': float(os.getenv('MIN_QUALITY_SCORE', '0.8')),
                'enable_duplicate_detection': os.getenv('ENABLE_DUPLICATE_DETECTION', 'true').lower() == 'true',
                'validation_timeout': int(os.getenv('VALIDATION_TIMEOUT', '30'))
            },
            'monitoring': {
                'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
                'metrics_collection': os.getenv('METRICS_COLLECTION', 'true').lower() == 'true',
                'alert_threshold': float(os.getenv('ALERT_THRESHOLD', '0.9'))
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

# Usage
config = HAIngestorConfig()

# Access configuration
ha_url = config.get('ha_ingestor.url')
min_quality = config.get('quality.min_quality_score')
check_interval = config.get('monitoring.health_check_interval')

print(f"HA-Ingestor URL: {ha_url}")
print(f"Minimum quality score: {min_quality}")
print(f"Health check interval: {check_interval}s")
```

## 📋 **Integration Checklist**

### **Pre-Integration Setup**
- [ ] **HA-Ingestor v0.3.0** deployed and operational
- [ ] **Health endpoints** responding correctly
- [ ] **Enhanced features** verified and working
- [ ] **Data quality** metrics being collected
- [ ] **Performance monitoring** active

### **Integration Implementation**
- [ ] **Event processing** pipeline configured
- [ ] **Quality validation** logic implemented
- [ ] **Error handling** and resilience added
- [ ] **Monitoring integration** configured
- [ ] **Configuration management** implemented

### **Testing & Validation**
- [ ] **Event quality** validation working
- [ ] **Error scenarios** handled correctly
- [ ] **Performance metrics** being collected
- [ ] **Health monitoring** operational
- [ ] **Integration tests** passing

### **Production Deployment**
- [ ] **Configuration** environment-specific
- [ ] **Error handling** production-ready
- [ ] **Monitoring** alerts configured
- [ ] **Documentation** updated
- [ ] **Team training** completed

## 🎯 **Next Steps**

### **Immediate Actions**
1. **Review integration methods** and choose appropriate approach
2. **Implement basic integration** using provided examples
3. **Test with HA-Ingestor v0.3.0** to verify functionality
4. **Configure monitoring** and alerting

### **Short-term (1-2 weeks)**
1. **Enhance error handling** and resilience
2. **Implement advanced monitoring** and dashboards
3. **Optimize performance** based on metrics
4. **Document integration** patterns and best practices

### **Long-term (1-3 months)**
1. **Scale integration** to handle increased load
2. **Implement advanced analytics** using enhanced data
3. **Add machine learning** capabilities
4. **Create comprehensive** monitoring and alerting

---

## **Support & Resources**

### **Documentation**
- **README.md**: Complete project documentation
- **CHANGELOG.md**: Version history and changes
- **API Reference**: Endpoint documentation
- **Configuration Guide**: Setup and tuning

### **Examples & Code**
- **Integration examples** in this guide
- **Sample applications** in the examples directory
- **Test cases** for validation and testing
- **Configuration templates** for common scenarios

### **Community & Support**
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Documentation**: Comprehensive guides and references
- **Examples**: Real-world integration examples

---

**HA-Ingestor v0.3.0 provides a robust foundation for building advanced Home Assistant analytics and automation systems. By following this integration guide, you can leverage the enhanced data collection, quality validation, and monitoring capabilities to create powerful, production-ready applications.**

**For additional support or questions, please refer to the documentation or create an issue on GitHub.**
