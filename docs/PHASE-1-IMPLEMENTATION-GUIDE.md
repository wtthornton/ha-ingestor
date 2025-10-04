# 🛠️ Phase 1 Implementation Guide: Critical Infrastructure Stabilization

## 📋 Overview

This guide provides detailed implementation instructions for **Phase 1: Critical Infrastructure Stabilization** of the HA Ingestor stabilization plan. Phase 1 focuses on implementing comprehensive logging, centralized log aggregation, and performance metrics collection.

**Phase Duration**: 5-7 days  
**Priority**: P0 - CRITICAL  
**Risk Level**: LOW (foundation exists)  
**Dependencies**: None

---

## 🎯 Phase 1 Objectives

1. **Enhanced Logging Framework** - Implement structured logging across all services
2. **Centralized Log Aggregation** - Set up ELK stack for log collection and analysis
3. **Performance Metrics Collection** - Implement comprehensive metrics collection and storage

---

## 📊 Implementation Roadmap

### Day 1-2: Enhanced Logging Framework (Story 6.1)

**Objective**: Implement structured logging with correlation IDs across all services

#### Task 1: Enhanced Logging Configuration
```bash
# Files to modify:
- shared/logging_config.py
- shared/correlation_middleware.py (new)
- shared/log_validator.py (new)
```

**Implementation Steps:**
1. **Enhance shared logging configuration**
   ```python
   # shared/logging_config.py
   import json
   import logging
   import time
   from datetime import datetime
   from typing import Dict, Any, Optional
   import uuid
   
   class StructuredLogger:
       def __init__(self, service_name: str):
           self.service_name = service_name
           self.logger = logging.getLogger(service_name)
           
       def log(self, level: str, message: str, correlation_id: str = None, 
               context: Dict[str, Any] = None, performance: Dict[str, float] = None):
           log_entry = {
               "timestamp": datetime.utcnow().isoformat() + "Z",
               "level": level.upper(),
               "service": self.service_name,
               "message": message,
               "correlation_id": correlation_id or str(uuid.uuid4()),
               "context": context or {},
               "performance": performance or {}
           }
           self.logger.log(getattr(logging, level.upper()), json.dumps(log_entry))
   ```

2. **Create correlation ID middleware**
   ```python
   # shared/correlation_middleware.py
   import uuid
   from typing import Optional
   import asyncio
   
   class CorrelationContext:
       def __init__(self):
           self._context = asyncio.local()
           
       def set_correlation_id(self, correlation_id: str):
           self._context.correlation_id = correlation_id
           
       def get_correlation_id(self) -> Optional[str]:
           return getattr(self._context, 'correlation_id', None)
           
       def generate_correlation_id(self) -> str:
           correlation_id = f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"
           self.set_correlation_id(correlation_id)
           return correlation_id
   
   correlation_context = CorrelationContext()
   ```

3. **Create log validation framework**
   ```python
   # shared/log_validator.py
   import json
   from typing import Dict, Any
   
   class LogValidator:
       REQUIRED_FIELDS = ["timestamp", "level", "service", "message", "correlation_id"]
       
       @staticmethod
       def validate_log_entry(log_entry: Dict[str, Any]) -> bool:
           for field in LogValidator.REQUIRED_FIELDS:
               if field not in log_entry:
                   return False
           return True
   ```

#### Task 2: Service Logging Implementation
**Services to update:**
- `services/websocket-ingestion/src/main.py`
- `services/enrichment-pipeline/src/main.py`
- `services/data-retention/src/main.py`
- `services/admin-api/src/main.py`
- `services/health-dashboard/src/main.py`
- `services/weather-api/src/main.py`

**Implementation for each service:**
```python
# Example for websocket-ingestion service
from shared.logging_config import StructuredLogger
from shared.correlation_middleware import correlation_context

logger = StructuredLogger("websocket-ingestion")

async def process_event(event_data):
    correlation_id = correlation_context.get_correlation_id()
    start_time = time.time()
    
    try:
        # Process event
        result = await process_home_assistant_event(event_data)
        
        duration_ms = (time.time() - start_time) * 1000
        logger.log("INFO", "Event processed successfully", 
                  correlation_id=correlation_id,
                  context={"event_id": event_data.get("id"), 
                          "entity_id": event_data.get("entity_id")},
                  performance={"duration_ms": duration_ms})
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.log("ERROR", f"Error processing event: {str(e)}", 
                  correlation_id=correlation_id,
                  context={"event_id": event_data.get("id"), 
                          "error_type": type(e).__name__},
                  performance={"duration_ms": duration_ms})
        raise
```

#### Task 3: Performance Logging Enhancement
```python
# shared/performance_monitor.py
import time
import functools
from typing import Callable, Any

def monitor_performance(operation_name: str):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            correlation_id = correlation_context.get_correlation_id()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log("INFO", f"{operation_name} completed", 
                          correlation_id=correlation_id,
                          performance={"duration_ms": duration_ms, 
                                     "operation": operation_name})
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log("ERROR", f"{operation_name} failed: {str(e)}", 
                          correlation_id=correlation_id,
                          context={"error_type": type(e).__name__},
                          performance={"duration_ms": duration_ms, 
                                     "operation": operation_name})
                raise
                
        return async_wrapper
    return decorator
```

### Day 3-4: Centralized Log Aggregation (Story 6.2)

**Objective**: Set up ELK stack for centralized log collection and analysis

#### Task 1: ELK Stack Setup
```yaml
# docker-compose.yml additions
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: ha-ingestor-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - ha-ingestor-network

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: ha-ingestor-logstash
    volumes:
      - ./infrastructure/logstash/pipeline:/usr/share/logstash/pipeline
      - ./infrastructure/logstash/config:/usr/share/logstash/config
    ports:
      - "5044:5044"
      - "5000:5000/tcp"
      - "5000:5000/udp"
      - "9600:9600"
    environment:
      LS_JAVA_OPTS: "-Xmx256m -Xms256m"
    depends_on:
      - elasticsearch
    networks:
      - ha-ingestor-network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: ha-ingestor-kibana
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch
    networks:
      - ha-ingestor-network

volumes:
  elasticsearch_data:

networks:
  ha-ingestor-network:
    external: true
```

#### Task 2: Logstash Configuration
```ruby
# infrastructure/logstash/pipeline/logstash.conf
input {
  tcp {
    port => 5000
    codec => json_lines
  }
  
  udp {
    port => 5000
    codec => json_lines
  }
}

filter {
  if [service] {
    mutate {
      add_tag => [ "ha-ingestor" ]
    }
  }
  
  date {
    match => [ "timestamp", "ISO8601" ]
  }
  
  mutate {
    convert => { "performance.duration_ms" => "float" }
    convert => { "performance.memory_usage_mb" => "float" }
    convert => { "performance.cpu_usage_percent" => "float" }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "ha-ingestor-logs-%{+YYYY.MM.dd}"
  }
  
  stdout {
    codec => rubydebug
  }
}
```

#### Task 3: Docker Log Driver Configuration
```yaml
# Update each service in docker-compose.yml
services:
  websocket-ingestion:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
        labels: "service=websocket-ingestion,environment=production"
    
  enrichment-pipeline:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
        labels: "service=enrichment-pipeline,environment=production"
    
  # ... repeat for all services
```

#### Task 4: Log Collection Script
```python
# scripts/log-collector.py
import json
import socket
import time
import logging
from pathlib import Path

class LogCollector:
    def __init__(self, logstash_host="localhost", logstash_port=5000):
        self.logstash_host = logstash_host
        self.logstash_port = logstash_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((logstash_host, logstash_port))
        
    def send_log(self, log_entry: dict):
        try:
            self.socket.send((json.dumps(log_entry) + "\n").encode())
        except Exception as e:
            print(f"Error sending log to Logstash: {e}")
            
    def close(self):
        self.socket.close()

# Integration with existing logging
from shared.logging_config import StructuredLogger
log_collector = LogCollector()

class AggregatedLogger(StructuredLogger):
    def log(self, level: str, message: str, **kwargs):
        # Log to both local and centralized system
        super().log(level, message, **kwargs)
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "service": self.service_name,
            "message": message,
            **kwargs
        }
        log_collector.send_log(log_entry)
```

### Day 5-6: Performance Metrics Collection (Story 6.3)

**Objective**: Implement comprehensive performance metrics collection and storage

#### Task 1: Metrics Collection Framework
```python
# shared/metrics_collector.py
import time
import asyncio
from typing import Dict, Any, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class MetricsCollector:
    def __init__(self, service_name: str, influxdb_client: InfluxDBClient):
        self.service_name = service_name
        self.influxdb_client = influxdb_client
        self.write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        self.bucket = "ha-ingestor-metrics"
        self.org = "ha-ingestor"
        
    def record_timing(self, operation: str, duration_ms: float, tags: Dict[str, str] = None):
        point = Point("service_performance") \
            .tag("service", self.service_name) \
            .tag("operation", operation) \
            .tag("status", tags.get("status", "success") if tags else "success") \
            .field("duration_ms", duration_ms) \
            .field("timestamp", int(time.time()))
            
        if tags:
            for key, value in tags.items():
                point.tag(key, value)
                
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        
    def record_counter(self, metric_name: str, value: int, tags: Dict[str, str] = None):
        point = Point("service_counters") \
            .tag("service", self.service_name) \
            .tag("metric", metric_name) \
            .field("value", value) \
            .field("timestamp", int(time.time()))
            
        if tags:
            for key, value in tags.items():
                point.tag(key, value)
                
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        
    def record_gauge(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        point = Point("service_gauges") \
            .tag("service", self.service_name) \
            .tag("metric", metric_name) \
            .field("value", value) \
            .field("timestamp", int(time.time()))
            
        if tags:
            for key, value in tags.items():
                point.tag(key, value)
                
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
```

#### Task 2: System Resource Monitoring
```python
# shared/system_metrics.py
import psutil
import asyncio
from typing import Dict, Any

class SystemMetricsCollector:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        
    async def collect_system_metrics(self):
        while True:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics_collector.record_gauge("cpu_usage_percent", cpu_percent)
                
                # Memory metrics
                memory = psutil.virtual_memory()
                self.metrics_collector.record_gauge("memory_usage_percent", memory.percent)
                self.metrics_collector.record_gauge("memory_usage_mb", memory.used / 1024 / 1024)
                
                # Disk metrics
                disk = psutil.disk_usage('/')
                self.metrics_collector.record_gauge("disk_usage_percent", 
                                                  (disk.used / disk.total) * 100)
                self.metrics_collector.record_gauge("disk_free_gb", disk.free / 1024 / 1024 / 1024)
                
                # Network metrics
                network = psutil.net_io_counters()
                self.metrics_collector.record_gauge("network_bytes_sent", network.bytes_sent)
                self.metrics_collector.record_gauge("network_bytes_recv", network.bytes_recv)
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)  # Wait longer on error
```

#### Task 3: Service Integration
```python
# services/websocket-ingestion/src/main.py
from shared.metrics_collector import MetricsCollector
from shared.system_metrics import SystemMetricsCollector
from influxdb_client import InfluxDBClient

# Initialize metrics collection
influxdb_client = InfluxDBClient(
    url="http://influxdb:8086",
    token="your-token-here",
    org="ha-ingestor"
)

metrics_collector = MetricsCollector("websocket-ingestion", influxdb_client)
system_metrics = SystemMetricsCollector(metrics_collector)

# Start system metrics collection
asyncio.create_task(system_metrics.collect_system_metrics())

# Example usage in service operations
async def process_home_assistant_event(event_data):
    start_time = time.time()
    
    try:
        # Process event
        result = await process_event_data(event_data)
        
        # Record success metrics
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_timing("process_event", duration_ms, 
                                      {"status": "success", "event_type": "state_changed"})
        metrics_collector.record_counter("events_processed", 1)
        
        return result
        
    except Exception as e:
        # Record error metrics
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_timing("process_event", duration_ms, 
                                      {"status": "error", "error_type": type(e).__name__})
        metrics_collector.record_counter("events_failed", 1)
        raise
```

### Day 7: Integration Testing and Documentation

#### Task 1: Integration Testing
```python
# tests/integration/test_logging_metrics.py
import pytest
import asyncio
import json
from shared.logging_config import StructuredLogger
from shared.metrics_collector import MetricsCollector

@pytest.mark.asyncio
async def test_structured_logging():
    logger = StructuredLogger("test-service")
    correlation_id = "test-correlation-123"
    
    logger.log("INFO", "Test message", 
              correlation_id=correlation_id,
              context={"test_key": "test_value"})
    
    # Verify log format and content
    # This would check log files or captured logs
    
@pytest.mark.asyncio
async def test_metrics_collection():
    # Test metrics collection functionality
    pass

@pytest.mark.asyncio
async def test_log_aggregation():
    # Test log aggregation and search
    pass
```

#### Task 2: Performance Testing
```python
# tests/performance/test_logging_overhead.py
import time
import asyncio
from shared.logging_config import StructuredLogger

@pytest.mark.asyncio
async def test_logging_performance_overhead():
    logger = StructuredLogger("performance-test")
    
    # Test logging overhead
    start_time = time.time()
    
    for i in range(1000):
        logger.log("INFO", f"Performance test message {i}")
    
    duration = time.time() - start_time
    avg_duration_ms = (duration / 1000) * 1000
    
    # Assert logging overhead is acceptable (< 1ms per log entry)
    assert avg_duration_ms < 1.0, f"Logging overhead too high: {avg_duration_ms}ms"
```

#### Task 3: Documentation Updates
- Update `docs/architecture/logging-architecture.md`
- Create `docs/operations/logging-operations.md`
- Update `docs/DEVELOPMENT.md` with logging setup instructions
- Create `docs/troubleshooting/logging-troubleshooting.md`

---

## 🧪 Testing Strategy

### Unit Tests
- Log format validation
- Correlation ID generation and propagation
- Metrics collection accuracy
- Performance monitoring decorators

### Integration Tests
- End-to-end logging flow
- Log aggregation functionality
- Metrics storage and retrieval
- Service-to-service correlation tracking

### Performance Tests
- Logging overhead measurement
- High-volume log processing
- Metrics collection performance
- System resource impact

### Security Tests
- Log data sanitization
- Access control validation
- Secure log transmission
- Audit logging verification

---

## 📊 Success Criteria

### Technical Success Criteria
- [ ] All services logging in structured JSON format
- [ ] Correlation IDs propagating across all services
- [ ] ELK stack operational and collecting logs
- [ ] Performance metrics being collected and stored
- [ ] Log search and analysis functional
- [ ] Logging overhead < 5% performance impact

### Operational Success Criteria
- [ ] Centralized log dashboard accessible
- [ ] Real-time log streaming operational
- [ ] Log retention policies implemented
- [ ] Performance metrics API functional
- [ ] Documentation complete and current

---

## 🚨 Troubleshooting Guide

### Common Issues

#### Logs Not Appearing in Kibana
1. Check Elasticsearch cluster health
2. Verify Logstash pipeline configuration
3. Check log format compatibility
4. Verify network connectivity between services

#### High Logging Overhead
1. Enable asynchronous logging
2. Implement log buffering
3. Optimize JSON serialization
4. Review log levels and filtering

#### Metrics Collection Issues
1. Verify InfluxDB connectivity
2. Check metrics schema consistency
3. Validate timestamp formats
4. Review retention policies

#### Correlation ID Issues
1. Verify middleware installation
2. Check service-to-service communication
3. Validate correlation ID format
4. Review request tracing

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] All logging configurations tested
- [ ] ELK stack infrastructure ready
- [ ] InfluxDB metrics schema configured
- [ ] Environment variables set
- [ ] Docker images built and tested

### Deployment
- [ ] Deploy ELK stack services
- [ ] Update service configurations
- [ ] Deploy enhanced logging framework
- [ ] Deploy metrics collection
- [ ] Verify service connectivity

### Post-Deployment
- [ ] Verify log aggregation working
- [ ] Check metrics collection
- [ ] Test log search functionality
- [ ] Validate performance impact
- [ ] Monitor system health

---

## 📚 References

### Documentation
- [Story 6.1: Enhanced Logging Framework](docs/stories/6.1.enhanced-logging-framework.md)
- [Story 6.2: Centralized Log Aggregation](docs/stories/6.2.centralized-log-aggregation.md)
- [Story 6.3: Performance Metrics Collection](docs/stories/6.3.performance-metrics-collection.md)
- [Epic 6: Critical Infrastructure Stabilization](docs/prd/epic-6-critical-infrastructure-stabilization.md)

### External Resources
- [ELK Stack Documentation](https://www.elastic.co/guide/)
- [InfluxDB Python Client](https://influxdb-client.readthedocs.io/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)

---

**Implementation Guide Status**: Complete  
**Last Updated**: January 4, 2025  
**Next Review**: January 11, 2025  
**Owner**: BMad Master  
**Implementation Team**: Development Team
