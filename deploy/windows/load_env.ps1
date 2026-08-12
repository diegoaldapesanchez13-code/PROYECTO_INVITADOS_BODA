param([Parameter(Mandatory=$true)][string]$EnvFile)
if (!(Test-Path $EnvFile)) { throw "No existe el archivo de entorno: $EnvFile" }
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if (!$line -or $line.StartsWith('#')) { return }
    $parts = $line.Split('=', 2)
    if ($parts.Count -ne 2) { return }
    [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1], 'Process')
}
