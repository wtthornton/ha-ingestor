# Update Home Assistant Token Script
# This script helps you update the HOME_ASSISTANT_TOKEN without losing other settings

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " Home Assistant Token Update Utility" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Current Configuration:" -ForegroundColor Yellow
$envFile = ".env"
if (Test-Path $envFile) {
    $content = Get-Content $envFile
    $haUrl = ($content | Select-String "HOME_ASSISTANT_URL=" | Select-Object -First 1) -replace "HOME_ASSISTANT_URL=", ""
    $currentToken = ($content | Select-String "^HOME_ASSISTANT_TOKEN=" | Select-Object -First 1) -replace "HOME_ASSISTANT_TOKEN=", ""
    
    Write-Host "  URL: $haUrl" -ForegroundColor Green
    Write-Host "  Current Token (first 20 chars): $($currentToken.Substring(0, [Math]::Min(20, $currentToken.Length)))..." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "  ERROR: .env file not found!" -ForegroundColor Red
    exit 1
}

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " Instructions to Generate New Token:" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open Home Assistant: $haUrl" -ForegroundColor White
Write-Host "2. Click on your profile (bottom left)" -ForegroundColor White
Write-Host "3. Scroll down to 'Long-Lived Access Tokens'" -ForegroundColor White
Write-Host "4. Click 'CREATE TOKEN'" -ForegroundColor White
Write-Host "5. Give it a name like 'HA Ingestor'" -ForegroundColor White
Write-Host "6. Copy the token (it will only be shown once!)" -ForegroundColor White
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Prompt for new token
Write-Host "Paste your new long-lived access token here:" -ForegroundColor Yellow
Write-Host "(or press Ctrl+C to cancel)" -ForegroundColor Gray
Write-Host ""
$newToken = Read-Host "New Token"

if ([string]::IsNullOrWhiteSpace($newToken)) {
    Write-Host ""
    Write-Host "ERROR: No token provided. Exiting without changes." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " Updating Configuration..." -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Backup original file
$backupFile = ".env.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $envFile $backupFile
Write-Host "[✓] Backup created: $backupFile" -ForegroundColor Green

# Update token in .env file
$content = Get-Content $envFile
$updatedContent = $content | ForEach-Object {
    if ($_ -match "^HOME_ASSISTANT_TOKEN=") {
        "HOME_ASSISTANT_TOKEN=$newToken"
    } else {
        $_
    }
}

$updatedContent | Set-Content $envFile
Write-Host "[✓] Token updated in .env file" -ForegroundColor Green

# Test the new token
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " Testing New Token..." -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$headers = @{
    "Authorization" = "Bearer $newToken"
    "Content-Type" = "application/json"
}

try {
    $response = Invoke-WebRequest -Uri "$haUrl/api/" -Headers $headers -Method Get -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[✓] SUCCESS! Token is valid and working!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Response from Home Assistant:" -ForegroundColor Gray
        Write-Host $response.Content -ForegroundColor Gray
    }
} catch {
    Write-Host "[✗] ERROR: Token test failed!" -ForegroundColor Red
    Write-Host "    Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "    Message: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "The token has been updated in .env, but it's not working yet." -ForegroundColor Yellow
    Write-Host "Please verify you copied the correct token from Home Assistant." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To restore the original token:" -ForegroundColor Yellow
    Write-Host "    Copy-Item $backupFile .env" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " Next Steps" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Restart the WebSocket service:" -ForegroundColor White
Write-Host "    docker-compose restart websocket-ingestion" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Monitor the connection:" -ForegroundColor White
Write-Host "    docker logs -f homeiq-websocket | Select-String 'Connected|authentication'" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Verify events are flowing:" -ForegroundColor White
Write-Host "    docker exec homeiq-influxdb influx query 'from(bucket:\`"home_assistant_events\`") |> range(start: -5m) |> count()' --token homeiq-token --org homeiq" -ForegroundColor Cyan
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host " Token Update Complete!" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host ""

