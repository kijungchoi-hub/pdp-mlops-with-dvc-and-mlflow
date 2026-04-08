$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Run scripts/bootstrap.ps1 first."
}

$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') {
            return
        }
        $name, $value = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($name, $value)
        Set-Item -Path "Env:$name" -Value $value
    }
}

# Windows 시스템 권한 문제를 피하기 위해 DVC 상태를 저장소 내부에 유지합니다.
$env:DVC_SYSTEM_CONFIG_DIR = ".dvc\system"
$env:DVC_GLOBAL_CONFIG_DIR = ".dvc\global"
$env:DVC_SITE_CACHE_DIR = ".dvc\site-cache"
$env:ITERATIVE_DO_NOT_TRACK = "1"

New-Item -ItemType Directory -Force ".dvc\system", ".dvc\global", ".dvc\site-cache" | Out-Null

& ".venv\Scripts\dvc.exe" repro
& ".venv\Scripts\dvc.exe" metrics show
