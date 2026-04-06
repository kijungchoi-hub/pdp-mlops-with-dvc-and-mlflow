param(
    [string]$RemoteName = "storage",
    [string]$RemoteUrl = "s3://dvc",
    [string]$EndpointUrl = "http://localhost:9000",
    [string]$AccessKey = "minio",
    [string]$SecretKey = "minio123"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".dvc")) {
    throw "Run 'dvc init' first."
}

dvc remote add -d $RemoteName $RemoteUrl --force
dvc remote modify --local $RemoteName endpointurl $EndpointUrl
dvc remote modify --local $RemoteName access_key_id $AccessKey
dvc remote modify --local $RemoteName secret_access_key $SecretKey

Write-Host "Configured DVC remote '$RemoteName' -> $RemoteUrl"

