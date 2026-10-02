"""Running actions.

While the plugin handles the call, Flow's own window is still the foreground
window, so a komorebic command run right away would target Flow instead of the
user's window. Actions are handed to a detached process that waits a moment
(the `action_delay_ms` setting) for Flow to hide and give the focus back.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

from plugin.komorebi import CREATE_NO_WINDOW

DETACHED_PROCESS = 0x00000008
RUN_FLAG = "--run-steps"

PLUGIN_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = PLUGIN_DIR / "komorebi-palette.log"
LOG_MAX_BYTES = 256 * 1024


def log(message: str) -> None:
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > LOG_MAX_BYTES:
            LOG_FILE.unlink()
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n")
    except OSError:
        pass


def spawn(payload: Dict[str, Any]) -> None:
    """Run `payload` in a detached process (see `execute`)."""
    subprocess.Popen(
        [sys.executable, str(PLUGIN_DIR / "main.py"), RUN_FLAG, json.dumps(payload)],
        creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW, close_fds=True,
    )


def _open_file(path: str, editor: str) -> None:
    if editor:
        subprocess.Popen([editor, path])
        return
    try:
        os.startfile(path, "edit")  # default editor for the file type
    except OSError:
        subprocess.Popen(["notepad.exe", path])  # e.g. whkdrc has no extension


def _run(command: list) -> None:
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=30, creationflags=CREATE_NO_WINDOW)
    if completed.returncode != 0:
        log(f"{command} -> {completed.returncode}: {(completed.stderr or completed.stdout).strip()[:500]}")


def execute(payload: Dict[str, Any]) -> None:
    """Payload: {"komorebic": path, "editor": path, "delay": seconds, "steps": [...]}."""
    time.sleep(float(payload.get("delay", 0.6)))
    for step in payload.get("steps", []):
        kind, args = step[0], step[1:]
        try:
            if kind == "komorebic":
                _run([payload["komorebic"], *args])
            elif kind == "sleep":
                time.sleep(float(args[0]))
            elif kind == "kill":
                subprocess.run(["taskkill", "/f", "/im", args[0]], capture_output=True,
                               creationflags=CREATE_NO_WINDOW)
            elif kind == "delete":
                Path(args[0]).unlink(missing_ok=True)
            elif kind == "open":
                _open_file(args[0], payload.get("editor", ""))
            else:
                log(f"unknown step {step}")
        except (OSError, subprocess.SubprocessError) as error:
            log(f"{step} -> {error}")
