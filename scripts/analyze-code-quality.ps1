# Code Quality Analysis Script (PowerShell)
# Analyzes Python and TypeScript code for complexity, duplication, and maintainability

$ErrorActionPreference = "Continue"

# Create reports directory
New-Item -ItemType Directory -Force -Path reports/quality | Out-Null
New-Item -ItemType Directory -Force -Path reports/duplication | Out-Null
New-Item -ItemType Directory -Force -Path reports/coverage | Out-Null

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Code Quality Analysis Report" -ForegroundColor Blue
Write-Host "Generated: $(Get-Date)" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

# ============================================
# PYTHON SERVICES ANALYSIS
# ============================================

Write-Host "[1/6] Analyzing Python Code Complexity...`n" -ForegroundColor Green

# Check if radon is installed
if (Get-Command radon -ErrorAction SilentlyContinue) {
    Write-Host "Cyclomatic Complexity (average per module):"
    radon cc services/*/src/*.py services/*/src/**/*.py -a -s 2>$null
    
    Write-Host "`nMaintainability Index (A=85-100, B=65-84, C=50-64, D/F=0-49):"
    radon mi services/*/src/*.py services/*/src/**/*.py -s 2>$null
    
    # Generate JSON report
    radon cc services/ -a --json > reports/quality/python-complexity.json 2>$null
    radon mi services/ --json > reports/quality/python-maintainability.json 2>$null
    
    Write-Host "✓ Reports saved to reports/quality/`n" -ForegroundColor Green
} else {
    Write-Host "⚠ Radon not installed. Run: pip install -r requirements-quality.txt`n" -ForegroundColor Yellow
}

# ============================================
# PYTHON LINTING
# ============================================

Write-Host "[2/6] Running Python Linting (Pylint)...`n" -ForegroundColor Green

if (Get-Command pylint -ErrorAction SilentlyContinue) {
    # Run pylint on key services
    pylint services/data-api/src/ --output-format=text --reports=y > reports/quality/pylint-data-api.txt 2>&1
    pylint services/admin-api/src/ --output-format=text --reports=y > reports/quality/pylint-admin-api.txt 2>&1
    
    Write-Host "Pylint scores saved to reports/quality/pylint-*.txt"
    Write-Host "✓ Linting complete`n" -ForegroundColor Green
} else {
    Write-Host "⚠ Pylint not installed. Run: pip install -r requirements-quality.txt`n" -ForegroundColor Yellow
}

# ============================================
# TYPESCRIPT ANALYSIS
# ============================================

Write-Host "[3/6] Analyzing TypeScript Code...`n" -ForegroundColor Green

Push-Location services/health-dashboard

# Type checking
Write-Host "Running TypeScript type checking..."
npm run type-check 2>&1 | Tee-Object -FilePath ../../reports/quality/typescript-typecheck.txt

# ESLint with complexity rules
Write-Host "`nRunning ESLint with complexity analysis..."
npm run lint -- --format json --output-file ../../reports/quality/eslint-report.json 2>$null
npm run lint 2>&1 | Tee-Object -FilePath ../../reports/quality/eslint-report.txt

Pop-Location

Write-Host "✓ TypeScript analysis complete`n" -ForegroundColor Green

# ============================================
# CODE DUPLICATION DETECTION
# ============================================

Write-Host "[4/6] Detecting Code Duplication...`n" -ForegroundColor Green

if (Get-Command jscpd -ErrorAction SilentlyContinue) {
    Write-Host "Analyzing Python services..."
    jscpd services/data-api/src/ services/admin-api/src/ services/websocket-ingestion/src/ `
        --format python --threshold 3 --min-lines 5 `
        --output reports/duplication/python 2>$null
    
    Write-Host "`nAnalyzing TypeScript/React code..."
    jscpd services/health-dashboard/src/ `
        --config services/health-dashboard/.jscpd.json 2>$null
    
    Write-Host "✓ Duplication reports saved to reports/duplication/`n" -ForegroundColor Green
} else {
    Write-Host "⚠ jscpd not installed. Run: npm install -g jscpd`n" -ForegroundColor Yellow
}

# ============================================
# DEPENDENCY ANALYSIS
# ============================================

Write-Host "[5/6] Analyzing Dependencies...`n" -ForegroundColor Green

# Python dependencies
if (Get-Command pipdeptree -ErrorAction SilentlyContinue) {
    Write-Host "Python dependency tree:"
    pipdeptree --warn silence > reports/quality/python-dependencies.txt 2>$null
    Write-Host "✓ Saved to reports/quality/python-dependencies.txt" -ForegroundColor Green
}

# Security audit
if (Get-Command pip-audit -ErrorAction SilentlyContinue) {
    Write-Host "`nRunning security audit..."
    pip-audit --desc --format json > reports/quality/security-audit.json 2>$null
    Write-Host "✓ Security audit saved" -ForegroundColor Green
}

Write-Host ""

# ============================================
# GENERATE SUMMARY REPORT
# ============================================

Write-Host "[6/6] Generating Summary Report...`n" -ForegroundColor Green

$summaryContent = @"
# Code Quality Analysis Summary

Generated: $(Get-Date)

## Complexity Metrics

### Python Services
- **Complexity Reports**: ``python-complexity.json``
- **Maintainability Index**: ``python-maintainability.json``
- **Linting Reports**: ``pylint-*.txt``

**Target Thresholds:**
- Cyclomatic Complexity: < 15 (warn), < 20 (error)
- Maintainability Index: > 65 (B grade or better)
- Pylint Score: > 8.0 / 10.0

### TypeScript/React
- **Type Check**: ``typescript-typecheck.txt``
- **ESLint Report**: ``eslint-report.json`` / ``eslint-report.txt``

**Target Thresholds:**
- Complexity: < 15
- Max Lines per Function: < 100
- Max Nesting Depth: < 4

## Duplication Analysis

Reports in ``../duplication/`` directory.

**Target Threshold:** < 3% duplication

## Dependency Health

- **Dependency Tree**: ``python-dependencies.txt``
- **Security Audit**: ``security-audit.json``

## How to Read Reports

### Radon Complexity Scores
- **A (1-5)**: Low risk, simple code
- **B (6-10)**: Moderate complexity
- **C (11-20)**: Complex, consider refactoring
- **D (21-50)**: High risk, refactor recommended
- **F (51+)**: Very high risk, urgent refactoring needed

### Maintainability Index
- **A (85-100)**: Highly maintainable
- **B (65-84)**: Moderately maintainable
- **C (50-64)**: Difficult to maintain
- **D/F (0-49)**: Legacy code, high technical debt

### Pylint Scores
- **10/10**: Perfect (rare!)
- **8-10**: Good quality
- **6-8**: Acceptable, some issues
- **< 6**: Needs improvement

## Next Steps

1. Review high-complexity functions (C, D, F ratings)
2. Address code duplication > 5%
3. Fix security vulnerabilities (if any)
4. Improve low maintainability index scores
5. Add tests for complex functions

## Tools Used

- **radon**: Complexity and maintainability
- **pylint**: Python linting
- **ESLint**: TypeScript linting
- **jscpd**: Duplication detection
- **TypeScript**: Type checking
- **pip-audit**: Security scanning
"@

$summaryContent | Out-File -FilePath reports/quality/SUMMARY.md -Encoding UTF8

Write-Host "✓ Summary report created: reports/quality/SUMMARY.md`n" -ForegroundColor Green

# ============================================
# FINAL SUMMARY
# ============================================

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Analysis Complete!" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

Write-Host "Reports generated in: " -NoNewline
Write-Host "reports/quality/" -ForegroundColor Yellow
Write-Host "Duplication reports in: " -NoNewline
Write-Host "reports/duplication/`n" -ForegroundColor Yellow

Write-Host "Next steps:"
Write-Host "  1. Review: Get-Content reports/quality/SUMMARY.md"
Write-Host "  2. Check complexity: Get-Content reports/quality/python-complexity.json | ConvertFrom-Json"
Write-Host "  3. View duplication: Start-Process reports/duplication/html/index.html"
Write-Host "  4. Check ESLint: Get-Content reports/quality/eslint-report.txt"

Write-Host "`nDone!" -ForegroundColor Green

