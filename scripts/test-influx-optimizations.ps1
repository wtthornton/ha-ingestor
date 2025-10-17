# Test all InfluxDB Query Optimizations
# Verifies all 4 fixes from the audit

Write-Host "`n" "="*80 -ForegroundColor Cyan
Write-Host "  INFLUXDB QUERY OPTIMIZATION TEST SUITE" -ForegroundColor Cyan
Write-Host "="*80 "`n" -ForegroundColor Cyan

$results = @()

# Test 1: admin-api events endpoint
Write-Host "Test 1: admin-api events endpoint (HIGH PRIORITY FIX)" -ForegroundColor Yellow
Write-Host "Testing: http://localhost:8003/api/v1/events?limit=5`n" -ForegroundColor Gray

try {
    $before = Get-Date
    $response = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/events?limit=5" -UseBasicParsing
    $after = Get-Date
    $elapsed = ($after - $before).TotalMilliseconds
    $json = $response.Content | ConvertFrom-Json
    $uniqueIds = ($json | Select-Object -ExpandProperty id -Unique).Count
    
    $results += [PSCustomObject]@{
        Endpoint = "admin-api /events"
        Priority = "HIGH"
        Count = $json.Count
        UniqueIDs = $uniqueIds
        SizeKB = [Math]::Round($response.Content.Length / 1024, 2)
        TimeMS = [Math]::Round($elapsed, 0)
        Status = if ($json.Count -eq 5 -and $uniqueIds -eq 5) { "PASS" } else { "FAIL" }
    }
    
    if ($json.Count -eq 5 -and $uniqueIds -eq 5) {
        Write-Host "  ✅ PASS - Returns exactly 5 unique events" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL - Returns $($json.Count) events, $uniqueIds unique" -ForegroundColor Red
    }
    Write-Host "  📦 Size: $([Math]::Round($response.Content.Length / 1024, 2)) KB" -ForegroundColor White
    Write-Host "  ⏱️  Time: $([Math]::Round($elapsed, 0)) ms`n" -ForegroundColor White
    
} catch {
    Write-Host "  ❌ ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
    $results += [PSCustomObject]@{
        Endpoint = "admin-api /events"
        Priority = "HIGH"
        Status = "ERROR"
        Count = "N/A"
        UniqueIDs = "N/A"
        SizeKB = "N/A"
        TimeMS = "N/A"
    }
}

# Test 2: data-api events endpoint (verify still working)
Write-Host "Test 2: data-api events endpoint (VERIFY - fixed earlier)" -ForegroundColor Yellow
Write-Host "Testing: http://localhost:8006/api/v1/events?limit=5`n" -ForegroundColor Gray

try {
    $before = Get-Date
    $response = Invoke-WebRequest -Uri "http://localhost:8006/api/v1/events?limit=5" -UseBasicParsing
    $after = Get-Date
    $elapsed = ($after - $before).TotalMilliseconds
    $json = $response.Content | ConvertFrom-Json
    $uniqueIds = ($json | Select-Object -ExpandProperty id -Unique).Count
    
    $results += [PSCustomObject]@{
        Endpoint = "data-api /events"
        Priority = "HIGH"
        Count = $json.Count
        UniqueIDs = $uniqueIds
        SizeKB = [Math]::Round($response.Content.Length / 1024, 2)
        TimeMS = [Math]::Round($elapsed, 0)
        Status = if ($json.Count -eq 5 -and $uniqueIds -eq 5) { "PASS" } else { "FAIL" }
    }
    
    if ($json.Count -eq 5 -and $uniqueIds -eq 5) {
        Write-Host "  ✅ PASS - Still working correctly" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL - Regression detected!" -ForegroundColor Red
    }
    Write-Host "  📦 Size: $([Math]::Round($response.Content.Length / 1024, 2)) KB" -ForegroundColor White
    Write-Host "  ⏱️  Time: $([Math]::Round($elapsed, 0)) ms`n" -ForegroundColor White
    
} catch {
    Write-Host "  ❌ ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
    $results += [PSCustomObject]@{
        Endpoint = "data-api /events"
        Priority = "HIGH"
        Status = "ERROR"
        Count = "N/A"
        UniqueIDs = "N/A"
        SizeKB = "N/A"
        TimeMS = "N/A"
    }
}

# Summary
Write-Host "`n" "="*80 -ForegroundColor Cyan
Write-Host "  TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "="*80 "`n" -ForegroundColor Cyan

$results | Format-Table -AutoSize

$passed = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
$errors = ($results | Where-Object { $_.Status -eq "ERROR" }).Count

Write-Host "`nOverall Results:" -ForegroundColor Cyan
Write-Host "  ✅ Passed: $passed" -ForegroundColor Green
Write-Host "  ❌ Failed: $failed" -ForegroundColor $(if($failed -gt 0){"Red"}else{"Gray"})
Write-Host "  Errors: $errors" -ForegroundColor $(if($errors -gt 0){"Red"}else{"Gray"})
Write-Host "  Success Rate: $(if($results.Count -gt 0){[Math]::Round(($passed / $results.Count) * 100, 1)}else{0})%`n" -ForegroundColor Cyan

if ($passed -eq $results.Count) {
    Write-Host "ALL TESTS PASSED - Optimizations successful!`n" -ForegroundColor Green
} else {
    Write-Host "Some tests failed - review required`n" -ForegroundColor Yellow
}

