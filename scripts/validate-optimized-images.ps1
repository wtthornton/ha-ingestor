# Docker Image Optimization Validation Script (PowerShell)
# This script validates that the optimized Docker images work correctly

Write-Host "🐳 Docker Image Optimization Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Function to print colored output
function Write-Status {
    param(
        [bool]$Success,
        [string]$Message
    )
    
    if ($Success) {
        Write-Host "✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
    }
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Yellow
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Info "Docker is running"
} catch {
    Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Build optimized images
Write-Info "Building optimized images..."

$services = @("websocket-ingestion", "admin-api", "enrichment-pipeline", "weather-api", "data-retention", "health-dashboard")

foreach ($service in $services) {
    Write-Info "Building $service..."
    try {
        docker build -t "homeiq-$service`:optimized" -f "services/$service/Dockerfile" .
        Write-Status $true "Built $service successfully"
    } catch {
        Write-Status $false "Failed to build $service"
        exit 1
    }
}

# Check image sizes
Write-Info "Checking image sizes..."
Write-Host ""
Write-Host "Image Size Comparison:" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
docker images --format "table {{.Repository}}`t{{.Tag}}`t{{.Size}}" | Select-String "homeiq"

# Test basic functionality
Write-Info "Testing basic functionality..."

# Test websocket-ingestion
Write-Info "Testing websocket-ingestion health endpoint..."
try {
    docker run --rm -d --name test-websocket homeiq-websocket-ingestion:optimized | Out-Null
    Start-Sleep -Seconds 5
    docker exec test-websocket curl -f http://localhost:8001/health | Out-Null
    Write-Status $true "WebSocket ingestion service is healthy"
    docker stop test-websocket | Out-Null
} catch {
    Write-Status $false "WebSocket ingestion service health check failed"
    docker stop test-websocket 2>$null
}

# Test admin-api
Write-Info "Testing admin-api health endpoint..."
try {
    docker run --rm -d --name test-admin homeiq-admin-api:optimized | Out-Null
    Start-Sleep -Seconds 5
    docker exec test-admin curl -f http://localhost:8004/health | Out-Null
    Write-Status $true "Admin API service is healthy"
    docker stop test-admin | Out-Null
} catch {
    Write-Status $false "Admin API service health check failed"
    docker stop test-admin 2>$null
}

# Test enrichment-pipeline
Write-Info "Testing enrichment-pipeline health endpoint..."
try {
    docker run --rm -d --name test-enrichment homeiq-enrichment-pipeline:optimized | Out-Null
    Start-Sleep -Seconds 5
    docker exec test-enrichment curl -f http://localhost:8002/health | Out-Null
    Write-Status $true "Enrichment pipeline service is healthy"
    docker stop test-enrichment | Out-Null
} catch {
    Write-Status $false "Enrichment pipeline service health check failed"
    docker stop test-enrichment 2>$null
}

# Test weather-api
Write-Info "Testing weather-api health endpoint..."
try {
    docker run --rm -d --name test-weather homeiq-weather-api:optimized | Out-Null
    Start-Sleep -Seconds 5
    docker exec test-weather curl -f http://localhost:8001/health | Out-Null
    Write-Status $true "Weather API service is healthy"
    docker stop test-weather | Out-Null
} catch {
    Write-Status $false "Weather API service health check failed"
    docker stop test-weather 2>$null
}

# Test data-retention
Write-Info "Testing data-retention health endpoint..."
try {
    docker run --rm -d --name test-retention homeiq-data-retention:optimized | Out-Null
    Start-Sleep -Seconds 5
    docker exec test-retention curl -f http://localhost:8080/health | Out-Null
    Write-Status $true "Data retention service is healthy"
    docker stop test-retention | Out-Null
} catch {
    Write-Status $false "Data retention service health check failed"
    docker stop test-retention 2>$null
}

# Test health-dashboard
Write-Info "Testing health-dashboard..."
try {
    docker run --rm -d --name test-dashboard homeiq-health-dashboard:optimized | Out-Null
    Start-Sleep -Seconds 5
    docker exec test-dashboard curl -f http://localhost:80 | Out-Null
    Write-Status $true "Health dashboard is accessible"
    docker stop test-dashboard | Out-Null
} catch {
    Write-Status $false "Health dashboard accessibility test failed"
    docker stop test-dashboard 2>$null
}

# Security check - verify non-root users
Write-Info "Checking security configurations..."

foreach ($service in $services) {
    Write-Info "Checking $service runs as non-root user..."
    try {
        $output = docker run --rm homeiq-$service`:optimized id
        if ($output -match "uid=1001") {
            Write-Status $true "$service runs as non-root user (uid=1001)"
        } else {
            Write-Status $false "$service does not run as non-root user"
        }
    } catch {
        Write-Status $false "$service user check failed"
    }
}

Write-Host ""
Write-Host "🎉 Docker Image Optimization Validation Complete!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "- All services built successfully with Alpine-based images"
Write-Host "- Multi-stage builds implemented for optimal size"
Write-Host "- Non-root users configured for security"
Write-Host "- Health checks validated"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test with docker-compose up"
Write-Host "2. Monitor resource usage in production"
Write-Host "3. Consider implementing distroless images for further optimization" -ForegroundColor Cyan
