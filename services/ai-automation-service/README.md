# AI Automation Service

AI-powered Home Assistant automation discovery and recommendation system with device intelligence.

## Overview

**Epic AI-1: Pattern Automation** - Analyzes historical usage to detect patterns and suggest automations  
**Epic AI-2: Device Intelligence** - Discovers device capabilities and suggests unused features

### Features

**Pattern Detection (Epic AI-1):**
- 🔍 Time-of-day patterns (consistent usage times)
- 🔗 Device co-occurrence (frequently used together)
- ⚠️ Anomaly detection (repeated manual interventions)
- 💡 AI-generated automation suggestions

**Device Intelligence (Epic AI-2):**
- 📡 Universal device capability discovery (6,000+ Zigbee models)
- 📊 Utilization analysis (how much of device features you use)
- 💎 Feature suggestions (LED notifications, power monitoring, etc.)
- 🎯 Smart recommendations based on manufacturer specs

**Combined System:**
- 🤖 Unified daily batch job (3 AM)
- 💡 8-10 suggestions per day (mixed pattern + feature)
- ✅ User approval workflow
- 🚀 One-click deploy to Home Assistant

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

### Suggestions & Deployment
- `GET /api/suggestions` - List all suggestions (pattern + feature)
- `POST /api/deploy/{id}` - Deploy automation to Home Assistant
- `GET /api/suggestions/{id}` - Get specific suggestion

### Analysis & Patterns
- `POST /api/analysis/trigger` - Manually trigger analysis run
- `GET /api/analysis/status` - Check last analysis status
- `GET /api/patterns` - List detected patterns

### Device Intelligence
- `GET /api/device-intelligence/utilization` - Device utilization metrics
- `GET /api/device-intelligence/opportunities` - Unused feature opportunities
- `POST /api/device-intelligence/capabilities/refresh` - Refresh device capabilities

### System
- `GET /health` - Health check (includes device intelligence stats)
- `GET /docs` - OpenAPI documentation

## Architecture

**Unified Daily Batch Job (3 AM):**
1. Phase 1: Device Capability Update (Epic AI-2)
2. Phase 2: Fetch Events from InfluxDB (Shared)
3. Phase 3: Pattern Detection (Epic AI-1)
4. Phase 4: Feature Analysis (Epic AI-2)
5. Phase 5: Combined Suggestion Generation
6. Phase 6: Publish MQTT Notification

**Documentation:**
- PRD: `docs/prd.md` (Stories AI1.*, AI2.*)
- Epic AI-1 Stories: `docs/stories/story-ai1-*.md`
- Epic AI-2 Stories: `docs/stories/story-ai2-*.md`
- Architecture: `docs/architecture-device-intelligence.md`

## Development

### Epic AI-1 (Pattern Detection)
- Stories: `docs/stories/story-ai1-*.md`
- Components: `src/pattern_analyzer/`
- Tests: `tests/test_*_detector.py`

### Epic AI-2 (Device Intelligence)
- Stories: `docs/stories/story-ai2-*.md`
- Components: `src/device_intelligence/`
- Tests: `tests/test_feature_*.py`, `tests/test_database_models.py`

### Database
- **SQLite**: Patterns, suggestions, device capabilities, feature usage
- **Alembic migrations**: `alembic/versions/`
- **Models**: `src/database/models.py`

## Testing

```bash
pytest tests/
```

**Test Coverage:** 56/56 unit tests passing ✅

## Performance

- **Job Duration:** 7-15 minutes daily (3 AM)
- **Memory Usage:** 200-400MB peak
- **OpenAI Cost:** ~$0.003 per run (~$0.10/month)
- **Resource Reduction:** 99% less uptime vs real-time (2.5 hrs vs 730 hrs/month)

## Documentation

### User Documentation
- **PRD:** `docs/prd.md` (Complete product requirements)
- **Architecture:** `docs/architecture-device-intelligence.md`
- **Brief:** `docs/brief.md` (Project overview)

### Developer Documentation
- **Epic AI-1 Stories:** `docs/stories/story-ai1-*.md` (Pattern detection)
- **Epic AI-2 Stories:** `docs/stories/story-ai2-*.md` (Device intelligence)
- **MQTT Setup:** `docs/stories/MQTT_SETUP_GUIDE.md`
- **Implementation Guides:** `implementation/`

### Operations Documentation
- **Deployment:** `implementation/DEPLOYMENT_STORY_AI2-5.md`
- **Quick Reference:** `implementation/QUICK_REFERENCE_AI2.md`
- **Troubleshooting:** See deployment guide

---

**Version:** 2.0.0  
**Epic AI-1:** Complete (Pattern Detection)  
**Epic AI-2:** Complete (Device Intelligence - Stories 2.1-2.5)  
**Status:** Production Ready ✅

