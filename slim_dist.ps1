param(
    [string]$DistPath
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "dist slim_dist (Optimized Strategy)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path $DistPath)) {
    Write-Host "[ERROR] Directory not found: $DistPath" -ForegroundColor Red
    exit 1
}

$InitialSize = (Get-ChildItem -Path $DistPath -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "`nInitial Size: $([math]::Round($InitialSize, 2)) MB" -ForegroundColor Yellow

# 1. PDB
$pdbFiles = Get-ChildItem -Path $DistPath -Recurse -Include *.pdb -File
$pdbSize = ($pdbFiles | Measure-Object -Property Length -Sum).Sum / 1MB
if ($pdbFiles.Count -gt 0) {
    $pdbFiles | Remove-Item -Force
}

# 2. PYI
$pyiFiles = Get-ChildItem -Path $DistPath -Recurse -Include *.pyi -File
$pyiSize = ($pyiFiles | Measure-Object -Property Length -Sum).Sum / 1MB
if ($pyiFiles.Count -gt 0) {
    $pyiFiles | Remove-Item -Force
}

# 3. pycache
$pycacheDirs = Get-ChildItem -Path $DistPath -Recurse -Directory -Filter "__pycache__"
foreach ($dir in $pycacheDirs) {
    Remove-Item -Path $dir.FullName -Recurse -Force
}

# 4. test
$testDirs = Get-ChildItem -Path $DistPath -Recurse -Directory | Where-Object { $_.Name -match '^tests?$' }
foreach ($dir in $testDirs) {
    Remove-Item -Path $dir.FullName -Recurse -Force
}

# 5. docs
$docDirs = Get-ChildItem -Path $DistPath -Recurse -Directory | Where-Object { $_.Name -match '^(docs|examples|samples|demo)$' }
foreach ($dir in $docDirs) {
    Remove-Item -Path $dir.FullName -Recurse -Force
}

# 6. pyc
$pycFiles = Get-ChildItem -Path $DistPath -Recurse -Include *.pyc -File
if ($pycFiles.Count -gt 0) {
    $pycFiles | Remove-Item -Force
}

# 7. dist-info
$distInfoDirs = Get-ChildItem -Path $DistPath -Recurse -Directory -Filter "*.dist-info"
foreach ($infoDir in $distInfoDirs) {
    $filesToRemove = @("RECORD", "INSTALLER", "direct_url.json")
    foreach ($fileName in $filesToRemove) {
        $file = Join-Path $infoDir.FullName $fileName
        if (Test-Path $file) {
            Remove-Item $file -Force
        }
    }
}

$FinalSize = (Get-ChildItem -Path $DistPath -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
$SavedSize = $InitialSize - $FinalSize
$SavedPercent = if ($InitialSize -gt 0) { ($SavedSize / $InitialSize) * 100 } else { 0 }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "Final Size: $([math]::Round($FinalSize, 2)) MB (Saved $([math]::Round($SavedSize, 2)) MB)" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
