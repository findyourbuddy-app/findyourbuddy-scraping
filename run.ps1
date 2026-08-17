$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .env)) {
    Write-Warning ".env bulunamadi, .env.example'dan kopyalaniyor -- degerleri doldurmayi unutma"
    Copy-Item .env.example .env
}

uv sync
uv run python -m app.main
