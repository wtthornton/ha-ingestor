# Home Assistant Ingestor - Deployment Pipeline with API Key Validation (PowerShell)
# This script ensures all API keys and tokens are validated before deployment

param(
    [switch]$SkipValidation,
    [switch]$Verbose
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

Write-Host "🚀 Home Assistant Ingestor - Deployment Pipeline" -ForegroundColor $Blue
Write-Host "==================================================" -ForegroundColor $Blue

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Error ".env file not found!"
    Write-Status "Creating .env from template..."
    Copy-Item "infrastructure/env.example" ".env"
    Write-Warning "Please configure your .env file with valid API keys and tokens"
    exit 1
}

# Step 1: Validate API Keys and Tokens
if (-not $SkipValidation) {
    Write-Status "Step 1: Validating API keys and tokens..."
    try {
        $result = python tests/test_api_keys.py --env-file .env
        if ($LASTEXITCODE -eq 0) {
            Write-Success "All API keys and tokens are valid!"
        } else {
            Write-Error "API key validation failed!"
            Write-Warning "Please check your .env file and ensure all tokens are valid"
            exit 1
        }
    } catch {
        Write-Error "Failed to run API validation tests: $_"
        exit 1
    }
} else {
    Write-Warning "Skipping API key validation (--SkipValidation flag used)"
}

# Step 2: Backup current configuration
Write-Status "Step 2: Backing up current configuration..."
if (Test-Path ".env") {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Copy-Item ".env" ".env.backup.$timestamp"
    Write-Success "Configuration backed up"
}

# Step 3: Build Docker images
Write-Status "Step 3: Building Docker images..."
try {
    docker-compose build
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker images built successfully!"
    } else {
        Write-Error "Docker build failed!"
        exit 1
    }
} catch {
    Write-Error "Docker build failed: $_"
    exit 1
}

# Step 4: Start services
Write-Status "Step 4: Starting services..."
try {
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services started successfully!"
    } else {
        Write-Error "Service startup failed!"
        exit 1
    }
} catch {
    Write-Error "Service startup failed: $_"
    exit 1
}

# Step 5: Wait for services to be healthy
Write-Status "Step 5: Waiting for services to be healthy..."
Start-Sleep -Seconds 30

# Step 6: Run comprehensive smoke tests
Write-Status "Step 6: Running comprehensive smoke tests..."
try {
    $smokeTestResult = python tests/smoke_tests.py --admin-url "http://localhost:8003" --output json
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All smoke tests passed! System is deployment ready."
    } else {
        Write-Error "Smoke tests failed! System is not deployment ready."
        Write-Warning "Please check the smoke test results and fix critical issues."
        exit 1
    }
} catch {
    Write-Error "Failed to run smoke tests: $_"
    exit 1
}

# Step 7: Validate deployment
Write-Status "Step 7: Final deployment validation..."

# Check service health
$services = docker-compose ps --format json | ConvertFrom-Json
$unhealthyServices = $services | Where-Object { $_.State -like "*unhealthy*" }

if ($unhealthyServices) {
    Write-Warning "Some services are unhealthy. Checking logs..."
    docker-compose ps
    Write-Status "Checking logs for unhealthy services..."
    foreach ($service in $unhealthyServices) {
        Write-Status "Logs for $($service.Name):"
        docker-compose logs --tail=20 $service.Name
    }
} else {
    Write-Success "All services are healthy!"
}

# Test API endpoints
Write-Status "Testing API endpoints..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/api/v1/health" -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Success "Admin API is responding!"
    }
} catch {
    Write-Warning "Admin API is not responding yet (may still be starting)"
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Success "Health Dashboard is responding!"
    }
} catch {
    Write-Warning "Health Dashboard is not responding yet (may still be starting)"
}

# Final status
Write-Status "Deployment Summary:"
Write-Host "===================" -ForegroundColor $Blue
docker-compose ps

Write-Success "Deployment completed!"
Write-Status "Access points:"
Write-Host "  - Health Dashboard: http://localhost:3000" -ForegroundColor $Green
Write-Host "  - Admin API: http://localhost:8080" -ForegroundColor $Green
Write-Host "  - API Documentation: http://localhost:8080/docs" -ForegroundColor $Green
Write-Host "  - InfluxDB: http://localhost:8086" -ForegroundColor $Green

Write-Status "To view logs: docker-compose logs -f [service-name]"
Write-Status "To stop services: docker-compose down"
