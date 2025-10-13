import os
import sys
import csv
import subprocess
from datetime import datetime

# Try PySide6 first, fallback to PyQt5
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    USING_PYSIDE = True
except ImportError:  # pragma: no cover
    from PyQt5 import QtCore, QtGui, QtWidgets  # type: ignore
    USING_PYSIDE = False

# Imports that work both as package and as script
try:
    from .utils import list_windows_drives, human_size, parse_size
    from .search import SearchParams, SearchThread
except Exception:
    from utils import list_windows_drives, human_size, parse_size  # type: ignore
    from search import SearchParams, SearchThread  # type: ignore


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Buscador Rápido de Archivos (Windows)")
        self.resize(1100, 700)
        self._thread = None
        self._build_ui()
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

    def _build_ui(self):
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Search controls
        row1 = QtWidgets.QHBoxLayout()
        self.input_pattern = QtWidgets.QLineEdit()
        self.input_pattern.setPlaceholderText("Nombre a buscar (ej. *.pdf o reporte)")
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["contains", "startswith", "endswith", "equals"])
        self.chk_case = QtWidgets.QCheckBox("Distinguir mayúsculas/minúsculas")
        self.chk_regex = QtWidgets.QCheckBox("Regex")
        self.chk_wildcard = QtWidgets.QCheckBox("Wildcard (*, ?)")
        self.chk_dirs = QtWidgets.QCheckBox("Incluir carpetas")
        self.chk_dirs.setChecked(False)
        row1.addWidget(QtWidgets.QLabel("Patrón:"))
        row1.addWidget(self.input_pattern, 1)
        row1.addWidget(QtWidgets.QLabel("Modo:"))
        row1.addWidget(self.mode_combo)
        row1.addWidget(self.chk_case)
        row1.addWidget(self.chk_regex)
        row1.addWidget(self.chk_wildcard)
        row1.addWidget(self.chk_dirs)
        layout.addLayout(row1)

        # Drives and roots selection
        roots_box = QtWidgets.QGroupBox("Unidades / Carpetas raíz para buscar")
        roots_layout = QtWidgets.QVBoxLayout(roots_box)
        drives_row = QtWidgets.QHBoxLayout()
        self.btn_refresh_drives = QtWidgets.QPushButton("Actualizar unidades")
        self.btn_add_folder = QtWidgets.QPushButton("Agregar carpeta…")
        self.chk_all_drives = QtWidgets.QCheckBox("Todas las unidades")
        self.chk_all_drives.setChecked(True)
        drives_row.addWidget(self.btn_refresh_drives)
        drives_row.addWidget(self.btn_add_folder)
        drives_row.addStretch(1)
        drives_row.addWidget(self.chk_all_drives)
        roots_layout.addLayout(drives_row)
        self.drives_container = QtWidgets.QWidget()
        self.drives_layout = QtWidgets.QHBoxLayout(self.drives_container)
        self.drives_layout.setContentsMargins(0, 0, 0, 0)
        roots_layout.addWidget(self.drives_container)
        self.custom_roots_list = QtWidgets.QListWidget()
        self.custom_roots_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.custom_roots_list.setFixedHeight(70)
        roots_layout.addWidget(QtWidgets.QLabel("Carpetas personalizadas:"))
        roots_layout.addWidget(self.custom_roots_list)
        layout.addWidget(roots_box)

        # Advanced filters
        filters_box = QtWidgets.QGroupBox("Filtros")
        f_layout = QtWidgets.QGridLayout(filters_box)
        self.input_ext = QtWidgets.QLineEdit()
        self.input_ext.setPlaceholderText("Extensiones (ej: .pdf;.csv)")
        self.input_min = QtWidgets.QLineEdit()
        self.input_min.setPlaceholderText("Tamaño mínimo (ej: 10MB)")
        self.input_max = QtWidgets.QLineEdit()
        self.input_max.setPlaceholderText("Tamaño máximo (ej: 1GB)")
        self.chk_date_from = QtWidgets.QCheckBox("Desde")
        self.date_from = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.chk_date_to = QtWidgets.QCheckBox("Hasta")
        self.date_to = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        f_layout.addWidget(QtWidgets.QLabel("Extensiones:"), 0, 0)
        f_layout.addWidget(self.input_ext, 0, 1)
        f_layout.addWidget(QtWidgets.QLabel("Tamaño:"), 1, 0)
        f_layout.addWidget(self.input_min, 1, 1)
        f_layout.addWidget(self.input_max, 1, 2)
        f_layout.addWidget(self.chk_date_from, 2, 0)
        f_layout.addWidget(self.date_from, 2, 1)
        f_layout.addWidget(self.chk_date_to, 2, 2)
        f_layout.addWidget(self.date_to, 2, 3)
        layout.addWidget(filters_box)

        # Exclusions
        ex_box = QtWidgets.QGroupBox("Exclusiones")
        ex_layout = QtWidgets.QGridLayout(ex_box)
        self.chk_ex_system = QtWidgets.QCheckBox("Excluir carpetas del sistema")
        self.chk_ex_hidden = QtWidgets.QCheckBox("Excluir ocultos")
        self.chk_ex_offline = QtWidgets.QCheckBox("Excluir OneDrive sin conexión")
        self.ex_list = QtWidgets.QListWidget()
        self.ex_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.btn_ex_add = QtWidgets.QPushButton("Agregar exclusión…")
        self.btn_ex_del = QtWidgets.QPushButton("Quitar")
        ex_layout.addWidget(self.chk_ex_system, 0, 0)
        ex_layout.addWidget(self.chk_ex_hidden, 0, 1)
        ex_layout.addWidget(self.chk_ex_offline, 0, 2)
        ex_layout.addWidget(QtWidgets.QLabel("Rutas a excluir:"), 1, 0)
        ex_layout.addWidget(self.ex_list, 2, 0, 1, 3)
        ex_layout.addWidget(self.btn_ex_add, 3, 1)
        ex_layout.addWidget(self.btn_ex_del, 3, 2)
        layout.addWidget(ex_box)

        # Actions
        actions = QtWidgets.QHBoxLayout()
        self.btn_search = QtWidgets.QPushButton("Buscar")
        self.btn_stop = QtWidgets.QPushButton("Detener")
        self.btn_clear = QtWidgets.QPushButton("Limpiar")
        self.btn_export = QtWidgets.QPushButton("Exportar CSV")
        self.btn_stop.setEnabled(False)
        actions.addWidget(self.btn_search)
        actions.addWidget(self.btn_stop)
        actions.addWidget(self.btn_clear)
        actions.addWidget(self.btn_export)
        actions.addStretch(1)
        layout.addLayout(actions)

        # Status/progress
        status_row = QtWidgets.QHBoxLayout()
        self.lbl_status = QtWidgets.QLabel("Listo")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        status_row.addWidget(self.lbl_status, 1)
        status_row.addWidget(self.progress)
        layout.addLayout(status_row)

        # Results table
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nombre", "Ruta", "Tamaño", "Modificado", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        # Context menu
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemDoubleClicked.connect(lambda _: self._open_current())

        # Wire up
        self.btn_refresh_drives.clicked.connect(self._populate_drives)
        self.btn_add_folder.clicked.connect(self._add_custom_folder)
        self.btn_search.clicked.connect(self._start_search)
        self.btn_stop.clicked.connect(self._stop_search)
        self.btn_clear.clicked.connect(self._clear_results)
        self.btn_export.clicked.connect(self._export_csv)
        self.btn_ex_add.clicked.connect(self._add_exclusion)
        self.btn_ex_del.clicked.connect(self._remove_exclusion)

        self._populate_drives()
        self._load_settings()

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_open = menu.addAction("Abrir")
        act_open_folder = menu.addAction("Abrir ubicación")
        act_copy_path = menu.addAction("Copiar ruta")
        action = menu.exec(self.table.viewport().mapToGlobal(pos)) if USING_PYSIDE else menu.exec_(self.table.viewport().mapToGlobal(pos))
        if not action:
            return
        row = self.table.currentRow()
        if row < 0:
            return
        path = self.table.item(row, 1).text()
        if action == act_open:
            self._open_current()
        elif action == act_open_folder:
            self._open_in_explorer(path)
        elif action == act_copy_path:
            cb = QtWidgets.QApplication.clipboard()
            cb.setText(path)

    def _open_path(self, path: str):
        try:
            os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Abrir", "No se pudo abrir el elemento.")

    def _open_in_explorer(self, path: str):
        try:
            if os.path.isdir(path):
                subprocess.Popen(["explorer", path])
            else:
                subprocess.Popen(["explorer", "/select,", path])
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Explorador", "No se pudo abrir el explorador.")

    def _open_current(self):
        row = self.table.currentRow()
        if row < 0:
            return
        path = self.table.item(row, 1).text()
        self._open_path(path)

    def _populate_drives(self):
        while self.drives_layout.count():
            item = self.drives_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for drv in list_windows_drives():
            chk = QtWidgets.QCheckBox(drv)
            chk.setChecked(True)
            self.drives_layout.addWidget(chk)
        self.drives_layout.addStretch(1)

    def _add_custom_folder(self):
        dlg = QtWidgets.QFileDialog(self, "Seleccionar carpeta")
        dlg.setFileMode(QtWidgets.QFileDialog.Directory)
        dlg.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        if dlg.exec():
            folders = dlg.selectedFiles()
            for f in folders:
                items = self.custom_roots_list.findItems(f, QtCore.Qt.MatchExactly)
                if not items:
                    self.custom_roots_list.addItem(f)

    def _add_exclusion(self):
        dlg = QtWidgets.QFileDialog(self, "Seleccionar carpeta a excluir")
        dlg.setFileMode(QtWidgets.QFileDialog.Directory)
        dlg.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        if dlg.exec():
            for f in dlg.selectedFiles():
                if not self.ex_list.findItems(f, QtCore.Qt.MatchExactly):
                    self.ex_list.addItem(f)

    def _remove_exclusion(self):
        for it in self.ex_list.selectedItems():
            row = self.ex_list.row(it)
            self.ex_list.takeItem(row)

    def _gather_roots(self) -> list[str]:
        roots: list[str] = []
        if self.chk_all_drives.isChecked():
            roots.extend(list_windows_drives())
        else:
            for i in range(self.drives_layout.count()):
                item = self.drives_layout.itemAt(i)
                w = item.widget()
                if isinstance(w, QtWidgets.QCheckBox) and w.isChecked():
                    roots.append(w.text())
        for i in range(self.custom_roots_list.count()):
            roots.append(self.custom_roots_list.item(i).text())
        norm: list[str] = []
        for r in roots:
            try:
                if os.path.exists(r):
                    norm.append(os.path.normpath(r))
            except Exception:
                pass
        seen = set()
        unique: list[str] = []
        for r in norm:
            if r not in seen:
                seen.add(r)
                unique.append(r)
        return unique

    def _qdate_to_epoch(self, qdate: 'QtCore.QDate', end=False) -> int:
        dt = QtCore.QDateTime(qdate)
        if end:
            dt = dt.addSecs(23 * 3600 + 59 * 60 + 59)
        return int(dt.toSecsSinceEpoch()) if hasattr(dt, 'toSecsSinceEpoch') else int(dt.toMSecsSinceEpoch() / 1000)

    def _start_search(self):
        if self._thread and self._thread.isRunning():
            return
        pattern = self.input_pattern.text().strip()
        mode = self.mode_combo.currentText()
        match_case = self.chk_case.isChecked()
        use_regex = self.chk_regex.isChecked()
        use_wildcard = self.chk_wildcard.isChecked()
        include_dirs = self.chk_dirs.isChecked()
        roots = self._gather_roots()
        if not roots:
            QtWidgets.QMessageBox.information(self, "Raíces", "No hay unidades o carpetas seleccionadas.")
            return
        exts = [e.strip().lower() if e.strip().startswith('.') else ('.' + e.strip().lower()) for e in self.input_ext.text().split(';') if e.strip()]
        min_b = parse_size(self.input_min.text().strip())
        max_b = parse_size(self.input_max.text().strip())
        dfrom = self._qdate_to_epoch(self.date_from.date(), end=False) if self.chk_date_from.isChecked() else None
        dto = self._qdate_to_epoch(self.date_to.date(), end=True) if self.chk_date_to.isChecked() else None
        ex_paths = [self.ex_list.item(i).text() for i in range(self.ex_list.count())]
        params = SearchParams(pattern, mode, match_case, use_regex, use_wildcard, include_dirs, roots,
                              extensions=exts, min_size=min_b, max_size=max_b, date_from=dfrom, date_to=dto,
                              exclude_system=self.chk_ex_system.isChecked(), exclude_hidden=self.chk_ex_hidden.isChecked(),
                              exclude_offline=self.chk_ex_offline.isChecked(), excluded_paths=ex_paths)
        self._thread = SearchThread(params)
        self._thread.found.connect(self._on_found)
        self._thread.status.connect(self._on_status)
        self._thread.started_search.connect(self._on_search_started)
        self._thread.finished_search.connect(self._on_search_finished)
        self._thread.start()

    def _stop_search(self):
        if self._thread and self._thread.isRunning():
            self._thread.cancel()

    def _clear_results(self):
        self.table.setRowCount(0)
        self.lbl_status.setText("Listo")

    def _settings(self) -> QtCore.QSettings:
        return QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, 'fp', 'FileSearcherQt')

    def _load_settings(self):
        s = self._settings()
        self.input_pattern.setText(s.value('pattern', '', str))
        self.mode_combo.setCurrentText(s.value('mode', 'contains', str))
        self.chk_case.setChecked(s.value('case', False, bool))
        self.chk_regex.setChecked(s.value('regex', False, bool))
        self.chk_wildcard.setChecked(s.value('wildcard', False, bool))
        self.chk_dirs.setChecked(s.value('include_dirs', False, bool))
        self.chk_all_drives.setChecked(s.value('all_drives', True, bool))
        self.custom_roots_list.clear()
        for p in s.value('custom_roots', [], list):
            self.custom_roots_list.addItem(p)
        self.input_ext.setText(s.value('ext', '', str))
        self.input_min.setText(s.value('min', '', str))
        self.input_max.setText(s.value('max', '', str))
        if s.value('date_from_en', False, bool):
            self.chk_date_from.setChecked(True)
            df = s.value('date_from', '', str)
            if df:
                self.date_from.setDate(QtCore.QDate.fromString(df, 'yyyy-MM-dd'))
        if s.value('date_to_en', False, bool):
            self.chk_date_to.setChecked(True)
            dt = s.value('date_to', '', str)
            if dt:
                self.date_to.setDate(QtCore.QDate.fromString(dt, 'yyyy-MM-dd'))
        self.chk_ex_system.setChecked(s.value('ex_system', True, bool))
        self.chk_ex_hidden.setChecked(s.value('ex_hidden', False, bool))
        self.chk_ex_offline.setChecked(s.value('ex_offline', True, bool))
        self.ex_list.clear()
        for p in s.value('ex_paths', [], list):
            self.ex_list.addItem(p)
        widths = s.value('col_widths', [], list)
        if widths:
            for i, w in enumerate(widths):
                try:
                    self.table.setColumnWidth(i, int(w))
                except Exception:
                    pass

    def _save_settings(self):
        s = self._settings()
        s.setValue('pattern', self.input_pattern.text())
        s.setValue('mode', self.mode_combo.currentText())
        s.setValue('case', self.chk_case.isChecked())
        s.setValue('regex', self.chk_regex.isChecked())
        s.setValue('wildcard', self.chk_wildcard.isChecked())
        s.setValue('include_dirs', self.chk_dirs.isChecked())
        s.setValue('all_drives', self.chk_all_drives.isChecked())
        s.setValue('custom_roots', [self.custom_roots_list.item(i).text() for i in range(self.custom_roots_list.count())])
        s.setValue('ext', self.input_ext.text())
        s.setValue('min', self.input_min.text())
        s.setValue('max', self.input_max.text())
        s.setValue('date_from_en', self.chk_date_from.isChecked())
        s.setValue('date_to_en', self.chk_date_to.isChecked())
        s.setValue('date_from', self.date_from.date().toString('yyyy-MM-dd'))
        s.setValue('date_to', self.date_to.date().toString('yyyy-MM-dd'))
        s.setValue('ex_system', self.chk_ex_system.isChecked())
        s.setValue('ex_hidden', self.chk_ex_hidden.isChecked())
        s.setValue('ex_offline', self.chk_ex_offline.isChecked())
        s.setValue('ex_paths', [self.ex_list.item(i).text() for i in range(self.ex_list.count())])
        widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
        s.setValue('col_widths', widths)

    def _export_csv(self):
        if self.table.rowCount() == 0:
            QtWidgets.QMessageBox.information(self, "Exportar", "No hay resultados.")
            return
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar CSV", "resultados.csv", "CSV (*.csv)")
        if not fname:
            return
        try:
            with open(fname, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                w.writerow(headers)
                for r in range(self.table.rowCount()):
                    row = [self.table.item(r, c).text() if self.table.item(r, c) else '' for c in range(self.table.columnCount())]
                    w.writerow(row)
            QtWidgets.QMessageBox.information(self, "Exportar", "CSV guardado.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Exportar", f"Error: {e}")

    def _on_search_started(self):
        self.btn_search.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setVisible(True)
        # Disable sorting during streaming inserts
        self._prev_sorting = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self._clear_results()
        self._found_count = 0

    def _on_found(self, item: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name_item = QtWidgets.QTableWidgetItem(item['name'])
        path_item = QtWidgets.QTableWidgetItem(item['path'])
        size_item = QtWidgets.QTableWidgetItem(human_size(item['size']))
        dt = datetime.fromtimestamp(item['mtime']) if item['mtime'] else None
        mtime_text = dt.strftime('%Y-%m-%d %H:%M') if dt else ''
        mtime_item = QtWidgets.QTableWidgetItem(mtime_text)
        type_text = 'Carpeta' if item['is_dir'] else 'Archivo'
        type_item = QtWidgets.QTableWidgetItem(type_text)
        if item['is_dir']:
            name_item.setForeground(QtGui.QBrush(QtGui.QColor('#555')))
            path_item.setForeground(QtGui.QBrush(QtGui.QColor('#555')))
        self.table.setItem(row, 0, name_item)
        self.table.setItem(row, 1, path_item)
        self.table.setItem(row, 2, size_item)
        self.table.setItem(row, 3, mtime_item)
        self.table.setItem(row, 4, type_item)
        self._found_count = getattr(self, '_found_count', 0) + 1
        self.lbl_status.setText(f"Resultados: {self._found_count}")

    def _on_status(self, path: str):
        self.lbl_status.setText(f"Escaneando: {path}")

    def _on_search_finished(self):
        self.btn_search.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setVisible(False)
        # Re-enable sorting after finish
        if getattr(self, '_prev_sorting', True):
            self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"Listo. Resultados: {getattr(self, '_found_count', 0)}")
        self._save_settings()

    def closeEvent(self, e):
        self._save_settings()
        super().closeEvent(e)


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec()) if USING_PYSIDE else sys.exit(app.exec_())

