param(
    [switch]$SkipBackendTests,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"

Write-Host "[prepush] Starting pre-push validation..." -ForegroundColor Cyan

$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    if (-not $SkipBackendTests) {
        Write-Host "[prepush] Running backend test suite in Docker..." -ForegroundColor Yellow
        docker compose exec -T backend pytest -q
        Write-Host "[prepush] Backend tests passed." -ForegroundColor Green
    }
    else {
        Write-Host "[prepush] Skipping backend tests." -ForegroundColor DarkYellow
    }

    if (-not $SkipFrontendBuild) {
        Write-Host "[prepush] Running frontend production build..." -ForegroundColor Yellow
        Push-Location (Join-Path $repoRoot "frontend")
        try {
            npm run build
        }
        finally {
            Pop-Location
        }
        Write-Host "[prepush] Frontend build passed." -ForegroundColor Green
    }
    else {
        Write-Host "[prepush] Skipping frontend build." -ForegroundColor DarkYellow
    }

    Write-Host "[prepush] All checks passed. Safe to push." -ForegroundColor Green
}
finally {
    Pop-Location
}
