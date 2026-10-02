"""Access to komorebi: komorebic CLI, window manager state and static configuration."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_KOMOREBIC = r"C:\Program Files\komorebi\bin\komorebic.exe"
CREATE_NO_WINDOW = 0x08000000

# komorebi's own defaults when komorebi.json sets no padding
DEFAULT_PADDING = 10


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

def find_komorebic(configured: str = "") -> str:
    """Configured path, then PATH, then the default installer location."""
    if configured and Path(configured).is_file():
        return configured
    return shutil.which("komorebic") or DEFAULT_KOMOREBIC


def config_path(configured: str = "") -> Path:
    if configured:
        return Path(os.path.expandvars(configured))
    home = os.environ.get("KOMOREBI_CONFIG_HOME") or str(Path.home())
    return Path(home) / "komorebi.json"


def whkdrc_path(configured: str = "") -> Path:
    if configured:
        return Path(os.path.expandvars(configured))
    home = os.environ.get("WHKD_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(home) / "whkdrc"


def socket_path() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", "")) / "komorebi" / "komorebi.sock"


# --------------------------------------------------------------------------
# komorebic
# --------------------------------------------------------------------------

def komorebic_output(komorebic: str, *args: str, timeout: float = 3) -> Optional[str]:
    """Run komorebic and return its stdout, or None on failure."""
    try:
        completed = subprocess.run(
            [komorebic, *args], capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, creationflags=CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout if completed.returncode == 0 else None


def get_state(komorebic: str) -> Optional[Dict[str, Any]]:
    """The window manager state, or None when komorebi does not respond."""
    output = komorebic_output(komorebic, "state")
    if not output:
        return None
    try:
        return json.loads(output)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# State helpers
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Focus:
    monitor: int
    workspace: int
    workspace_count: int


@dataclass(frozen=True)
class Window:
    exe: str
    title: str
    workspace: int  # 1-based, as shown to the user
    hwnd: int = 0

    @property
    def exe_name(self) -> str:
        return self.exe[:-4] if self.exe.lower().endswith(".exe") else self.exe


def _workspaces(state: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    monitors = state["monitors"]
    index = monitors["focused"]
    return index, monitors["elements"][index]["workspaces"]


def get_focus(state: Optional[Dict[str, Any]]) -> Optional[Focus]:
    try:
        monitor, workspaces = _workspaces(state)
        return Focus(monitor, workspaces["focused"], len(workspaces["elements"]))
    except (KeyError, IndexError, TypeError):
        return None


def get_windows(state: Optional[Dict[str, Any]]) -> List[Window]:
    """Managed windows on the focused monitor, one entry per window."""
    try:
        _, workspaces = _workspaces(state)
    except (KeyError, IndexError, TypeError):
        return []

    windows = []
    for index, workspace in enumerate(workspaces["elements"]):
        raw = []
        for container in (workspace.get("containers") or {}).get("elements", []):
            raw += (container.get("windows") or {}).get("elements", [])
        monocle = workspace.get("monocle_container")
        if monocle:
            raw += (monocle.get("windows") or {}).get("elements", [])
        raw += workspace.get("floating_windows") or []
        if workspace.get("maximized_window"):
            raw.append(workspace["maximized_window"])
        windows += [Window(w["exe"], w.get("title") or "", index + 1, w.get("hwnd") or 0)
                    for w in raw if isinstance(w, dict) and w.get("exe")]
    return windows


# --------------------------------------------------------------------------
# Static configuration (komorebi.json)
# --------------------------------------------------------------------------

def load_config(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _workspace_config(config: Dict[str, Any], monitor: int, workspace: int) -> Tuple[Dict, Dict]:
    try:
        monitor_config = config["monitors"][monitor]
        return monitor_config, monitor_config["workspaces"][workspace]
    except (KeyError, IndexError, TypeError):
        return {}, {}


def configured_gaps(config: Dict[str, Any], monitor: int, workspace: int) -> Tuple[int, int]:
    """(workspace padding, container padding) as komorebi.json defines them."""
    monitor_config, workspace_config = _workspace_config(config, monitor, workspace)

    def pick(key: str, default_key: str) -> int:
        for source, name in ((workspace_config, key), (monitor_config, key), (config, default_key)):
            if isinstance(source.get(name), int):
                return source[name]
        return DEFAULT_PADDING

    return (pick("workspace_padding", "default_workspace_padding"),
            pick("container_padding", "default_container_padding"))


def to_cli_layout(name: str) -> str:
    """'UltrawideVerticalStack' -> 'ultrawide-vertical-stack', 'BSP' -> 'bsp'."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", "-", name).lower()


def configured_layout(config: Dict[str, Any], monitor: int, workspace: int) -> Tuple[str, Dict[int, str]]:
    """(base layout, {container count: layout}) for a workspace, in komorebic syntax."""
    _, workspace_config = _workspace_config(config, monitor, workspace)
    layout = to_cli_layout(workspace_config.get("layout") or "BSP")
    rules = {}
    for threshold, rule_layout in (workspace_config.get("layout_rules") or {}).items():
        if str(threshold).isdigit() and isinstance(rule_layout, str):
            rules[int(threshold)] = to_cli_layout(rule_layout)
    return layout, dict(sorted(rules.items()))
