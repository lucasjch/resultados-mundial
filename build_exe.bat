@echo off
REM Build script: compila gui.py a .exe con PyInstaller
REM Uso: .\build_exe.bat

chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   Build PRODE Mundial 2026 (GUI .exe)
echo ==========================================

REM 0. Garantizar pkg_resources (necesario para altgraph/PyInstaller)
echo [0/4] Verificando pkg_resources...
python -c "import pkg_resources" 2>nul
if %errorlevel% neq 0 (
    echo   Instalando setuptools compatible...
    pip install setuptools==69.5.1
) else (
    echo   pkg_resources OK.
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
echo [2/5] Verificando datos de simulacion...
set GROUP_FILE=prode_mundial\output\fase_grupos.json
if not exist "%GROUP_FILE%" (
    echo   Ejecutando simulacion base...
    python prode_mundial\main.py
) else (
    echo   Datos existentes, saltando simulacion.
)

REM 2.5. Descargar banderas si faltan
echo [3/5] Verificando banderas...
set FLAG_DIR=prode_mundial\output\flags
if not exist "%FLAG_DIR%" mkdir "%FLAG_DIR%"
set FLAG_COUNT=0
for /f %%i in ('dir /b "%FLAG_DIR%\*.png" 2^>nul ^| find /c /v ""') do set FLAG_COUNT=%%i
if %FLAG_COUNT% lss 48 (
    echo   Descargando %FLAG_COUNT% de 48 banderas...
    python -c "import os,requests; codes=['mx','kr','za','cz','ca','ch','qa','ba','br','ma','gb-sct','ht','us','py','au','tr','de','ec','ci','cw','nl','jp','se','tn','be','eg','ir','nz','es','uy','sa','cv','fr','no','sn','iq','ar','dz','at','jo','pt','co','uz','cd','gb-eng','hr','gh','pa']; out=os.path.join('prode_mundial','output','flags'); os.makedirs(out,exist_ok=True); ok=0; [exec('') for _ in [None]] or None; [requests.get(f'https://flagcdn.com/24x18/{c}.png',timeout=10).content for c in codes if not os.path.exists(os.path.join(out,f'{c}.png')) and (open(os.path.join(out,f'{c}.png'),'wb').write(requests.get(f'https://flagcdn.com/24x18/{c}.png',timeout=10).content) or ok:=ok+1)]; print(f'  Descargadas {ok} banderas faltantes')"
) else (
    echo   %FLAG_COUNT% banderas presentes.
)

REM 3. Compilar .exe
echo [4/5] Compilando GUI...

python -m PyInstaller --onefile --windowed ^
    --name "ProdeMundial2026" ^
    --distpath dist ^
    --workpath build_tmp ^
    --specpath build_tmp ^
    --add-data "%CD%\prode_mundial\output;prode_mundial\output" ^
    --add-data "%CD%\prode_mundial\output\flags;prode_mundial\output\flags" ^
    --hidden-import json ^
    --hidden-import math ^
    --hidden-import setuptools ^
    --hidden-import sv_ttk ^
    --hidden-import prode_mundial.predictor ^
    --hidden-import prode_mundial.optimizer ^
    --hidden-import prode_mundial.data ^
    --hidden-import prode_mundial.bracket ^
    --hidden-import prode_mundial.top_scorer ^
    --hidden-import prode_mundial.output ^
    --hidden-import prode_mundial.analysis ^
    --hidden-import prode_mundial.friendlies_data ^
    "%CD%\prode_mundial\gui.py"

if %errorlevel% equ 0 (
    echo [5/5] Limpiando temporales...
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
