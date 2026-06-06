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
echo  1. Simulacion completa (1500 sims por partido)
echo  2. Tabla de goleadores
echo  3. Ver predicciones
echo  4. Optimizador (X2 + Campeon + SF + Goleador)
echo  5. Salir
echo.
echo ====================================
set /p op="Seleccione opcion [1-5]: "

if "%op%"=="1" goto simular
if "%op%"=="2" goto top
if "%op%"=="3" goto ver_predicciones
if "%op%"=="4" goto optimizer
if "%op%"=="5" goto salir
goto menu

:simular
cls
echo ====================================
echo  Simulacion completa (1500 sims por partido)
echo ====================================
echo.
echo  Promediando 1500 simulaciones Poisson por partido...
echo  Tiempo estimado: ~10 segundos
echo.
python prode_mundial/main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: La simulacion fallo!
)
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
