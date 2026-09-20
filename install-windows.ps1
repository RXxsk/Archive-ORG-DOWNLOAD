$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==============================================" -ForegroundColor DarkCyan
Write-Host "          2DoArchive - Windows" -ForegroundColor Cyan
Write-Host "             Create By RXx8" -ForegroundColor DarkCyan
Write-Host "==============================================" -ForegroundColor DarkCyan
Write-Host ""

# ============================================================
# CONFIGURACION
# ============================================================

$RepoRaw = "https://raw.githubusercontent.com/RXxsk/Archive-ORG-DOWNLOAD/refs/heads/main"

$Target = Join-Path $HOME "2DoArchive"
$Bin = Join-Path $Target "bin"
$Program = Join-Path $Target "2doarchive.py"
$Command = Join-Path $Bin "archive.cmd"

# ============================================================
# CREAR CARPETAS
# ============================================================

Write-Host "[1/6] Preparando carpetas..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path $Target | Out-Null
New-Item -ItemType Directory -Force -Path $Bin | Out-Null

# ============================================================
# DESCARGAR 2DOARCHIVE.PY DESDE GITHUB
# ============================================================

Write-Host "[2/6] Descargando 2doarchive.py desde GitHub..." -ForegroundColor Yellow

$PythonURL = "$RepoRaw/2doarchive.py?cb=$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"

$TempProgram = Join-Path $Target "2doarchive.py.download"

try {

    Invoke-WebRequest `
        -Uri $PythonURL `
        -OutFile $TempProgram `
        -UseBasicParsing `
        -Headers @{
            "Cache-Control" = "no-cache"
            "Pragma" = "no-cache"
        }

    if (!(Test-Path $TempProgram)) {
        throw "No se pudo descargar 2doarchive.py."
    }

    $Size = (Get-Item $TempProgram).Length

    if ($Size -lt 1000) {
        throw "El archivo descargado parece estar incompleto."
    }

    Move-Item -Force $TempProgram $Program

    Write-Host "[OK] 2doarchive.py actualizado." -ForegroundColor Green
}
catch {

    if (Test-Path $TempProgram) {
        Remove-Item -Force $TempProgram -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "[ERROR] No se pudo descargar 2doarchive.py." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# CREAR COMANDO "archive"
# ============================================================

Write-Host "[3/6] Configurando comando archive..." -ForegroundColor Yellow

$CommandContent = @'
@echo off
setlocal

set "PROGRAM=%USERPROFILE%\2DoArchive\2doarchive.py"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 "%PROGRAM%" %*
    exit /b %errorlevel%
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "%PROGRAM%" %*
    exit /b %errorlevel%
)

echo.
echo [2DoArchive] ERROR: Python 3 no esta instalado.
echo.
echo Instala Python 3 y vuelve a ejecutar "archive".
echo.
pause
exit /b 1
'@

Set-Content `
    -Path $Command `
    -Value $CommandContent `
    -Encoding ASCII

Write-Host "[OK] Comando archive creado." -ForegroundColor Green

# ============================================================
# AGREGAR BIN AL PATH DEL USUARIO
# ============================================================

Write-Host "[4/6] Configurando PATH..." -ForegroundColor Yellow

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ([string]::IsNullOrWhiteSpace($UserPath)) {
    $UserPath = ""
}

$PathEntries = $UserPath -split ";" |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

$AlreadyExists = $false

foreach ($Entry in $PathEntries) {
    if ($Entry.TrimEnd("\") -ieq $Bin.TrimEnd("\")) {
        $AlreadyExists = $true
        break
    }
}

if (!$AlreadyExists) {

    if ($UserPath -and !$UserPath.EndsWith(";")) {
        $UserPath += ";"
    }

    $UserPath += $Bin

    [Environment]::SetEnvironmentVariable(
        "Path",
        $UserPath,
        "User"
    )

    Write-Host "[OK] PATH actualizado." -ForegroundColor Green
}
else {
    Write-Host "[OK] PATH ya estaba configurado." -ForegroundColor Green
}

# Actualizar PATH de esta misma ventana
$env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
            [Environment]::GetEnvironmentVariable("Path", "Machine")

# ============================================================
# CARPETA DE DESCARGAS
# ============================================================

Write-Host "[5/6] Creando carpeta de descargas..." -ForegroundColor Yellow

$DownloadFolder = Join-Path $HOME "Carpeta Descargas Archive-ORG"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $DownloadFolder | Out-Null

Write-Host "[OK] $DownloadFolder" -ForegroundColor Green

# ============================================================
# VERIFICACION
# ============================================================

Write-Host "[6/6] Verificando instalacion..." -ForegroundColor Yellow

$EverythingOK = $true

if (!(Test-Path $Program)) {
    Write-Host "[ERROR] Falta 2doarchive.py" -ForegroundColor Red
    $EverythingOK = $false
}

if (!(Test-Path $Command)) {
    Write-Host "[ERROR] Falta archive.cmd" -ForegroundColor Red
    $EverythingOK = $false
}

if (!(Test-Path $DownloadFolder)) {
    Write-Host "[ERROR] Falta carpeta de descargas" -ForegroundColor Red
    $EverythingOK = $false
}


Write-Host ""

if ($EverythingOK) {

    Write-Host "==============================================" -ForegroundColor Green
    Write-Host "       2DoArchive instalado correctamente" -ForegroundColor Green
    Write-Host "==============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Programa:" -ForegroundColor Cyan
    Write-Host "  $Program"
    Write-Host ""
    Write-Host "Descargas:" -ForegroundColor Cyan
    Write-Host "  $DownloadFolder"
    Write-Host ""
    Write-Host "Comando:" -ForegroundColor Cyan
    Write-Host "  archive"
    Write-Host ""
    Write-Host "IMPORTANTE: cierra esta ventana de PowerShell" -ForegroundColor Yellow
    Write-Host "y abre una nueva para que Windows cargue el PATH."
    Write-Host ""

}
else {

    Write-Host "==============================================" -ForegroundColor Red
    Write-Host "       LA INSTALACION NO SE COMPLETO" -ForegroundColor Red
    Write-Host "==============================================" -ForegroundColor Red
    Write-Host ""

    exit 1
}
