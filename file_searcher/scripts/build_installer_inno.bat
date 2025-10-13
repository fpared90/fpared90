@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

REM Ensure we run from package root (file_searcher)
pushd "%~dp0.." 2>nul
if errorlevel 1 pushd "%~dp0" 2>nul

echo =============================================================
echo [FileSearcher] Construyendo instalador con Inno Setup
echo Carpeta: %CD%
echo (Ejecutar app en dev: python -m file_searcher)
echo =============================================================

REM Check that PyInstaller output exists
if not exist "dist\FileSearcher\FileSearcher.exe" (
  echo [Error] No existe dist\FileSearcher\FileSearcher.exe. Primero ejecute scripts\build_exe.bat
  goto :end_fail
)

REM Locate ISCC (Inno Setup compiler)
set "ISCC_CMD=iscc"
where iscc >nul 2>nul || (
  set "ISCC_CMD=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if not exist "%ISCC_CMD%" (
  echo [Error] No se encontr? iscc. Instale Inno Setup y agregue iscc al PATH.
  goto :end_fail
)

echo [Build] Compilando installer\file_searcher.iss ...
"%ISCC_CMD%" installer\file_searcher.iss
if errorlevel 1 (
  echo [Error] Fall? la compilaci?n del instalador.
  goto :end_fail
)

echo [OK] Instalador generado en installer\output\FileSearcher-Setup.exe

:end_ok
popd >nul 2>&1
if not defined CI pause
exit /b 0

:end_fail
popd >nul 2>&1
if not defined CI pause
exit /b 1
