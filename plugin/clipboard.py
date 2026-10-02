"""Copy text to the Windows clipboard with the Win32 API (no dependencies)."""

from __future__ import annotations

import ctypes
from ctypes import wintypes

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_user32.OpenClipboard.argtypes = [wintypes.HWND]
_user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
_user32.SetClipboardData.restype = wintypes.HANDLE
_kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
_kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
_kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalLock.restype = wintypes.LPVOID
_kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]


def copy(text: str) -> bool:
    data = ctypes.create_unicode_buffer(text)
    size = ctypes.sizeof(data)
    if not _user32.OpenClipboard(None):
        return False
    try:
        _user32.EmptyClipboard()
        handle = _kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
        if not handle:
            return False
        pointer = _kernel32.GlobalLock(handle)
        ctypes.memmove(pointer, data, size)
        _kernel32.GlobalUnlock(handle)
        return bool(_user32.SetClipboardData(CF_UNICODETEXT, handle))
    finally:
        _user32.CloseClipboard()
