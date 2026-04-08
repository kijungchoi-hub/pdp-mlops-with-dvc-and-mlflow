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

Write-Host "부트스트랩이 완료되었습니다."
Write-Host "다음 순서:"
Write-Host "  1. 필요하면 .env 값을 수정하세요"
Write-Host "  2. docker compose up -d"
Write-Host "  3. .\\scripts\\configure_dvc_remote.ps1"
Write-Host "  4. .\\scripts\\run_pipeline.ps1"
