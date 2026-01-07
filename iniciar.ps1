# Iniciar Sistema de Gestion Comunitaria

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host " SISTEMA DE GESTION COMUNITARIA" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Seleccione que componente desea iniciar:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. API Local (Servidor - DEBE INICIARSE PRIMERO)" -ForegroundColor White
Write-Host "2. Sistema de Censo de Habitantes" -ForegroundColor White
Write-Host "3. Sistema de Control de Pagos" -ForegroundColor White
Write-Host "4. Iniciar TODO (API + Censo + Pagos)" -ForegroundColor White
Write-Host "5. Salir" -ForegroundColor White
Write-Host ""

$opcion = Read-Host "Ingrese su opcion (1-5)"

switch ($opcion) {
    "1" {
        Write-Host "`nIniciando API Local..." -ForegroundColor Green
        python src/api_local.py
    }
    "2" {
        Write-Host "`nIniciando Sistema de Censo..." -ForegroundColor Green
        python src/censo_habitantes.py
    }
    "3" {
        Write-Host "`nIniciando Sistema de Control de Pagos..." -ForegroundColor Green
        python src/control_pagos.py
    }
    "4" {
        Write-Host "`nIniciando todos los componentes..." -ForegroundColor Green
        Write-Host "Nota: Se abriran multiples ventanas" -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; python src/api_local.py"
        Start-Sleep -Seconds 2
        Start-Process powershell -ArgumentList "-Command", "cd '$scriptPath'; python src/censo_habitantes.py"
        Start-Sleep -Seconds 1
        Start-Process powershell -ArgumentList "-Command", "cd '$scriptPath'; python src/control_pagos.py"
    }
    "5" {
        Write-Host "`nSaliendo..." -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "`nOpcion invalida" -ForegroundColor Red
    }
}
