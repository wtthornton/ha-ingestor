# PowerShell Setup Script for N-Level Synergy Detection (Windows)
# Epic AI-4, Story AI4.1: Device Embedding Generation
# Created: October 19, 2025

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║  N-Level Synergy Detection - Windows Setup        ║" -ForegroundColor Blue
Write-Host "║  Epic AI-4: HuggingFace Models + OpenVINO INT8    ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Configuration
$MODELS_DIR = ".\models\nlevel-synergy"
$CACHE_DIR = ".\models\cache"

# Step 1: Check Python version
Write-Host "🐍 Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "   $pythonVersion" -ForegroundColor Green

# Step 2: Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
Write-Host "   This will take a few minutes (downloading ~1GB)..." -ForegroundColor Cyan

cd services\ai-automation-service

if (Test-Path "requirements-nlevel.txt") {
    Write-Host "   Installing from requirements-nlevel.txt..." -ForegroundColor Cyan
    pip install -r requirements-nlevel.txt
    Write-Host "   ✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ❌ requirements-nlevel.txt not found!" -ForegroundColor Red
    exit 1
}

cd ..\..

# Step 3: Run database migration
Write-Host ""
Write-Host "🗄️  Running database migration..." -ForegroundColor Yellow

if (Test-Path "alembic.ini") {
    alembic upgrade head
    Write-Host "   ✅ Migration complete" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  alembic.ini not found - skipping migration" -ForegroundColor Yellow
}

# Step 4: Create model directories
Write-Host ""
Write-Host "📁 Creating model directories..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path "$MODELS_DIR\embedding-int8" | Out-Null
New-Item -ItemType Directory -Force -Path "$MODELS_DIR\reranker-int8" | Out-Null
New-Item -ItemType Directory -Force -Path "$MODELS_DIR\classifier-int8" | Out-Null
New-Item -ItemType Directory -Force -Path "$CACHE_DIR" | Out-Null

Write-Host "   ✅ Directories created" -ForegroundColor Green

# Step 5: Quantize models using Python
Write-Host ""
Write-Host "🤖 Quantizing models (this will take ~5 minutes)..." -ForegroundColor Yellow
Write-Host "   Downloading and converting to INT8..." -ForegroundColor Cyan

python -c @"
import sys
import os
from pathlib import Path

print('  [1/3] Quantizing embedding model...')
try:
    from optimum.intel.openvino import OVModelForFeatureExtraction
    
    model_path = Path('$MODELS_DIR/embedding-int8')
    if not (model_path / 'openvino_model.xml').exists():
        model = OVModelForFeatureExtraction.from_pretrained(
            'sentence-transformers/all-MiniLM-L6-v2',
            export=True,
            cache_dir='$CACHE_DIR'
        )
        model.save_pretrained(str(model_path))
        print('     ✅ Embedding model quantized (20MB)')
    else:
        print('     ✅ Embedding model already exists')
except Exception as e:
    print(f'     ❌ Error: {e}')
    sys.exit(1)

print('  [2/3] Downloading pre-quantized re-ranker...')
try:
    from optimum.intel.openvino import OVModelForSequenceClassification
    
    model_path = Path('$MODELS_DIR/reranker-int8')
    if not (model_path / 'openvino_model.xml').exists():
        model = OVModelForSequenceClassification.from_pretrained(
            'OpenVINO/bge-reranker-base-int8-ov',
            cache_dir='$CACHE_DIR'
        )
        model.save_pretrained(str(model_path))
        print('     ✅ Re-ranker downloaded (280MB)')
    else:
        print('     ✅ Re-ranker already exists')
except Exception as e:
    print(f'     ❌ Error: {e}')
    sys.exit(1)

print('  [3/3] Quantizing classifier model...')
try:
    from optimum.intel.openvino import OVModelForSeq2SeqLM
    
    model_path = Path('$MODELS_DIR/classifier-int8')
    if not (model_path / 'openvino_model.xml').exists():
        model = OVModelForSeq2SeqLM.from_pretrained(
            'google/flan-t5-small',
            export=True,
            cache_dir='$CACHE_DIR'
        )
        model.save_pretrained(str(model_path))
        print('     ✅ Classifier quantized (80MB)')
    else:
        print('     ✅ Classifier already exists')
except Exception as e:
    print(f'     ❌ Error: {e}')
    sys.exit(1)

print('✅ All models ready!')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Model quantization failed" -ForegroundColor Red
    exit 1
}

# Step 6: Summary
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║           Setup Complete! 🎉                       ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

Write-Host "📊 Model Sizes:" -ForegroundColor Green
Get-ChildItem -Path "$MODELS_DIR" -Directory | ForEach-Object {
    $size = (Get-ChildItem -Path $_.FullName -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "   $($_.Name): $([math]::Round($size, 1)) MB" -ForegroundColor Cyan
}

$totalSize = (Get-ChildItem -Path "$MODELS_DIR" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "   TOTAL: $([math]::Round($totalSize, 1)) MB" -ForegroundColor Green

Write-Host ""
Write-Host "✅ Next steps:" -ForegroundColor Yellow
Write-Host "   1. Verify setup: python scripts\verify-nlevel-setup.py" -ForegroundColor Cyan
Write-Host "   2. Test components (see GETTING_STARTED_EPIC_AI4.md)" -ForegroundColor Cyan
Write-Host "   3. Start implementing device_embedding_generator.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Ready to build N-Level Synergy Detection!" -ForegroundColor Green

