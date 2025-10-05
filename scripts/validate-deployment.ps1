# HA Ingestor Deployment Validation Script
# Validates all services are running and healthy

Write-Host "🔍 HA Ingestor Deployment Validation" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

$services = @(
    @{Name="InfluxDB"; Port=8086; Endpoint="/health"},
    @{Name="WebSocket Ingestion"; Port=8001; Endpoint="/health"},
    @{Name="Enrichment Pipeline"; Port=8002; Endpoint="/health"},
    @{Name="Data Retention"; Port=8080; Endpoint="/health"},
    @{Name="Admin API"; Port=8003; Endpoint="/health"},
    @{Name="Health Dashboard"; Port=3000; Endpoint="/"}
)

$allHealthy = $true

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)$($service.Endpoint)" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Name) - Healthy (Port $($service.Port))" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($service.Name) - Unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
            $allHealthy = $false
        }
    }
    catch {
        Write-Host "❌ $($service.Name) - Unhealthy or unreachable" -ForegroundColor Red
        $allHealthy = $false
    }
}

Write-Host ""
Write-Host "📊 Resource Usage:" -ForegroundColor Cyan
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

Write-Host ""
if ($allHealthy) {
    Write-Host "🎉 All services are healthy and running!" -ForegroundColor Green
    Write-Host "🌐 Dashboard: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 Admin API: http://localhost:8003" -ForegroundColor Cyan
    Write-Host "📊 InfluxDB: http://localhost:8086" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Some services need attention. Check logs with:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs <service-name>" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📋 Quick Commands:" -ForegroundColor Cyan
Write-Host "   View all logs: docker-compose logs" -ForegroundColor Gray
Write-Host "   Restart services: docker-compose restart" -ForegroundColor Gray
Write-Host "   Check status: docker-compose ps" -ForegroundColor Gray
