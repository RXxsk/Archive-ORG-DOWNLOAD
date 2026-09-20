$ErrorActionPreference = "Stop"
Write-Host "[2DoArchive] Instalador para Windows" -ForegroundColor Cyan

$target = Join-Path $HOME "2DoArchive"
$bin = Join-Path $target "bin"
New-Item -ItemType Directory -Force -Path $target, $bin | Out-Null

Copy-Item -Force ".\2doarchive.py" $target
Copy-Item -Force ".\run.bat" $target

$launcher = @"
@echo off
py -3 "%USERPROFILE%\2DoArchive\2doarchive.py" %*
if errorlevel 1 python "%USERPROFILE%\2DoArchive\2doarchive.py" %*
"@
Set-Content -Path (Join-Path $bin "archive.cmd") -Value $launcher -Encoding ASCII

# Add the launcher directory to the user's PATH if it is not already there.
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$parts = @()
if ($userPath) { $parts = $userPath -split ';' | Where-Object { $_ -ne "" } }
if ($parts -notcontains $bin) {
    $newPath = (($parts + $bin) -join ';')
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
}

Write-Host ""
Write-Host "✓ 2DoArchive instalado en: $target" -ForegroundColor Green
Write-Host "✓ Comando creado: archive" -ForegroundColor Green
Write-Host ""
Write-Host "Cierra y vuelve a abrir CMD/PowerShell y escribe:"
Write-Host "  archive" -ForegroundColor Yellow
