# ==============================================
# CENTRAL COMMAND MASTER CLEAN-UP AND REBUILD SCRIPT
# Version: 1.0.0
# Date: 2025-10-06
# Author: DKI Services / Central Command Automation
# ==============================================

# --- CONFIGURATION ---
$BasePath = "F:\The Central Command"
$ProtocolFile = "$BasePath\The War Room\SOP's\READ FILES\diagnostics_protocols\MASTER_DIAGNOSTIC_PROTOCOL_2025-10-05.md"
$LogFile = "$BasePath\Reorganization_Report_$(Get-Date -Format yyyy-MM-dd_HH-mm).log"

# --- INITIALIZATION ---
Write-Host "[START] Central Command Master Cleanup" -ForegroundColor Cyan
"=== CENTRAL COMMAND REORGANIZATION LOG ===" | Out-File $LogFile -Encoding utf8 -Force
Add-Content $LogFile "Date: $(Get-Date)"
Add-Content $LogFile "Source Protocol: $ProtocolFile"
Add-Content $LogFile "============================================="

# --- STEP 1: PARSE PROTOCOL FILE ---
Write-Host "[INFO] Parsing diagnostic protocol..." -ForegroundColor Yellow
$ProtocolContent = Get-Content $ProtocolFile -Raw

# Regex to extract system address and name lines from protocol
$SystemPattern = '(?m)^\|\s*(\d[-\d\.x]*)\s*\|\s*([^|]+?)\s*\|'
$Systems = [System.Collections.Generic.List[Hashtable]]::new()

foreach ($match in [regex]::Matches($ProtocolContent, $SystemPattern)) {
    $item = @{
        Address = $match.Groups[1].Value.Trim()
        Name = $match.Groups[2].Value.Trim() -replace '\s+', '_'
    }
    $Systems.Add($item)
}

Write-Host "[OK] Found $($Systems.Count) system definitions." -ForegroundColor Green
Add-Content $LogFile "Systems Detected: $($Systems.Count)"

# --- STEP 2: BUILD DIRECTORY STRUCTURE ---
foreach ($sys in $Systems) {
    $addr = $sys.Address
    $name = $sys.Name

    # Clean name for path safety
    $safeName = $name -replace '[^A-Za-z0-9_-]', ''

    # Determine Complex Root
    $complexPrefix = $addr.Split('-')[0]
    $ComplexPath = Join-Path $BasePath ("${complexPrefix}_complex")

    if (-not (Test-Path $ComplexPath)) {
        New-Item -ItemType Directory -Force -Path $ComplexPath | Out-Null
        Add-Content $LogFile "Created Complex: $ComplexPath"
    }

    # Create System Folder
    $SystemPath = Join-Path $ComplexPath ("${addr}_$safeName")
    if (-not (Test-Path $SystemPath)) {
        New-Item -ItemType Directory -Force -Path $SystemPath | Out-Null
        Add-Content $LogFile "Created System Folder: $SystemPath"
    }

    # Create Test Plan Folder
    $TestPlanPath = Join-Path $SystemPath "test_plans"
    if (-not (Test-Path $TestPlanPath)) {
        New-Item -ItemType Directory -Force -Path $TestPlanPath | Out-Null
    }

    # Create Default Test Plan File
    $PlanFile = Join-Path $TestPlanPath ("${safeName}_testplan.md")
    if (-not (Test-Path $PlanFile)) {
        "# $name Test Plan`nAddress: $addr`nCreated: $(Get-Date)" | Out-File $PlanFile -Encoding utf8
        Add-Content $LogFile "Created Test Plan: $PlanFile"
    }
}

# --- STEP 3: ORGANIZE EXISTING SUBSYSTEM FOLDERS ---
Write-Host "[INFO] Reorganizing subsystem folders..." -ForegroundColor Yellow
$SubSystems = Get-ChildItem -Path $BasePath -Directory -Recurse | Where-Object { $_.Name -match '_subsystem$' }

foreach ($sub in $SubSystems) {
    $parentMatch = $Systems | Where-Object { $sub.Name -like ("$($_.Name)*") }
    if ($parentMatch) {
        $ParentAddr = $parentMatch.Address.Split('.')[0]
        $ParentFolder = Get-ChildItem -Path $BasePath -Recurse -Directory | Where-Object { $_.Name -match "^${ParentAddr}_" }
        if ($ParentFolder) {
            $Target = Join-Path $ParentFolder.FullName "subsystems"
            if (-not (Test-Path $Target)) { New-Item -ItemType Directory -Force -Path $Target | Out-Null }
            Move-Item $sub.FullName $Target -Force
            Add-Content $LogFile "Moved: $($sub.FullName) -> $Target"
        }
    }
}

# --- STEP 4: CLEAN UNUSED DIRECTORIES ---
Write-Host "[INFO] Cleaning orphaned folders..." -ForegroundColor Yellow
$Orphans = Get-ChildItem -Path $BasePath -Directory | Where-Object { $_.Name -match '_test|_temp|backup' }
foreach ($orphan in $Orphans) {
    Remove-Item -Recurse -Force -Path $orphan.FullName
    Add-Content $LogFile "Removed orphaned folder: $($orphan.FullName)"
}

# --- STEP 5: FINAL SUMMARY ---
Write-Host "[DONE] Cleanup and reorganization completed." -ForegroundColor Cyan
Add-Content $LogFile "============================================="
Add-Content $LogFile "Cleanup Complete: $(Get-Date)"

Write-Host "[LOG] Detailed report saved to:`n$LogFile" -ForegroundColor Magenta
