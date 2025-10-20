# Setup Script for Code Quality Tools (PowerShell)
# Installs all necessary tools for code quality analysis

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Code Quality Tools Setup" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

# ============================================
# Python Tools
# ============================================

Write-Host "[1/4] Installing Python quality tools...`n" -ForegroundColor Green

if (Get-Command pip -ErrorAction SilentlyContinue) {
    pip install -r requirements-quality.txt
    Write-Host "✓ Python tools installed`n" -ForegroundColor Green
} else {
    Write-Host "⚠ pip not found. Please install Python first.`n" -ForegroundColor Yellow
}

# ============================================
# Node.js Global Tools
# ============================================

Write-Host "[2/4] Installing Node.js global tools...`n" -ForegroundColor Green

if (Get-Command npm -ErrorAction SilentlyContinue) {
    # Install jscpd globally for cross-language duplication detection
    npm install -g jscpd
    Write-Host "✓ Node.js tools installed`n" -ForegroundColor Green
} else {
    Write-Host "⚠ npm not found. Please install Node.js first.`n" -ForegroundColor Yellow
}

# ============================================
# Frontend Dependencies
# ============================================

Write-Host "[3/4] Setting up frontend quality tools...`n" -ForegroundColor Green

if (Test-Path "services/health-dashboard") {
    Push-Location services/health-dashboard
    
    # Install jscpd as dev dependency (if not already installed)
    $jscpdInstalled = npm list jscpd 2>$null
    if (-not $jscpdInstalled) {
        npm install --save-dev jscpd
    }
    
    # Create reports directory
    New-Item -ItemType Directory -Force -Path reports | Out-Null
    
    Pop-Location
    Write-Host "✓ Frontend tools ready`n" -ForegroundColor Green
} else {
    Write-Host "⚠ health-dashboard not found`n" -ForegroundColor Yellow
}

# ============================================
# Create Reports Directories
# ============================================

Write-Host "[4/4] Creating reports directories...`n" -ForegroundColor Green

New-Item -ItemType Directory -Force -Path reports/quality | Out-Null
New-Item -ItemType Directory -Force -Path reports/duplication | Out-Null
New-Item -ItemType Directory -Force -Path reports/coverage | Out-Null
New-Item -ItemType File -Force -Path reports/.gitkeep | Out-Null

Write-Host "✓ Directories created`n" -ForegroundColor Green

# ============================================
# Verify Installation
# ============================================

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Verifying Installation" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

Write-Host "Checking Python tools..."
if (Get-Command radon -ErrorAction SilentlyContinue) { Write-Host "  ✓ radon" } else { Write-Host "  ✗ radon" }
if (Get-Command pylint -ErrorAction SilentlyContinue) { Write-Host "  ✓ pylint" } else { Write-Host "  ✗ pylint" }
if (Get-Command prospector -ErrorAction SilentlyContinue) { Write-Host "  ✓ prospector" } else { Write-Host "  ✗ prospector" }
if (Get-Command mypy -ErrorAction SilentlyContinue) { Write-Host "  ✓ mypy" } else { Write-Host "  ✗ mypy" }
if (Get-Command pip-audit -ErrorAction SilentlyContinue) { Write-Host "  ✓ pip-audit" } else { Write-Host "  ✗ pip-audit" }

Write-Host "`nChecking Node.js tools..."
if (Get-Command jscpd -ErrorAction SilentlyContinue) { Write-Host "  ✓ jscpd" } else { Write-Host "  ✗ jscpd" }

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "Next steps:"
Write-Host "  1. Run full analysis: .\scripts\analyze-code-quality.ps1"
Write-Host "  2. View guide: Get-Content README-QUALITY-ANALYSIS.md"

Write-Host "`nDone!" -ForegroundColor Blue

