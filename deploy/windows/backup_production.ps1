param(
    [string]$EnvFile = ".\.env.production",
    [string]$BackupRoot = "D:\DIRTEC_BACKUPS",
    [string]$PgDump = "",
    [int]$RetentionDays = 14
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\load_env.ps1" -EnvFile $EnvFile

if (!$PgDump) {
    $candidate = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\pg_dump.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($candidate) { $PgDump = $candidate.FullName }
}
if (!$PgDump -or !(Test-Path $PgDump)) { throw "No se encontró pg_dump. Pasa -PgDump con su ruta real." }

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$dest = Join-Path $BackupRoot $stamp
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$env:PGPASSWORD = $env:POSTGRES_PASSWORD
& $PgDump `
    --host=$env:POSTGRES_HOST `
    --port=$env:POSTGRES_PORT `
    --username=$env:POSTGRES_USER `
    --format=custom `
    --file=(Join-Path $dest 'dirtec_event_studio.dump') `
    $env:POSTGRES_DB
if ($LASTEXITCODE -ne 0) { throw 'pg_dump falló.' }

if (Test-Path .\media) {
    Copy-Item .\media (Join-Path $dest 'media') -Recurse -Force
}
Get-FileHash (Join-Path $dest 'dirtec_event_studio.dump') -Algorithm SHA256 |
    Format-List | Out-File (Join-Path $dest 'database.sha256.txt') -Encoding utf8

Get-ChildItem $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$RetentionDays) } |
    Remove-Item -Recurse -Force

Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
Write-Host "BACKUP PRODUCCION COMPLETO: $dest"
