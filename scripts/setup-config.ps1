# Setup configuration files for HA Ingestor
# Creates .env files from templates

Write-Host "🔧 HA Ingestor Configuration Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Change to infrastructure directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptPath "..\infrastructure")

# Function to setup config file
function Setup-Config {
    param(
        [string]$template,
        [string]$target
    )
    
    if (-not (Test-Path $template)) {
        Write-Host "⚠️  Warning: Template $template not found, skipping" -ForegroundColor Yellow
        return
    }
    
    if (Test-Path $target) {
        Write-Host "⚠️  $target already exists, skipping" -ForegroundColor Yellow
        return
    }
    
    Copy-Item $template $target
    Write-Host "✅ Created $target" -ForegroundColor Green
}

# Setup configuration files
Write-Host "Creating configuration files from templates..."
Write-Host ""

Setup-Config "env.websocket.template" ".env.websocket"
Setup-Config "env.weather.template" ".env.weather"
Setup-Config "env.influxdb.template" ".env.influxdb"

Write-Host ""
Write-Host "✅ Configuration setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit configuration files in infrastructure directory"
Write-Host "2. Or use the dashboard: http://localhost:3000/ (Configuration tab)"
Write-Host "3. Start services: docker-compose up -d"
Write-Host ""
Write-Host "Configuration files:"
Write-Host "  - infrastructure\.env.websocket  (Home Assistant)"
Write-Host "  - infrastructure\.env.weather    (Weather API)"
Write-Host "  - infrastructure\.env.influxdb   (Database)"
Write-Host ""
