# Automation Miner

Community knowledge crawler for Home Assistant automations.

## Overview

The Automation Miner service crawls high-quality Home Assistant automations from community sources (Discourse, GitHub), normalizes them into structured metadata, and provides a query API for the AI Automation service.

**Epic:** AI-4 (Community Knowledge Augmentation)  
**Story:** AI4.1 (Community Corpus Foundation)

## Features

- **Selective Crawling:** Only fetches high-quality automations (500+ votes)
- **Normalization:** Extracts structured metadata (devices, integrations, use cases)
- **Storage:** SQLite-based corpus with query API
- **Performance:** <100ms query response time
- **Quality:** 2,000+ automations, avg quality ≥0.7

## Architecture

```
automation-miner (Port 8019)
├─ Crawler (DiscourseClient, GitHubClient)
├─ Parser (AutomationParser, PII removal, deduplication)
├─ Storage (SQLite corpus via SQLAlchemy)
├─ Query API (FastAPI endpoints)
└─ Health Check (/health)
```

## API Endpoints

### Query API
- `GET /api/automation-miner/corpus/search` - Search automations
- `GET /api/automation-miner/corpus/stats` - Corpus statistics
- `GET /api/automation-miner/corpus/{id}` - Get single automation
- `GET /health` - Health check

### Query Parameters
- `device` - Filter by device type (e.g., "light", "motion_sensor")
- `integration` - Filter by integration (e.g., "mqtt", "zigbee2mqtt")
- `use_case` - Filter by use case ("energy", "comfort", "security", "convenience")
- `min_quality` - Minimum quality score (0.0-1.0, default 0.7)
- `limit` - Maximum results (default 50)

## Database Schema

**Table:** `community_automations`
- `id` - Primary key
- `source` - 'discourse' or 'github'
- `source_id` - Unique post/repo ID
- `title` - Automation title
- `description` - Normalized description (PII removed)
- `devices` - JSON array of device types
- `integrations` - JSON array of integrations
- `triggers` - JSON array of trigger metadata
- `conditions` - JSON array of condition metadata
- `actions` - JSON array of action metadata
- `use_case` - 'energy', 'comfort', 'security', or 'convenience'
- `complexity` - 'low', 'medium', or 'high'
- `quality_score` - 0.0-1.0 (calculated from votes, recency, completeness)
- `vote_count` - Number of community votes
- `created_at` - Original post creation date
- `updated_at` - Last update date
- `last_crawled` - Last crawl timestamp
- `metadata` - JSON for additional data

## Installation

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start server
uvicorn src.api.main:app --reload --port 8019
```

### Docker

```bash
# Build image
docker build -t automation-miner .

# Run container
docker run -p 8019:8019 -v $(pwd)/data:/app/data automation-miner
```

### Docker Compose

```yaml
automation-miner:
  build: ./services/automation-miner
  ports:
    - "8019:8019"
  volumes:
    - ./services/automation-miner/data:/app/data
  environment:
    - ENABLE_AUTOMATION_MINER=true
  healthcheck:
    test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8019/health')"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Configuration

Environment variables:
- `ENABLE_AUTOMATION_MINER` - Enable/disable service (default: false)
- `MINER_DB_PATH` - Database file path (default: data/automation_miner.db)
- `DISCOURSE_BASE_URL` - Discourse API base URL (default: https://community.home-assistant.io)
- `GITHUB_TOKEN` - Optional GitHub API token (for higher rate limits)

## Usage

### Search Automations

```bash
# Search by device
curl "http://localhost:8019/api/automation-miner/corpus/search?device=motion_sensor&limit=10"

# Search by use case
curl "http://localhost:8019/api/automation-miner/corpus/search?use_case=security&min_quality=0.8"

# Get statistics
curl "http://localhost:8019/api/automation-miner/corpus/stats"
```

### Example Response

```json
{
  "automations": [
    {
      "id": 1,
      "title": "Motion-activated night lighting",
      "description": "Turn on lights when motion detected at night",
      "devices": ["motion_sensor", "light"],
      "integrations": ["mqtt", "zigbee2mqtt"],
      "use_case": "comfort",
      "complexity": "low",
      "quality_score": 0.89,
      "vote_count": 542
    }
  ],
  "count": 1
}
```

## Development

### Run Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Coverage
pytest --cov=src --cov-report=html
```

### Manual Crawl

```bash
# Trigger initial crawl
python -m src.cli crawl --initial

# Dry run (no database changes)
python -m src.cli crawl --dry-run
```

## Performance Targets

- **Initial Crawl:** <3 hours for 2,000-3,000 automations
- **Query API:** <100ms p95 response time
- **Storage:** <500MB database size
- **Memory:** <200MB crawler peak usage

## Quality Targets

- **Corpus Size:** 2,000+ automations
- **Avg Quality:** ≥0.7
- **Device Coverage:** 50+ unique device types
- **Integration Coverage:** 30+ integrations
- **Deduplication:** <5% duplicates

## Troubleshooting

### Health Check Failing
```bash
# Check service status
curl http://localhost:8019/health

# Check logs
docker logs automation-miner

# Verify database
sqlite3 data/automation_miner.db "SELECT COUNT(*) FROM community_automations;"
```

### Crawl Failing
- Check rate limits (Discourse: 2 req/sec)
- Verify network connectivity
- Check API endpoint availability
- Review logs for HTTP errors

## Integration

The Automation Miner integrates with:
- **Story AI4.2:** Pattern Enhancement (queries corpus during pattern detection)
- **Story AI4.3:** Device Discovery (provides device recommendations)
- **Story AI4.4:** Weekly Refresh (incremental corpus updates)

## License

See project LICENSE file.

## Authors

- BMad Master (Epic AI-4 design)
- Dev Agent (Implementation)

