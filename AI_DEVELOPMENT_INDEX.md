# ha-ingestor AI Development Index

## 🎯 **Quick Navigation for AI Assistants**

This index provides AI assistants with immediate access to all key files, patterns, and implementation details in the ha-ingestor project.

## 📚 **Documentation Files (Read First)**

### **Essential Context Files**
- **`PROJECT_OVERVIEW.md`** - Complete project overview and architecture
- **`PROJECT_CONTEXT.md`** - Detailed architecture and design patterns  
- **`DEVELOPMENT_PATTERNS.md`** - Established coding patterns and best practices
- **`AI_ASSISTANT_GUIDE.md`** - Quick reference with code templates
- **`TROUBLESHOOTING_GUIDE.md`** - Common issues and solutions

### **Configuration & Examples**
- **`config-examples/mqtt-config-examples.yaml`** - MQTT configuration templates
- **`config-examples/influxdb-schema-examples.yaml`** - Database schema examples
- **`examples/common_patterns_demo.py`** - Implementation pattern examples

## 🏗️ **Core Application Files**

### **Main Entry Points**
- **`ha_ingestor/main.py`** - Main application entry point and orchestration
- **`ha_ingestor/pipeline.py`** - Core event processing pipeline
- **`ha_ingestor/config.py`** - Configuration management and validation

### **Data Models**
- **`ha_ingestor/models/events.py`** - Event data models (MQTT, WebSocket)
- **`ha_ingestor/models/influxdb_point.py`** - InfluxDB data point models
- **`ha_ingestor/models/optimized_schema.py`** - Optimized database schemas

### **Ingestion Layer**
- **`ha_ingestor/mqtt/client.py`** - MQTT client implementation
- **`ha_ingestor/mqtt/topic_patterns.py`** - MQTT topic pattern definitions
- **`ha_ingestor/websocket/client.py`** - WebSocket client implementation

### **Processing Pipeline**
- **`ha_ingestor/filters/base.py`** - Base filter classes and infrastructure
- **`ha_ingestor/filters/domain_filter.py`** - Domain-based filtering
- **`ha_ingestor/filters/entity_filter.py`** - Entity-based filtering
- **`ha_ingestor/filters/attribute_filter.py`** - Attribute-based filtering
- **`ha_ingestor/filters/time_filter.py`** - Time-based filtering
- **`ha_ingestor/filters/performance.py`** - Performance monitoring filters

- **`ha_ingestor/transformers/base.py`** - Base transformer classes
- **`ha_ingestor/transformers/field_mapper.py`** - Field mapping transformations
- **`ha_ingestor/transformers/type_converter.py`** - Type conversion transformations
- **`ha_ingestor/transformers/custom_transformer.py`** - Custom function transformations
- **`ha_ingestor/transformers/rule_engine.py`** - Rule-based transformation engine
- **`ha_ingestor/transformers/schema_transformer.py`** - Schema transformation logic

### **Storage Layer**
- **`ha_ingestor/influxdb/writer.py`** - InfluxDB write operations
- **`ha_ingestor/influxdb/retention_policies.py`** - Data retention management

### **Monitoring & Observability**
- **`ha_ingestor/health/checks.py`** - Health check implementations
- **`ha_ingestor/health/server.py`** - Health monitoring server
- **`ha_ingestor/metrics/collector.py`** - Metrics collection system
- **`ha_ingestor/metrics/prometheus_collector.py`** - Prometheus metrics export
- **`ha_ingestor/monitoring/connection_monitor.py`** - Connection monitoring
- **`ha_ingestor/monitoring/performance_monitor.py`** - Performance monitoring

### **Utilities & Helpers**
- **`ha_ingestor/utils/logging.py`** - Structured logging setup
- **`ha_ingestor/utils/error_handling.py`** - Error handling utilities
- **`ha_ingestor/utils/retry.py`** - Retry logic implementations

## 🔧 **Development & Testing Files**

### **Project Configuration**
- **`pyproject.toml`** - Dependencies and project configuration
- **`pytest.ini`** - Test configuration
- **`.cursorrules`** - AI Assistant coding standards

### **Testing**
- **`tests/`** - Test suite directory
- **`tests/unit/`** - Unit tests
- **`tests/test_integration.py`** - Integration tests
- **`tests/conftest.py`** - Test fixtures and configuration

### **Examples & Demos**
- **`examples/`** - Implementation examples
- **`test_*.py`** - Various test scripts and utilities

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

## 🎯 **Common Development Tasks**

### **Adding New Filters**
1. **File**: Create new file in `ha_ingestor/filters/`
2. **Pattern**: Inherit from `BaseFilter` in `ha_ingestor/filters/base.py`
3. **Example**: See `ha_ingestor/filters/domain_filter.py`
4. **Registration**: Add to filter registry in pipeline

### **Adding New Transformers**
1. **File**: Create new file in `ha_ingestor/transformers/`
2. **Pattern**: Inherit from `Transformer` in `ha_ingestor/transformers/base.py`
3. **Example**: See `ha_ingestor/transformers/field_mapper.py`
4. **Registration**: Add to transformer registry in pipeline

### **Adding New Data Models**
1. **File**: Create new file in `ha_ingestor/models/`
2. **Pattern**: Use Pydantic BaseModel with proper validation
3. **Example**: See `ha_ingestor/models/events.py`
4. **Integration**: Update pipeline to handle new model types

### **Adding New Configuration Options**
1. **File**: Modify `ha_ingestor/config.py`
2. **Pattern**: Add new fields to Settings class with validation
3. **Example**: See existing configuration fields in the file
4. **Usage**: Access via `get_settings()` function

### **Adding New Metrics**
1. **File**: Modify `ha_ingestor/metrics/collector.py`
2. **Pattern**: Use Prometheus client metrics
3. **Example**: See existing metric definitions
4. **Collection**: Update relevant components to record metrics

## 🔍 **Key Implementation Patterns**

### **Async-First Architecture**
- All I/O operations use `asyncio` and async/await
- Never use blocking operations in async context
- Use `asyncio.gather()` for concurrent operations

### **Pipeline Pattern**
- Data flows through configurable stages
- Each stage has single responsibility
- Stages are pluggable and configurable

### **Factory Pattern**
- Dynamic component creation based on configuration
- Centralized instantiation logic
- Easy to extend with new component types

### **Configuration Management**
- Use Pydantic for all configuration models
- Environment variable overrides with validation
- Sensible defaults and clear descriptions

### **Error Handling**
- Custom exception hierarchy
- Retry logic with exponential backoff
- Comprehensive error logging and context

### **Logging & Monitoring**
- Structured logging with structlog
- Prometheus metrics collection
- Health checks and performance monitoring

## 🚨 **Common Issues & Quick Fixes**

### **Import Errors**
- Check `__init__.py` files in package directories
- Ensure all modules are properly exported
- Verify import paths and package structure

### **Configuration Errors**
- Check environment variables and Pydantic models
- Use `Settings().model_dump()` to debug configuration
- Verify required fields and validation rules

### **Async/Await Errors**
- Ensure all async functions are properly awaited
- Use `pytest-asyncio` for testing async code
- Check for blocking operations in async context

### **Performance Issues**
- Monitor filter execution times
- Check batch sizes and timeouts
- Use performance monitoring tools

## 📊 **Monitoring & Debugging**

### **Health Endpoints**
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed

# Metrics endpoint
curl http://localhost:8000/metrics
```

### **Logging**
```bash
# Enable debug logging
LOG_LEVEL=DEBUG poetry run python -m ha_ingestor.main

# View logs
tail -f logs/ha-ingestor.log
```

### **Testing**
```bash
# Run specific test file
poetry run pytest tests/test_filters.py -v

# Run with coverage
poetry run pytest tests/ --cov=ha_ingestor --cov-report=html
```

## 💡 **Pro Tips for AI Assistants**

1. **Always check existing patterns** before creating new implementations
2. **Reference the examples** in `examples/common_patterns_demo.py`
3. **Use established naming conventions** consistently
4. **Follow the async-first pattern** for all I/O operations
5. **Implement proper error handling** with custom exceptions
6. **Add comprehensive docstrings** for public APIs
7. **Use type hints** throughout the codebase
8. **Check test coverage** when adding new functionality
9. **Reference the troubleshooting guide** for common issues
10. **Maintain backward compatibility** when possible

## 🔗 **External Resources**

- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- [InfluxDB Documentation](https://docs.influxdata.com/)
- [MQTT Documentation](https://mqtt.org/documentation)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Context7 Development Standards](https://buildermethods.com/agent-os)

---

**Remember**: This project follows established patterns and conventions. Always check existing implementations before creating new ones, and refer to the documentation files for detailed guidance.
