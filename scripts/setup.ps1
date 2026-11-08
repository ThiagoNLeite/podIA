# podIA — setup no Windows (PowerShell). Uso: .\scripts\setup.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"

# 1. .env
$envFile = Join-Path $backend ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root ".env.example") $envFile
    Write-Host "Criado backend\.env a partir do .env.example"
}
if (-not (Select-String -Path $envFile -Pattern "^GEMINI_API_KEY=\S+" -Quiet)) {
    Write-Warning "GEMINI_API_KEY vazia em backend\.env — sem ela, só o gerador local (sem IA) funciona."
}

# 2. Ferramentas do sistema
foreach ($tool in @("ffmpeg", "espeak-ng")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Warning "$tool não encontrado no PATH. Instale: winget install Gyan.FFmpeg / winget install eSpeak-NG.eSpeak-NG"
    }
}

# 3. Backend (Python 3.12)
$venvPy = Join-Path $backend ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    py -3.12 -m venv (Join-Path $backend ".venv")
}
& $venvPy -m pip install -q --upgrade pip
& $venvPy -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu
& $venvPy -m pip install -q -r (Join-Path $backend "requirements.txt")

# 4. App
$mobile = Join-Path $root "mobile"
if (Test-Path (Join-Path $mobile "package.json")) {
    Push-Location $mobile; npm install; Pop-Location
}

# 5. Testes
Push-Location $backend
& $venvPy -m pytest -q
Pop-Location
Write-Host "Pronto! Backend: docker compose up --build  (ou: cd backend; .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0)"
