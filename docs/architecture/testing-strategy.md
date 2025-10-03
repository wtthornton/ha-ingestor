# Testing Strategy

### Testing Pyramid

```
E2E Tests (Integration)
/        \
Integration Tests (API)
/            \
Frontend Unit  Backend Unit
```

### Test Organization

#### Frontend Tests
```
frontend/tests/
├── components/
│   ├── HealthDashboard.test.tsx
│   ├── EventList.test.tsx
│   └── ConfigForm.test.tsx
├── services/
│   └── api.test.ts
└── __mocks__/
    └── api.ts
```

#### Backend Tests
```
services/*/tests/
├── test_websocket_client.py
├── test_event_processor.py
├── test_weather_service.py
├── test_influxdb_client.py
└── test_api_endpoints.py
```

#### E2E Tests
```
tests/
├── test_integration.py
├── test_data_flow.py
└── fixtures/
    └── sample_events.json
```

### Test Examples

#### Frontend Component Test
```typescript
import { render, screen } from '@testing-library/react';
import { HealthDashboard } from '../HealthDashboard';

test('displays system health status', () => {
  const mockHealth = {
    service_status: { websocket_client: 'healthy' },
    event_stats: { events_per_hour: 100 }
  };
  
  render(<HealthDashboard health={mockHealth} />);
  expect(screen.getByText('healthy')).toBeInTheDocument();
});
```

#### Backend API Test
```python
import pytest
from fastapi.testclient import TestClient
from admin_api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "service_status" in response.json()
```

#### E2E Test
```python
import pytest
import asyncio
from services.websocket_ingestion.src.websocket_client import WebSocketClient

@pytest.mark.asyncio
async def test_end_to_end_data_flow():
    # Test complete data flow from HA to InfluxDB
    client = WebSocketClient("ws://test-ha:8123/websocket")
    await client.connect()
    
    # Simulate event and verify storage
    event = await client.receive_event()
    assert event is not None
    
    # Verify event stored in InfluxDB
    stored_event = await query_influxdb(event.entity_id)
    assert stored_event is not None
```
