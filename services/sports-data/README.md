# Sports Data Service

FastAPI microservice for NFL & NHL sports data integration with team-based filtering.

## Features

- 🏈 NFL game data via ESPN API
- 🏒 NHL game data via NHL Official API or ESPN
- ⚡ Team-specific filtering (only fetch selected teams)
- 💾 Smart caching (15s for live, 5m for upcoming)
- 📊 API usage tracking and monitoring
- 🔒 Rate limiting to stay within free tiers
- 🏥 Health check endpoint

## Quick Start

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API key

# Run service
python -m uvicorn src.main:app --reload --port 8005
```

### Docker

```bash
# Build
docker build -t sports-data .

# Run
docker run -p 8005:8005 --env-file .env sports-data
```

### Docker Compose

```bash
# Start with other services
docker-compose up sports-data
```

## API Endpoints

### Health Check
```
GET /health
```

Returns service health status.

### Live Games
```
GET /api/v1/games/live?team_ids=sf,dal&league=NFL
```

Get live games for selected teams.

**Parameters:**
- `team_ids` (required): Comma-separated team IDs
- `league` (optional): Filter by NFL or NHL

### Upcoming Games
```
GET /api/v1/games/upcoming?team_ids=sf,dal&hours=24
```

Get upcoming games in next N hours.

**Parameters:**
- `team_ids` (required): Comma-separated team IDs
- `hours` (optional): Hours to look ahead (default: 24)
- `league` (optional): Filter by NFL or NHL

### Available Teams
```
GET /api/v1/teams?league=NFL
```

Get list of all available teams.

### API Usage
```
GET /api/v1/metrics/api-usage
```

Get API usage statistics and cache performance.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SPORTS_API_KEY` | API key for sports data provider | - |
| `SPORTS_API_PROVIDER` | Provider (espn, nhl_official) | espn |
| `PORT` | Service port | 8005 |
| `LOG_LEVEL` | Logging level | INFO |

### Team-Based Filtering

**Critical Feature:** Only fetches data for teams the user explicitly selects.

Benefits:
- Stays within free API tier limits (100 calls/day)
- Faster response times
- Lower memory usage
- Better user experience

Example: 3 teams selected = ~36 API calls/day (well within limit)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_cache_service.py -v
```

## Architecture

```
Client (Dashboard)
    ↓ HTTP
Sports Data Service (FastAPI)
    ├── API Clients (ESPN/NHL)
    ├── Cache Layer (15s-5m TTL)
    └── Team Filtering
        ↓ HTTP
External APIs (ESPN/NHL)
```

## Performance

- **Cache Hit Rate:** 80%+ expected
- **API Response:** <500ms
- **Live Game Updates:** 15s latency
- **Memory:** <128MB
- **CPU:** <5% average

## Rate Limiting

### Free Tier (ESPN API):
- 100 calls/day limit
- 3-5 teams recommended
- ~12 calls per team per day
- Caching prevents repeated calls

### Paid Tier (SportsData.io):
- Unlimited calls
- Advanced statistics
- Play-by-play data

## Error Handling

- **API Timeout:** 10s max, fallback to cache
- **API Error:** Return cached data if available
- **No Cache:** Return empty list with error message
- **Rate Limit:** Return 429 with retry-after header

## Monitoring

Health check endpoint includes:
- Service status
- Cache connectivity
- API connectivity
- Last update timestamp

## Future Improvements

- [ ] Redis for distributed caching
- [ ] Database for user preferences
- [ ] WebSocket for real-time updates
- [ ] More leagues (MLB, NBA, MLS)
- [ ] Enhanced team data from API

## License

Part of HA Ingestor project.

---

**Created:** October 12, 2025  
**Version:** 1.0.0  
**Status:** Production Ready (pending Docker integration)

