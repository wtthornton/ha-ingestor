# Epic AI-3 Deployment Verification Script
# Story AI3.8: Frontend Synergy Tab
# Verifies that all Epic AI-3 components are working

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Epic AI-3 Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check 1: Backend API Health
Write-Host "1. Checking Backend API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8018/api/synergies/stats" -Method Get
    Write-Host "   ✅ API Endpoint: WORKING" -ForegroundColor Green
    Write-Host "   📊 Total Synergies: $($response.data.total_synergies)" -ForegroundColor White
    Write-Host "   📊 Synergy Types: $($response.data.by_type.Keys.Count)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "   ❌ API Endpoint: FAILED" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
}

# Check 2: Frontend Accessibility
Write-Host "2. Checking Frontend UI..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3001/synergies" -Method Get -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Frontend Page: ACCESSIBLE" -ForegroundColor Green
        Write-Host "   📄 Status Code: 200" -ForegroundColor White
    }
} catch {
    Write-Host "   ❌ Frontend Page: NOT ACCESSIBLE" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
}
Write-Host ""

# Check 3: Service Status
Write-Host "3. Checking Docker Services..." -ForegroundColor Yellow
$services = docker-compose ps --filter "name=ai-automation" --format "table {{.Name}}\t{{.Status}}"
Write-Host $services -ForegroundColor White
Write-Host ""

# Check 4: Recent Logs
Write-Host "4. Checking Recent Logs (Last 20 lines)..." -ForegroundColor Yellow
Write-Host "---" -ForegroundColor Gray
docker-compose logs --tail=20 ai-automation-service | Select-String -Pattern "synergy|Synergy|Phase 3c"
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Wait for next 3 AM batch OR trigger manually:" -ForegroundColor White
Write-Host "   curl -X POST http://localhost:8018/api/analysis/trigger" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Monitor logs for synergy detection:" -ForegroundColor White
Write-Host "   docker-compose logs -f ai-automation-service | findstr synergy" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Browse Synergies UI:" -ForegroundColor White
Write-Host "   http://localhost:3001/synergies" -ForegroundColor Gray
Write-Host ""

