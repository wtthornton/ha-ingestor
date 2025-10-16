# BMAD Structure Restructuring - Phase 2
# Move implementation notes from docs/ to implementation/

Write-Host "Phase 2: Moving implementation notes from docs/ to implementation/" -ForegroundColor Cyan
Write-Host "=" * 70

$movedCount = 0
$errors = @()

# Status Reports
$statusReports = @(
    "DEPLOYMENT_SUCCESS_REPORT.md",
    "SERVICES_TAB_DEPLOYMENT_VERIFIED.md",
    "READY_FOR_QA.md"
)

# Enhancement Plans
$enhancementPlans = @(
    "CONTAINER_MANAGEMENT_ENHANCEMENT_PLAN.md",
    "DASHBOARD_ENHANCEMENT_ROADMAP.md",
    "EPIC_19_AND_20_EXECUTION_PLAN.md"
)

# Documentation Update Notes
$docUpdates = @(
    "DOCUMENTATION_UPDATES_OCTOBER_11_2025.md",
    "DOCUMENTATION_UPDATES_OCTOBER_2025.md",
    "DOCUMENTATION_UPDATES_SUMMARY.md",
    "DOCUMENTATION_UPDATES_WIZARD.md"
)

# Analysis Reports
$analysisReports = @(
    "IMPROVEMENTS_VISUAL_COMPARISON.md",
    "TOP_10_IMPROVEMENTS_ANALYSIS.md",
    "DOCUMENTATION_DEDUPLICATION_REPORT.md"
)

# Changelogs
$changelogs = @(
    "CHANGELOG_EPIC_23.md"
)

# Test Results
$testResults = @(
    "E2E_TEST_RESULTS.md"
)

function Move-ToImplementation {
    param(
        [string]$FileName,
        [string]$Destination = "implementation"
    )
    
    $sourcePath = "docs\$FileName"
    $destPath = "$Destination\$FileName"
    
    if (Test-Path $sourcePath) {
        try {
            Move-Item -Path $sourcePath -Destination $destPath -Force
            Write-Host "  ✅ Moved: $FileName → $Destination\" -ForegroundColor Green
            return $true
        } catch {
            $script:errors += "Failed to move $FileName`: $($_.Exception.Message)"
            Write-Host "  ❌ Error: $FileName" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "  ⏩ Skipped: $FileName (already moved)" -ForegroundColor Yellow
        return $false
    }
}

# Move Status Reports
Write-Host "`n📊 Status Reports..." -ForegroundColor Yellow
foreach ($file in $statusReports) {
    if (Move-ToImplementation $file) { $movedCount++ }
}

# Move Enhancement Plans
Write-Host "`n📋 Enhancement Plans..." -ForegroundColor Yellow
foreach ($file in $enhancementPlans) {
    if (Move-ToImplementation $file) { $movedCount++ }
}

# Move Documentation Update Notes
Write-Host "`n📝 Documentation Update Notes..." -ForegroundColor Yellow
foreach ($file in $docUpdates) {
    if (Move-ToImplementation $file) { $movedCount++ }
}

# Move Analysis Reports
Write-Host "`n📈 Analysis Reports..." -ForegroundColor Yellow
foreach ($file in $analysisReports) {
    if (Move-ToImplementation $file "implementation\analysis") { $movedCount++ }
}

# Move Changelogs
Write-Host "`n📜 Changelogs..." -ForegroundColor Yellow
foreach ($file in $changelogs) {
    if (Move-ToImplementation $file) { $movedCount++ }
}

# Move Test Results
Write-Host "`n✅ Test Results..." -ForegroundColor Yellow
# Create verification directory if it doesn't exist
if (-not (Test-Path "implementation\verification")) {
    New-Item -ItemType Directory -Path "implementation\verification" -Force | Out-Null
}
foreach ($file in $testResults) {
    if (Move-ToImplementation $file "implementation\verification") { $movedCount++ }
}

# Move subdirectories
Write-Host "`n📁 Moving Subdirectories..." -ForegroundColor Yellow

# docs/fixes/ → implementation/fixes/
if (Test-Path "docs\fixes") {
    try {
        if (Test-Path "implementation\fixes") {
            # Merge directories
            Get-ChildItem "docs\fixes" | ForEach-Object {
                Move-Item -Path $_.FullName -Destination "implementation\fixes\" -Force
            }
            Remove-Item "docs\fixes" -Force -Recurse
        } else {
            Move-Item -Path "docs\fixes" -Destination "implementation\fixes" -Force
        }
        Write-Host "  ✅ Moved: docs/fixes/ → implementation/fixes/" -ForegroundColor Green
        $movedCount++
    } catch {
        $errors += "Failed to move docs/fixes/: $($_.Exception.Message)"
        Write-Host "  ❌ Error moving docs/fixes/" -ForegroundColor Red
    }
} else {
    Write-Host "  ⏩ Skipped: docs/fixes/ (already moved)" -ForegroundColor Yellow
}

# docs/implementation/ → implementation/ (merge)
if (Test-Path "docs\implementation") {
    try {
        Get-ChildItem "docs\implementation" | ForEach-Object {
            Move-Item -Path $_.FullName -Destination "implementation\" -Force
        }
        Remove-Item "docs\implementation" -Force -Recurse
        Write-Host "  ✅ Merged: docs/implementation/ → implementation/" -ForegroundColor Green
        $movedCount++
    } catch {
        $errors += "Failed to merge docs/implementation/: $($_.Exception.Message)"
        Write-Host "  ❌ Error merging docs/implementation/" -ForegroundColor Red
    }
} else {
    Write-Host "  ⏩ Skipped: docs/implementation/ (already moved)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "Phase 2 Complete!" -ForegroundColor Green
Write-Host "Files moved: $movedCount" -ForegroundColor Cyan

if ($errors.Count -gt 0) {
    Write-Host "`n⚠️ Errors encountered:" -ForegroundColor Yellow
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
} else {
    Write-Host "✅ No errors!" -ForegroundColor Green
}


