# AI Automation Service

AI-powered Home Assistant automation discovery and recommendation system.

## Overview

Analyzes Home Assistant historical data to detect patterns and suggest automations.

**Phase 1 MVP Features:**
- 🔍 Pattern Detection (time-of-day, co-occurrence, anomaly)
- 💡 Smart Suggestions (5-10 per week, AI-generated)
- ✅ User Approval Workflow
- 🚀 Auto-Deploy to Home Assistant

## Quick Start

### Prerequisites

- Python 3.11+
- Home Assistant with MQTT integration
- OpenAI API key
- Data API service running (port 8006)

### Configuration

1. Configure credentials in `infrastructure/env.ai-automation`
2. See `docs/stories/MQTT_SETUP_GUIDE.md` for details

### Running Locally

```bash
cd services/ai-automation-service

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start service
python -m uvicorn src.main:app --host 0.0.0.0 --port 8011 --reload
```

### Running with Docker

```bash
# From project root
docker-compose up -d ai-automation-service
```

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation
- `GET /api/suggestions` - List suggestions (Story 1.10)
- `POST /api/deploy/{id}` - Deploy automation (Story 1.11)

## Architecture

See PRD: `docs/prd/ai-automation/`

## Development

See implementation guides in story files: `docs/stories/story-ai1-*.md`

## Testing

```bash
pytest tests/
```

## Documentation

- **PRD:** `docs/prd/ai-automation/`
- **Stories:** `docs/stories/story-ai1-*.md`
- **MQTT Setup:** `docs/stories/MQTT_SETUP_GUIDE.md`

---

**Version:** 1.0.0  
**Epic:** Epic-AI-1  
**Status:** Phase 1 MVP In Development

