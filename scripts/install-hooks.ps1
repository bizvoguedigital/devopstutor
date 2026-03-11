$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    git config core.hooksPath .githooks
    Write-Host "[hooks] Installed repo hooks."
    $hooksPath = git config core.hooksPath
    Write-Host "[hooks] core.hooksPath=$hooksPath"
}
finally {
    Pop-Location
}
