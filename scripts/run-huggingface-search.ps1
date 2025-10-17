# HuggingFace Resource Search Runner (PowerShell)
# Run this script to search HuggingFace for relevant models and datasets

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "HuggingFace Resource Search for Home Assistant Pattern Detection" -ForegroundColor Cyan
Write-Host "================================================================================`n" -ForegroundColor Cyan

# Check if Python is available
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} else {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

Write-Host "Using: $pythonCmd" -ForegroundColor Green

# Check if huggingface_hub is installed
Write-Host "`nChecking dependencies..." -ForegroundColor Yellow

$checkInstall = & $pythonCmd -c "import huggingface_hub" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nhuggingface_hub not installed. Installing..." -ForegroundColor Yellow
    & $pythonCmd -m pip install huggingface_hub
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nERROR: Failed to install huggingface_hub" -ForegroundColor Red
        Write-Host "Try manually: pip install huggingface_hub" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "huggingface_hub already installed" -ForegroundColor Green
}

# Run the search script
Write-Host "`nStarting HuggingFace search..." -ForegroundColor Yellow
Write-Host "This may take 2-5 minutes depending on your connection...`n" -ForegroundColor Yellow

& $pythonCmd scripts/search-huggingface-resources.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n================================================================================" -ForegroundColor Green
    Write-Host "Search Complete!" -ForegroundColor Green
    Write-Host "================================================================================`n" -ForegroundColor Green
    
    Write-Host "Results saved to: docs/kb/huggingface-research/" -ForegroundColor Cyan
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "1. Review: docs/kb/huggingface-research/SEARCH_SUMMARY.md" -ForegroundColor White
    Write-Host "2. Check top 5 results in each category" -ForegroundColor White
    Write-Host "3. Visit HuggingFace pages for promising models" -ForegroundColor White
    Write-Host "4. Test on sample HA data" -ForegroundColor White
    Write-Host "`nPress any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} else {
    Write-Host "`nERROR: Search failed. Check output above for details." -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

