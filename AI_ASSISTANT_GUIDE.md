# AI Assistant Programming Guide

## 🚀 Quick Reference for AI Assistants

This guide provides AI assistants with quick access to common patterns, templates, and solutions for the ha-ingestor project.

## 📋 Project Quick Facts

- **Language**: Python 3.12+
- **Architecture**: Async-first, event-driven pipeline
- **Main Entry Point**: `ha_ingestor/main.py`
- **Configuration**: Environment variables + Pydantic settings
- **Testing**: pytest with async support
- **Code Quality**: Black, Ruff, MyPy

## 🔧 Common Code Templates

### 1. **New Filter Implementation**
```python
from typing import Any, Dict, Optional
from ha_ingestor.filters.base import BaseFilter
from ha_ingestor.models.events import BaseEvent

class CustomFilter(BaseFilter):
    """AI ASSISTANT CONTEXT: Custom filter for specific use case."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize filter-specific configuration
        
    async def filter(self, event: BaseEvent) -> bool:
        """Filter logic goes here."""
        # Implement your filtering logic
        return True  # or False based on conditions
```

### 2. **New Transformer Implementation**
```python
from typing import Any, Dict, Optional
from ha_ingestor.transformers.base import BaseTransformer
from ha_ingestor.models.events import BaseEvent
from ha_ingestor.models.influxdb_point import InfluxDBPoint

class CustomTransformer(BaseTransformer):
    """AI ASSISTANT CONTEXT: Custom transformer for data modification."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize transformer-specific configuration
        
    async def transform(self, event: BaseEvent) -> InfluxDBPoint:
        """Transform event to InfluxDB point."""
        # Implement your transformation logic
        return InfluxDBPoint(
            measurement="custom_measurement",
            tags={"entity_id": event.entity_id},
            fields={"value": event.value},
            timestamp=event.timestamp
        )
```

### 3. **New Model Definition**
```python
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class CustomEvent(BaseModel):
    """AI ASSISTANT CONTEXT: Custom event model."""
    
    entity_id: str = Field(..., description="Entity identifier")
    value: Any = Field(..., description="Event value")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### 4. **New Metric Definition**
```python
from prometheus_client import Counter, Histogram, Gauge
from ha_ingestor.metrics.registry import MetricsRegistry

# AI ASSISTANT CONTEXT: Define metrics for monitoring
custom_counter = Counter(
    "custom_events_total",
    "Total number of custom events processed",
    ["event_type", "status"]
)

custom_histogram = Histogram(
    "custom_processing_duration_seconds",
    "Time spent processing custom events",
    ["event_type"]
)

custom_gauge = Gauge(
    "custom_active_connections",
    "Number of active custom connections"
)
```

### 5. **New Health Check**
```python
from ha_ingestor.health.checks import HealthCheck
from typing import Dict, Any

class CustomHealthCheck(HealthCheck):
    """AI ASSISTANT CONTEXT: Custom health check for service monitoring."""
    
    async def check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            # Implement your health check logic
            return {
                "status": "healthy",
                "details": "Custom service is responding"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "details": f"Custom service error: {str(e)}"
            }
```

## 🎯 Common Development Tasks

### **Task 1: Add New MQTT Topic Pattern**
1. **Location**: `ha_ingestor/mqtt/topic_patterns.py`
2. **Pattern**: Add new topic pattern to `TOPIC_PATTERNS` dictionary
3. **Example**:
```python
TOPIC_PATTERNS = {
    # ... existing patterns ...
    "custom_sensor": {
        "pattern": "homeassistant/sensor/{entity_id}/state",
        "entity_type": "sensor",
        "attributes": ["unit_of_measurement", "friendly_name"]
    }
}
```

### **Task 2: Modify Filter Configuration**
1. **Location**: `ha_ingestor/config.py`
2. **Pattern**: Add new filter type to `FilterConfig` model
3. **Example**:
```python
class FilterConfig(BaseModel):
    # ... existing fields ...
    custom_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom filter configuration"
    )
```

### **Task 3: Add New Environment Variable**
1. **Location**: `ha_ingestor/config.py`
2. **Pattern**: Add to `Settings` class with proper validation
3. **Example**:
```python
class Settings(BaseSettings):
    # ... existing fields ...
    custom_service_url: str = Field(
        default="http://localhost:8080",
        description="Custom service URL"
    )
    
    class Config:
        env_file = ".env"
```

### **Task 4: Create New Test**
1. **Location**: `tests/` directory
2. **Pattern**: Use pytest with async support
3. **Example**:
```python
import pytest
from ha_ingestor.filters.custom_filter import CustomFilter

@pytest.mark.asyncio
async def test_custom_filter():
    """Test custom filter functionality."""
    config = {"enabled": True}
    filter_instance = CustomFilter(config)
    
    # Create test event
    event = BaseEvent(entity_id="test.entity", value=42)
    
    # Test filter
    result = await filter_instance.filter(event)
    assert result is True
```

## 🚨 Common Issues & Quick Fixes

### **Issue 1: Import Errors**
- **Solution**: Check `__init__.py` files in package directories
- **Pattern**: Ensure all modules are properly exported

### **Issue 2: Configuration Validation Errors**
- **Solution**: Check environment variables and Pydantic models
- **Pattern**: Use `Settings().model_dump()` to debug configuration

### **Issue 3: Async/Await Errors**
- **Solution**: Ensure all async functions are properly awaited
- **Pattern**: Use `pytest-asyncio` for testing async code

### **Issue 4: Type Checking Errors**
- **Solution**: Run `mypy ha_ingestor/` to identify type issues
- **Pattern**: Add proper type hints and use `typing` module

### **Issue 5: Test Failures**
- **Solution**: Check test dependencies and mock external services
- **Pattern**: Use `pytest-mock` for mocking

## 📚 Quick Reference Links

### **Core Files**
- **Main Application**: `ha_ingestor/main.py`
- **Configuration**: `ha_ingestor/config.py`
- **Pipeline**: `ha_ingestor/pipeline.py`
- **Models**: `ha_ingestor/models/`

### **Key Directories**
- **Filters**: `ha_ingestor/filters/`
- **Transformers**: `ha_ingestor/transformers/`
- **MQTT**: `ha_ingestor/mqtt/`
- **WebSocket**: `ha_ingestor/websocket/`
- **InfluxDB**: `ha_ingestor/influxdb/`

### **Testing**
- **Test Directory**: `tests/`
- **Unit Tests**: `tests/unit/`
- **Integration Tests**: `tests/test_integration.py`

### **Configuration Files**
- **Environment**: `.env`, `env.example`
- **Dependencies**: `pyproject.toml`, `poetry.lock`
- **Docker**: `Dockerfile`, `docker-compose.yml`

## 🔍 Debugging Commands

### **Code Quality**
```bash
# Format code
poetry run black ha_ingestor/ tests/

# Lint code
poetry run ruff check ha_ingestor/ tests/

# Type check
poetry run mypy ha_ingestor/

# Run tests
poetry run pytest tests/ -v
```

### **Service Management**
```bash
# Start service
poetry run python -m ha_ingestor.main

# Check health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics

# View logs
tail -f logs/ha-ingestor.log
```

## 💡 Pro Tips for AI Assistants

1. **Always check existing patterns** before creating new implementations
2. **Use type hints** consistently throughout the codebase
3. **Follow the async-first pattern** for all I/O operations
4. **Reference the Context7 standards** in `.agent-os/` directory
5. **Check test coverage** when adding new functionality
6. **Use structured logging** with appropriate log levels
7. **Validate configuration** with Pydantic models
8. **Implement proper error handling** with custom exceptions
9. **Add comprehensive docstrings** for public APIs
10. **Follow the established naming conventions** for consistency
