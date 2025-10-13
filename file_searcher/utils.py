import os
import re
import ctypes
from ctypes import wintypes


def list_windows_drives() -> list[str]:
    drives: list[str] = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        root = f"{letter}:\\"
        if os.path.exists(root):
            drives.append(root)
    return drives


def human_size(num: int | float | str) -> str:
    try:
        num = int(num)
    except Exception:
        return ""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


_SIZE_UNITS = {"b": 1, "kb": 1024, "mb": 1024 ** 2, "gb": 1024 ** 3, "tb": 1024 ** 4}


def parse_size(text: str) -> int | None:
    if not text:
        return None
    s = text.strip().replace(',', '.').replace(' ', '')
    m = re.match(r'^(\d+(?:\.\d+)?)([a-zA-Z]{0,2})$', s)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2).lower()
    if unit == '':
        return int(val)
    mult = _SIZE_UNITS.get(unit)
    if mult is None:
        return None
    return int(val * mult)


FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_OFFLINE = 0x1000
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x40000

GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
GetFileAttributesW.restype = wintypes.DWORD


def get_file_attributes(path: str) -> int:
    try:
        st = os.stat(path, follow_symlinks=False)
        attrs = getattr(st, 'st_file_attributes', 0)
        if attrs:
            return int(attrs)
    except Exception:
        pass
    try:
        return int(GetFileAttributesW(path))
    except Exception:
        return 0


def is_system_path(path: str) -> bool:
    p = os.path.normcase(os.path.abspath(path))
    drive, _ = os.path.splitdrive(p)
    base = drive or 'C:'
    system_dirs = [
        os.path.join(base, '\\Windows'),
        os.path.join(base, '\\Windows.old'),
        os.path.join(base, '\\Program Files'),
        os.path.join(base, '\\Program Files (x86)'),
        os.path.join(base, '\\ProgramData'),
        os.path.join(base, '\\$Recycle.Bin'),
        os.path.join(base, '\\System Volume Information'),
    ]
    for s in system_dirs:
        if p.startswith(os.path.normcase(s)):
            return True
    return False
