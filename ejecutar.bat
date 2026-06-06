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
echo  1. Ensemble 100 semillas (default)
echo  2. Simulacion con seed personalizada
echo  3. Ver predicciones
echo  4. Tabla de goleadores
echo  5. Optimizador (X2 + Campeon + SF + Goleador)
echo  6. Salir
echo.
echo ====================================
set /p op="Seleccione opcion [1-6]: "

if "%op%"=="1" goto ensemble
if "%op%"=="2" goto custom
if "%op%"=="3" goto ver_predicciones
if "%op%"=="4" goto top
if "%op%"=="5" goto optimizer
if "%op%"=="6" goto salir
goto menu

:ensemble
cls
echo ====================================
echo  Ensemble 100 semillas + Fase KO determinista
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
set /p seed="Ingrese seed (Enter = 256): "
if "%seed%"=="" set seed=256
echo.
echo  Ejecutando simulacion con seed !seed!...
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

:optimizer
cls
echo ====================================
echo  OPTIMIZADOR PRODE 2026
echo ====================================
echo  Analiza X2, campeon, semifinalistas
echo  y goleador. Recomienda los mejores
echo  picks para maximizar puntos.
echo.
echo  NOTA: Tarda ~75s (Monte Carlo 1000 sims)
echo.
pause
cls
echo ====================================
echo  Ejecutando optimizador...
echo ====================================
echo.
python prode_mundial/optimizer.py
echo.
pause
goto menu

:ver_predicciones
cls
echo ====================================
echo       VER PREDICCIONES
echo ====================================
echo.
echo  1. Fase de Grupos (todos los grupos)
echo  2. Grupo especifico (A-L)
echo  3. Tabla de posiciones
echo  4. Playoffs (R32 a Final)
echo  5. Volver al menu principal
echo.
echo ====================================
set /p op="Seleccione opcion [1-5]: "

if "%op%"=="1" goto ver_grupos
if "%op%"=="2" goto ver_grupo_esp
if "%op%"=="3" goto ver_tabla
if "%op%"=="4" goto ver_playoffs
if "%op%"=="5" goto menu
goto ver_predicciones

:ver_grupos
cls
echo ====================================
echo  FASE DE GRUPOS
echo ====================================
python prode_mundial/display.py --grupos
echo.
pause
goto ver_predicciones

:ver_grupo_esp
cls
echo ====================================
echo  GRUPO ESPECIFICO
echo ====================================
echo.
set /p g="Ingrese letra del grupo (A-L): "
echo.
python prode_mundial/display.py --grupo %g%
echo.
pause
goto ver_predicciones

:ver_tabla
cls
echo ====================================
echo  TABLA DE POSICIONES
echo ====================================
python prode_mundial/display.py --tabla
echo.
pause
goto ver_predicciones

:ver_playoffs
cls
echo ====================================
echo  PLAYOFFS
echo ====================================
python prode_mundial/display.py --playoffs
echo.
pause
goto ver_predicciones

:salir
echo.
echo  Hasta luego!
echo.
timeout /t 2 >nul
endlocal
