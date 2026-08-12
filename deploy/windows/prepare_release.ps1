param(
    [string]$EnvFile = ".\.env.production",
    [string]$Python = ".\venv\Scripts\python.exe"
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\load_env.ps1" -EnvFile $EnvFile
& $Python manage.py check
& $Python manage.py check --deploy
& $Python manage.py makemigrations --check --dry-run
& $Python manage.py migrate --check
& $Python manage.py collectstatic --noinput
Write-Host 'RELEASE PREPARADO.'
