# InfluxDB Schema Reset & Validation Script (PowerShell Version)
# This script resets InfluxDB and ensures the correct schema for hybrid architecture

param(
    [switch]$DryRun = $false
)

# Configuration
$InfluxDBUrl = "http://localhost:8086"
$OrgName = if ($env:INFLUXDB_ORG) { $env:INFLUXDB_ORG } else { "homeiq" }
$BucketName = if ($env:INFLUXDB_BUCKET) { $env:INFLUXDB_BUCKET } else { "home_assistant_events" }
$AdminToken = if ($env:INFLUXDB_TOKEN) { $env:INFLUXDB_TOKEN } else { "homeiq-token" }
$Username = if ($env:INFLUXDB_USERNAME) { $env:INFLUXDB_USERNAME } else { "admin" }
$Password = if ($env:INFLUXDB_PASSWORD) { $env:INFLUXDB_PASSWORD } else { "admin123" }

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Purple = "Magenta"
}

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓ SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[⚠ WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[✗ ERROR] $Message" -ForegroundColor $Colors.Red
}

function Write-Header {
    param([string]$Message)
    Write-Host "===========================================" -ForegroundColor $Colors.Purple
    Write-Host " $Message" -ForegroundColor $Colors.Purple
    Write-Host "===========================================" -ForegroundColor $Colors.Purple
}

function Wait-ForInfluxDB {
    Write-Status "Waiting for InfluxDB to be ready..."
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "$InfluxDBUrl/health" -Method Get -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "InfluxDB is ready!"
                return $true
            }
        }
        catch {
            # InfluxDB not ready yet
        }
        
        Write-Status "Attempt $attempt/$maxAttempts - InfluxDB not ready yet. Waiting..."
        Start-Sleep -Seconds 5
        $attempt++
    }
    
    Write-Error "InfluxDB failed to start within expected time"
    return $false
}

function Create-Organization {
    Write-Status "Creating organization: $OrgName"
    
    try {
        # Check if organization already exists
        $orgs = docker exec homeiq-influxdb influx org list --host $InfluxDBUrl --token $AdminToken --json
        $orgExists = $orgs | ConvertFrom-Json | Where-Object { $_.name -eq $OrgName }
        
        if ($orgExists) {
            Write-Warning "Organization '$OrgName' already exists"
        } else {
            docker exec homeiq-influxdb influx org create --name $OrgName --description "Home Assistant Data Ingestion Organization" --token $AdminToken --host $InfluxDBUrl
            Write-Success "Organization '$OrgName' created"
        }
    }
    catch {
        Write-Error "Failed to create organization: $_"
        return $false
    }
    return $true
}

function Create-Bucket {
    param(
        [string]$Name,
        [string]$Retention = "365d"
    )
    
    Write-Status "Creating bucket: $Name with $Retention retention"
    
    try {
        # Check if bucket already exists
        $buckets = docker exec homeiq-influxdb influx bucket list --org $OrgName --host $InfluxDBUrl --token $AdminToken --json
        $bucketExists = $buckets | ConvertFrom-Json | Where-Object { $_.name -eq $Name }
        
        if ($bucketExists) {
            Write-Warning "Bucket '$Name' already exists - removing and recreating"
            docker exec homeiq-influxdb influx bucket delete --name $Name --org $OrgName --token $AdminToken --host $InfluxDBUrl
        }
        
        # Create bucket with specified retention
        docker exec homeiq-influxdb influx bucket create --name $Name --org $OrgName --retention $Retention --token $AdminToken --host $InfluxDBUrl
        Write-Success "Bucket '$Name' created with $Retention retention"
    }
    catch {
        Write-Error "Failed to create bucket '$Name': $_"
        return $false
    }
    return $true
}

function Create-AdditionalBuckets {
    Write-Status "Creating additional buckets for hybrid architecture..."
    
    $buckets = @(
        @{ Name = "sports_data"; Retention = "90d" },
        @{ Name = "weather_data"; Retention = "180d" },
        @{ Name = "system_metrics"; Retention = "30d" }
    )
    
    foreach ($bucket in $buckets) {
        if (-not (Create-Bucket -Name $bucket.Name -Retention $bucket.Retention)) {
            return $false
        }
    }
    
    Write-Success "Additional buckets created"
    return $true
}

function Validate-Schema {
    Write-Status "Validating schema with test data point..."
    
    try {
        # Create test data point with all expected tags and fields
        $timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        $testData = "home_assistant_events,entity_id=sensor.living_room_temperature,domain=sensor,device_class=temperature,area=living_room,device_name=`"Living Room Temperature Sensor`",device_id=zwave_001,area_id=room_001,entity_category=null,integration=zwave,weather_condition=clear,time_of_day=afternoon state_value=`"22.5`",previous_state=`"22.3`",normalized_value=22.5,unit_of_measurement=`"°C`",confidence=0.95,context_id=`"ctx_001`",context_parent_id=`"automation_001`",context_user_id=`"user_001`",duration_seconds=3600,energy_consumption=0.0,weather_temp=22.5,weather_humidity=45.0,weather_pressure=1013.25,manufacturer=`"Z-Wave Alliance`",model=`"ZW100`",sw_version=`"1.0.0`" $timestamp"
        
        $testData | docker exec -i homeiq-influxdb influx write --bucket $BucketName --org $OrgName --token $AdminToken --host $InfluxDBUrl --precision ns
        
        Write-Success "Test data point created"
        return $true
    }
    catch {
        Write-Error "Failed to create test data point: $_"
        return $false
    }
}

function Verify-Schema {
    Write-Status "Verifying schema structure..."
    
    try {
        # Query the test data and check schema
        $query = 'from(bucket: "' + $BucketName + '") |> range(start: -1h) |> limit(n:1) |> schema.fieldsAsCols()'
        $schemaResult = docker exec homeiq-influxdb influx query --org $OrgName --token $AdminToken --host $InfluxDBUrl $query
        
        Write-Success "Schema verification completed"
        Write-Host $schemaResult
        return $true
    }
    catch {
        Write-Error "Schema verification failed: $_"
        return $false
    }
}

function Cleanup-TestData {
    Write-Status "Cleaning up test data..."
    
    try {
        # Delete the test data point
        $startTime = (Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ssZ")
        $endTime = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        
        $predicate = 'entity_id="sensor.living_room_temperature"'
        docker exec homeiq-influxdb influx delete --bucket $BucketName --org $OrgName --token $AdminToken --host $InfluxDBUrl --start $startTime --stop $endTime --predicate $predicate
        
        Write-Success "Test data cleaned up"
    }
    catch {
        Write-Warning "Failed to cleanup test data: $_"
    }
}

function Show-FinalStatus {
    Write-Status "Final InfluxDB Status:"
    Write-Host ""
    Write-Host "📊 Organization: $OrgName"
    Write-Host "📦 Buckets:"
    
    try {
        $buckets = docker exec homeiq-influxdb influx bucket list --org $OrgName --host $InfluxDBUrl --token $AdminToken --json
        $bucketList = $buckets | ConvertFrom-Json
        foreach ($bucket in $bucketList) {
            $retentionDays = [math]::Round($bucket.retentionRules[0].everySeconds / 86400)
            Write-Host "  - $($bucket.name) (retention: $retentionDays days)"
        }
    }
    catch {
        Write-Host "  - Unable to retrieve bucket list"
    }
    
    Write-Host ""
    Write-Host "🔑 Admin Token: $AdminToken"
    Write-Host "🌐 URL: $InfluxDBUrl"
    Write-Host ""
    Write-Success "InfluxDB reset and schema validation completed!"
}

# Main execution
function Main {
    Write-Header "InfluxDB Schema Reset & Validation Script (PowerShell)"
    
    if ($DryRun) {
        Write-Warning "DRY RUN MODE - No changes will be made"
        return
    }
    
    # Wait for InfluxDB to be ready
    if (-not (Wait-ForInfluxDB)) {
        exit 1
    }
    
    # Create organization
    if (-not (Create-Organization)) {
        exit 1
    }
    
    # Create main bucket
    if (-not (Create-Bucket -Name $BucketName -Retention "365d")) {
        exit 1
    }
    
    # Create additional buckets
    if (-not (Create-AdditionalBuckets)) {
        exit 1
    }
    
    # Validate schema
    if (-not (Validate-Schema)) {
        exit 1
    }
    
    if (-not (Verify-Schema)) {
        exit 1
    }
    
    # Clean up test data
    Cleanup-TestData
    
    # Display final status
    Show-FinalStatus
}

# Run main function
Main
