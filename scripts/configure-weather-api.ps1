# Weather API Configuration Script
param(
    [Parameter(Mandatory=$true)]
    [string]$ApiKey
)

Write-Host "Configuring Weather API..." -ForegroundColor Green

# Create .env file from template if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item "infrastructure/env.example" ".env"
}

# Read current .env content
$envContent = Get-Content ".env"

# Update weather configuration
$updatedContent = @()
foreach ($line in $envContent) {
    if ($line -match "^WEATHER_API_KEY=") {
        $updatedContent += "WEATHER_API_KEY=$ApiKey"
        Write-Host "Updated WEATHER_API_KEY" -ForegroundColor Green
    } elseif ($line -match "^WEATHER_ENRICHMENT_ENABLED=") {
        $updatedContent += "WEATHER_ENRICHMENT_ENABLED=true"
        Write-Host "Updated WEATHER_ENRICHMENT_ENABLED=true" -ForegroundColor Green
    } elseif ($line -match "^ENABLE_WEATHER_API=") {
        $updatedContent += "ENABLE_WEATHER_API=true"
        Write-Host "Updated ENABLE_WEATHER_API=true" -ForegroundColor Green
    } else {
        $updatedContent += $line
    }
}

# Write updated content back to .env
$updatedContent | Set-Content ".env"

Write-Host ""
Write-Host "Weather API configuration complete!" -ForegroundColor Green
Write-Host "API Key: $ApiKey" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart services: docker-compose restart websocket-ingestion" -ForegroundColor White
Write-Host "2. Check dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "3. Weather API calls should start appearing" -ForegroundColor White
