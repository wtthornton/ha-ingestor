# Sports Data Service

FastAPI service for fetching and caching sports data (NFL/NHL) from ESPN API with InfluxDB persistence.

## Features

- **ESPN API Integration**: Free access to NFL and NHL game data
- **Team-Based Filtering**: Query only your favorite teams
- **Smart Caching**: 15s cache for live games, 5min for upcoming
- **InfluxDB Persistence**: Store game data for 2 years (Story 12.1)
- **Circuit Breaker**: Graceful degradation if InfluxDB unavailable
- **Health Monitoring**: Comprehensive health checks with stats

## Quick Start

### Environment Variables

Copy `infrastructure/env.sports.template` and configure:

```bash
# Required
INFLUXDB_ENABLED=true                          # Enable/disable persistence
INFLUXDB_URL=http://influxdb:8086              # InfluxDB server
INFLUXDB_TOKEN=your-token-here                 # InfluxDB auth token
INFLUXDB_DATABASE=sports_data                  # Database name

# Optional
INFLUXDB_RETENTION_DAYS=730                    # 2 years retention
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3            # Failures before circuit opens
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60             # Recovery timeout
```

### Running the Service

```bash
# Development
cd services/sports-data
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8005

# Production (Docker)
docker-compose up sports-data
```

## API Endpoints

### Games

- `GET /api/v1/games/live?league=nfl&team_ids=ne,sf` - Live games
- `GET /api/v1/games/upcoming?league=nfl&team_ids=ne` - Upcoming games
- `GET /api/v1/teams?league=nfl` - Available teams

### History (Story 12.2)

- `GET /api/v1/games/history?team=Patriots&season=2025` - Historical games
- `GET /api/v1/games/timeline/{game_id}?sport=nfl` - Score progression
- `GET /api/v1/games/schedule/Patriots?season=2025` - Team schedule + stats

### Home Assistant (Story 12.3)

- `GET /api/v1/ha/game-status/{team}?sport=nfl` - Quick status check
- `GET /api/v1/ha/game-context/{team}?sport=nfl` - Full game context
- `POST /api/v1/webhooks/register` - Register webhook
- `GET /api/v1/webhooks/list` - List webhooks
- `DELETE /api/v1/webhooks/{id}` - Unregister webhook

### Health

- `GET /health` - Health check with InfluxDB status

### Metrics

- `GET /api/v1/metrics/api-usage` - API usage statistics
- `GET /api/v1/cache/stats` - Cache performance

## Architecture

```
ESPN API → Sports Data Service → Cache (15s TTL)
                               → InfluxDB (2-year retention)
```

### InfluxDB Schema

**Measurements:** `nfl_scores`, `nhl_scores`

**Tags (indexed):**
- game_id, season, week, home_team, away_team, status

**Fields:**
- home_score, away_score, quarter/period, time_remaining

## Circuit Breaker

Prevents cascading failures when InfluxDB is unavailable:

1. After 3 consecutive failures → opens circuit (blocks writes)
2. After 60 seconds → allows retry
3. On success → closes circuit (normal operation)

API continues working even when circuit is open.

## Testing

```bash
# Run unit tests
pytest tests/test_circuit_breaker.py
pytest tests/test_influxdb_writer.py

# Run integration tests
pytest tests/test_integration_influxdb.py

# All tests
pytest
```

## Deployment

### Docker Compose

```yaml
sports-data:
  build: ./services/sports-data
  ports:
    - "8005:8005"
  environment:
    - INFLUXDB_ENABLED=true
    - INFLUXDB_URL=http://influxdb:8086
    - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
    - INFLUXDB_DATABASE=sports_data
  depends_on:
    - influxdb
```

### Retention Policy Setup

```bash
# Check retention configuration
python -m src.setup_retention

# Manual configuration (InfluxDB CLI)
influx bucket update --name sports_data --retention 17520h  # 730 days
```

## Troubleshooting

### InfluxDB writes failing

1. Check health endpoint: `curl http://localhost:8005/health`
2. Look for circuit breaker status: `"circuit_breaker": "open"`
3. Check InfluxDB connectivity: `curl http://localhost:8086/health`
4. Verify INFLUXDB_TOKEN is correct

### Circuit breaker stuck open

- Wait 60 seconds for auto-recovery, or
- Restart service to reset circuit breaker

### Disable InfluxDB persistence

Set `INFLUXDB_ENABLED=false` - service continues without persistence.

## Dependencies

- **FastAPI 0.104.1**: Web framework
- **aiohttp 3.9.0**: Async HTTP client
- **influxdb3-python**: InfluxDB v3 client (Story 12.1)
- **pytest 7.4.3**: Testing framework

## Story 12.1 Changes

- Added InfluxDB persistence layer
- Implemented circuit breaker pattern
- Non-blocking async writes
- 2-year data retention
- Health check with InfluxDB stats
- Comprehensive unit/integration tests

## Story 12.2 Changes

- Historical query endpoints (`/history`, `/timeline`, `/schedule`)
- Simple built-in pagination (no extra libraries)
- 5-minute query result caching
- Computed statistics (wins, losses, win percentage)
- Team season records and schedules
- <100ms query response times

## Story 12.3 Changes (NEW) ⭐

- **Background event detection** (checks every 15 seconds)
- **HMAC-signed webhooks** (game_started, score_changed, game_ended)
- **HA automation endpoints** (<50ms response time)
- **Webhook management** (register/unregister via REST API)
- **Event detection latency**: 11-16 seconds (ESPN lag + check + delivery)
- **Fire-and-forget delivery** with retry (3 attempts, exponential backoff)

## Home Assistant Integration

### Quick Setup

1. **Register webhook in HA:**

```bash
curl -X POST "http://localhost:8005/api/v1/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://homeassistant.local:8123/api/webhook/patriots_game",
    "events": ["game_started", "score_changed", "game_ended"],
    "secret": "your-secure-secret-min-16-chars",
    "team": "ne",
    "sport": "nfl"
  }'
```

2. **Create automation:**

```yaml
# configuration.yaml
webhook:
  patriots_game:
    
# automations.yaml
automation:
  - alias: "Patriots Game - Turn On TV"
    trigger:
      - platform: webhook
        webhook_id: "patriots_game"
        allowed_methods: [POST]
    condition:
      - "{{ trigger.json.event == 'game_started' }}"
      - "{{ trigger.json.home_team == 'ne' or trigger.json.away_team == 'ne' }}"
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.living_room_tv
      - service: notify.mobile_app
        data:
          message: "Patriots game starting!"
```

### Example: Flash Lights When Team Scores

```yaml
automation:
  - alias: "Patriots Score - Flash Lights"
    trigger:
      - platform: webhook
        webhook_id: "patriots_game"
    condition:
      - "{{ trigger.json.event == 'score_changed' }}"
      - "{{ trigger.json.home_diff > 0 or trigger.json.away_diff > 0 }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          flash: long
          rgb_color: [0, 32, 91]  # Patriots blue
```

### Example: Query Game Status in Automation

```yaml
automation:
  - alias: "Pre-Game Routine"
    trigger:
      - platform: time
        at: "12:00:00"
    condition:
      # Check if Patriots playing today
      - condition: template
        value_template: >
          {% set status = states.sensor.patriots_game_status.state %}
          {{ status == 'upcoming' }}
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.game_day

# Sensor to poll game status
sensor:
  - platform: rest
    name: "Patriots Game Status"
    resource: http://localhost:8005/api/v1/ha/game-status/ne?sport=nfl
    scan_interval: 300  # Check every 5 minutes
    value_template: "{{ value_json.status }}"
    json_attributes:
      - opponent
      - start_time
```

### Webhook Signature Verification (Optional)

```python
# Home Assistant custom component to verify HMAC signatures
import hmac
import hashlib

def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature"""
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

## License

Part of Home Assistant Ingestor project.
