"""Friendly application names ("Sublime Text" rather than "sublime_text.exe").

The name comes from the version resource (FileDescription, ProductName) of the
executable that owns the window, read with the Win32 API (no dependencies).
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from functools import lru_cache
from typing import Dict, Optional

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# Hosts whose description says nothing about the app they display
GENERIC_HOSTS = {"applicationframehost.exe"}

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_version = ctypes.WinDLL("version", use_last_error=True)

_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                 ctypes.POINTER(wintypes.DWORD)]
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_version.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
_version.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
_version.VerQueryValueW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p),
                                    ctypes.POINTER(wintypes.UINT)]


def process_path(hwnd: int) -> Optional[str]:
    """Full path of the executable that owns a window."""
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return None
    process = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not process:
        return None
    try:
        size = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not _kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
            return None
        return buffer.value
    finally:
        _kernel32.CloseHandle(process)


@lru_cache(maxsize=None)
def version_strings(path: str) -> Dict[str, str]:
    """FileDescription and ProductName from an executable's version resource."""
    size = _version.GetFileVersionInfoSizeW(path, None)
    if not size:
        return {}
    data = ctypes.create_string_buffer(size)
    if not _version.GetFileVersionInfoW(path, 0, size, data):
        return {}

    pointer, length = ctypes.c_void_p(), wintypes.UINT()
    translations = []
    if _version.VerQueryValueW(data, "\\VarFileInfo\\Translation", ctypes.byref(pointer), ctypes.byref(length)):
        words = ctypes.cast(pointer, ctypes.POINTER(wintypes.WORD))
        translations = [(words[i], words[i + 1]) for i in range(0, length.value // 2, 2)]
    translations += [(0x0409, 0x04B0), (0x0409, 0x04E4)]  # common fallbacks

    strings = {}
    for field in ("FileDescription", "ProductName"):
        for language, codepage in translations:
            key = f"\\StringFileInfo\\{language:04x}{codepage:04x}\\{field}"
            if _version.VerQueryValueW(data, key, ctypes.byref(pointer), ctypes.byref(length)) and length.value:
                value = ctypes.wstring_at(pointer).strip()  # NUL-terminated
                if value:
                    strings[field] = value
                    break
    return strings


def file_description(path: str) -> Optional[str]:
    return version_strings(path).get("FileDescription")


def _is_meaningful(name: Optional[str]) -> bool:
    """Rejects names such as "Notepad.exe" or "Microsoft® Windows® Operating System"."""
    if not name:
        return False
    lowered = name.lower()
    return not (lowered.endswith(".exe") or "operating system" in lowered or "exploitation" in lowered)


def friendly_name(strings: Dict[str, str]) -> Optional[str]:
    description, product = strings.get("FileDescription"), strings.get("ProductName")
    description = description if _is_meaningful(description) else None
    product = product if _is_meaningful(product) else None
    # "Windows Terminal Host" describes the process, "Windows Terminal" the app
    if description and product and description != product and description.startswith(product):
        return product
    return description or product


def display_name(hwnd: int, exe: str) -> str:
    """The app name to show for a window, falling back to the exe name."""
    fallback = exe[:-4] if exe.lower().endswith(".exe") else exe
    if exe.lower() in GENERIC_HOSTS or not hwnd:
        return fallback
    path = process_path(hwnd)
    return (friendly_name(version_strings(path)) if path else None) or fallback
