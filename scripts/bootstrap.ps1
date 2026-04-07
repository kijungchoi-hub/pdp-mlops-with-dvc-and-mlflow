param(
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

Require-Command git
Require-Command python
Require-Command pip
Require-Command dvc

if (-not (Test-Path .git)) {
    git init
}

if (-not (Test-Path .dvc)) {
    dvc init
}

python -m venv $VenvPath
& "$VenvPath\Scripts\python.exe" -m pip install --upgrade pip
& "$VenvPath\Scripts\python.exe" -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Bootstrap completed."
Write-Host "Next:"
Write-Host "  1. Update .env values if needed"
Write-Host "  2. docker compose up -d"
Write-Host "  3. .\\scripts\\configure_dvc_remote.ps1"
Write-Host "  4. .\\scripts\\run_pipeline.ps1"
