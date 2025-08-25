# ha-ingestor Development Patterns

## 🎯 **Overview**
This document outlines the established development patterns used throughout the ha-ingestor project. AI assistants should follow these patterns when implementing new features or modifying existing code.

## 🏗️ **Architecture Patterns**

### **1. Async-First Architecture**
**Pattern**: All I/O operations use `asyncio` and async/await syntax.

**Implementation**:
```python
# ✅ CORRECT: Async function with proper await
async def process_event(self, event: BaseEvent) -> Optional[InfluxDBPoint]:
    try:
        # Apply filters
        if not await self._apply_filters(event):
            return None

        # Apply transformations
        point = await self._apply_transformations(event)
        return point

    except Exception as e:
        logger.error(f"Error processing event {event.entity_id}: {e}")
        return None

# ❌ INCORRECT: Blocking operations in async context
async def process_event(self, event: BaseEvent) -> Optional[InfluxDBPoint]:
    # This blocks the event loop
    time.sleep(1)  # Don't do this!
    return point
```

**Key Principles**:
- Use `async def` for functions that perform I/O operations
- Always `await` async function calls
- Never use blocking operations (`time.sleep`, `requests.get`, etc.) in async context
- Use `asyncio.gather()` for concurrent operations

### **2. Pipeline Pattern**
**Pattern**: Data flows through a series of processing stages (filters → transformers → writers).

**Implementation**:
```python
class EventPipeline:
    def __init__(self, filters: List[BaseFilter], transformers: List[BaseTransformer]):
        self.filters = filters
        self.transformers = transformers

    async def process_event(self, event: BaseEvent) -> Optional[InfluxDBPoint]:
        # Stage 1: Apply filters
        for filter_instance in self.filters:
            if not await filter_instance.filter(event):
                return None

        # Stage 2: Apply transformations
        current_data = event
        for transformer in self.transformers:
            current_data = await transformer.transform(current_data)

        return current_data
```

**Key Principles**:
- Each stage has a single responsibility
- Stages are configurable and pluggable
- Data flows through stages sequentially
- Each stage can filter out or modify data

### **3. Factory Pattern**
**Pattern**: Dynamic creation of components based on configuration.

**Implementation**:
```python
class FilterFactory:
    @staticmethod
    def create_filter(filter_type: str, config: Dict[str, Any]) -> BaseFilter:
        if filter_type == "domain":
            return DomainFilter(config)
        elif filter_type == "entity":
            return EntityFilter(config)
        elif filter_type == "attribute":
            return AttributeFilter(config)
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")

# Usage
filter_config = {"type": "domain", "include_domains": ["sensor"]}
filter_instance = FilterFactory.create_filter(filter_config["type"], filter_config)
```

**Key Principles**:
- Centralized component creation logic
- Configuration-driven instantiation
- Easy to extend with new component types
- Consistent initialization patterns

## 🔧 **Code Organization Patterns**

### **1. Module Structure**
**Pattern**: Each module has a clear, single responsibility.

**Implementation**:
```python
# ha_ingestor/filters/domain_filter.py
"""
Domain-based filtering for Home Assistant events.

This module provides filtering based on entity domains (sensor, switch, etc.).
"""

from typing import Any, Dict, Optional
from ha_ingestor.filters.base import BaseFilter
from ha_ingestor.models.events import BaseEvent

class DomainFilter(BaseFilter):
    """Filter events based on entity domain."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.include_domains = config.get("include_domains", [])
        self.exclude_domains = config.get("exclude_domains", [])

    async def filter(self, event: BaseEvent) -> bool:
        """Filter logic implementation."""
        # Implementation here
        pass
```

**Key Principles**:
- One class per file (with exceptions for closely related classes)
- Clear module docstring explaining purpose
- Consistent import organization
- Logical grouping of related functionality

### **2. Package Organization**
**Pattern**: Use `__init__.py` files for clean imports and package structure.

**Implementation**:
```python
# ha_ingestor/filters/__init__.py
"""
Event filtering system for ha-ingestor.

This package provides various filtering mechanisms for Home Assistant events.
"""

from .base import BaseFilter
from .domain_filter import DomainFilter
from .entity_filter import EntityFilter
from .attribute_filter import AttributeFilter
from .time_filter import TimeFilter

__all__ = [
    "BaseFilter",
    "DomainFilter",
    "EntityFilter",
    "AttributeFilter",
    "TimeFilter"
]

# Usage in other modules
from ha_ingestor.filters import DomainFilter, EntityFilter
```

**Key Principles**:
- Export only public interfaces in `__all__`
- Provide convenient import paths
- Hide internal implementation details
- Maintain backward compatibility

### **3. Configuration Management**
**Pattern**: Use Pydantic models for configuration validation and management.

**Implementation**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class FilterConfig(BaseModel):
    """Configuration for event filtering."""

    enabled: bool = Field(default=True, description="Whether the filter is enabled")
    filter_type: str = Field(..., description="Type of filter to use")
    priority: int = Field(default=100, ge=0, le=1000, description="Filter priority")

    class Config:
        extra = "forbid"  # Reject unknown fields

class PipelineConfig(BaseModel):
    """Configuration for the event processing pipeline."""

    filters: List[FilterConfig] = Field(default_factory=list)
    transformers: List[Dict[str, Any]] = Field(default_factory=list)
    batch_size: int = Field(default=100, gt=0, description="Batch size for processing")
    batch_timeout: float = Field(default=5.0, gt=0, description="Batch timeout in seconds")
```

**Key Principles**:
- Use Pydantic for all configuration models
- Provide sensible defaults
- Include field descriptions and validation rules
- Use `extra = "forbid"` to catch configuration errors early

## 📝 **Coding Style Patterns**

### **1. Naming Conventions**
**Pattern**: Consistent naming across the codebase.

**Implementation**:
```python
# ✅ CORRECT: Follow established conventions

# Classes: PascalCase
class EventProcessor:
    pass

class MQTTClient:
    pass

# Functions and methods: snake_case
async def process_event(self, event: BaseEvent) -> Optional[InfluxDBPoint]:
    pass

def get_filter_config(self) -> FilterConfig:
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_BATCH_SIZE = 100
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30.0

# Variables: snake_case
current_batch = []
filter_instances = []
connection_status = "connected"
```

**Key Principles**:
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Variables: `snake_case`
- Be descriptive and avoid abbreviations

### **2. Type Hints**
**Pattern**: Comprehensive type hints for all public APIs.

**Implementation**:
```python
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

class EventProcessor:
    def __init__(self, filters: List[BaseFilter], transformers: List[BaseTransformer]):
        self.filters = filters
        self.transformers = transformers

    async def process_event(self, event: BaseEvent) -> Optional[InfluxDBPoint]:
        """Process a single event through the pipeline."""
        pass

    def get_processing_stats(self) -> Dict[str, Union[int, float]]:
        """Get current processing statistics."""
        pass

    async def shutdown(self, timeout: Optional[float] = None) -> None:
        """Shutdown the processor gracefully."""
        pass
```

**Key Principles**:
- Use type hints for all function parameters and return values
- Import types from `typing` module
- Use `Optional[T]` for nullable values
- Use `Union[T1, T2]` for multiple possible types
- Use generic types like `List[T]`, `Dict[K, V]`

### **3. Docstrings**
**Pattern**: Comprehensive docstrings for all public APIs.

**Implementation**:
```python
class EventProcessor:
    """
    Processes Home Assistant events through a configurable pipeline.

    This class implements the main event processing logic, applying filters
    and transformations before writing to InfluxDB.

    Attributes:
        filters: List of filter instances to apply to events
        transformers: List of transformer instances to apply to events
        processed_count: Total number of events processed
        filtered_count: Total number of events filtered out
    """

    async def process_event(self, event: BaseEvent) -> Optional[InfluxDBPoint]:
        """
        Process a single event through the pipeline.

        Args:
            event: The Home Assistant event to process

        Returns:
            InfluxDBPoint if event passes all filters and transformations,
            None if event is filtered out or processing fails

        Raises:
            ProcessingError: If event processing fails
        """
        pass
```

**Key Principles**:
- Use Google-style docstrings
- Document all parameters, return values, and exceptions
- Include usage examples for complex methods
- Explain the purpose and behavior clearly

## 🧪 **Testing Patterns**

### **1. Test Organization**
**Pattern**: Organize tests to mirror the source code structure.

**Implementation**:
```
tests/
├── unit/                          # Unit tests
│   ├── test_filters/             # Test filter implementations
│   ├── test_transformers/        # Test transformer implementations
│   └── test_models/              # Test data models
├── integration/                   # Integration tests
│   ├── test_pipeline.py          # Test complete pipeline
│   └── test_influxdb.py          # Test InfluxDB integration
└── conftest.py                   # Shared test fixtures
```

**Key Principles**:
- Mirror source code structure in test organization
- Separate unit tests from integration tests
- Use descriptive test file names
- Group related tests in subdirectories

### **2. Test Fixtures**
**Pattern**: Use pytest fixtures for common test data and setup.

**Implementation**:
```python
# tests/conftest.py
import pytest
from ha_ingestor.models.events import BaseEvent
from ha_ingestor.filters.base import BaseFilter

@pytest.fixture
def sample_event() -> BaseEvent:
    """Create a sample event for testing."""
    return BaseEvent(
        entity_id="sensor.temperature_living_room",
        value=22.5,
        domain="sensor",
        timestamp=datetime.utcnow()
    )

@pytest.fixture
def mock_filter() -> BaseFilter:
    """Create a mock filter for testing."""
    class MockFilter(BaseFilter):
        def __init__(self, should_pass: bool = True):
            super().__init__({})
            self.should_pass = should_pass

        async def filter(self, event: BaseEvent) -> bool:
            return self.should_pass

    return MockFilter()

# Usage in tests
@pytest.mark.asyncio
async def test_filter_passes_event(sample_event, mock_filter):
    """Test that filter passes events correctly."""
    result = await mock_filter.filter(sample_event)
    assert result is True
```

**Key Principles**:
- Use fixtures for common test data
- Make fixtures reusable across test modules
- Use descriptive fixture names
- Keep fixtures simple and focused

### **3. Async Testing**
**Pattern**: Use pytest-asyncio for testing async code.

**Implementation**:
```python
import pytest
from ha_ingestor.filters.domain_filter import DomainFilter

@pytest.mark.asyncio
async def test_domain_filter_include():
    """Test domain filter with include domains."""
    config = {"include_domains": ["sensor", "switch"]}
    filter_instance = DomainFilter(config)

    # Test included domain
    event = BaseEvent(entity_id="sensor.temperature", domain="sensor")
    result = await filter_instance.filter(event)
    assert result is True

    # Test excluded domain
    event = BaseEvent(entity_id="light.living_room", domain="light")
    result = await filter_instance.filter(event)
    assert result is False
```

**Key Principles**:
- Use `@pytest.mark.asyncio` decorator for async tests
- Test both success and failure cases
- Use descriptive test names
- Test edge cases and error conditions

## 🚨 **Error Handling Patterns**

### **1. Custom Exceptions**
**Pattern**: Define custom exception classes for different error types.

**Implementation**:
```python
class HAIngestorError(Exception):
    """Base exception for ha-ingestor errors."""
    pass

class ConfigurationError(HAIngestorError):
    """Raised when configuration is invalid."""
    pass

class ConnectionError(HAIngestorError):
    """Raised when connection to external service fails."""
    pass

class ProcessingError(HAIngestorError):
    """Raised when event processing fails."""
    pass

# Usage
def validate_config(config: Dict[str, Any]) -> None:
    if "required_field" not in config:
        raise ConfigurationError("Missing required field: required_field")
```

**Key Principles**:
- Create a hierarchy of custom exceptions
- Use descriptive exception names
- Include relevant context in error messages
- Catch specific exceptions, not generic ones

### **2. Retry Logic**
**Pattern**: Use tenacity for retry logic with exponential backoff.

**Implementation**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def write_to_influxdb(self, point: InfluxDBPoint) -> None:
    """Write point to InfluxDB with retry logic."""
    try:
        await self.client.write_point(point)
    except Exception as e:
        logger.warning(f"Failed to write to InfluxDB: {e}")
        raise  # Retry will be handled by tenacity
```

**Key Principles**:
- Use tenacity for retry logic
- Configure appropriate retry strategies
- Log retry attempts for debugging
- Don't retry indefinitely

## 📊 **Logging Patterns**

### **1. Structured Logging**
**Pattern**: Use structlog for structured logging with context.

**Implementation**:
```python
import structlog

logger = structlog.get_logger()

class EventProcessor:
    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(processor_name=name)

    async def process_event(self, event: BaseEvent) -> None:
        self.logger.info(
            "Processing event",
            entity_id=event.entity_id,
            domain=event.domain,
            event_type="ingestion"
        )

        try:
            # Process event
            result = await self._process(event)
            self.logger.info(
                "Event processed successfully",
                entity_id=event.entity_id,
                result="success"
            )
        except Exception as e:
            self.logger.error(
                "Event processing failed",
                entity_id=event.entity_id,
                error=str(e),
                result="failure"
            )
            raise
```

**Key Principles**:
- Use structlog for all logging
- Include relevant context in log messages
- Use consistent log levels
- Bind context to logger instances

### **2. Log Levels**
**Pattern**: Use appropriate log levels for different types of messages.

**Implementation**:
```python
# DEBUG: Detailed information for debugging
logger.debug("Filter configuration loaded", filters=filter_names)

# INFO: General information about program execution
logger.info("Event processing started", batch_size=batch_size)

# WARNING: Something unexpected happened but program can continue
logger.warning("Connection attempt failed, retrying", attempt=attempt_number)

# ERROR: Something failed and needs attention
logger.error("Failed to write to InfluxDB", error=str(e))

# CRITICAL: Program cannot continue
logger.critical("Database connection lost, shutting down")
```

**Key Principles**:
- DEBUG: Detailed debugging information
- INFO: General program flow information
- WARNING: Unexpected but recoverable situations
- ERROR: Errors that need attention
- CRITICAL: Program cannot continue

## 🔍 **Performance Patterns**

### **1. Batch Processing**
**Pattern**: Process events in batches for better performance.

**Implementation**:
```python
class BatchProcessor:
    def __init__(self, batch_size: int = 100, batch_timeout: float = 5.0):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.current_batch: List[Any] = []
        self.last_batch_time = datetime.utcnow()

    async def add_item(self, item: Any) -> bool:
        """Add item to batch. Returns True if batch is ready."""
        self.current_batch.append(item)

        # Check if batch is ready
        batch_ready = (
            len(self.current_batch) >= self.batch_size or
            (datetime.utcnow() - self.last_batch_time).total_seconds() >= self.batch_timeout
        )

        return batch_ready

    def get_batch(self) -> List[Any]:
        """Get current batch and reset."""
        batch = self.current_batch.copy()
        self.current_batch.clear()
        self.last_batch_time = datetime.utcnow()
        return batch
```

**Key Principles**:
- Process items in batches for efficiency
- Use both size and time-based batching
- Avoid keeping items in memory indefinitely
- Monitor batch performance metrics

### **2. Connection Pooling**
**Pattern**: Reuse connections to external services.

**Implementation**:
```python
class ConnectionPool:
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.available_connections: List[Any] = []
        self.in_use_connections: Set[Any] = set()

    async def get_connection(self) -> Any:
        """Get an available connection from the pool."""
        if self.available_connections:
            connection = self.available_connections.pop()
            self.in_use_connections.add(connection)
            return connection

        if len(self.in_use_connections) < self.max_connections:
            connection = await self._create_connection()
            self.in_use_connections.add(connection)
            return connection

        # Wait for a connection to become available
        return await self._wait_for_connection()

    def return_connection(self, connection: Any) -> None:
        """Return a connection to the pool."""
        self.in_use_connections.discard(connection)
        self.available_connections.append(connection)
```

**Key Principles**:
- Limit the number of concurrent connections
- Reuse connections when possible
- Handle connection failures gracefully
- Monitor connection pool metrics

## 💡 **Best Practices Summary**

1. **Always use async/await** for I/O operations
2. **Follow established naming conventions** consistently
3. **Use type hints** for all public APIs
4. **Write comprehensive docstrings** explaining purpose and behavior
5. **Implement proper error handling** with custom exceptions
6. **Use structured logging** with appropriate context
7. **Write tests** for all new functionality
8. **Follow the pipeline pattern** for data processing
9. **Use configuration models** with Pydantic validation
10. **Monitor performance** and optimize bottlenecks
11. **Handle failures gracefully** with retry logic
12. **Keep modules focused** on single responsibilities
13. **Use dependency injection** for better testability
14. **Document configuration options** clearly
15. **Maintain backward compatibility** when possible

## 🔗 **Related Documentation**

- **`.cursorrules`**: AI Assistant coding standards
- **`PROJECT_CONTEXT.md`**: Detailed architecture context
- **`AI_ASSISTANT_GUIDE.md`**: Quick reference for AI assistants
- **`examples/common_patterns_demo.py`**: Implementation examples
- **`tests/`**: Test examples and patterns
