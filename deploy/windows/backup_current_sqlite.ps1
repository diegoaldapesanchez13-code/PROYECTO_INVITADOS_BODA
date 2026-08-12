param(
    [string]$Python = ".\venv\Scripts\python.exe",
    [string]$BackupRoot = ".\backups"
)
$ErrorActionPreference = 'Stop'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$dest = Join-Path $BackupRoot "pre_postgres_$stamp"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$env:DJANGO_DB_ENGINE = 'sqlite'
& $Python manage.py check
& $Python manage.py data_inventory (Join-Path $dest 'inventory_sqlite.json') --hash-media
& $Python manage.py export_portable_backup (Join-Path $dest 'data.fixture.json')
Copy-Item .\db.sqlite3 (Join-Path $dest 'db.sqlite3') -Force
if (Test-Path .\media) { Copy-Item .\media (Join-Path $dest 'media') -Recurse -Force }

$hash = Get-FileHash (Join-Path $dest 'db.sqlite3') -Algorithm SHA256
$hash | Format-List | Out-File (Join-Path $dest 'db.sqlite3.sha256.txt') -Encoding utf8
Write-Host "BACKUP COMPLETO: $dest"
