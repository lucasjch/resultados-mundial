@echo off
REM Build script: compila gui.py a .exe con PyInstaller
REM Uso: .\build_exe.bat

chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   Build PRODE Mundial 2026 (GUI .exe)
echo ==========================================

REM 1. Verificar PyInstaller
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/3] Instalando PyInstaller...
    pip install pyinstaller
) else (
    echo [1/3] PyInstaller encontrado.
)

REM 2. Generar datos si no existen
set GROUP_FILE=prode_mundial\output\fase_grupos.json
if not exist "%GROUP_FILE%" (
    echo [2/3] Ejecutando simulacion base...
    python prode_mundial\main.py
) else (
    echo [2/3] Datos existentes, saltando simulacion.
)

REM 3. Compilar .exe
echo [3/3] Compilando GUI...

pyinstaller --onefile --windowed ^
    --name "ProdeMundial2026" ^
    --distpath dist ^
    --workpath build_tmp ^
    --specpath build_tmp ^
    --add-data "prode_mundial\output;output" ^
    --add-data "prode_mundial\__init__.py;." ^
    --hidden-import json ^
    --hidden-import math ^
    --icon "prode_mundial\output\wc26_icon.ico" ^
    prode_mundial\gui.py

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo   EXITO: .exe generado en:
    echo   dist\ProdeMundial2026.exe
    echo ==========================================
) else (
    echo.
    echo   ERROR: Fallo la compilacion.
    echo   Revisar dependencias e intentar de nuevo.
)

pause
