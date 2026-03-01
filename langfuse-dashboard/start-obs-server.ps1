# ─────────────────────────────────────────────────────────────────────────────
#  start-obs-server.ps1
#  Starts the PharmaGenie Observability API on port 8001 (no Docker needed).
#  Run this from the langfuse-dashboard folder:
#
#    cd langfuse-dashboard
#    .\start-obs-server.ps1
# ─────────────────────────────────────────────────────────────────────────────

$venvActivate = "$PSScriptRoot\..\venv\Scripts\Activate.ps1"
$serverDir    = "$PSScriptRoot\server"

Write-Host ""
Write-Host "== PharmaGenie Observability Server ==" -ForegroundColor Cyan
Write-Host ""

# ── Activate venv ─────────────────────────────────────────────────────────────
if (Test-Path $venvActivate) {
    Write-Host "Activating venv..." -ForegroundColor Gray
    & $venvActivate
} else {
    Write-Warning "venv not found at $venvActivate — using system Python"
}

# ── Check .env exists ─────────────────────────────────────────────────────────
$envFile = "$serverDir\.env"
if (-not (Test-Path $envFile)) {
    Write-Warning ".env not found!  Copy .env.example → server\.env and fill in your Langfuse keys."
    Write-Host "  Get free keys at: https://cloud.langfuse.com" -ForegroundColor Yellow
    exit 1
}

# ── Check keys are filled in ──────────────────────────────────────────────────
$envContent = Get-Content $envFile -Raw
if ($envContent -match "PASTE_YOUR") {
    Write-Host ""
    Write-Host "ACTION NEEDED:" -ForegroundColor Yellow
    Write-Host "  1. Open  langfuse-dashboard\server\.env" -ForegroundColor White
    Write-Host "  2. Sign up free at https://cloud.langfuse.com" -ForegroundColor White
    Write-Host "  3. Create a project, go to Settings > API Keys" -ForegroundColor White
    Write-Host "  4. Replace PASTE_YOUR_PUBLIC_KEY_HERE  with your pk-lf-... key" -ForegroundColor White
    Write-Host "  5. Replace PASTE_YOUR_SECRET_KEY_HERE  with your sk-lf-... key" -ForegroundColor White
    Write-Host "  6. Re-run this script" -ForegroundColor White
    Write-Host ""
    Write-Host "  (OPENAI_API_KEY is only needed for the /run/* agent endpoints)" -ForegroundColor Gray
    Write-Host ""
}

# ── Launch server ─────────────────────────────────────────────────────────────
Write-Host "Starting server on http://localhost:8001 ..." -ForegroundColor Green
Write-Host "  Swagger docs  →  http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "  Health check  →  http://localhost:8001/health" -ForegroundColor Cyan
Write-Host "  Langfuse dash →  https://cloud.langfuse.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

Set-Location $serverDir
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
