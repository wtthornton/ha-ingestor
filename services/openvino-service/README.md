# OpenVINO Service

**AI Model Inference with Intel OpenVINO - Embeddings, Re-ranking, and Classification**

Containerized AI service providing fast model inference using Intel OpenVINO optimization for embeddings generation, document re-ranking, and text classification.

---

## 📊 Overview

**Port:** 8026 (external) → 8019 (internal)
**Technology:** Python 3.11, OpenVINO, Transformers, FastAPI
**Container:** `homeiq-openvino-service`
**Phase:** Phase 1 AI Containerization (October 2025)

### Purpose

High-performance AI inference for:
- Text embedding generation (semantic search)
- Document re-ranking (relevance scoring)
- Text classification (intent detection)
- Optimized with Intel OpenVINO toolkit

---

## 🎯 Features

### Models Included

1. **all-MiniLM-L6-v2** (Sentence Transformers)
   - Purpose: Generate text embeddings
   - Dimensions: 384
   - Use case: Semantic search, clustering

2. **bge-reranker-base** (BAAI)
   - Purpose: Re-rank documents by relevance
   - Use case: Search result optimization

3. **flan-t5-small** (Google)
   - Purpose: Text classification
   - Use case: Intent detection, categorization

### OpenVINO Optimization

- 2-3x faster inference vs standard PyTorch
- Reduced memory footprint
- INT8 quantization support
- CPU-optimized execution

---

## 🔌 API Endpoints

### Embeddings

```bash
POST /embed
Content-Type: application/json

{
  "text": "Turn off living room lights",
  "model": "all-MiniLM-L6-v2"
}

Response:
{
  "embedding": [0.123, -0.456, ...],  # 384 dimensions
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384,
  "inference_time_ms": 45
}
```

### Re-ranking

```bash
POST /rerank
Content-Type: application/json

{
  "query": "turn on lights",
  "documents": [
    "light.living_room is currently off",
    "light.bedroom is currently on",
    "switch.hallway controls multiple lights"
  ]
}

Response:
{
  "ranked_documents": [
    {"text": "light.living_room is currently off", "score": 0.92},
    {"text": "switch.hallway controls multiple lights", "score": 0.76},
    {"text": "light.bedroom is currently on", "score": 0.43}
  ],
  "model": "bge-reranker-base",
  "inference_time_ms": 120
}
```

### Classification

```bash
POST /classify
Content-Type: application/json

{
  "text": "What's the temperature in the bedroom?",
  "labels": ["query", "command", "question"]
}

Response:
{
  "label": "question",
  "confidence": 0.89,
  "all_scores": {
    "question": 0.89,
    "query": 0.08,
    "command": 0.03
  }
}
```

### Health

```bash
GET /health

Response:
{
  "status": "healthy",
  "models_loaded": 3,
  "openvino_version": "2024.0",
  "models": {
    "embeddings": "all-MiniLM-L6-v2",
    "reranker": "bge-reranker-base",
    "classifier": "flan-t5-small"
  }
}
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Service Configuration
OPENVINO_SERVICE_PORT=8019
LOG_LEVEL=INFO

# Model Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANKER_MODEL=BAAI/bge-reranker-base
CLASSIFIER_MODEL=google/flan-t5-small

# OpenVINO Settings
OPENVINO_DEVICE=CPU
OPENVINO_NUM_THREADS=4
OPENVINO_ENABLE_CACHING=true

# Performance
MODEL_CACHE_DIR=/app/.cache/models
MAX_BATCH_SIZE=32
```

---

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Start service (takes 60-90 seconds for model loading)
docker-compose up openvino-service

# Check health
curl http://localhost:8026/health
```

### Standalone Docker

```bash
# Build
docker build -t homeiq-openvino -f services/openvino-service/Dockerfile .

# Run (models will download on first run)
docker run -p 8026:8019 \
  -v openvino_cache:/app/.cache \
  homeiq-openvino
```

### Local Development

```bash
cd services/openvino-service

# Install dependencies (including OpenVINO)
pip install -r requirements.txt

# Download models (first run only)
python -c "from transformers import AutoTokenizer, AutoModel; \
  AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')"

# Run
python src/main.py
```

---

## 📊 Performance

### Model Loading Times
- First startup: 60-90 seconds (downloads + optimization)
- Subsequent startups: 10-15 seconds (cached models)
- Hot reload: Not required

### Inference Performance

| Operation | Avg Time | Batch (32) |
|-----------|----------|------------|
| Embedding (single) | 20-50ms | 200-400ms |
| Re-rank (10 docs) | 80-150ms | 500-800ms |
| Classification | 30-70ms | 150-300ms |

### Resource Usage
- Memory: 512MB-1GB (model dependent)
- CPU: 2-4 cores recommended
- Storage: ~500MB (cached models)

---

## 🏗️ Architecture

### Model Pipeline

```
FastAPI Service (8019)
├── Model Manager
│   ├── Load models on startup
│   ├── OpenVINO optimization
│   └── Cache management
├── Embedding Endpoint
│   └── all-MiniLM-L6-v2 (384 dims)
├── Reranker Endpoint
│   └── bge-reranker-base
└── Classifier Endpoint
    └── flan-t5-small
```

### OpenVINO Conversion

```python
# Models are converted to OpenVINO IR format
Original PyTorch Model
    ↓
ONNX Export
    ↓
OpenVINO IR (XML + BIN)
    ↓
Optimized Inference
```

---

## 🧪 Testing

### Unit Tests

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Manual Testing

```bash
# Test embeddings
curl -X POST http://localhost:8026/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}'

# Test re-ranking
curl -X POST http://localhost:8026/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "automation",
    "documents": ["lights", "automation", "sensors"]
  }'
```

---

## 🔍 Troubleshooting

### Long Startup Time (>2 minutes)

**Cause:** Models downloading for first time

**Solution:**
```bash
# Pre-download models before deployment
docker run --rm homeiq-openvino python -c "
from transformers import AutoModel
AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
"
```

### High Memory Usage

**Optimization:**
```bash
# Enable model quantization (in code)
# Convert models to INT8 for lower memory
OPENVINO_PRECISION=INT8
```

### Slow Inference

**Check CPU:**
```bash
# Increase thread count
OPENVINO_NUM_THREADS=8  # Match CPU cores
```

---

## 📚 Related Documentation

- [AI Core Service](../ai-core-service/README.md) - AI orchestration
- [ML Service](../ml-service/README.md) - Clustering
- [Phase 1 AI Models](../ai-automation-service/README-PHASE1-MODELS.md)
- [OpenVINO Toolkit](https://docs.openvino.ai/)

---

## 🤝 Integration

### Used By
- AI Core Service (8018)
- AI Automation Service (8024)
- Automation Miner (8029)

### Model Sources
- HuggingFace Transformers
- Sentence Transformers
- BAAI (Beijing Academy of AI)

---

## 🔧 Development

### Adding New Models

```python
# services/openvino-service/src/models.py
class ModelManager:
    def load_custom_model(self, model_name: str):
        # Load from HuggingFace
        model = AutoModel.from_pretrained(model_name)

        # Convert to OpenVINO
        ov_model = convert_to_openvino(model)

        return ov_model
```

### Model Caching

```bash
# Models cached in volume
docker volume inspect homeiq_openvino_cache

# Clear cache
docker volume rm homeiq_openvino_cache
```

---

**Version:** 1.0.0 (Phase 1)
**Status:** ✅ Production Ready
**Last Updated:** October 25, 2025
**OpenVINO Version:** 2024.0
