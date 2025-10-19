#!/bin/bash
# Model Quantization Script for N-Level Synergy Detection
# Epic AI-4, Story AI4.1: Device Embedding Generation
# Created: October 19, 2025

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODELS_DIR="./models/nlevel-synergy"
CACHE_DIR="./models/cache"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  N-Level Synergy Detection - Model Quantization   ║${NC}"
echo -e "${BLUE}║  Epic AI-4: HuggingFace Models + OpenVINO INT8    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Create directories
echo -e "${YELLOW}📁 Creating model directories...${NC}"
mkdir -p "$MODELS_DIR/embedding-int8"
mkdir -p "$MODELS_DIR/reranker-int8"
mkdir -p "$MODELS_DIR/classifier-int8"
mkdir -p "$CACHE_DIR"

# Check if optimum-cli is installed
if ! command -v optimum-cli &> /dev/null; then
    echo -e "${RED}❌ Error: optimum-cli not found${NC}"
    echo -e "${YELLOW}Please install: pip install optimum[openvino,intel]${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# ============================================================================
# 1. Quantize Embedding Model (sentence-transformers/all-MiniLM-L6-v2)
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📦 [1/3] Quantizing Embedding Model...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Model: sentence-transformers/all-MiniLM-L6-v2"
echo -e "Task: feature-extraction"
echo -e "Quantization: INT8 weight quantization"
echo -e "Target: ~20MB (vs ~80MB FP32)"
echo ""

if [ -f "$MODELS_DIR/embedding-int8/openvino_model.xml" ]; then
    echo -e "${GREEN}✅ Embedding model already quantized (skipping)${NC}"
else
    optimum-cli export openvino \
        --model sentence-transformers/all-MiniLM-L6-v2 \
        --task feature-extraction \
        --weight-format int8 \
        --cache-dir "$CACHE_DIR" \
        "$MODELS_DIR/embedding-int8"
    
    echo -e "${GREEN}✅ Embedding model quantized successfully!${NC}"
fi

echo ""

# ============================================================================
# 2. Download Pre-Quantized Re-Ranker (OpenVINO/bge-reranker-base-int8-ov)
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📦 [2/3] Downloading Pre-Quantized Re-Ranker...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Model: OpenVINO/bge-reranker-base-int8-ov"
echo -e "Size: ~280MB (already INT8 quantized)"
echo -e "Note: No conversion needed (pre-optimized)"
echo ""

if [ -f "$MODELS_DIR/reranker-int8/openvino_model.xml" ]; then
    echo -e "${GREEN}✅ Re-ranker model already downloaded (skipping)${NC}"
else
    python3 << EOF
from optimum.intel.openvino import OVModelForSequenceClassification
import sys

try:
    print("Downloading pre-quantized re-ranker model...")
    model = OVModelForSequenceClassification.from_pretrained(
        'OpenVINO/bge-reranker-base-int8-ov',
        cache_dir='$CACHE_DIR'
    )
    model.save_pretrained('$MODELS_DIR/reranker-int8')
    print("✅ Re-ranker model downloaded successfully!")
except Exception as e:
    print(f"❌ Error downloading re-ranker: {e}")
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Re-ranker model ready!${NC}"
    else
        echo -e "${RED}❌ Failed to download re-ranker${NC}"
        exit 1
    fi
fi

echo ""

# ============================================================================
# 3. Quantize Classifier Model (google/flan-t5-small)
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📦 [3/3] Quantizing Classifier Model...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Model: google/flan-t5-small"
echo -e "Task: text2text-generation"
echo -e "Quantization: INT8 weight quantization"
echo -e "Target: ~80MB (vs ~300MB FP32)"
echo ""

if [ -f "$MODELS_DIR/classifier-int8/openvino_model.xml" ]; then
    echo -e "${GREEN}✅ Classifier model already quantized (skipping)${NC}"
else
    optimum-cli export openvino \
        --model google/flan-t5-small \
        --task text2text-generation \
        --weight-format int8 \
        --cache-dir "$CACHE_DIR" \
        "$MODELS_DIR/classifier-int8"
    
    echo -e "${GREEN}✅ Classifier model quantized successfully!${NC}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Model Quantization Complete!            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}📊 Model Sizes:${NC}"
echo -e "┌────────────────────────────────────────────────────┐"
echo -e "│ Model                        │ Size                │"
echo -e "├────────────────────────────────────────────────────┤"

if [ -d "$MODELS_DIR/embedding-int8" ]; then
    EMB_SIZE=$(du -sh "$MODELS_DIR/embedding-int8" | cut -f1)
    echo -e "│ Embedding (all-MiniLM-L6-v2) │ ${EMB_SIZE}               │"
fi

if [ -d "$MODELS_DIR/reranker-int8" ]; then
    RERANK_SIZE=$(du -sh "$MODELS_DIR/reranker-int8" | cut -f1)
    echo -e "│ Re-ranker (bge-reranker)     │ ${RERANK_SIZE}              │"
fi

if [ -d "$MODELS_DIR/classifier-int8" ]; then
    CLASS_SIZE=$(du -sh "$MODELS_DIR/classifier-int8" | cut -f1)
    echo -e "│ Classifier (flan-t5-small)   │ ${CLASS_SIZE}               │"
fi

TOTAL_SIZE=$(du -sh "$MODELS_DIR" | cut -f1)
echo -e "├────────────────────────────────────────────────────┤"
echo -e "│ ${GREEN}TOTAL${NC}                        │ ${GREEN}${TOTAL_SIZE}${NC}              │"
echo -e "└────────────────────────────────────────────────────┘"
echo ""

echo -e "${YELLOW}📁 Models saved to: ${MODELS_DIR}${NC}"
echo -e "${YELLOW}📁 Cache directory: ${CACHE_DIR}${NC}"
echo ""

echo -e "${GREEN}✅ Next steps:${NC}"
echo -e "   1. Run verification: ${BLUE}python scripts/verify-nlevel-setup.py${NC}"
echo -e "   2. Run database migration: ${BLUE}alembic upgrade head${NC}"
echo -e "   3. Start Story AI4.1 implementation"
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Ready for N-Level Synergy Detection! 🚀          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"

