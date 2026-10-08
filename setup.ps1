$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (!(Test-Path .venv)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
if (!(Test-Path .env)) { Copy-Item .env.example .env }
& .\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed." }
Write-Host "Setup complete. Add your private configuration to .env, then follow README.md."
