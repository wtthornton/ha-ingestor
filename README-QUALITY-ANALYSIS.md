# Code Quality Analysis Guide

This project includes comprehensive code quality analysis tools for both Python and TypeScript/React code.

## Quick Start

### 1. Install Quality Tools

```bash
# Install Python quality tools
pip install -r requirements-quality.txt

# Install JavaScript duplication detector (optional)
npm install -g jscpd
```

### 2. Run Analysis

**Full Analysis (Recommended):**
```bash
# Bash/Linux/macOS
./scripts/analyze-code-quality.sh

# PowerShell/Windows
.\scripts\analyze-code-quality.ps1
```

**Quick Check (Fast, for pre-commit):**
```bash
./scripts/quick-quality-check.sh
```

**Frontend Only:**
```bash
cd services/health-dashboard
npm run analyze:all
```

## What Gets Analyzed

### Python Services
- **Cyclomatic Complexity** (radon) - How complex is the code?
- **Maintainability Index** (radon) - How easy is it to maintain?
- **Code Quality** (pylint) - Style, bugs, and best practices
- **Code Duplication** (jscpd) - Copy-paste code detection
- **Security Issues** (pip-audit) - Known vulnerabilities
- **Dependencies** (pipdeptree) - Dependency tree analysis

### TypeScript/React
- **Type Safety** (tsc) - TypeScript type checking
- **Code Quality** (ESLint) - Linting with complexity rules
- **Code Duplication** (jscpd) - Duplicate code detection
- **Complexity Metrics** (ESLint rules) - Function/file complexity

## Understanding the Reports

### Complexity Scores (Radon)

| Grade | Complexity | Risk | Action |
|-------|------------|------|--------|
| **A** | 1-5 | Low | Good! |
| **B** | 6-10 | Moderate | Acceptable |
| **C** | 11-20 | High | Refactor if touched |
| **D** | 21-50 | Very High | Prioritize refactoring |
| **F** | 51+ | Extreme | Urgent refactoring |

### Maintainability Index

| Grade | Score | Meaning |
|-------|-------|---------|
| **A** | 85-100 | Highly maintainable |
| **B** | 65-84 | Moderately maintainable |
| **C** | 50-64 | Difficult to maintain |
| **D/F** | 0-49 | Legacy code, high debt |

### Pylint Scores

- **10/10**: Perfect (very rare!)
- **8-10**: Good quality code
- **6-8**: Acceptable with some issues
- **< 6**: Needs improvement

### Code Duplication

- **0-3%**: Excellent
- **3-5%**: Acceptable
- **5-10%**: Needs attention
- **10%+**: Serious issue

## Quality Thresholds

### Python
```yaml
complexity:
  warn: 15
  error: 20

maintainability:
  minimum: 65  # B grade

pylint:
  minimum: 8.0

duplication:
  maximum: 3%
```

### TypeScript/React
```yaml
complexity:
  max: 15

max_lines_per_function: 100

max_depth: 4

max_params: 5

duplication:
  maximum: 3%
```

## Tools Included

### Python Tools

1. **Radon** - Complexity and maintainability metrics
   ```bash
   radon cc services/data-api/src/ -a
   radon mi services/data-api/src/ -s
   ```

2. **Pylint** - Comprehensive linting
   ```bash
   pylint services/data-api/src/
   ```

3. **Prospector** - Meta-tool (runs multiple analyzers)
   ```bash
   prospector services/data-api/src/
   ```

4. **Pip-audit** - Security vulnerability scanner
   ```bash
   pip-audit --desc
   ```

5. **Pipdeptree** - Dependency tree visualization
   ```bash
   pipdeptree --warn silence
   ```

### TypeScript Tools

1. **ESLint** - Linting with complexity rules
   ```bash
   cd services/health-dashboard
   npm run lint
   ```

2. **TypeScript Compiler** - Type checking
   ```bash
   npm run type-check
   ```

3. **Jscpd** - Duplication detection
   ```bash
   npm run analyze:duplication
   ```

## Configuration Files

- **requirements-quality.txt** - Python quality tools
- **services/health-dashboard/.eslintrc.cjs** - ESLint config with complexity rules
- **services/health-dashboard/.jscpd.json** - Frontend duplication config
- **.jscpd.json** - Project-wide duplication config

## Reports Location

All reports are generated in:
```
reports/
├── quality/
│   ├── SUMMARY.md                    # Executive summary
│   ├── python-complexity.json        # Complexity data
│   ├── python-maintainability.json   # Maintainability data
│   ├── pylint-*.txt                  # Linting reports
│   ├── typescript-typecheck.txt      # Type errors
│   ├── eslint-report.json            # ESLint findings
│   ├── python-dependencies.txt       # Dependency tree
│   └── security-audit.json           # Security issues
└── duplication/
    ├── python/                       # Python duplication
    ├── html/                         # HTML reports
    └── index.html                    # Main duplication report
```

## Pre-commit Integration

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
./scripts/quick-quality-check.sh
if [ $? -ne 0 ]; then
    echo "Quality checks failed. Commit aborted."
    exit 1
fi
```

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Code Quality Analysis
  run: |
    pip install -r requirements-quality.txt
    ./scripts/analyze-code-quality.sh
    
- name: Upload Quality Reports
  uses: actions/upload-artifact@v3
  with:
    name: quality-reports
    path: reports/
```

## Viewing Reports

### Summary
```bash
cat reports/quality/SUMMARY.md
```

### Complexity Issues
```bash
# Show files with complexity > 10
radon cc services/ -n C -s
```

### Duplication Report
```bash
# Open HTML report in browser
open reports/duplication/html/index.html  # macOS
xdg-open reports/duplication/html/index.html  # Linux
start reports/duplication/html/index.html  # Windows
```

### Security Issues
```bash
cat reports/quality/security-audit.json | jq
```

## Best Practices

1. **Run before commits**: Use `quick-quality-check.sh`
2. **Review complexity**: Focus on C, D, F rated functions
3. **Refactor gradually**: Don't try to fix everything at once
4. **Set team standards**: Agree on acceptable thresholds
5. **Track over time**: Run weekly and track trends
6. **Fix security issues**: Always address security findings first

## Troubleshooting

### "Command not found"
Install missing tools:
```bash
pip install -r requirements-quality.txt
npm install -g jscpd
```

### "Permission denied"
Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### Reports are empty
Check if paths are correct and services exist:
```bash
ls -la services/data-api/src/
```

## Getting Help

Run individual tools for detailed help:
```bash
radon --help
pylint --help
eslint --help
jscpd --help
```

## Example Workflow

```bash
# 1. Make code changes
vim services/data-api/src/main.py

# 2. Quick check before commit
./scripts/quick-quality-check.sh

# 3. If issues found, run full analysis
./scripts/analyze-code-quality.sh

# 4. Review reports
cat reports/quality/SUMMARY.md

# 5. Fix high-priority issues
# ... make fixes ...

# 6. Verify fixes
./scripts/quick-quality-check.sh

# 7. Commit
git add .
git commit -m "Refactor: Reduce complexity in data processing"
```

## Quality Metrics Dashboard

Consider adding to your health dashboard:
- Complexity trends over time
- Duplication percentage
- Maintainability scores per service
- Security vulnerability count
- Test coverage percentage

---

**Questions?** See the full analysis results in `reports/quality/SUMMARY.md` after running the analysis script.

