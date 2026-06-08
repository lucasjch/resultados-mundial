@echo off
REM Build script: compila gui.py a .exe con PyInstaller
REM Uso: .\build_exe.bat

chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   Build PRODE Mundial 2026 (GUI .exe)
echo ==========================================

REM 0. Garantizar setuptools (necesario para PyInstaller)
echo [0/4] Verificando setuptools...
python -c "import setuptools" 2>nul
if %errorlevel% neq 0 (
    echo   Instalando setuptools...
    pip install setuptools
) else (
    echo   setuptools OK.
)

REM 1. Verificar PyInstaller
echo [1/4] Verificando PyInstaller...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo   Instalando PyInstaller...
    pip install pyinstaller
) else (
    echo   PyInstaller OK.
)

REM 2. Generar datos si no existen
echo [2/4] Verificando datos de simulacion...
set GROUP_FILE=prode_mundial\output\fase_grupos.json
if not exist "%GROUP_FILE%" (
    echo   Ejecutando simulacion base...
    python prode_mundial\main.py
) else (
    echo   Datos existentes, saltando simulacion.
)

REM 3. Compilar .exe
echo [3/4] Compilando GUI...

python -m PyInstaller --onefile --windowed ^
    --name "ProdeMundial2026" ^
    --distpath dist ^
    --workpath build_tmp ^
    --specpath build_tmp ^
    --add-data "prode_mundial/output;output" ^
    --add-data "prode_mundial/__init__.py;." ^
    --hidden-import json ^
    --hidden-import math ^
    --hidden-import setuptools ^
    prode_mundial/gui.py

if %errorlevel% equ 0 (
    echo [4/4] Limpiando temporales...
    if exist "build_tmp" rmdir /s /q build_tmp
    if exist "ProdeMundial2026.spec" del /q ProdeMundial2026.spec
    echo.
    echo ==========================================
    echo   EXITO: .exe generado en:
    echo   dist\ProdeMundial2026.exe
    echo ==========================================
) else (
    echo.
    echo   ERROR: Fallo la compilacion.
    echo   Revisar output arriba para mas detalles.
)

pause
