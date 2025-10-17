#!/bin/bash
# HuggingFace Resource Search Runner (Bash)
# Run this script to search HuggingFace for relevant models and datasets

echo ""
echo "================================================================================"
echo "HuggingFace Resource Search for Home Assistant Pattern Detection"
echo "================================================================================"
echo ""

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python not found. Please install Python 3.8+"
    exit 1
fi

echo "Using: $PYTHON_CMD"

# Check if huggingface_hub is installed
echo ""
echo "Checking dependencies..."

if ! $PYTHON_CMD -c "import huggingface_hub" 2>/dev/null; then
    echo ""
    echo "huggingface_hub not installed. Installing..."
    $PYTHON_CMD -m pip install huggingface_hub
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to install huggingface_hub"
        echo "Try manually: pip install huggingface_hub"
        exit 1
    fi
else
    echo "huggingface_hub already installed"
fi

# Run the search script
echo ""
echo "Starting HuggingFace search..."
echo "This may take 2-5 minutes depending on your connection..."
echo ""

$PYTHON_CMD scripts/search-huggingface-resources.py

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo "Search Complete!"
    echo "================================================================================"
    echo ""
    echo "Results saved to: docs/kb/huggingface-research/"
    echo ""
    echo "Next steps:"
    echo "1. Review: docs/kb/huggingface-research/SEARCH_SUMMARY.md"
    echo "2. Check top 5 results in each category"
    echo "3. Visit HuggingFace pages for promising models"
    echo "4. Test on sample HA data"
    echo ""
else
    echo ""
    echo "ERROR: Search failed. Check output above for details."
    exit 1
fi

