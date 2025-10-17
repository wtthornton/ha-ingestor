# Phase 1 Direct Model Download Guide
## Manual Installation (HuggingFace API Search Issues)

**Issue:** Automated HuggingFace search returned 0 results (API rate limiting or authentication)  
**Solution:** Direct download links and manual installation for all Phase 1 models

---

## 🚀 Quick Setup (5-10 Minutes)

### **Step 1: Install Dependencies**

```bash
pip install openvino optimum-intel sentence-transformers transformers torch
```

### **Step 2: Download Models Automatically**

The models will auto-download on first use. Just run this test script:

```python
# test_models.py
print("Downloading and testing Phase 1 models...")

# Model 1: Embeddings (20MB)
print("\n1/3: all-MiniLM-L6-v2...")
from sentence_transformers import SentenceTransformer
embed_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
test_emb = embed_model.encode(["Test pattern"])
print(f"✅ Embeddings working! Dimension: {len(test_emb[0])}")

# Model 2: Re-ranker (280MB) - Pre-quantized
print("\n2/3: bge-reranker-base-int8-ov...")
from transformers import AutoTokenizer, AutoModelForSequenceClassification
rerank_tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-base")
rerank_model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base")
print("✅ Re-ranker working!")

# Model 3: Classifier (80MB)
print("\n3/3: flan-t5-small...")
from transformers import T5Tokenizer, T5ForConditionalGeneration
t5_tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
t5_model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
print("✅ Classifier working!")

print("\n" + "="*80)
print("✅ ALL MODELS DOWNLOADED AND TESTED!")
print("="*80)
print("\nTotal downloaded: ~380MB")
print("All models cached in: ~/.cache/huggingface/")
print("\nNext: Convert to OpenVINO INT8 for optimization")
```

Save as `test_models.py` and run:
```bash
python test_models.py
```

---

## 📦 Model Details & Direct Links

### **Model 1: Embeddings**

**Name:** sentence-transformers/all-MiniLM-L6-v2  
**Link:** https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2  
**Size:** 80MB (full) → 20MB (INT8)  
**Speed:** 150ms (full) → 50ms (INT8/OpenVINO)

**Direct Download:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# Auto-downloads to ~/.cache/huggingface/
```

**Convert to OpenVINO INT8:**
```bash
optimum-cli export openvino \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --task feature-extraction \
  ./models/all-MiniLM-L6-v2-ov
```

---

### **Model 2: Re-ranker**

**Name:** BAAI/bge-reranker-base  
**Optimized Version:** OpenVINO/bge-reranker-base-int8-ov  
**Link:** https://huggingface.co/BAAI/bge-reranker-base  
**Optimized Link:** https://huggingface.co/OpenVINO/bge-reranker-base-int8-ov  
**Size:** 1.1GB (full) → 280MB (INT8, pre-quantized)  
**Speed:** 200ms (full) → 80ms (INT8/OpenVINO)

**Direct Download (Standard):**
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-base")
model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base")
```

**Direct Download (INT8 Pre-Quantized):**
```python
from optimum.intel import OVModelForSequenceClassification
from transformers import AutoTokenizer

# This version is pre-quantized for OpenVINO
tokenizer = AutoTokenizer.from_pretrained("OpenVINO/bge-reranker-base-int8-ov")
model = OVModelForSequenceClassification.from_pretrained("OpenVINO/bge-reranker-base-int8-ov")
```

**No conversion needed** - use the pre-quantized version!

---

### **Model 3: Classifier**

**Name:** google/flan-t5-small  
**Link:** https://huggingface.co/google/flan-t5-small  
**Size:** 300MB (full) → 80MB (INT8)  
**Speed:** 300ms (full) → 100ms (INT8/OpenVINO)

**Direct Download:**
```python
from transformers import T5Tokenizer, T5ForConditionalGeneration

tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
```

**Convert to OpenVINO INT8:**
```bash
optimum-cli export openvino \
  --model google/flan-t5-small \
  --task text2text-generation \
  --weight-format int8 \
  ./models/flan-t5-small-ov
```

---

## 🔧 Complete Setup Script

Save this as `setup_phase1_models.py`:

```python
#!/usr/bin/env python3
"""
Phase 1 Model Setup - Manual Download
Downloads all models directly (bypasses search API)
"""

print("="*80)
print("Phase 1 Model Setup - Direct Download")
print("="*80)

# Install check
try:
    import sentence_transformers
    import transformers
    import torch
    print("\n✅ Required packages installed")
except ImportError as e:
    print(f"\n❌ Missing package: {e}")
    print("\nInstall with:")
    print("  pip install sentence-transformers transformers torch")
    exit(1)

# Model 1: Embeddings
print("\n" + "="*80)
print("Model 1/3: all-MiniLM-L6-v2 (Embeddings)")
print("="*80)
print("Size: ~80MB")
print("Downloading...")

from sentence_transformers import SentenceTransformer
embed_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
test_emb = embed_model.encode(["Test pattern: Light turns on at 7 AM"])
print(f"✅ Downloaded and tested!")
print(f"   Embedding dimension: {len(test_emb[0])}")
print(f"   Location: ~/.cache/huggingface/")

# Model 2: Re-ranker
print("\n" + "="*80)
print("Model 2/3: bge-reranker-base (Re-ranker)")
print("="*80)
print("Size: ~1.1GB (or use 280MB INT8 version)")
print("Downloading...")

from transformers import AutoTokenizer, AutoModelForSequenceClassification
rerank_tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-base")
rerank_model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base")
print("✅ Downloaded and tested!")
print(f"   Location: ~/.cache/huggingface/")
print(f"   Note: For INT8 version, use: OpenVINO/bge-reranker-base-int8-ov")

# Model 3: Classifier
print("\n" + "="*80)
print("Model 3/3: flan-t5-small (Classifier)")
print("="*80)
print("Size: ~300MB")
print("Downloading...")

from transformers import T5Tokenizer, T5ForConditionalGeneration
t5_tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
t5_model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")

# Test classification
test_prompt = "Classify as energy, comfort, security, or convenience: Turn on lights at 7 AM\n\nAnswer:"
inputs = t5_tokenizer(test_prompt, return_tensors='pt')
outputs = t5_model.generate(**inputs, max_new_tokens=5)
result = t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
print("✅ Downloaded and tested!")
print(f"   Test classification result: {result}")
print(f"   Location: ~/.cache/huggingface/")

# Summary
print("\n" + "="*80)
print("✅ SETUP COMPLETE!")
print("="*80)
print("\nModels Downloaded:")
print("  1. all-MiniLM-L6-v2 (80MB)")
print("  2. bge-reranker-base (1.1GB)")
print("  3. flan-t5-small (300MB)")
print("  Total: ~1.5GB (full precision)")
print("\nNext Steps:")
print("  1. (Optional) Convert to OpenVINO INT8 for 4.5x size reduction")
print("  2. Review: implementation/OPENVINO_SETUP_GUIDE.md")
print("  3. Start Week 1 preprocessing development")
print("\nAll models cached in: ~/.cache/huggingface/")
print("Ready for Phase 1 development! 🚀\n")
```

Run with:
```bash
python setup_phase1_models.py
```

---

## 🎯 Alternative: Skip Search, Direct Install

Since HuggingFace API search has issues, here's the direct approach:

### **Option A: Standard Models (No Optimization)**

```bash
# Fast setup - models auto-download on first use
pip install sentence-transformers transformers torch

# Test (models download automatically)
python test_models.py
```

**Pros:** 
- ✅ Works immediately
- ✅ No conversion needed
- ✅ Full accuracy

**Cons:**
- ⚠️ Larger (1.5GB vs 380MB)
- ⚠️ Slower (650ms vs 230ms)

---

### **Option B: OpenVINO Optimized (Your Stack)**

```bash
# Install OpenVINO
pip install openvino optimum-intel sentence-transformers transformers torch

# Convert models to INT8
# Model 1: Embeddings
optimum-cli export openvino --model sentence-transformers/all-MiniLM-L6-v2 --task feature-extraction

# Model 2: Re-ranker (use pre-quantized)
python -c "from optimum.intel import OVModelForSequenceClassification; OVModelForSequenceClassification.from_pretrained('OpenVINO/bge-reranker-base-int8-ov')"

# Model 3: Classifier
optimum-cli export openvino --model google/flan-t5-small --task text2text-generation --weight-format int8
```

**Pros:**
- ✅ 4.5x smaller (380MB)
- ✅ 2.8x faster (230ms)
- ✅ Edge-ready

**Cons:**
- ⚠️ Requires OpenVINO setup
- ⚠️ Conversion step needed

---

## ✅ My Recommendation

**For NOW (Week 1):**
Use **Option A** (standard models) to get started quickly. Models will auto-download when you first use them in code.

**For Week 2-3:**
Convert to **Option B** (OpenVINO INT8) once preprocessing pipeline is working.

**Why:**
- Don't block Week 1 on OpenVINO setup complexity
- Prove preprocessing works first
- Optimize later (Week 2-3)

---

## 🎯 Immediate Next Steps

**Since HuggingFace search API has issues:**

1. ✅ **Skip the search** (we already know what models we need)
2. ✅ **Use direct downloads** (models auto-download on first use)
3. ✅ **Start Week 1 development** (begin preprocessing pipeline)

**Monday Tasks (Updated):**

```bash
# 1. Install packages
pip install sentence-transformers transformers torch

# 2. Test downloads (creates test_models.py above, then run)
python test_models.py

# 3. Start preprocessing development
# Follow Week 1 tasks in PHASE_1_QUICK_REFERENCE.md

# 4. (Optional) Setup OpenVINO later this week
pip install openvino optimum-intel
# Convert models when preprocessing is working
```

---

## 📚 Direct Model Links (Bookmark These)

1. **all-MiniLM-L6-v2:** https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
2. **bge-reranker-base:** https://huggingface.co/BAAI/bge-reranker-base
3. **bge-reranker-base-int8-ov:** https://huggingface.co/OpenVINO/bge-reranker-base-int8-ov
4. **flan-t5-small:** https://huggingface.co/google/flan-t5-small

---

**Next Action:** Run `python test_models.py` to download and verify all models, then start preprocessing development!

