# ha-ingestor Project Overview

## 🎯 **Project Purpose**
**ha-ingestor** is a production-grade Python service that ingests Home Assistant activity data in real-time and writes it to InfluxDB with advanced filtering, transformation, and monitoring capabilities.

## 🏗️ **Core Architecture**

### **Data Flow Pipeline**
```
Home Assistant → MQTT/WebSocket → ha-ingestor → Filters → Transformers → InfluxDB
     ↓              ↓              ↓           ↓         ↓           ↓
  Events      Raw Messages   Event Models  Filtered   Transformed  Time-Series
```

### **Key Components**
1. **Ingestion Layer**: MQTT and WebSocket clients for Home Assistant
2. **Processing Pipeline**: Configurable filters and transformers
3. **Storage Layer**: InfluxDB writer with batching and retry logic
4. **Monitoring**: Health checks, metrics, and observability
5. **Configuration**: Environment-based settings with Pydantic validation

## 📁 **Project Structure**

### **Core Application (`ha_ingestor/`)**
```
ha_ingestor/
├── main.py                 # Application entry point
├── config.py              # Configuration management
├── pipeline.py            # Main processing pipeline
├── mqtt/                  # MQTT client and topic patterns
├── websocket/             # WebSocket client for HA API
├── filters/               # Event filtering system
├── transformers/          # Data transformation engine
├── models/                # Data models and schemas
├── influxdb/              # InfluxDB operations
├── monitoring/            # Health checks and metrics
├── health/                # Health monitoring system
├── metrics/               # Prometheus metrics collection
├── retention/             # Data retention policies
├── alerting/              # Alerting and notification system
├── dashboards/            # Operational dashboards
├── migration/             # Database migration scripts
└── utils/                 # Utility functions and helpers
```

### **Configuration & Examples**
```
├── .cursorrules           # AI Assistant coding standards
├── PROJECT_CONTEXT.md     # Detailed architecture context
├── AI_ASSISTANT_GUIDE.md  # Quick reference for AI assistants
├── TROUBLESHOOTING_GUIDE.md # Common issues and solutions
├── config-examples/       # Configuration templates
│   ├── mqtt-config-examples.yaml
│   └── influxdb-schema-examples.yaml
└── examples/              # Implementation examples
    └── common_patterns_demo.py
```

### **Testing & Development**
```
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── test_*.py         # Integration tests
├── pyproject.toml         # Dependencies and project config
├── pytest.ini            # Test configuration
└── .agent-os/            # Context7 development standards
```

## 🔧 **Technology Stack**

### **Core Technologies**
- **Python 3.12+**: Async-first architecture with asyncio
- **FastAPI**: HTTP endpoints and health checks
- **paho-mqtt**: MQTT client functionality
- **websockets**: WebSocket client for Home Assistant
- **influxdb-client**: InfluxDB operations and batching

### **Data Processing**
- **Pydantic**: Data validation and settings management
- **structlog**: Structured logging with correlation tracking
- **tenacity**: Retry logic and circuit breaker patterns

### **Monitoring & Observability**
- **prometheus-client**: Metrics collection and export
- **psutil**: System resource monitoring
- **aiohttp**: Async HTTP client for external services

### **Development Tools**
- **Poetry**: Dependency management
- **Black**: Code formatting (88 char line length)
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking
- **pytest**: Testing framework with async support

## 🚀 **Quick Start Commands**

### **Development Setup**
```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest tests/ -v

# Start service
poetry run python -m ha_ingestor.main

# Check health
curl http://localhost:8000/health
```

### **Code Quality**
```bash
# Format code
poetry run black ha_ingestor/ tests/

# Lint code
poetry run ruff check ha_ingestor/ tests/

# Type check
poetry run mypy ha_ingestor/
```

## 📊 **Key Features**

### **Data Ingestion**
- **Real-time MQTT**: Subscribe to Home Assistant MQTT topics
- **WebSocket API**: Connect to Home Assistant WebSocket API
- **Event Parsing**: Convert raw events to structured data models
- **Connection Management**: Automatic reconnection and error handling

### **Data Processing**
- **Configurable Filters**: Domain, entity, attribute, and time-based filtering
- **Transformation Pipeline**: Field mapping, type conversion, data enrichment
- **Batch Processing**: Optimized InfluxDB writes with configurable batch sizes
- **Error Handling**: Comprehensive error handling with retry logic

### **Data Storage**
- **InfluxDB Integration**: Optimized time-series data storage
- **Schema Optimization**: Efficient tag and field organization
- **Retention Policies**: Configurable data lifecycle management
- **Connection Pooling**: Optimized database connections

### **Monitoring & Observability**
- **Health Checks**: Service dependency monitoring
- **Metrics Collection**: Prometheus-compatible metrics export
- **Performance Monitoring**: Filter execution timing and throughput
- **Structured Logging**: Correlation tracking and context management

## 🎯 **Common Use Cases**

### **1. Home Automation Monitoring**
- Track sensor values over time
- Monitor device states and changes
- Analyze automation triggers and responses

### **2. Energy Management**
- Monitor power consumption
- Track energy usage patterns
- Analyze cost implications

### **3. Environmental Monitoring**
- Temperature and humidity tracking
- Air quality monitoring
- Climate system performance

### **4. Security & Access Control**
- Motion sensor activity
- Door/window state changes
- User access patterns

## 🔍 **Configuration Examples**

### **Environment Variables**
```bash
# Home Assistant
HA_WEBSOCKET_URL=http://192.168.1.86:8123/api/websocket
HA_WEBSOCKET_TOKEN=your_long_lived_access_token

# MQTT
MQTT_BROKER=192.168.1.86
MQTT_PORT=1883
MQTT_USERNAME=mqtt_user
MQTT_PASSWORD=mqtt_password

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=home_assistant
```

### **Filter Configuration**
```yaml
filters:
  domain_filter:
    enabled: true
    include_domains: ["sensor", "binary_sensor", "switch"]
    exclude_domains: ["device_tracker"]

  entity_filter:
    enabled: true
    include_entities: ["sensor.temperature_living_room"]
    exclude_entities: ["sensor.test_sensor"]
```

## 🚨 **Troubleshooting Quick Reference**

### **Common Issues**
1. **Connection Failures**: Check network connectivity and credentials
2. **Data Not Appearing**: Verify filter configurations and InfluxDB permissions
3. **High Memory Usage**: Reduce batch sizes and optimize filters
4. **Performance Issues**: Monitor metrics and optimize transformation logic

### **Debug Commands**
```bash
# Enable debug logging
LOG_LEVEL=DEBUG poetry run python -m ha_ingestor.main

# Check service health
curl http://localhost:8000/health/detailed

# View metrics
curl http://localhost:8000/metrics

# Check logs
tail -f logs/ha-ingestor.log
```

## 📚 **Documentation Index**

- **`.cursorrules`**: AI Assistant coding standards
- **`PROJECT_CONTEXT.md`**: Detailed architecture and design patterns
- **`AI_ASSISTANT_GUIDE.md`**: Quick reference for AI assistants
- **`TROUBLESHOOTING_GUIDE.md`**: Common issues and solutions
- **`README.md`**: Quick start and basic usage
- **`DEVELOPMENT.md`**: Development setup and guidelines
- **`DEPLOYMENT.md`**: Production deployment instructions

## 🔗 **External Resources**

- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- [InfluxDB Documentation](https://docs.influxdata.com/)
- [MQTT Documentation](https://mqtt.org/documentation)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Context7 Development Standards](https://buildermethods.com/agent-os)

## 💡 **AI Assistant Tips**

1. **Always check existing patterns** in `examples/common_patterns_demo.py`
2. **Reference configuration examples** in `config-examples/` directory
3. **Use established naming conventions** from the codebase
4. **Follow async-first patterns** for all I/O operations
5. **Implement proper error handling** with custom exceptions
6. **Add comprehensive docstrings** for public APIs
7. **Use type hints consistently** throughout the codebase
8. **Reference the troubleshooting guide** for common issues
9. **Check Context7 standards** in `.agent-os/` directory
10. **Maintain test coverage** when adding new functionality
