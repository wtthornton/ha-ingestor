# Data Models Sub-Spec

## Overview

Implement comprehensive data models for MQTT messages, WebSocket events, and InfluxDB data points with validation and transformation capabilities.

## Technical Requirements

### MQTT Event Models
- Parse MQTT topic structure (domain/entity_id/state)
- Extract entity information and state data
- Handle different entity types (sensor, binary_sensor, switch, etc.)
- Validate message format and content
- Transform to standardized internal format

### WebSocket Event Models
- Parse Home Assistant event structure
- Extract event type, entity_id, and event data
- Handle different event types with appropriate schemas
- Validate event format and required fields
- Transform to standardized internal format

### InfluxDB Point Models
- Define consistent schema for time-series data
- Include proper tags for efficient querying
- Structure fields for data analysis
- Add metadata for event source and processing
- Optimize for InfluxDB performance

### Data Transformation Pipeline
- Convert source events to internal event format
- Apply validation and sanitization
- Transform to InfluxDB point format
- Handle data type conversions and formatting
- Maintain data lineage and audit trail

## Implementation Details

### Model Structure

#### MQTT Event Model
```python
class MQTTEvent(BaseModel):
    topic: str
    payload: str
    timestamp: datetime
    domain: str
    entity_id: str
    state: str
    attributes: Optional[Dict[str, Any]]
    source: Literal["mqtt"] = "mqtt"
    
    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str
    @field_validator("payload")
    @classmethod
    def validate_payload(cls, v: str) -> str
```

#### WebSocket Event Model
```python
class WebSocketEvent(BaseModel):
    event_type: str
    entity_id: Optional[str]
    domain: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    source: Literal["websocket"] = "websocket"
    
    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str
    @field_validator("data")
    @classmethod
    def validate_data(cls, v: Dict[str, Any]) -> Dict[str, Any]
```

#### InfluxDB Point Model
```python
class InfluxDBPoint(BaseModel):
    measurement: str
    tags: Dict[str, str]
    fields: Dict[str, Any]
    timestamp: datetime
    
    @field_validator("measurement")
    @classmethod
    def validate_measurement(cls, v: str) -> str
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Dict[str, str]) -> Dict[str, str]
```

### Transformation Functions
```python
def mqtt_to_internal(mqtt_event: MQTTEvent) -> InternalEvent
def websocket_to_internal(ws_event: WebSocketEvent) -> InternalEvent
def internal_to_influxdb(event: InternalEvent) -> InfluxDBPoint
def validate_event_data(event: Union[MQTTEvent, WebSocketEvent]) -> bool
```

### Testing Requirements
- Unit tests for all model validation
- Tests for data transformation functions
- Tests for edge cases and error conditions
- Performance tests for transformation pipeline
- Integration tests with sample Home Assistant data

## Dependencies

- Pydantic for data validation
- Configuration management from Phase 1
- Logging system from Phase 1
- Sample Home Assistant data for testing
- InfluxDB schema design knowledge
