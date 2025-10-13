@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

REM Ensure we run from package root (file_searcher)
pushd "%~dp0.." 2>nul
if errorlevel 1 pushd "%~dp0" 2>nul

echo =============================================================
echo [FileSearcher] Construyendo ejecutable con PyInstaller
echo Carpeta: %CD%
echo Ejecutar app (dev): python -m file_searcher
echo =============================================================

REM Detect Python launcher or python
set "PY_CMD="
py -3 -V >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD (
  python -V >nul 2>nul && set "PY_CMD=python"
)
if not defined PY_CMD (
  echo [Error] No se encontro Python en PATH. Instale Python 3.9+.
  goto :end_fail
)

REM Verify PyInstaller availability (via module)
%PY_CMD% -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
  echo [Info] Instalando PyInstaller localmente...
  %PY_CMD% -m pip install --user pyinstaller || (
    echo [Error] PyInstaller no esta instalado. Intente: pip install pyinstaller
    goto :end_fail
  )
)

REM Clean previous builds (optional)
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist FileSearcher.spec del /q FileSearcher.spec

REM Determine Qt binding to collect resources
set "QT_COLLECT="
%PY_CMD% -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('PySide6') else 1)" >nul 2>nul
if %ERRORLEVEL%==0 set "QT_COLLECT=--collect-all PySide6"
if not defined QT_COLLECT (
  %PY_CMD% -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('PyQt5') else 1)" >nul 2>nul
  if %ERRORLEVEL%==0 set "QT_COLLECT=--collect-all PyQt5"
)

REM Optional icon
set "ICON_FLAG="
if exist assets\icon.ico set "ICON_FLAG=--icon assets\icon.ico"

set "NAME=FileSearcher"
echo [Build] Ejecutando PyInstaller con entrada __main__.py ...
%PY_CMD% -m PyInstaller __main__.py ^
  --name %NAME% ^
  --noconfirm ^
  --clean ^
  --windowed ^
  %QT_COLLECT% ^
  %ICON_FLAG%

if errorlevel 1 (
  echo [Error] Fallo PyInstaller.
  goto :end_fail
)

if not exist "dist\%NAME%\%NAME%.exe" (
  echo [Error] No se encontro dist\%NAME%\%NAME%.exe. Revise la salida anterior.
  goto :end_fail
)

echo [OK] Ejecutable generado: dist\%NAME%\%NAME%.exe

echo.
echo Para ejecutar en desarrollo: python -m file_searcher

:end_ok
popd >nul 2>&1
if not defined CI pause
exit /b 0

:end_fail
popd >nul 2>&1
if not defined CI pause
exit /b 1
