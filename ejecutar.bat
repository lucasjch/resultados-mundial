@echo off
title Prode Mundial 2026
chcp 65001 >nul
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
set PYTHONIOENCODING=utf-8

:menu
cls
echo ====================================
echo       PRODE MUNDIAL 2026
echo ====================================
echo.
echo  1. Simulacion completa (seed 256)
echo  2. Simulacion con seed personalizada
echo  3. Tabla de goleadores
echo  4. Salir
echo.
echo ====================================
set /p op="Seleccione opcion [1-4]: "

if "%op%"=="1" goto full
if "%op%"=="2" goto custom
if "%op%"=="3" goto top
if "%op%"=="4" goto salir
goto menu

:full
cls
echo ====================================
echo  Simulacion completa - Seed 256
echo ====================================
echo.
python prode_mundial/main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: La simulacion fallo!
)
echo.
pause
goto menu

:custom
cls
echo ====================================
echo  Seed personalizada
echo ====================================
echo.
set /p seed="Ingrese seed (Enter = 42): "
if "%seed%"=="" set seed=42
echo.
echo  Ejecutando simulacion con seed !seed!...
echo.
python prode_mundial/main.py !seed!
echo.
pause
goto menu

:top
cls
echo ====================================
echo  Tabla de Goleadores
echo ====================================
echo.
python prode_mundial/main.py --goleadores
echo.
pause
goto menu

:salir
echo.
echo  Hasta luego!
echo.
timeout /t 2 >nul
endlocal
