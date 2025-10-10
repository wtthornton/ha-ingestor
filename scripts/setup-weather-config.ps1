# Weather API Configuration Setup Script
# This script helps configure the weather enrichment service

Write-Host "🌤️  Weather API Configuration Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item "infrastructure/env.example" ".env"
    Write-Host "✅ .env file created" -ForegroundColor Green
} else {
    Write-Host "📄 .env file already exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔑 OpenWeatherMap API Key Setup Required" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Red
Write-Host ""
Write-Host "To enable weather enrichment, you need to:" -ForegroundColor White
Write-Host "1. Visit: https://openweathermap.org/api" -ForegroundColor Cyan
Write-Host "2. Sign up for a free account" -ForegroundColor White
Write-Host "3. Get your API key from: https://home.openweathermap.org/api_keys" -ForegroundColor Cyan
Write-Host "4. Replace 'your_openweathermap_api_key_here' in .env with your actual key" -ForegroundColor White
Write-Host ""
Write-Host "📊 Free Tier Limits:" -ForegroundColor Yellow
Write-Host "   • 60 calls/minute" -ForegroundColor White
Write-Host "   • 1,000 calls/day" -ForegroundColor White
Write-Host "   • Perfect for development and small deployments" -ForegroundColor White
Write-Host ""

# Check current weather configuration
Write-Host "🔍 Current Weather Configuration:" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$envContent = Get-Content ".env" -ErrorAction SilentlyContinue
if ($envContent) {
    $weatherApiKey = ($envContent | Where-Object { $_ -match "WEATHER_API_KEY" }) -replace "WEATHER_API_KEY=", ""
    $weatherEnabled = ($envContent | Where-Object { $_ -match "WEATHER_ENRICHMENT_ENABLED" }) -replace "WEATHER_ENRICHMENT_ENABLED=", ""
    $weatherLocation = ($envContent | Where-Object { $_ -match "WEATHER_DEFAULT_LOCATION" }) -replace "WEATHER_DEFAULT_LOCATION=", ""
    
    Write-Host "API Key: $weatherApiKey" -ForegroundColor $(if ($weatherApiKey -eq "your_openweathermap_api_key_here") { "Red" } else { "Green" })
    Write-Host "Enabled: $weatherEnabled" -ForegroundColor $(if ($weatherEnabled -eq "true") { "Green" } else { "Yellow" })
    Write-Host "Location: $weatherLocation" -ForegroundColor White
} else {
    Write-Host "❌ .env file not found or empty" -ForegroundColor Red
}

Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Green
Write-Host "==============" -ForegroundColor Green
Write-Host "1. Edit .env file and add your OpenWeatherMap API key" -ForegroundColor White
Write-Host "2. Run: docker-compose restart websocket-ingestion" -ForegroundColor White
Write-Host "3. Check dashboard at http://localhost:3000" -ForegroundColor White
Write-Host "4. Weather API calls should start appearing in the dashboard" -ForegroundColor White
Write-Host ""

# Offer to open the .env file for editing
$openFile = Read-Host "Would you like to open .env file for editing? (y/n)"
if ($openFile -eq "y" -or $openFile -eq "Y") {
    Write-Host "📝 Opening .env file for editing..." -ForegroundColor Yellow
    notepad .env
}

Write-Host ""
Write-Host "Weather configuration setup complete!" -ForegroundColor Green
