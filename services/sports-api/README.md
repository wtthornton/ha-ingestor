# Sports API Service

Real-time NFL and NHL data integration service for the Home Assistant Ingestor ecosystem.

## Overview

The Sports API Service provides real-time and historical sports data from API-SPORTS, enabling Home Assistant automations based on live games, scores, standings, and player statistics.

### Features

- **NFL Data**: Scores, standings, fixtures, players, and injury reports
- **NHL Data**: Scores, standings, and fixtures
- **Real-Time Updates**: Live scores updated every ~15 seconds during games
- **Intelligent Caching**: Minimizes API calls with TTL-based caching
- **Rate Limiting**: Token bucket algorithm prevents quota exhaustion
- **InfluxDB Storage**: Time-series storage for historical analysis
- **Health Monitoring**: Comprehensive health checks and metrics

## Architecture

Built following Context7 KB best practices:

- **aiohttp**: Async HTTP client with connection pooling
- **Python 3.11**: Modern async/await support
- **Pydantic**: Type-safe data models
- **InfluxDB**: Optimized time-series storage
- **Docker**: Containerized deployment

See `docs/architecture/sports-api-integration.md` for complete architecture.

## Configuration

### Environment Variables

Create `.env` file or set environment variables:

```bash
# Required
API_SPORTS_KEY=your-api-key-here

# Service Configuration
SPORTS_API_PORT=8015
NFL_ENABLED=true
NHL_ENABLED=true

# Rate Limiting
API_SPORTS_REQUESTS_PER_SECOND=1
API_SPORTS_BURST_SIZE=5
API_SPORTS_DAILY_LIMIT=500

# Caching (TTL in seconds)
CACHE_LIVE_SCORES_TTL=15
CACHE_RECENT_SCORES_TTL=300
CACHE_FIXTURES_TTL=3600
CACHE_STANDINGS_TTL=3600

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=home_assistant
INFLUXDB_BUCKET=sports_data

# Logging
LOG_LEVEL=INFO
```

See `infrastructure/env.sports.template` for all configuration options.

### Getting an API Key

1. Visit [API-SPORTS](https://api-sports.io)
2. Sign up for a free account
3. Subscribe to NFL and/or NHL API
4. Copy your API key to `API_SPORTS_KEY`

Free tier typically includes:
- 100-500 requests per day
- Live updates every ~15 seconds
- Historical data access

## Local Development

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- API-SPORTS API key

### Setup

1. **Install dependencies:**

```bash
cd services/sports-api
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp infrastructure/env.sports.template .env
# Edit .env with your API key
```

3. **Run service:**

```bash
# Standalone
python -m src.main

# With Docker Compose
docker-compose up sports-api
```

4. **Verify health:**

```bash
curl http://localhost:8015/health
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_api_client.py -v
```

## API Endpoints

### Health Check

```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2025-10-11T12:00:00Z",
  "service": "sports-api",
  "version": "1.0.0",
  "components": {
    "nfl_client": "not_initialized",
    "nhl_client": "not_initialized",
    "cache": "not_initialized",
    "influxdb": "not_initialized"
  },
  "configuration": {
    "nfl_enabled": true,
    "nhl_enabled": true,
    "api_key_configured": true
  }
}
```

**API Endpoints** (Story 10.6 - Fully Operational):

**NFL:**
- `GET /api/nfl/scores?date=YYYY-MM-DD` - NFL scores
- `GET /api/nfl/standings?season=YYYY` - NFL standings
- `GET /api/nfl/fixtures?season=YYYY&week=N` - NFL schedule
- `GET /api/nfl/injuries?team=TEAM` - NFL injuries

**NHL:**
- `GET /api/nhl/scores?date=YYYY-MM-DD` - NHL scores
- `GET /api/nhl/standings?season=YYYY` - NHL standings
- `GET /api/nhl/fixtures?season=YYYY` - NHL schedule

**Admin:**
- `GET /api/sports/stats` - Service statistics
- `POST /api/sports/cache/clear` - Clear cache
- `GET /health` - Health check

See `API.md` for complete documentation.

## Docker Deployment

### Development

```bash
docker-compose up sports-api
```

### Production

```bash
docker-compose -f docker-compose.prod.yml up -d sports-api
```

### Service Configuration

```yaml
sports-api:
  ports:
    - "8015:8015"
  environment:
    - API_SPORTS_KEY=${API_SPORTS_KEY}
    - SPORTS_API_PORT=8015
    - NFL_ENABLED=true
    - NHL_ENABLED=true
  depends_on:
    - influxdb
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8015/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Project Structure

```
sports-api/
├── src/
│   ├── __init__.py
│   ├── main.py              # Service entry point
│   ├── api_client.py        # Base API client
│   └── health_check.py      # Health check handler
├── tests/
│   ├── __init__.py
│   ├── test_api_client.py   # API client tests
│   └── test_main.py         # Service tests
├── Dockerfile               # Production image
├── Dockerfile.dev           # Development image
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Dependencies

- `aiohttp==3.9.1` - Async HTTP client/server
- `python-dotenv==1.0.0` - Environment variable management
- `pydantic==2.5.0` - Data validation
- `influxdb-client-3>=3.0.0` - InfluxDB client
- `pytest==7.4.3` - Testing framework
- `pytest-asyncio==0.21.1` - Async test support

See `requirements.txt` for complete list.

## Development Roadmap

### ✅ Story 10.1: Service Foundation (Complete)
- Base service structure
- API client with Context7 KB patterns
- Docker configuration
- Health check endpoint

### ✅ Story 10.2: NFL Client (Complete)
- NFL API endpoints (scores, standings, fixtures, players, injuries)
- Pydantic data models (NFLScore, NFLStanding, NFLPlayer, NFLInjury, NFLFixture)
- Comprehensive unit and integration tests (40 tests, 88% coverage)

### ✅ Story 10.3: NHL Client (Complete)
- NHL API endpoints (scores, standings, fixtures)
- Pydantic data models (NHLScore, NHLStanding, NHLFixture)
- 16 tests, 92% coverage

### ✅ Story 10.4: InfluxDB Integration (Complete)
- 6 InfluxDB measurements with optimized schema
- Batch writer with Context7 KB patterns
- 3 retention policies (2-5 years)

### ✅ Story 10.5: Rate Limiting & Caching (Complete)
- Token bucket rate limiter (100% coverage)
- TTL-based cache manager (100% coverage)
- Circuit breaker for resilience

### ✅ Story 10.6: Endpoints & Integration (Complete)
- 9 REST API endpoints fully operational
- Cache-first pattern for performance
- Full integration: API → Cache → InfluxDB

### 📋 Story 10.4: InfluxDB Integration
- Schema design
- Batch writer
- Retention policies

### 📋 Story 10.5: Rate Limiting & Caching
- Token bucket rate limiter
- TTL-based cache
- Circuit breaker

### 📋 Story 10.6: Service Endpoints
- REST API endpoints
- Enrichment pipeline integration
- Admin API integration

### 📋 Story 10.7: Testing & Deployment
- Comprehensive testing
- Production deployment
- Monitoring and alerting

## Troubleshooting

### Service won't start

**Check API key:**
```bash
echo $API_SPORTS_KEY
```

**Check logs:**
```bash
docker logs ha-sports-api
```

### Health check fails

**Verify service is running:**
```bash
curl -v http://localhost:8015/health
```

**Check port availability:**
```bash
netstat -an | grep 8015
```

### API errors

**Check API key validity:**
- Visit API-SPORTS dashboard
- Verify key is active
- Check remaining quota

**Check rate limits:**
- Review daily request count
- Adjust cache TTLs if needed
- Consider upgrading API plan

## Contributing

1. Follow BMAD methodology
2. Implement stories sequentially
3. Write tests for all features
4. Update documentation
5. Maintain >90% test coverage

## Related Documentation

- **Architecture**: `docs/architecture/sports-api-integration.md`
- **Epic**: `docs/stories/epic-10-sports-api-integration.md`
- **Stories**: `docs/stories/10.*.md`
- **Context7 KB**: `docs/kb/context7-cache/`

## Support

For issues or questions:
1. Check troubleshooting guide
2. Review architecture documentation
3. Check story implementation notes
4. Review Context7 KB for library patterns

## License

Part of the Home Assistant Ingestor project.

