# Getting Started: Epic AI-4 Implementation
## N-Level Synergy Detection with HuggingFace Models

**Status:** Ready for Development  
**Created:** October 19, 2025  
**Story:** AI4.1 - Device Embedding Generation

---

## 🎯 Quick Start (5 Minutes)

### Prerequisites Check

```bash
# 1. Verify Python version (3.11+)
python --version

# 2. Check you're in the right directory
cd services/ai-automation-service

# 3. Verify base dependencies installed
pip list | grep -E "(transformers|optimum|openvino)"
```

### Installation Steps

```bash
# Step 1: Install dependencies (~3 minutes)
pip install -r requirements.txt
pip install -r requirements-nlevel.txt

# Step 2: Run database migration (~30 seconds)
cd ../..
alembic upgrade head

# Step 3: Quantize models (~5 minutes, one-time)
bash scripts/quantize-nlevel-models.sh

# Step 4: Verify setup (~10 seconds)
python scripts/verify-nlevel-setup.py
```

If all checks pass ✅, you're ready to start!

---

## 📚 What You're Building

### The Big Picture

**Epic AI-4** adds **multi-hop automation chain discovery** to the existing AI automation service. Instead of just suggesting 2-device automations (motion → light), we'll discover complex chains like:

```
Motion Sensor → Light → Thermostat → Music
(Presence detected → Turn on light → Adjust temp → Play music)
```

### Technology Stack

| Component | Purpose | Size | Speed |
|-----------|---------|------|-------|
| **sentence-transformers/all-MiniLM-L6-v2** | Device embeddings | 20MB | 50ms |
| **OpenVINO/bge-reranker-base-int8-ov** | Path quality ranking | 280MB | 80ms |
| **google/flan-t5-small** | Chain categorization | 80MB | 100ms |

**Total:** 380MB, <5s detection time

---

## 📋 Story AI4.1: Device Embedding Generation

### What You'll Build This Week

**Goal:** Generate semantic embeddings for all smart home devices so we can find similar devices for multi-hop chains.

**Week 1 (Days 1-5):**
1. Database setup (migration already created ✅)
2. Descriptor builder (natural language device descriptions)
3. Model integration (OpenVINO INT8 embedding model)
4. Generator implementation (batch processing + caching)
5. Unit tests

**Week 2 (Days 6-10):**
6. Integration testing with real data
7. Performance benchmarks
8. Code review and refinement
9. Documentation
10. Story completion

### File Structure Created

```
services/ai-automation-service/
├── src/nlevel_synergy/              ✅ NEW MODULE
│   ├── __init__.py                  ✅ Module exports
│   ├── descriptor_builder.py        ✅ Natural language generation
│   ├── embedding_model.py           ✅ OpenVINO model wrapper
│   ├── embedding_cache.py           ✅ In-memory cache
│   └── device_embedding_generator.py  🚧 TO IMPLEMENT
├── alembic/versions/
│   └── 20251019_add_nlevel_synergy_tables.py  ✅ Migration
├── requirements-nlevel.txt          ✅ Dependencies
└── tests/
    └── test_nlevel_synergy.py       🚧 TO IMPLEMENT

scripts/
├── quantize-nlevel-models.sh        ✅ Model setup
└── verify-nlevel-setup.py           ✅ Verification

models/nlevel-synergy/               ⏳ Will be created by setup script
├── embedding-int8/
├── reranker-int8/
└── classifier-int8/
```

---

## 🚀 Development Workflow

### Day 1-2: Database Setup & Descriptor Builder

**Tasks:**
1. ✅ Migration already created - just run it
2. ✅ Descriptor builder already implemented
3. Test descriptor generation manually

**Try it yourself:**

```python
# Test descriptor builder
from nlevel_synergy.descriptor_builder import DeviceDescriptorBuilder

builder = DeviceDescriptorBuilder()

# Example entity
entity = {
    'entity_id': 'binary_sensor.kitchen_motion',
    'device_class': 'motion',
    'area_id': 'kitchen'
}

# Generate descriptor
descriptor = builder.create_descriptor(device={}, entity=entity)
print(descriptor)
# Output: "motion sensor that detects presence in kitchen area"
```

**Acceptance:**
- [ ] Descriptor builder generates clear descriptions
- [ ] Handles missing data gracefully
- [ ] Supports all device types

### Day 3-4: Model Integration

**Tasks:**
1. ✅ Model wrapper already implemented
2. Run model quantization script
3. Test model loading and inference

**Try it yourself:**

```python
# Test embedding model
from nlevel_synergy.embedding_model import DeviceEmbeddingModel

model = DeviceEmbeddingModel()
model.load_model()

# Generate embeddings
texts = [
    "motion sensor that detects presence in kitchen area",
    "dimmable light with RGB color in living room area"
]

embeddings = model.encode(texts, normalize=True)
print(f"Shape: {embeddings.shape}")  # (2, 384)

# Calculate similarity
similarity = embeddings[0] @ embeddings[1]
print(f"Similarity: {similarity:.4f}")
```

**Acceptance:**
- [ ] Model loads successfully
- [ ] Generates 384-dim embeddings
- [ ] Inference <5ms per device
- [ ] Normalized embeddings (L2 norm ≈ 1.0)

### Day 5-7: Generator Implementation

**What to implement:**

Create `device_embedding_generator.py` with:
- Batch processing (32 devices at a time)
- 30-day caching strategy
- Error handling and logging
- Integration with data-api

**Starter template:**

```python
# services/ai-automation-service/src/nlevel_synergy/device_embedding_generator.py

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DeviceEmbeddingGenerator:
    """Generate and manage device embeddings."""
    
    def __init__(self, db_session, data_api_client, capability_service, cache_days=30):
        self.db = db_session
        self.data_api = data_api_client
        self.capability_service = capability_service
        self.cache_days = cache_days
        
        # Initialize components (already implemented)
        from .descriptor_builder import DeviceDescriptorBuilder
        from .embedding_model import DeviceEmbeddingModel
        
        self.descriptor_builder = DeviceDescriptorBuilder(capability_service)
        self.embedding_model = DeviceEmbeddingModel()
        self.embedding_model.load_model()
    
    async def generate_all_embeddings(self, force_refresh=False):
        """
        Generate embeddings for all devices.
        
        TODO: Implement this method
        Steps:
        1. Get all devices/entities from data-api
        2. Check cache (skip if fresh and not force_refresh)
        3. Generate descriptors for devices needing update
        4. Batch generate embeddings (32 at a time)
        5. Store in database
        6. Return statistics
        """
        pass
```

**Acceptance:**
- [ ] Generates embeddings for all devices
- [ ] Caches embeddings for 30 days
- [ ] Batch processing (32 devices)
- [ ] Error handling for failed devices
- [ ] Returns statistics dict

### Day 8-9: Testing

**Unit tests to write:**

```python
# tests/test_nlevel_synergy.py

import pytest
from nlevel_synergy import DeviceDescriptorBuilder, DeviceEmbeddingModel

class TestDescriptorBuilder:
    def test_motion_sensor_descriptor(self):
        """Test descriptor generation for motion sensor."""
        # TODO: Implement
        pass
    
    def test_light_descriptor_with_capabilities(self):
        """Test descriptor with device capabilities."""
        # TODO: Implement
        pass

class TestEmbeddingModel:
    def test_model_loading(self):
        """Test model loads successfully."""
        # TODO: Implement
        pass
    
    def test_embedding_generation(self):
        """Test embedding generation."""
        # TODO: Implement
        pass
```

**Run tests:**

```bash
# Run unit tests
pytest tests/test_nlevel_synergy.py -v

# Run with coverage
pytest tests/test_nlevel_synergy.py --cov=nlevel_synergy --cov-report=term-missing
```

**Acceptance:**
- [ ] 100% test coverage for descriptor builder
- [ ] 100% test coverage for embedding model
- [ ] Integration tests pass
- [ ] Performance benchmarks meet targets

---

## 🎓 Learning Resources

### Understanding Embeddings

**What are embeddings?**
- Numerical representations of text (384-dimensional vectors)
- Similar text → similar vectors
- Used for semantic search and similarity

**Example:**
```
"motion sensor in kitchen"    → [0.23, -0.15, 0.87, ..., 0.42]
"presence detector in kitchen" → [0.21, -0.17, 0.85, ..., 0.40]
                                  ↑ Very similar vectors!

"thermostat in bedroom"        → [-0.42, 0.73, -0.11, ..., 0.68]
                                  ↑ Different vector
```

### Key Concepts

**Semantic Similarity:**
```python
# Dot product of normalized vectors
similarity = embedding1 @ embedding2  # Range: -1 to 1
# High similarity (>0.7) = related devices
# Low similarity (<0.3) = unrelated devices
```

**Batch Processing:**
```python
# Efficient: Process 32 devices at once
embeddings = model.encode(texts, batch_size=32)

# Inefficient: One at a time
for text in texts:
    embedding = model.encode([text])  # Slow!
```

**Normalization:**
```python
# Normalized embeddings enable fast dot-product similarity
normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
similarity = normalized[0] @ normalized[1]  # Fast!
```

---

## 🐛 Troubleshooting

### Model Loading Fails

**Error:** `FileNotFoundError: Model not found`

**Solution:**
```bash
# Quantize models first
bash scripts/quantize-nlevel-models.sh

# Verify models exist
ls -lh models/nlevel-synergy/
```

### Database Migration Fails

**Error:** `alembic.util.exc.CommandError`

**Solution:**
```bash
# Check current version
alembic current

# Upgrade to latest
alembic upgrade head

# Verify tables
sqlite3 data/ai_automation.db ".schema device_embeddings"
```

### Memory Issues

**Error:** `RuntimeError: Out of memory`

**Solution:**
```python
# Reduce batch size
embeddings = model.encode(texts, batch_size=16)  # Instead of 32

# Clear cache
cache.clear()
```

---

## ✅ Definition of Done (Story AI4.1)

Before marking Story AI4.1 complete, verify:

### Code Complete
- [ ] `device_embedding_generator.py` implemented
- [ ] All unit tests passing (100% coverage)
- [ ] Integration tests passing
- [ ] Code reviewed and approved

### Performance
- [ ] Model size ≤25MB (INT8)
- [ ] Inference <5ms per device
- [ ] Cache hit rate >90% after initial run
- [ ] Embedding quality: same-class similarity >0.7

### Documentation
- [ ] Code comments complete
- [ ] API documentation updated
- [ ] Story completion notes in `implementation/`

### Integration
- [ ] Database migration applied
- [ ] Models quantized and tested
- [ ] No regressions in existing tests

---

## 🚀 Next Steps After Story AI4.1

Once Story AI4.1 is complete:

1. **Story AI4.2: Multi-Hop Path Discovery** (Week 3-4)
   - Implement BFS graph traversal
   - Similarity-guided device pairing
   - Path scoring algorithm

2. **Story AI4.3: Path Re-Ranking** (Week 5)
   - Integrate cross-encoder model
   - Quality ranking system

3. **Continue through Epic AI-4** (8-10 weeks total)
   - See `implementation/EPIC_AI4_IMPLEMENTATION_ROADMAP.md`

---

## 📞 Getting Help

### Resources
- **Epic Document:** `docs/prd/epic-ai4-nlevel-synergy-detection.md`
- **Story Document:** `docs/stories/story-ai4-01-device-embedding-generation.md`
- **Implementation Roadmap:** `implementation/EPIC_AI4_IMPLEMENTATION_ROADMAP.md`

### Context7 Best Practices
- Semantic search: `util.semantic_search()`
- Normalization: `util.normalize_embeddings()`
- Batch processing: `batch_size=32`

---

**Ready to start? Begin with Day 1 tasks! 🚀**

```bash
# Create feature branch
git checkout -b feature/ai4.1-device-embeddings

# Start coding!
code services/ai-automation-service/src/nlevel_synergy/device_embedding_generator.py
```

