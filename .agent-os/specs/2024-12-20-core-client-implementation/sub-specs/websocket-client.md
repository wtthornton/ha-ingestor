# WebSocket Client Sub-Spec

## Overview

Implement a WebSocket client for connecting to Home Assistant WebSocket API and subscribing to real-time events from the event bus.

## Technical Requirements

### Connection Management
- Connect to Home Assistant WebSocket API using long-lived access token
- Support both secure (WSS) and insecure (WS) connections
- Implement automatic reconnection with exponential backoff
- Handle connection state changes and authentication

### Event Subscription
- Subscribe to Home Assistant event types:
  - `state_changed` - Entity state changes
  - `automation_triggered` - Automation executions
  - `service_called` - Service calls
  - `event` - Custom events
- Support filtering by entity_id, domain, or event type
- Handle subscription confirmations and failures

### Heartbeat Management
- Implement WebSocket ping/pong for connection health
- Monitor connection health and detect stale connections
- Automatic reconnection on heartbeat failures
- Configurable heartbeat interval from settings

### Message Processing
- Parse WebSocket messages and extract event data
- Validate event format and content
- Transform WebSocket events to internal event format
- Handle malformed or invalid events gracefully

## Implementation Details

### Class Structure
```python
class WebSocketClient:
    def __init__(self, config: Settings)
    async def connect(self) -> bool
    async def disconnect(self) -> None
    async def subscribe_events(self, event_types: List[str]) -> bool
    async def start_listening(self) -> None
    async def stop_listening(self) -> None
    def is_connected(self) -> bool
    async def _handle_message(self, message: dict) -> None
    async def _send_ping(self) -> None
    async def _reconnect(self) -> None
```

### Configuration Dependencies
- `ha_ws_url` - WebSocket API URL (ws:// or wss://)
- `ha_ws_token` - Long-lived access token
- `ha_ws_heartbeat_interval` - Heartbeat interval in seconds

### Home Assistant API Integration
- Authenticate using long-lived access token
- Subscribe to events using `subscribe_events` command
- Handle `auth_ok` and `auth_invalid` responses
- Process `event` messages with event data

### Testing Requirements
- Unit tests for connection management
- Integration tests with real Home Assistant instance
- Error handling tests for authentication failures
- Performance tests for event processing
- Memory leak tests for long-running connections

## Dependencies

- `websockets` or `aiohttp` library for WebSocket support
- Configuration management from Phase 1
- Logging system from Phase 1
- Data models for WebSocket events
- Home Assistant instance with WebSocket API enabled
