param(
    [Parameter(Mandatory=$true)][string]$BackupDir,
    [string]$EnvFile = ".\.env.production",
    [string]$Python = ".\venv\Scripts\python.exe"
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\load_env.ps1" -EnvFile $EnvFile
if ($env:DJANGO_DB_ENGINE -notin @('postgres','postgresql')) { throw 'DJANGO_DB_ENGINE debe ser postgresql.' }

& $Python manage.py check
& $Python manage.py migrate
& $Python manage.py loaddata (Join-Path $BackupDir 'data.fixture.json')
& $Python manage.py reset_postgres_sequences

if (Test-Path (Join-Path $BackupDir 'media')) {
    New-Item -ItemType Directory -Force -Path .\media | Out-Null
    Copy-Item (Join-Path $BackupDir 'media\*') .\media -Recurse -Force
}

& $Python manage.py data_inventory .\migration_inventory_postgres.json --hash-media
& $Python scripts\compare_inventories.py (Join-Path $BackupDir 'inventory_sqlite.json') .\migration_inventory_postgres.json
Write-Host 'POSTGRESQL CARGADO Y VERIFICADO.'
