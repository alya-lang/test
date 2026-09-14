param(
    [string]$Pkg = "",
    [switch]$Fmt
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$LibDir = Join-Path $RootDir "Lib"
if (-not (Test-Path $LibDir)) {
    $LibDir = Join-Path (Split-Path -Parent $RootDir) "Lib"
}

# Ensure toolchain auto-installation is enabled for local runs
$env:ALYA_TOOLCHAIN_AUTO_INSTALL = "1"

# Verify alyac command
try {
    $alyacVer = & alyac --version 2>&1
    Write-Host "✓ Local Alya compiler: $alyacVer" -ForegroundColor Green
} catch {
    Write-Error "'alyac' is not in PATH. Please run 'cargo install-quick' inside Src/alya first."
    exit 1
}

$Passed = @()
$Failed = @()

function Test-SinglePackage($dir) {
    $pkgName = Split-Path -Leaf $dir
    $manifest = Join-Path $dir "alya.toml"
    if (-not (Test-Path $manifest)) { return }

    Write-Host "`n----------------------------------------------------" -ForegroundColor Cyan
    Write-Host "📦 Testing Package: Lib/$pkgName (Windows)" -ForegroundColor Cyan
    Write-Host "----------------------------------------------------" -ForegroundColor Cyan

    Push-Location $dir
    try {
        if ($Fmt) {
            Write-Host "--> Checking format: alyac fmt . --check" -ForegroundColor Yellow
            & alyac fmt . --check
        }
        
        $lockFile = Join-Path $dir "alya.lock"
        if (Test-Path $lockFile) {
            Write-Host "--> Resolving dependencies: alyac install"
            & alyac install
        }

        Write-Host "--> Running tests: alyac test"
        & alyac test
        if ($LASTEXITCODE -eq 0) {
            $script:Passed += $pkgName
        } else {
            $script:Failed += $pkgName
        }
    } catch {
        $script:Failed += $pkgName
    } finally {
        Pop-Location
    }
}

if ($Pkg -ne "") {
    $pkgs = $Pkg -split "," | ForEach-Object { $_.Trim() }
    foreach ($p in $pkgs) {
        $target = Join-Path $LibDir $p
        if (Test-Path $target) {
            Test-SinglePackage $target
        } else {
            Write-Warning "Package '$p' not found in Lib/"
        }
    }
} else {
    Get-ChildItem -Path $LibDir -Directory | ForEach-Object {
        Test-SinglePackage $_.FullName
    }
}

Write-Host "`n====================================================" -ForegroundColor Cyan
Write-Host "             TEST SUMMARY (WINDOWS)                 " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
if ($Passed.Count -gt 0) {
    Write-Host "`n  Passed Packages ($($Passed.Count)):" -ForegroundColor Green
    foreach ($p in $Passed) { Write-Host "    ✓ $p" -ForegroundColor Green }
}
if ($Failed.Count -gt 0) {
    Write-Host "`n  Failed Packages ($($Failed.Count)):" -ForegroundColor Red
    foreach ($p in $Failed) { Write-Host "    ✗ $p" -ForegroundColor Red }
    exit 1
} else {
    Write-Host "`n🎉 All Windows package tests passed successfully!`n" -ForegroundColor Green
}
