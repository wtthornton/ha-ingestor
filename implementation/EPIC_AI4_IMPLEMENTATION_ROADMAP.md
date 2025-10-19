# Epic AI-4 Implementation Roadmap
## N-Level Synergy Detection with HuggingFace Models

**Status:** Ready for Implementation  
**Created:** October 19, 2025  
**Epic Document:** [docs/prd/epic-ai4-nlevel-synergy-detection.md](../docs/prd/epic-ai4-nlevel-synergy-detection.md)

---

## 📋 Quick Reference

**Total Duration:** 8-10 weeks  
**Total Story Points:** 47  
**Team Size:** 1-2 developers  
**Dependencies:** Epics AI-1, AI-2, AI-3 (complete)

**Key Deliverables:**
- ✅ Device embedding generation system
- ✅ Multi-hop path discovery algorithm
- ✅ Path re-ranking with cross-encoder
- ✅ Automation chain classification
- ✅ API integration + health dashboard UI
- ✅ Performance optimization (INT8 models)
- ✅ Comprehensive testing suite

---

## 🎯 Implementation Overview

### What We're Building

**N-Level Synergy Detection** extends the existing 2-device synergy detection to discover **multi-hop automation chains** (2-5 devices) using HuggingFace models optimized with OpenVINO INT8 quantization.

**Example Output:**
```json
{
  "chain": ["motion_sensor", "light", "thermostat"],
  "category": "comfort",
  "complexity": "medium",
  "score": 0.87,
  "rationale": "When motion detected in kitchen, turn on light, then adjust temperature"
}
```

### Technology Stack

| Component | Technology | Size | Speed |
|-----------|-----------|------|-------|
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 (INT8) | 20MB | 50ms |
| **Re-ranking** | OpenVINO/bge-reranker-base-int8-ov | 280MB | 80ms |
| **Classification** | google/flan-t5-small (INT8) | 80MB | 100ms |
| **TOTAL** | 3 models | **380MB** | **<5s** |

---

## 📅 Week-by-Week Implementation Plan

### Week 1-2: Story AI4.1 - Device Embedding Generation (8 points)

**Goal:** Generate semantic embeddings for all devices

**Tasks:**
1. **Day 1-2:** Database setup
   - Run migration: `alembic upgrade head`
   - Create `device_embeddings` table
   - Add columns to `synergy_opportunities`

2. **Day 3-4:** Descriptor builder
   - Implement `DeviceDescriptorBuilder` class
   - Create natural language device descriptions
   - Test with sample devices

3. **Day 5-6:** Model integration
   - Install dependencies: `pip install -r requirements-nlevel.txt`
   - Quantize models: `bash scripts/quantize-nlevel-models.sh`
   - Implement `DeviceEmbeddingModel` with OpenVINO
   - Test model loading and inference

4. **Day 7-8:** Generator implementation
   - Implement `DeviceEmbeddingGenerator`
   - Add caching logic (30-day refresh)
   - Batch processing (32 devices at a time)
   - Write unit tests

5. **Day 9-10:** Testing & integration
   - Integration tests with real data
   - Performance benchmarks
   - Code review and refinement

**Deliverables:**
- ✅ `device_embeddings` table with 20-50 embeddings
- ✅ Embedding generation script
- ✅ 100% test coverage for embedding generation
- ✅ Documentation

**Acceptance Criteria:**
- Model size ≤25MB (INT8)
- Inference <5ms per device
- Cache hit rate >90% after initial run
- Same-class similarity >0.7

---

### Week 3-4: Story AI4.2 - Multi-Hop Path Discovery (13 points)

**Goal:** Implement graph traversal to find automation chains

**Tasks:**
1. **Day 1-3:** BFS algorithm
   - Implement `MultiHopPathFinder` class
   - BFS search with configurable depth (2-5)
   - Similarity-guided device pairing
   - Avoid circular paths

2. **Day 4-5:** Path scoring
   - Semantic coherence calculation
   - Area consistency bonus
   - Domain diversity scoring
   - Combined score formula

3. **Day 6-7:** Compatible device pairing
   - Use `util.semantic_search()` (Context7 best practice)
   - Find top 5 similar devices per hop
   - Area boost (+0.1 similarity)
   - Filter visited devices

4. **Day 8-10:** Testing & optimization
   - Unit tests (BFS correctness)
   - Integration tests (end-to-end)
   - Performance optimization (<3s for depth=3)
   - Code review

**Deliverables:**
- ✅ Multi-hop path discovery algorithm
- ✅ 50-100 candidate paths per run
- ✅ Performance <3s for 20 devices, depth=3
- ✅ Comprehensive tests

**Acceptance Criteria:**
- Generates 50-100 candidate paths
- <3s for 20 devices, depth=3
- >70% paths are logically valid
- Memory <200MB

---

### Week 5: Story AI4.3 - Path Re-Ranking (5 points)

**Goal:** Re-rank paths using cross-encoder for quality

**Tasks:**
1. **Day 1-2:** Re-ranker integration
   - Load `OpenVINO/bge-reranker-base-int8-ov`
   - Implement `PathReranker` class
   - Batch processing (32 pairs)

2. **Day 3:** Path-to-description conversion
   - Natural language generation
   - Format: "When X, then Y, then Z"

3. **Day 4:** Score combination
   - Combine embedding + rerank scores (50/50)
   - Sort by final score
   - Return top 10 paths

4. **Day 5:** Testing
   - Unit tests
   - Integration tests
   - Performance benchmarks

**Deliverables:**
- ✅ Re-ranking system
- ✅ Top 10 highest-quality paths
- ✅ 80ms re-ranking time

**Acceptance Criteria:**
- Re-ranking <100ms (100 paths)
- +10-15% quality boost vs similarity alone
- Model size 280MB (pre-quantized)

---

### Week 6: Story AI4.4 - Chain Classification (5 points)

**Goal:** Classify chains by category and complexity

**Tasks:**
1. **Day 1-2:** Model integration
   - Quantize `google/flan-t5-small` to INT8
   - Implement `ChainClassifier` class
   - Structured prompt engineering

2. **Day 3:** Classification logic
   - Classify: energy, comfort, security, convenience
   - Complexity: easy, medium, advanced
   - Fallback parsing with keywords

3. **Day 4-5:** Testing
   - Labeled test dataset
   - Accuracy measurement
   - Prompt refinement

**Deliverables:**
- ✅ Chain classification system
- ✅ 75-80% accuracy
- ✅ 100ms per classification

**Acceptance Criteria:**
- Classification accuracy ≥75%
- Inference <100ms
- Model size 80MB (INT8)

---

### Week 7: Story AI4.5 - API Integration (3 points)

**Goal:** Expose n-level synergies via API

**Tasks:**
1. **Day 1-2:** API endpoint
   - Route: `GET /api/v1/synergies/nlevel`
   - Query params: max_depth, min_similarity, top_k
   - JSON response format

2. **Day 3:** Integration
   - Combine 2-level + n-level results
   - Sort by score
   - Deduplication

3. **Day 4-5:** Testing
   - API tests
   - Integration tests
   - Documentation

**Deliverables:**
- ✅ `/api/v1/synergies/nlevel` endpoint
- ✅ Combined synergy results
- ✅ API documentation

**Acceptance Criteria:**
- API response <6s (including detection)
- Proper error handling
- Complete documentation

---

### Week 8: Story AI4.6 - Performance Optimization (5 points)

**Goal:** Optimize for edge deployment

**Tasks:**
1. **Day 1-2:** Model optimization
   - Verify INT8 quantization
   - GPU acceleration (if available)
   - Model preloading

2. **Day 3:** Caching optimization
   - In-memory embedding cache
   - Lazy loading
   - LRU eviction

3. **Day 4-5:** Benchmarking
   - Run benchmark suite (10, 20, 50, 100 devices)
   - Memory profiling
   - Performance tuning

**Deliverables:**
- ✅ Optimized detection pipeline
- ✅ <5s for 20 devices, <500MB memory
- ✅ Comprehensive benchmarks

**Acceptance Criteria:**
- P95 latency <5s (20 devices)
- Peak memory <500MB
- Cache hit rate >80%

---

### Week 9-10: Story AI4.7 - Testing & Validation (8 points)

**Goal:** Comprehensive testing and validation

**Tasks:**
1. **Week 9 Day 1-3:** Test dataset creation
   - Create 50 sample homes
   - Label expected synergies
   - Edge cases

2. **Week 9 Day 4-5:** Accuracy testing
   - Precision/recall measurement
   - F1 score calculation
   - Manual review

3. **Week 10 Day 1-2:** Load testing
   - Stress tests (100+ devices)
   - Memory leak tests
   - Concurrency tests

4. **Week 10 Day 3-4:** User acceptance testing
   - Manual review of suggestions
   - User feedback collection
   - Comparison vs 2-level

5. **Week 10 Day 5:** Deployment prep
   - Final bug fixes
   - Documentation
   - Deployment checklist

**Deliverables:**
- ✅ Test dataset (50 homes)
- ✅ Accuracy metrics (80-85% precision)
- ✅ Production-ready system
- ✅ Complete documentation

**Acceptance Criteria:**
- Precision ≥80%
- Recall ≥70%
- F1 score ≥75%
- Manual approval ≥75%
- All performance targets met

---

## 🚀 Getting Started

### Prerequisites

1. **System Requirements:**
   - Python 3.11+
   - 2GB free disk space
   - 1GB RAM minimum
   - CPU with AVX2 support

2. **Dependencies:**
   ```bash
   # Install base requirements
   cd services/ai-automation-service
   pip install -r requirements.txt
   
   # Install n-level synergy dependencies
   pip install -r requirements-nlevel.txt
   ```

3. **Database Migration:**
   ```bash
   # Run migration
   alembic upgrade head
   
   # Verify tables created
   sqlite3 data/ai_automation.db ".schema device_embeddings"
   ```

4. **Model Setup:**
   ```bash
   # Quantize models (one-time, ~5 minutes)
   bash scripts/quantize-nlevel-models.sh
   
   # Verify models
   ls -lh models/nlevel-synergy/
   ```

### First Steps

1. **Start with Story AI4.1:**
   - Read story document: `docs/stories/story-ai4-01-device-embedding-generation.md`
   - Create feature branch: `git checkout -b feature/ai4.1-device-embeddings`
   - Follow week 1-2 implementation plan

2. **Development Workflow:**
   - Implement code
   - Write tests (TDD recommended)
   - Run tests: `pytest tests/test_nlevel_synergy.py`
   - Code review
   - Merge to main

3. **Testing:**
   ```bash
   # Unit tests
   pytest tests/test_device_embedding_generation.py -v
   
   # Integration tests
   pytest tests/integration/test_embedding_integration.py -v
   
   # Benchmarks
   python scripts/benchmark_nlevel_synergy.py
   ```

---

## 📊 Success Metrics Dashboard

### Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Detection Time (20 devices)** | <5s | ___ s | ⏳ |
| **Memory Usage** | <500MB | ___ MB | ⏳ |
| **Model Size** | 380MB | ___ MB | ⏳ |
| **Precision** | ≥80% | ___ % | ⏳ |
| **Recall** | ≥70% | ___ % | ⏳ |

### Milestone Checklist

- [ ] Story AI4.1: Device Embedding Generation (Week 1-2)
- [ ] Story AI4.2: Multi-Hop Path Discovery (Week 3-4)
- [ ] Story AI4.3: Path Re-Ranking (Week 5)
- [ ] Story AI4.4: Chain Classification (Week 6)
- [ ] Story AI4.5: API Integration (Week 7)
- [ ] Story AI4.6: Performance Optimization (Week 8)
- [ ] Story AI4.7: Testing & Validation (Week 9-10)
- [ ] Production deployment
- [ ] Health dashboard integration

---

## 🔗 Related Documentation

### Epic & Stories
- [Epic AI-4 PRD](../docs/prd/epic-ai4-nlevel-synergy-detection.md)
- [Story AI4.1: Device Embeddings](../docs/stories/story-ai4-01-device-embedding-generation.md)
- [Story AI4.2: Multi-Hop Discovery](../docs/stories/story-ai4-02-multihop-path-discovery.md)
- [Story AI4.3: Path Re-Ranking](../docs/stories/story-ai4-03-path-reranking.md)
- [Story AI4.4: Chain Classification](../docs/stories/story-ai4-04-chain-classification.md)
- [Story AI4.5: API Integration](../docs/stories/story-ai4-05-api-integration.md)
- [Story AI4.6: Performance Optimization](../docs/stories/story-ai4-06-performance-optimization.md)
- [Story AI4.7: Testing & Validation](../docs/stories/story-ai4-07-testing-validation.md)

### Technical References
- [OpenVINO INT8 Quantization Guide](https://docs.openvino.ai/latest/openvino_docs_model_optimization_guide.html)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [HuggingFace Optimum Intel](https://huggingface.co/docs/optimum/intel/index)

### Context7 Best Practices
- All implementation follows Context7-researched best practices
- Semantic search with `util.semantic_search()`
- OpenVINO INT8 quantization
- Batch processing optimization
- Structured prompts for classification

---

## ⚠️ Known Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Model accuracy <75%** | High | Medium | Improve prompts, add few-shot examples, fallback to rules |
| **Performance >5s** | Medium | Low | Optimize graph search, reduce candidate set, increase caching |
| **Memory >500MB** | Low | Low | Already using INT8, pre-quantized models |
| **Complex deployment** | Medium | Medium | Provide setup scripts, Docker image with models |

---

## 🎓 Learning Resources

### HuggingFace Models
- [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [bge-reranker-base-int8-ov](https://huggingface.co/OpenVINO/bge-reranker-base-int8-ov)
- [flan-t5-small](https://huggingface.co/google/flan-t5-small)

### OpenVINO
- [OpenVINO Getting Started](https://docs.openvino.ai/latest/get_started.html)
- [Model Optimization Guide](https://docs.openvino.ai/latest/openvino_docs_model_optimization_guide.html)

### Context7 Integration
- Memory ID 10014278: Proactive Context7 usage for library best practices
- Memory ID 10046243: Phase 1 MVP optimized local stack (OpenVINO INT8)

---

**Document Version:** 1.0  
**Last Updated:** October 19, 2025  
**Next Review:** Start of Week 1 (Story AI4.1 kickoff)  
**Owner:** Dev Team + BMad Master (AI Agent)

---

**Ready to start? Begin with Story AI4.1! 🚀**

