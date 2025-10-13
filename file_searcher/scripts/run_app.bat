@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo --- FileSearcher launcher ---
echo Script: %~f0

REM Move to repo root (parent of package) so -m file_searcher resolves
pushd "%~dp0..\.." 2>nul
if errorlevel 1 pushd "%~dp0" 2>nul

echo CWD: %CD%

REM Basic verifier: ensure the package folder exists here
if not exist "file_searcher" (
  echo [Error] No se encontro la carpeta "file_searcher" en: %CD%
  echo Ubicacion del script: %~dp0
  echo Asegure que este script este en file_searcher\scripts\
  goto :end
)
if not exist "file_searcher\__main__.py" (
  if not exist "file_searcher\app.py" (
    echo [Error] La carpeta "file_searcher" no parece un paquete valido (falta __main__.py o app.py)
    goto :end
  )
)

set "PY_CMD="
py -3 -V >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD (
  python -V >nul 2>nul && set "PY_CMD=python"
)
if not defined PY_CMD (
  echo [Error] Python no encontrado en PATH. Instale Python 3.9+.
  goto :end
)

echo Verificando import de modulo...
%PY_CMD% -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('file_searcher') else 1)"
if errorlevel 1 (
  echo [Error] Python no puede importar el modulo "file_searcher" desde: %CD%
  echo Tip: abra una consola aqui y ejecute: python -m file_searcher
  goto :end
)

echo Ejecutando: %PY_CMD% -m file_searcher
%PY_CMD% -m file_searcher
if errorlevel 1 (
  echo [Error] La aplicacion termino con error (%errorlevel%). Revise mensajes arriba.
) else (
  echo [OK] Aplicacion finalizada.
)

:end
popd >nul 2>&1
if not defined CI pause
