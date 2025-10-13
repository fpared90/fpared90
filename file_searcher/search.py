import os
import re
import fnmatch

# Try PySide6 first, fallback to PyQt5
try:
    from PySide6 import QtCore
    Signal = QtCore.Signal
    Slot = QtCore.Slot
except ImportError:  # pragma: no cover
    from PyQt5 import QtCore  # type: ignore
    Signal = QtCore.pyqtSignal  # type: ignore
    Slot = QtCore.pyqtSlot  # type: ignore

# Imports that work both as package and as script
try:
    from .utils import (
        list_windows_drives,
        human_size,
        parse_size,
        get_file_attributes,
        is_system_path,
        FILE_ATTRIBUTE_HIDDEN,
        FILE_ATTRIBUTE_OFFLINE,
        FILE_ATTRIBUTE_RECALL_ON_OPEN,
    )
except Exception:
    from utils import (  # type: ignore
        list_windows_drives,
        human_size,
        parse_size,
        get_file_attributes,
        is_system_path,
        FILE_ATTRIBUTE_HIDDEN,
        FILE_ATTRIBUTE_OFFLINE,
        FILE_ATTRIBUTE_RECALL_ON_OPEN,
    )


class SearchParams(QtCore.QObject):
    def __init__(self, pattern: str, mode: str, match_case: bool, use_regex: bool, use_wildcard: bool,
                 include_dirs: bool, roots,
                 extensions=None, min_size=None, max_size=None,
                 date_from=None, date_to=None,
                 exclude_system=False, exclude_hidden=False, exclude_offline=False, excluded_paths=None):
        super().__init__()
        self.pattern = pattern
        self.mode = mode
        self.match_case = match_case
        self.use_regex = use_regex
        self.use_wildcard = use_wildcard
        self.include_dirs = include_dirs
        self.roots = roots
        self.extensions = [e.lower() for e in (extensions or []) if e]
        self.min_size = min_size
        self.max_size = max_size
        self.date_from = date_from
        self.date_to = date_to
        self.exclude_system = exclude_system
        self.exclude_hidden = exclude_hidden
        self.exclude_offline = exclude_offline
        self.excluded_paths = [os.path.normcase(os.path.abspath(p)) for p in (excluded_paths or [])]


class SearchThread(QtCore.QThread):
    found = Signal(dict)
    status = Signal(str)
    started_search = Signal()
    finished_search = Signal()

    def __init__(self, params: SearchParams, parent=None):
        super().__init__(parent)
        self.params = params
        self._cancel = False

        self._compiled_regex = None
        if self.params.use_regex and self.params.pattern:
            flags = 0 if self.params.match_case else re.IGNORECASE
            try:
                self._compiled_regex = re.compile(self.params.pattern, flags)
            except re.error:
                self._compiled_regex = None

    def cancel(self):
        self._cancel = True

    def _name_matches(self, name: str) -> bool:
        p = self.params
        if not p.pattern:
            return True
        candidate = name if p.match_case else name.lower()
        pattern = p.pattern if p.match_case else p.pattern.lower()
        if p.use_regex and self._compiled_regex is not None:
            return self._compiled_regex.search(name) is not None
        if p.use_regex and self._compiled_regex is None:
            return False
        if p.use_wildcard:
            return fnmatch.fnmatch(candidate, pattern)
        if p.mode == 'contains':
            return pattern in candidate
        if p.mode == 'startswith':
            return candidate.startswith(pattern)
        if p.mode == 'endswith':
            return candidate.endswith(pattern)
        if p.mode == 'equals':
            return candidate == pattern
        return False

    def run(self):
        self.started_search.emit()
        try:
            for root in self.params.roots:
                if self._cancel:
                    break
                self._scan_root(root)
        finally:
            self.finished_search.emit()

    def _scan_root(self, root: str):
        stack = [root]
        while stack and not self._cancel:
            current = stack.pop()
            self.status.emit(current)
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        if self._cancel:
                            return
                        try:
                            is_dir = entry.is_dir(follow_symlinks=False)
                        except PermissionError:
                            continue
                        name = entry.name
                        if is_dir:
                            stack.append(entry.path)
                            if self._passes_filters(entry.path, True, name):
                                self._emit_result(entry, is_dir=True)
                        else:
                            if self._passes_filters(entry.path, False, name):
                                self._emit_result(entry, is_dir=False)
            except (PermissionError, FileNotFoundError, OSError):
                pass

    def _passes_filters(self, path: str, is_dir: bool, name: str) -> bool:
        p = self.params
        if is_dir and not p.include_dirs:
            return False
        if not self._name_matches(name):
            return False
        npath = os.path.normcase(os.path.abspath(path))
        for ex in p.excluded_paths:
            if npath.startswith(ex):
                return False
        if p.exclude_system and is_system_path(path):
            return False
        attrs = get_file_attributes(path)
        if p.exclude_hidden and (attrs & FILE_ATTRIBUTE_HIDDEN):
            return False
        if p.exclude_offline and (attrs & (FILE_ATTRIBUTE_OFFLINE | FILE_ATTRIBUTE_RECALL_ON_OPEN)):
            return False
        try:
            st = os.stat(path, follow_symlinks=False)
        except Exception:
            return False
        if not is_dir:
            if p.extensions:
                ext = os.path.splitext(name)[1].lower()
                if ext not in p.extensions:
                    return False
            if p.min_size is not None and st.st_size < p.min_size:
                return False
            if p.max_size is not None and st.st_size > p.max_size:
                return False
        if p.date_from is not None and st.st_mtime < p.date_from:
            return False
        if p.date_to is not None and st.st_mtime > p.date_to:
            return False
        return True

    def _emit_result(self, entry: os.DirEntry, is_dir: bool):
        try:
            stat = entry.stat(follow_symlinks=False)
            size = stat.st_size if not is_dir else 0
            mtime = stat.st_mtime
        except (PermissionError, FileNotFoundError, OSError):
            size = 0
            mtime = 0
        item = {
            'name': entry.name,
            'path': entry.path,
            'is_dir': is_dir,
            'size': size,
            'mtime': mtime,
        }
        self.found.emit(item)
