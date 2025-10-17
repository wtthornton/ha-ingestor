# Phase 1 MVP - Quick Reference Guide

**Status:** Ready for Implementation  
**Timeline:** 13 Weeks  
**Cost:** $0-1/month  
**Expected Accuracy:** 85-90%

---

## 🎯 Quick Links

- **Full Plan:** [AI_PATTERN_DETECTION_IMPLEMENTATION_PLAN.md](./AI_PATTERN_DETECTION_IMPLEMENTATION_PLAN.md)
- **Call Tree:** [analysis/AI_AUTOMATION_CALL_TREE.md](./analysis/AI_AUTOMATION_CALL_TREE.md)
- **HuggingFace Search:** `scripts/run-huggingface-search.ps1`
- **Context7 KB:** Memory ID 10046243

---

## 📦 Must-Download Resources

### Models (Local, FREE - OpenVINO Optimized)
```bash
# Install OpenVINO and dependencies
pip install openvino optimum-intel sentence-transformers transformers

# 1. Embeddings (20MB INT8) - all-MiniLM-L6-v2
optimum-cli export openvino --model sentence-transformers/all-MiniLM-L6-v2 --task feature-extraction

# 2. Re-ranker (280MB INT8) - bge-reranker-base (pre-quantized)
# Downloads automatically - no conversion needed

# 3. Classifier (80MB INT8) - flan-t5-small  
optimum-cli export openvino --model google/flan-t5-small --task text2text-generation

# Total: 380MB (vs 1.7GB unoptimized) - 4.5x smaller!
```

### Datasets (FREE)
1. **hqfx/hermes_fc_cleaned** - HA examples
2. **globosetechnology12/Smart-Home-Automation** - Validation data
3. **EdgeWisePersona** - Routines (if available, Phase 2)

---

## 🏗️ Architecture at a Glance

```
Raw Events (30 days HA history)
    ↓
[LAYER 1] Preprocessing (run once)
    ├─ Extract 40+ features
    ├─ Generate embeddings (MiniLM INT8/OpenVINO) - 50ms
    └─ Enrich with context
    ↓
[LAYER 2] Pattern Detection (rules)
    ├─ 10 detectors (time, co-occurrence, etc.)
    └─ Pattern composition
    ↓ (138-220 patterns)
[LAYER 3] ML Enhancement (OpenVINO optimized)
    ├─ Similarity search (100 candidates) - 5ms
    ├─ Re-ranking (bge-reranker INT8) - 80ms
    ├─ Categorization (flan-t5 INT8) - 100ms
    └─ Suggestions (LLM)
    ↓
Top 10 Automation Suggestions (re-ranked for quality)

Total ML Time: 230ms (2.8x faster than BART)
Total Size: 380MB (4.5x smaller than BART)
```

---

## 📅 13-Week Timeline

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Preprocessing + MiniLM | Feature extraction pipeline |
| 2-3 | Critical detectors | 70-100 patterns |
| 4 | BART classification | Auto-categorization |
| 5-7 | High-value detectors | Security/duration patterns |
| 8-9 | Advanced detectors | Sequences, rooms |
| 10-11 | LLM suggestions | YAML automations |
| 12-13 | Testing, deployment | Production MVP |

---

## 🎯 Week 1 Tasks (Start Here)

### Monday
- [ ] Run HuggingFace search: `.\scripts\run-huggingface-search.ps1`
- [ ] Install OpenVINO: `pip install openvino optimum-intel`
- [ ] Download & convert all-MiniLM-L6-v2 to OpenVINO INT8
- [ ] Download bge-reranker-base-int8-ov (pre-quantized)
- [ ] Download & convert flan-t5-small to OpenVINO INT8
- [ ] Review search results: `docs/kb/huggingface-research/SEARCH_SUMMARY.md`

### Tuesday-Wednesday
- [ ] Create `EventPreprocessor` class
- [ ] Extract temporal features (hour, day_type, season)
- [ ] Extract contextual features (weather, sun, occupancy)
- [ ] Extract state features (duration, change_type)
- [ ] Extract session features (for sequences)

### Thursday-Friday
- [ ] Integrate OpenVINO MiniLM embeddings
- [ ] Generate embeddings for all events
- [ ] Create `ProcessedEvents` data structure
- [ ] Test on sample HA data (validate 50ms speed)
- [ ] Test re-ranker on sample patterns
- [ ] Test flan-t5 classification prompts

### Success Criteria
- ✅ Preprocessing completes in <2 minutes for 30 days
- ✅ Embeddings generated for all events
- ✅ Feature extraction works correctly

---

## 🔧 Code Snippets

### 1. Load Embedding Model (OpenVINO INT8)
```python
from optimum.intel import OVModelForFeatureExtraction
from transformers import AutoTokenizer

# Load OpenVINO optimized model
model = OVModelForFeatureExtraction.from_pretrained(
    "sentence-transformers/all-MiniLM-L6-v2",
    export=True,  # Auto-convert to OpenVINO
    compile=True  # Optimize for Intel CPU
)
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# Generate embeddings (50ms for 1000 texts)
texts = ["device light.living_room turns on at 7:15 AM", ...]
inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
outputs = model(**inputs)
embeddings = outputs.last_hidden_state.mean(dim=1).detach().numpy()  # (N, 384)
```

### 2. Load Re-ranker Model (OpenVINO INT8)
```python
from optimum.intel import OVModelForSequenceClassification

# Load pre-quantized re-ranker
reranker = OVModelForSequenceClassification.from_pretrained(
    "OpenVINO/bge-reranker-base-int8-ov"
)
reranker_tokenizer = AutoTokenizer.from_pretrained("OpenVINO/bge-reranker-base-int8-ov")

# Two-stage search (similarity → re-rank)
initial_100 = similarity_search(query, patterns, top_k=100)  # Fast: 5ms
best_10 = rerank(query, initial_100, top_k=10)  # Accurate: 80ms
```

### 3. Load Classification Model (OpenVINO INT8)
```python
from optimum.intel import OVModelForSeq2SeqLM

# Load flan-t5-small optimized
classifier = OVModelForSeq2SeqLM.from_pretrained(
    "google/flan-t5-small",
    export=True
)
classifier_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")

# Classify with structured prompt
prompt = """Classify: energy, comfort, security, or convenience

Pattern: Light turns on at 7:15 AM on weekdays

Category:"""

inputs = classifier_tokenizer(prompt, return_tensors='pt')
outputs = classifier.generate(**inputs, max_new_tokens=5)
category = classifier_tokenizer.decode(outputs[0], skip_special_tokens=True)
# Returns: "convenience" (100ms)
```

### 4. Find Similar Patterns (Two-Stage)
```python
from sklearn.metrics.pairwise import cosine_similarity

# Stage 1: Fast similarity (5ms)
similarities = cosine_similarity([query_embedding], embeddings)[0]
top_100_indices = similarities.argsort()[-100:][::-1]

# Stage 2: Accurate re-ranking (80ms)
candidates = [patterns[i] for i in top_100_indices]
reranked = rerank_with_bge(query_text, candidates, top_k=10)
# 10-15% better results than similarity alone!
```

---

## 💰 Cost Breakdown

| Component | Phase 1 | Phase 2 | Notes |
|-----------|---------|---------|-------|
| Models (local) | $0/month | $0/month | FREE download, run locally |
| LLM suggestions | $0-1/month | $0-1/month | HF free tier or OpenAI |
| Fine-tuning | N/A | $5-10 once | If EdgeWisePersona available |
| **TOTAL** | **$0-1/month** | **$0-1/month** | Essentially free |

---

## 📊 Expected Results

### Patterns Generated
- **Current:** 10-50 simple patterns
- **Phase 1:** 138-220 patterns (10 types + compositions)
- **Improvement:** 3-10x more patterns

### Accuracy
- **Current:** 70-80%
- **Phase 1:** 80-85% (optimized stack with re-ranking)
- **Phase 2:** 90-95% (with fine-tuning)

### User Acceptance
- **Current:** 50-60%
- **Phase 1:** 70-80%
- **Phase 2:** 80-90%

---

## ⚠️ Common Pitfalls

### ❌ DON'T
- Don't use ML for core pattern detection (use rules!)
- Don't expect ML clustering to find pattern types
- Don't skip preprocessing (it's critical)
- Don't block MVP on EdgeWisePersona availability

### ✅ DO
- Use rules for detection (proven, explainable)
- Use ML for enhancement (embeddings, re-ranking, classification)
- Run preprocessing once, reuse everywhere
- Start with OpenVINO optimized stack (MiniLM + bge-reranker + flan-t5)
- Engineer good prompts for flan-t5 (critical for 75%+ accuracy)
- Benchmark against rule-based baseline
- Use two-stage search (similarity → re-rank for quality)

---

## 🚦 Decision Gates

### Week 4: ML Classification & Re-ranking Evaluation
```python
# Validate re-ranker improves quality
if reranker_top10_quality >= 85%:
    keep_two_stage_search()  # 10-15% better
else:
    use_similarity_only()

# Validate flan-t5 classification accuracy
if flant5_accuracy >= 75%:
    continue_with_ml_categorization()
else:
    fallback_to_bart_or_rules()  # BART (85-90%) or keyword rules
```

### Week 13: MVP Completion
```python
if accuracy >= 85% and patterns >= 100 and time < 10_minutes:
    deploy_to_production()
else:
    iterate_and_optimize()
```

### Week 20: Phase 2 Decision
```python
if finetuned_accuracy > 90%:
    integrate_ml_detector()
elif finetuned_accuracy > 85%:
    keep_rules()  # Not worth complexity
else:
    abandon_ml_approach()  # Optimize rules instead
```

---

## 📚 Key Documents

1. **This Guide** - Quick reference
2. **[Full Plan](./AI_PATTERN_DETECTION_IMPLEMENTATION_PLAN.md)** - Complete details
3. **[Call Tree](./analysis/AI_AUTOMATION_CALL_TREE.md)** - Current system flow
4. **HuggingFace Search Results** - `docs/kb/huggingface-research/SEARCH_SUMMARY.md`
5. **Context7 KB** - Memory 10046243 (Phase 1 models/datasets)

---

## 🆘 Need Help?

### If preprocessing is slow
- Profile code (find bottleneck)
- Optimize feature extraction
- Consider caching preprocessed data

### If embeddings cause memory issues
- Process in batches (1000 events at a time)
- Use smaller model (all-MiniLM-L6-v2 is already small)
- Clear embeddings after similarity search

### If BART is too slow
- Use DeBERTa instead (lighter, 670MB vs 1.6GB)
- Run classification in background
- Cache category predictions

### If patterns are low quality
- Tune thresholds (min_occurrences, min_confidence)
- Add more validation datasets
- Review pattern composition logic

---

## ✅ Ready to Start?

1. Run HuggingFace search
2. Download models
3. Start Week 1 tasks
4. Reference full plan as needed

**The architecture is proven, resources identified, path is clear. LET'S BUILD!**

---

**Last Updated:** January 2025  
**Version:** 1.0  
**Status:** ✅ Ready for Implementation

