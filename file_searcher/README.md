
Here are some ideas to get you started:

- 🔭 I’m currently working on BancoEstado Contacto 24 H.
- 🌱 I’m currently learning Python.
- 👯 I’m looking to collaborate on proyect.
- 🤔 I’m looking for help with Python.
- 💬 Ask me about my favorities.
- 📫 How to reach me: fpared90.
- 😄 Pronouns: He.
- ⚡ Fun fact: I pad for Stardock.


---

File Searcher (Windows) con Qt

- Requisitos: Python 3.9+ y PySide6 (recomendado) o PyQt5.
- Instalación: `pip install PySide6`  (o `pip install PyQt5`).
- Ejecución: `python file_searcher_qt.py`.
- Uso:
  - Ingrese el nombre/patrón a buscar (texto, wildcard como `*.pdf`, o regex).
  - Elija el modo: contains/startswith/endswith/equals.
  - Opciones: distinguir mayúsculas, usar regex o wildcard, incluir carpetas.
  - Seleccione “Todas las unidades” o marque unidades específicas y/o agregue carpetas raíz.
  - Presione Buscar. Puede detener en cualquier momento.
  - Resultados: clic derecho para Abrir, Abrir ubicación o Copiar ruta.

Notas
- La búsqueda se ejecuta en un hilo para mantener la UI fluida.
- Para mejor rendimiento se usa `os.scandir`; permisos denegados se omiten.
- En Windows puede abrir directamente los archivos con `os.startfile`.

Instalador .exe
- Opción A (portable .exe):
  1) Instale PyInstaller: `pip install pyinstaller`
  2) Construya: `scripts\\build_exe.bat`
  3) Ejecute: `dist\\FileSearcher\\FileSearcher.exe`

- Opción B (instalador .exe con Inno Setup):
  1) Construya primero con PyInstaller (pasos de A)
  2) Instale Inno Setup y asegure `iscc` en PATH
  3) Compile el instalador: `scripts\\build_installer_inno.bat`
  4) Obtendrá `installer\\output\\FileSearcher-Setup.exe`

Notas
- El build PyInstaller usa modo `windowed` y `onedir` (inicio más rápido para Qt).
- Si ve problemas con dependencias Qt, pruebe: `py -3 -m PyInstaller --noconfirm --clean --windowed --name FileSearcher --collect-all PySide6 file_searcher_qt.py`
- Para PyQt5, reemplace `--collect-all PySide6` por `--collect-all PyQt5` si fuese necesario.

Estructura del proyecto
- `file_searcher/`
  - `file_searcher_qt.py` (aplicación Qt)
  - `assets/` (iconos, opcional: `icon.ico`)
  - `scripts/` (`build_exe.bat`, `build_installer_inno.bat`)
  - `installer/` (`file_searcher.iss`, `output/`)

Cómo ejecutar desde código
- `python file_searcher\file_searcher_qt.py`

Cómo construir .exe portátil
- `file_searcher\scripts\build_exe.bat`
- Salida: `file_searcher\dist\FileSearcher\FileSearcher.exe`

Cómo construir el instalador
- Primero el .exe (paso anterior)
- `file_searcher\scripts\build_installer_inno.bat`
- Salida: `file_searcher\installer\output\FileSearcher-Setup.exe`

Atajo para ejecutar
- Doble clic en: `file_searcher\scripts\run_app.bat`
  - Lanza `python -m file_searcher`

Atajos adicionales
- Minimizado (cmd minimizado): `file_searcher\scripts\run_app_min.bat`
- Oculto (sin consola): `file_searcher\scripts\run_app_hidden.vbs`
