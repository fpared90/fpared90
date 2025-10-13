@echo off
setlocal EnableExtensions
chcp 65001 >nul

REM Launch minimized without console staying open
pushd "%~dp0..\.." 2>nul
if errorlevel 1 pushd "%~dp0" 2>nul

set "PY_CMD="
py -3 -V >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD (
  python -V >nul 2>nul && set "PY_CMD=python"
)
if not defined PY_CMD (
  exit /b 1
)

start "FileSearcher" /min %PY_CMD% -m file_searcher
exit /b 0
