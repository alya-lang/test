param(
    [switch]$Compiler,
    [switch]$Packages,
    [string]$Pkg = "",
    [switch]$Clippy,
    [switch]$Fmt,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
# Project root directory (parent of Tst/ or workspace root)
$RootDir = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $RootDir "Lib"))) {
    $RootDir = Split-Path -Parent $RootDir
}


# Check if Docker is available
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker daemon is not running. Please start Docker Desktop and try again."
        exit 1
    }
} catch {
    Write-Error "Docker is not installed or not in PATH."
    exit 1
}

# Handle cache cleaning
if ($Clean) {
    Write-Host "🧹 Cleaning Docker caches (alya-cargo-cache, alya-target-cache)..." -ForegroundColor Yellow
    docker volume rm alya-cargo-cache alya-target-cache -f 2>$null
    Write-Host "✓ Docker volume caches removed." -ForegroundColor Green
    if (-not ($Compiler -or $Packages -or $Pkg -or $Clippy -or $Fmt)) {
        exit 0
    }
}

# Determine what to run
$RunCompiler = "0"
$RunPackages = "0"
$TargetPkgs = ""

if ($Pkg -ne "") {
    $RunPackages = "1"
    $TargetPkgs = $Pkg
    if ($Compiler) { $RunCompiler = "1" }
} elseif ($Compiler -and -not $Packages) {
    $RunCompiler = "1"
} elseif ($Packages -and -not $Compiler) {
    $RunPackages = "1"
} else {
    # Default: Run both compiler tests and all package tests
    $RunCompiler = "1"
    $RunPackages = "1"
}

$RunClippy = if ($Clippy) { "1" } else { "0" }
$RunFmt = if ($Fmt) { "1" } else { "0" }

# Normalize path for Docker mount
$WorkspaceMount = $RootDir.Replace("\", "/")

Write-Host "🐳 Launching Alya Linux Test Container (rust:bookworm)..." -ForegroundColor Cyan
Write-Host "   Workspace : $WorkspaceMount" -ForegroundColor DarkGray
Write-Host "   Compiler  : $(if ($RunCompiler -eq '1') { 'YES' } else { 'NO' })" -ForegroundColor DarkGray
Write-Host "   Packages  : $(if ($RunPackages -eq '1') { if ($TargetPkgs) { $TargetPkgs } else { 'ALL' } } else { 'NO' })" -ForegroundColor DarkGray

docker run --rm `
    -v "${WorkspaceMount}:/workspace" `
    -v "alya-cargo-cache:/root/.cargo" `
    -v "alya-target-cache:/root/target" `
    -v "alya-pkg-cache:/root/.alya" `
    -e CARGO_TARGET_DIR=/root/target `
    -e RUN_COMPILER=$RunCompiler `
    -e RUN_PACKAGES=$RunPackages `
    -e TARGET_PKGS=$TargetPkgs `
    -e RUN_CLIPPY=$RunClippy `
    -e RUN_FMT=$RunFmt `
    -w /workspace `
    rust:bookworm bash /workspace/Tst/docker/run-tests.sh

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ All Linux tests completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Linux test suite failed." -ForegroundColor Red
    exit $LASTEXITCODE
}
