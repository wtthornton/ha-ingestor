# Stop and Remove All HA-Ingestor Containers
# PowerShell version for Windows
# Safe execution with confirmation and status checks
# DO NOT RUN without backing up data first!

$ErrorActionPreference = "Continue"

# Colors for output
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Blue }
function Write-Success { Write-Host "[SUCCESS] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[WARNING] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

# Banner
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  HA-INGESTOR COMPLETE TEARDOWN" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Warning "This script will:"
Write-Host "  1. Stop all running services"
Write-Host "  2. Remove all containers"
Write-Host "  3. Remove all images"
Write-Host "  4. Remove Docker network"
Write-Host "  5. Clean build cache"
Write-Host ""
Write-Info "Data volumes will be PRESERVED by default"
Write-Host ""

# Check if services are running
try {
    $containers = docker ps -a --filter "name=homeiq" --format "{{.Names}}" 2>$null
    $containerCount = ($containers | Measure-Object).Count
    Write-Info "Found $containerCount homeiq containers"
} catch {
    Write-Warning "Error checking containers. Is Docker running?"
    $containerCount = 0
}

if ($containerCount -eq 0) {
    Write-Warning "No homeiq containers found!"
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Info "Aborted by user"
        exit 0
    }
}

# Show current status
Write-Host ""
Write-Info "Current container status:"
try {
    docker ps -a --filter "name=homeiq" --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}" 2>$null
} catch {
    Write-Warning "Could not display container status"
}
Write-Host ""

# Confirmation prompt
Write-Warning "⚠️  IMPORTANT: Have you created backups?"
Write-Host ""
Write-Host "  Required backups:"
Write-Host "    ✓ InfluxDB data: docker exec homeiq-influxdb influx backup /tmp/backup"
Write-Host "    ✓ SQLite data: docker cp homeiq-data-api:/app/data/metadata.db `$HOME/backup-metadata.db"
Write-Host "    ✓ Environment: Copy-Item .env `$HOME/backup-env"
Write-Host ""
$backupConfirm = Read-Host "Have you completed backups? (yes/NO)"

if ($backupConfirm -ne "yes") {
    Write-Error "Backups not confirmed. Aborting for safety."
    Write-Info "Please create backups first!"
    exit 1
}

Write-Host ""
$finalConfirm = Read-Host "Are you SURE you want to tear down everything? (type 'yes' to continue)"

if ($finalConfirm -ne "yes") {
    Write-Info "Aborted by user"
    exit 0
}

Write-Host ""
Write-Info "Starting complete teardown..."
Write-Host ""

# Step 1: Stop services gracefully with docker-compose
Write-Info "Step 1/7: Stopping services gracefully (30s timeout)..."
if (Test-Path "docker-compose.yml") {
    try {
        docker-compose down --timeout 30 2>$null
        Write-Success "Graceful shutdown complete"
    } catch {
        Write-Warning "docker-compose down failed (may not be running)"
    }
} else {
    Write-Warning "docker-compose.yml not found, skipping graceful shutdown"
}
Write-Host ""

# Step 2: Force stop any remaining containers
Write-Info "Step 2/7: Force stopping any remaining containers..."
try {
    $running = docker ps --filter "name=homeiq" -q 2>$null
    if ($running) {
        $running | ForEach-Object { docker stop $_ 2>$null }
        $stoppedCount = ($running | Measure-Object).Count
        Write-Success "Stopped $stoppedCount running containers"
    } else {
        Write-Info "No running containers found"
    }
} catch {
    Write-Warning "Error stopping containers"
}
Write-Host ""

# Step 3: Remove all containers
Write-Info "Step 3/7: Removing all homeiq containers..."
try {
    $allContainers = docker ps -a --filter "name=homeiq" -q 2>$null
    if ($allContainers) {
        $allContainers | ForEach-Object { docker rm -f $_ 2>$null }
        $removedCount = ($allContainers | Measure-Object).Count
        Write-Success "Removed $removedCount containers"
    } else {
        Write-Info "No containers to remove"
    }
} catch {
    Write-Warning "Error removing containers"
}
Write-Host ""

# Step 4: Remove all images
Write-Info "Step 4/7: Removing all homeiq images..."
try {
    $allImages = docker images --filter=reference='*homeiq*' -q 2>$null
    if ($allImages) {
        $allImages | ForEach-Object { docker rmi -f $_ 2>$null }
        $removedCount = ($allImages | Measure-Object).Count
        Write-Success "Removed $removedCount images"
    } else {
        Write-Info "No images to remove"
    }
} catch {
    Write-Warning "Error removing images"
}
Write-Host ""

# Step 5: Remove networks
Write-Info "Step 5/7: Removing Docker networks..."
try {
    docker network rm homeiq-network 2>$null | Out-Null
    Write-Success "Network removed"
} catch {
    Write-Info "Network not found or already removed"
}
try {
    docker network rm homeiq-network-dev 2>$null | Out-Null
} catch {}
Write-Host ""

# Step 6: Clean build cache
Write-Info "Step 6/7: Cleaning Docker build cache..."
try {
    docker builder prune -a -f 2>$null | Out-Null
    Write-Success "Build cache cleaned"
} catch {
    Write-Warning "Error cleaning build cache"
}
Write-Host ""

# Step 7: Verify cleanup
Write-Info "Step 7/7: Verifying cleanup..."
Write-Host ""

try {
    $remainingContainers = (docker ps -a --filter "name=homeiq" -q 2>$null | Measure-Object).Count
    $remainingImages = (docker images --filter=reference='*homeiq*' -q 2>$null | Measure-Object).Count
    $remainingNetworks = (docker network ls 2>$null | Select-String "homeiq" | Measure-Object).Count

    Write-Info "Cleanup verification:"
    Write-Host "  Containers: $remainingContainers (should be 0)"
    Write-Host "  Images: $remainingImages (should be 0)"
    Write-Host "  Networks: $remainingNetworks (should be 0)"
    Write-Host ""

    if ($remainingContainers -eq 0 -and $remainingImages -eq 0 -and $remainingNetworks -eq 0) {
        Write-Success "✅ Complete teardown successful!"
    } else {
        Write-Warning "⚠️  Some items remain - may need manual cleanup"
    }
} catch {
    Write-Warning "Could not verify cleanup status"
}

# Show volume status
Write-Host ""
Write-Info "Volume status (preserved):"
try {
    $volumes = docker volume ls 2>$null | Select-String "homeiq"
    if ($volumes) {
        $volumes | ForEach-Object { Write-Host "  $_" }
    } else {
        Write-Info "No homeiq volumes found"
    }
} catch {
    Write-Warning "Could not check volume status"
}
Write-Host ""

# Next steps
Write-Host "==================================" -ForegroundColor Cyan
Write-Success "TEARDOWN COMPLETE!"
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "Next steps:"
Write-Host ""
Write-Host "  1. Rebuild images:"
Write-Host "     docker-compose build --no-cache --parallel"
Write-Host ""
Write-Host "  2. Deploy services:"
Write-Host "     docker-compose up -d"
Write-Host ""
Write-Host "  3. Monitor startup:"
Write-Host "     docker-compose ps"
Write-Host ""
Write-Host "  4. Validate deployment:"
Write-Host "     .\scripts\test-services.sh"
Write-Host "     curl http://localhost:3000"
Write-Host ""
Write-Info "Full rebuild guide: implementation\COMPLETE_SYSTEM_REBUILD_PLAN.md"
Write-Host ""

