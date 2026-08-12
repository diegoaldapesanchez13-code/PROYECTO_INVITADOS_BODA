param(
    [string]$EnvFile = ".\.env.production",
    [string]$Listen = "127.0.0.1:8001"
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\load_env.ps1" -EnvFile $EnvFile
$waitress = ".\venv\Scripts\waitress-serve.exe"
if (!(Test-Path $waitress)) { throw 'Waitress no está instalado en el venv.' }
& $waitress --listen=$Listen --threads=8 config.wsgi:application
