# ha-ingestor Project Context

## 🏗️ Architecture Overview

### High-Level Design
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Home Assistant│    │   ha-ingestor    │    │    InfluxDB     │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │   MQTT      │◄────┤ │   MQTT       │ │    │ │             │ │
│ │   Broker    │ │    │ │   Client     │ │    │ │             │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │             │ │
│                 │    │                  │    │ │             │ │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ │             │ │
│ │ WebSocket   │◄────┤ │  WebSocket   │ │    │ │             │ │
│ │   API       │ │    │ │   Client     │ │    │ │             │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │             │ │
└─────────────────┘    │                  │    │ │             │ │
                       │ ┌──────────────┐ │    │ │             │ │
                       │ │   Pipeline   │ │    │ │             │ │
                       │ │   Engine     │ │    │ │             │ │
                       │ └──────────────┘ │    │ │             │ │
                       │                  │    │ │             │ │
                       │ ┌──────────────┐ │    │ │             │ │
                       │ │  InfluxDB   │◄─────┘ │             │ │
                       │ │   Writer    │ │      │             │ │
                       │ └──────────────┘ │      │             │ │
                       └──────────────────┘      └─────────────┘
```

### Core Components

#### 1. **Ingestion Layer** (`mqtt/` & `websocket/`)
- **MQTT Client**: Connects to Home Assistant MQTT broker
- **WebSocket Client**: Connects to Home Assistant WebSocket API
- **Event Parsing**: Converts raw events to structured data models

#### 2. **Processing Pipeline** (`pipeline.py`)
- **Filter System**: Domain, entity, attribute, and time-based filtering
- **Transformation Engine**: Field mapping, type conversion, data enrichment
- **Batching**: Optimizes InfluxDB writes with configurable batch sizes

#### 3. **Data Models** (`models/`)
- **Event Models**: MQTT and WebSocket event representations
- **InfluxDB Points**: Optimized data structures for time-series storage
- **Schema Optimization**: Efficient tag and field organization

#### 4. **Storage Layer** (`influxdb/`)
- **Writer**: Handles InfluxDB operations with retry logic
- **Retention Policies**: Configurable data lifecycle management
- **Connection Pooling**: Optimized database connections

#### 5. **Monitoring & Observability** (`monitoring/`, `metrics/`, `health/`)
- **Health Checks**: Service dependency monitoring
- **Metrics Collection**: Prometheus-compatible metrics
- **Performance Monitoring**: Filter execution timing and throughput

## 🔧 Key Design Patterns

### 1. **Async-First Architecture**
- All I/O operations use `asyncio`
- Non-blocking event processing
- Efficient resource utilization

### 2. **Pipeline Pattern**
- Modular processing stages
- Configurable filter chains
- Pluggable transformations

### 3. **Factory Pattern**
- Dynamic filter creation
- Configurable transformer instantiation
- Runtime component assembly

### 4. **Observer Pattern**
- Event-driven processing
- Loose coupling between components
- Extensible event handling

### 5. **Strategy Pattern**
- Pluggable filter implementations
- Configurable transformation strategies
- Runtime algorithm selection

## 📊 Data Flow

### 1. **Event Ingestion**
```
Home Assistant Event → MQTT/WebSocket Client → Event Parser → Event Model
```

### 2. **Processing Pipeline**
```
Event Model → Filter Chain → Transformation Engine → InfluxDB Point
```

### 3. **Storage**
```
InfluxDB Point → Batch Buffer → InfluxDB Writer → InfluxDB
```

### 4. **Monitoring**
```
All Components → Metrics Collector → Prometheus Export → Grafana Dashboards
```

## 🎯 Common Development Tasks

### Adding New Filters
1. Create filter class in `filters/` directory
2. Inherit from `BaseFilter`
3. Implement `filter()` method
4. Add to filter registry
5. Update configuration schema

### Adding New Transformers
1. Create transformer class in `transformers/` directory
2. Inherit from `BaseTransformer`
3. Implement `transform()` method
4. Add to transformer registry
5. Update configuration schema

### Modifying Data Models
1. Update models in `models/` directory
2. Ensure Pydantic validation
3. Update InfluxDB schema if needed
4. Run migration scripts
5. Update tests

### Adding New Metrics
1. Define metric in `metrics/` directory
2. Add to Prometheus registry
3. Update Grafana dashboards
4. Add monitoring alerts

## 🚨 Common Issues & Solutions

### 1. **Connection Failures**
- Check network connectivity
- Verify credentials in environment
- Check service availability
- Review connection logs

### 2. **Performance Issues**
- Monitor filter execution times
- Check InfluxDB write performance
- Review batch sizes and timing
- Analyze memory usage

### 3. **Data Loss**
- Verify filter configurations
- Check transformation logic
- Monitor InfluxDB write success
- Review error logs

### 4. **Configuration Errors**
- Validate environment variables
- Check configuration file syntax
- Verify required dependencies
- Review startup logs

## 🔍 Debugging & Troubleshooting

### 1. **Enable Debug Logging**
```bash
LOG_LEVEL=DEBUG poetry run python -m ha_ingestor.main
```

### 2. **Check Health Endpoints**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

### 3. **Monitor Metrics**
```bash
curl http://localhost:8000/metrics
```

### 4. **Review Logs**
```bash
tail -f logs/ha-ingestor.log
```

## 📚 Related Documentation
- `README.md`: Quick start and basic usage
- `DEVELOPMENT.md`: Development setup and guidelines
- `DEPLOYMENT.md`: Production deployment instructions
- `CONTRIBUTING.md`: Contribution guidelines
- `.agent-os/`: Context7 development standards
