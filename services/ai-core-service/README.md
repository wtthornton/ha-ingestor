# AI Core Service

**AI Orchestration & Pattern Detection for HomeIQ**

The AI Core Service is the central orchestrator for all AI operations in HomeIQ, coordinating multiple AI models for pattern detection, automation mining, and intelligent recommendations.

---

## 📊 Overview

**Port:** 8018
**Technology:** Python 3.11, FastAPI, Async
**Container:** `homeiq-ai-core-service`
**Phase:** Phase 1 AI Containerization (October 2025)

### Purpose

Orchestrate and coordinate AI services for:
- Pattern detection in home automation behavior
- Automation mining and discovery
- Multi-model AI coordination
- Intelligent recommendation generation

---

## 🎯 Features

### AI Model Orchestration
- Coordinates OpenVINO, ML, NER, and OpenAI services
- Multi-model pipeline management
- Async service-to-service communication
- Fallback and retry logic

### Pattern Detection
- Time-based pattern analysis
- Device usage correlation
- Behavioral clustering
- Anomaly detection

### Automation Mining
- Discovers automation opportunities
- Analyzes event sequences
- Suggests new automations
- Confidence scoring

---

## 🔌 API Endpoints

### Health & Status
```bash
GET /health                # Service health check
GET /api/v1/status         # Detailed status with AI service health
```

### Pattern Analysis
```bash
POST /api/v1/analyze       # Analyze patterns in event data
POST /api/v1/detect        # Detect automation opportunities
GET /api/v1/patterns       # Get discovered patterns
```

### AI Coordination
```bash
GET /api/v1/models         # List available AI models
GET /api/v1/models/{id}/status  # Get model status
```

---

## 🏗️ Architecture

### Service Dependencies

```
AI Core Service (8018)
├── OpenVINO Service (8026)     # Embeddings, re-ranking
├── ML Service (8025)           # Clustering, anomaly detection
├── NER Service (8019)          # Named entity recognition
└── OpenAI Service (8020)       # GPT-4o-mini
```

### Data Flow

```
Event Data (InfluxDB)
    ↓
AI Core Service
    ├→ OpenVINO: Generate embeddings
    ├→ ML Service: Cluster patterns
    ├→ NER: Extract entities
    └→ OpenAI: Generate automation text
    ↓
Automation Suggestions (SQLite)
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Service Configuration
AI_CORE_SERVICE_PORT=8018
LOG_LEVEL=INFO

# AI Service URLs
OPENVINO_SERVICE_URL=http://openvino-service:8019
ML_SERVICE_URL=http://ml-service:8020
NER_SERVICE_URL=http://ner-service:8019
OPENAI_SERVICE_URL=http://openai-service:8020

# OpenAI Configuration
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=homeiq
INFLUXDB_BUCKET=home_assistant_events

# Data API
DATA_API_URL=http://data-api:8006
```

---

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Start AI Core and all dependencies
docker-compose up ai-core-service

# View logs
docker-compose logs -f ai-core-service
```

### Standalone Docker

```bash
# Build
docker build -t homeiq-ai-core -f services/ai-core-service/Dockerfile .

# Run
docker run -p 8018:8018 \
  --env-file infrastructure/env.ai-automation \
  homeiq-ai-core
```

### Local Development

```bash
cd services/ai-core-service

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

---

## 📊 Performance

### Response Times
- Health check: <10ms
- Pattern analysis: 1-5s (depends on data volume)
- Automation suggestions: 2-10s (includes OpenAI API)

### Resource Usage
- Memory: 128-256MB baseline
- CPU: Low (orchestration only, models run in separate services)
- Startup: 5-10 seconds

---

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8018/health

# Check AI service status
curl http://localhost:8018/api/v1/status

# Analyze patterns
curl -X POST http://localhost:8018/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'
```

---

## 🔍 Troubleshooting

### Service Won't Start

**Check dependencies:**
```bash
# Ensure all AI services are running
docker-compose ps openvino-service ml-service ner-service openai-service
```

### AI Services Unreachable

**Check network:**
```bash
docker exec -it homeiq-ai-core-service ping openvino-service
```

### OpenAI API Errors

**Verify API key:**
```bash
# Check if OPENAI_API_KEY is set
docker exec homeiq-ai-core-service printenv | grep OPENAI
```

---

## 📚 Related Documentation

- [AI Automation Service](../ai-automation-service/README.md) - User-facing AI automation
- [OpenVINO Service](../openvino-service/README.md) - Embeddings and re-ranking
- [ML Service](../ml-service/README.md) - Clustering and anomaly detection
- [Phase 1 AI Documentation](../ai-automation-service/README-PHASE1-MODELS.md)

---

## 🤝 Integration

### Used By
- AI Automation Service (8024)
- Automation Miner (8029)
- Device Intelligence Service (8028)

### Uses
- OpenVINO Service (8026)
- ML Service (8025)
- NER Service (8019)
- OpenAI Service (8020)
- Data API (8006)
- InfluxDB (8086)

---

**Version:** 1.0.0 (Phase 1)
**Status:** ✅ Production Ready
**Last Updated:** October 25, 2025
