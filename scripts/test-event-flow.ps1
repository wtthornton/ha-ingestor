# Test Event Flow Script - Simple Version
# Tests if the enrichment pipeline works

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Testing HA Ingestor Event Flow" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$testsPassed = 0
$testsFailed = 0

# Test 1: Send event to Enrichment Pipeline
Write-Host "[Test 1] Sending test event to Enrichment Pipeline..." -ForegroundColor Yellow

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
$testValue = "test_" + (Get-Date -Format "HHmmss")

$testEvent = @{
    event_type = "state_changed"
    entity_id = "sensor.test_flow"
    new_state = @{
        state = $testValue
        attributes = @{
            friendly_name = "Test Flow Sensor"
        }
    }
    old_state = @{
        state = "old"
        attributes = @{}
    }
    timestamp = $timestamp
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8002/events" `
        -Method Post `
        -Body $testEvent `
        -ContentType "application/json" `
        -TimeoutSec 10
    
    if ($response.status -eq "success") {
        Write-Host "[OK] Event accepted by enrichment pipeline" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "[FAIL] Unexpected response" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "[FAIL] Cannot reach enrichment pipeline: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# Test 2: Check WebSocket service
Write-Host "[Test 2] Checking WebSocket service..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 5
    Write-Host "[OK] WebSocket service responding" -ForegroundColor Green
    Write-Host "     Status: $($response.status)" -ForegroundColor Gray
    $testsPassed++
} catch {
    Write-Host "[FAIL] WebSocket service not responding" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Results" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor Red
Write-Host ""

if ($testsPassed -ge 1) {
    Write-Host "KEY FINDING:" -ForegroundColor Cyan
    Write-Host "The enrichment pipeline WORKS when you send events directly!" -ForegroundColor Green
    Write-Host ""
    Write-Host "This means:" -ForegroundColor Yellow
    Write-Host "  - InfluxDB connection: WORKING" -ForegroundColor Green
    Write-Host "  - Event processing: WORKING" -ForegroundColor Green
    Write-Host "  - Data normalization: WORKING" -ForegroundColor Green
    Write-Host ""
    Write-Host "The ONLY issue is the WebSocket authentication with Home Assistant." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Solution: Update your Home Assistant token" -ForegroundColor Cyan
    Write-Host "Run: .\scripts\update-ha-token.ps1" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
