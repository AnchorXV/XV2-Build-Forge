@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Nuitka Optimized Build for DBXV2 Build Forge
echo ========================================

REM Activate virtual environment
call .venv\Scripts\activate.bat

set APP_NAME=DBXV2 Build Forge
set MAIN_FILE=main.py

set CPU_CORES=%NUMBER_OF_PROCESSORS%
if not defined CPU_CORES set CPU_CORES=4
set /a BUILD_JOBS=%CPU_CORES%

set EXCLUDE_MODULES=unittest,test,pytest,_pytest,doctest,pdb,pdbpp
set EXCLUDE_MODULES=%EXCLUDE_MODULES%,setuptools,pip,distutils,pkg_resources
set EXCLUDE_MODULES=%EXCLUDE_MODULES%,email.mime,http.server,xmlrpc,pydoc
REM PySide6 exclusions for GUI app
set EXCLUDE_MODULES=%EXCLUDE_MODULES%,PySide6.QtWebEngine,PySide6.QtWebEngineWidgets,PySide6.Qt3D,PySide6.QtCharts,PySide6.QtNetwork,PySide6.QtSql,PySide6.QtMultimedia,PySide6.QtMultimediaWidgets,PySide6.QtQuick,PySide6.QtQml

echo.
echo [1/4] Cleaning old builds...
if exist main.dist rd /s /q main.dist
if exist main.build rd /s /q main.build
if not exist build\installer mkdir build\installer

echo.
echo [2/4] Compiling with Nuitka (this may take a few minutes)...
python -m nuitka --onefile ^
    --windows-console-mode=disable ^
    --lto=yes ^
    --jobs=%BUILD_JOBS% ^
    --enable-plugin=anti-bloat ^
    --enable-plugin=pyside6 ^
    --noinclude-pytest-mode=nofollow ^
    --noinclude-setuptools-mode=nofollow ^
    --nofollow-import-to=%EXCLUDE_MODULES% ^
    --python-flag=no_docstrings ^
    --output-dir=. ^
    -o "DBXV2_Build_Forge.exe" ^
    %MAIN_FILE%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Compilation failed!
    exit /b 1
)

echo.
echo ========================================
echo Build complete! The executable is DBXV2_Build_Forge.exe
echo ========================================
