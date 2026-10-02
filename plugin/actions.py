"""The catalogue of palette actions.

An action is a list of JSON-serialisable steps run by `executor.execute`:
    ["komorebic", *args]   run komorebic
    ["sleep", seconds]     wait
    ["kill", image]        taskkill /f /im <image>
    ["delete", path]       delete a file
    ["open", path]         open a file in the configured editor
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from plugin import appinfo, komorebi
from plugin.komorebi import Focus, Window
from plugin.settings import Settings

# (komorebic layout, title, description, extra search words)
LAYOUTS = [
    ("bsp", "BSP", "Binary space partitioning, like Hyprland's dwindle", "spiral dwindle"),
    ("columns", "Columns", "All windows side by side", ""),
    ("rows", "Rows", "All windows stacked top to bottom", ""),
    ("vertical-stack", "Vertical stack", "Main window on the left, others stacked on the right", ""),
    ("horizontal-stack", "Horizontal stack", "Main window on top, others below", ""),
    ("ultrawide-vertical-stack", "Ultrawide vertical stack",
     "Main window in the centre column, others on the sides", "three columns center"),
    ("grid", "Grid", "Even grid", ""),
    ("right-main-vertical-stack", "Right main vertical stack", "Main window on the right, others on the left", ""),
    ("scrolling", "Scrolling", "Scrolling columns, like niri or PaperWM", "niri paperwm"),
]


@dataclass
class Action:
    title: str
    subtitle: str
    icon: str
    steps: List[list] = field(default_factory=list)
    keywords: str = ""
    priority: int = 0
    change_query: Optional[str] = None  # when set, selecting rewrites the query instead of running steps

    @property
    def search_text(self) -> str:
        return f"{self.title} {self.keywords}"


@dataclass
class Context:
    settings: Settings
    komorebic: str
    keyword: str
    state: Optional[Dict[str, Any]]
    focus: Optional[Focus]
    config: Dict[str, Any]
    config_file: Path
    whkdrc_file: Path


def kc(*args: Any) -> list:
    """A komorebic step."""
    return ["komorebic", *[str(arg) for arg in args]]


# --------------------------------------------------------------------------
# komorebi lifecycle
# --------------------------------------------------------------------------

def restart_steps(settings: Settings) -> List[list]:
    flags = settings.start_flags
    return [kc("stop", *flags), ["sleep", 1], kc("start", *flags)]


def force_restart_steps(settings: Settings) -> List[list]:
    """Recover a komorebi that no longer answers on its socket."""
    return [
        ["kill", "komorebi.exe"],
        ["kill", "whkd.exe"],
        ["kill", "komorebi-bar.exe"],
        ["sleep", 1],
        kc("restore-windows"),  # reads komorebi.hwnd.json, works while komorebi is down
        ["delete", str(komorebi.socket_path())],
        kc("start", *settings.start_flags),
    ]


def not_responding_action(settings: Settings) -> Action:
    return Action("komorebi is not responding", "Select to force a restart · other actions will have no effect",
                  "restart", force_restart_steps(settings), priority=500)


# --------------------------------------------------------------------------
# Catalogue
# --------------------------------------------------------------------------

def window_actions(ctx: Context) -> List[Action]:
    return [
        Action("Promote to main tile",
               "Swap the focused window with the main tile (the centre column in ultrawide layouts)",
               "layout-ultrawide-vertical-stack", [kc("promote-swap")], "center centre middle main swap", 91),
        Action("Toggle float", "Float and center the focused window · run again to tile it back",
               "float", [kc("toggle-float")], "floating center", 90),
        Action("Toggle monocle", "The focused window fills the workspace · run again to restore",
               "monocle", [kc("toggle-monocle")], "fullscreen full", 89),
        Action("Toggle maximize", "Native Windows maximize, over any bar",
               "maximize", [kc("toggle-maximize")], "max fullscreen", 88),
        Action("Send to workspace…", f"Type a number: {ctx.keyword} send 3",
               "send", keywords="move", priority=87, change_query=f"{ctx.keyword} send "),
        Action("Go to app…", f"Type a name: {ctx.keyword} go spotify",
               "focus", keywords="focus switch", priority=86, change_query=f"{ctx.keyword} go "),
    ]


def workspace_actions(ctx: Context) -> List[Action]:
    focus = ctx.focus
    label = f" · workspace {focus.workspace + 1}" if focus else ""
    actions = []

    for slug, title, description, extra in LAYOUTS:
        steps = [kc("clear-workspace-layout-rules", focus.monitor, focus.workspace)] if focus else []
        steps.append(kc("change-layout", slug))
        actions.append(Action(f"Layout: {title}", description + label, f"layout-{slug}",
                              steps, f"layout {slug.replace('-', ' ')} {extra}", 70))

    if focus:
        layout, rules = komorebi.configured_layout(ctx.config, focus.monitor, focus.workspace)
        steps = [kc("clear-workspace-layout-rules", focus.monitor, focus.workspace)]
        steps += [kc("workspace-layout-rule", focus.monitor, focus.workspace, count, rule)
                  for count, rule in rules.items()]
        steps += [kc("change-layout", layout), kc("retile")]
        actions.append(Action("Layout: from config", f"Restore the layout and layout rules of komorebi.json{label}",
                              "layout-auto", steps, "auto automatic default reset", 71))

        padding, container = komorebi.configured_gaps(ctx.config, focus.monitor, focus.workspace)
        actions.append(Action("Reset gaps", f"Back to komorebi.json values ({padding} / {container} px)",
                              "gap-normal", [kc("focused-workspace-padding", padding),
                                             kc("focused-workspace-container-padding", container)],
                              "gaps padding default normal", 62))

    zen_padding, zen_container = ctx.settings.zen_workspace_padding, ctx.settings.zen_container_padding
    actions += [
        Action("Rename workspace…", f"Type a name: {ctx.keyword} rename Web",
               "rename", keywords="name", priority=65, change_query=f"{ctx.keyword} rename "),
        Action("Zen mode", f"Large gaps to focus ({zen_padding} / {zen_container} px)", "zen",
               [kc("focused-workspace-padding", zen_padding),
                kc("focused-workspace-container-padding", zen_container)],
               "gaps padding focus", 64),
        Action("No gaps", "Windows touching, no wasted space", "gap-none",
               [kc("focused-workspace-padding", 0), kc("focused-workspace-container-padding", 0)],
               "gaps padding zero", 63),
        Action("Toggle tiling", f"Turn tiling on or off{label}", "tiling",
               [kc("toggle-tiling")], "tile", 61),
        Action("Toggle window stacking", "New windows stack instead of splitting the space", "stack",
               [kc("toggle-workspace-window-container-behaviour")], "stack append container", 60),
    ]
    return actions


def komorebi_actions(ctx: Context) -> List[Action]:
    settings = ctx.settings
    return [
        Action("Toggle pause", "Pause or resume all tiling", "pause", [kc("toggle-pause")], "resume", 50),
        Action("Reload configuration", "Re-read komorebi.json (added or changed rules)", "reload",
               [kc("replace-configuration", ctx.config_file)], "config reload", 49),
        Action("Restart komorebi", "Clean stop, then start", "restart", restart_steps(settings),
               "relaunch", 48),
        Action("Force restart komorebi", "When komorebi stops responding: kill, restore hidden windows, start",
               "restart", force_restart_steps(settings), "kill stuck unstuck", 47),
        Action("Open komorebi.json", str(ctx.config_file), "config", [["open", str(ctx.config_file)]],
               "edit config configuration file", 40),
        Action("Open whkdrc", str(ctx.whkdrc_file), "config", [["open", str(ctx.whkdrc_file)]],
               "edit config hotkeys shortcuts keybindings file", 39),
    ]


def catalogue(ctx: Context) -> List[Action]:
    return window_actions(ctx) + workspace_actions(ctx) + komorebi_actions(ctx)


# --------------------------------------------------------------------------
# Actions built from the query
# --------------------------------------------------------------------------

def send_actions(ctx: Context, number: Optional[int]) -> List[Action]:
    count = ctx.focus.workspace_count if ctx.focus else 10
    targets = [number] if number else range(1, count + 1)
    return [Action(f"Send to workspace {n}", "The focused window moves, you stay here", "send",
                   [kc("send-to-workspace", n - 1)], "send", 100)
            for n in targets if 1 <= n <= count]


def rename_action(ctx: Context, name: str) -> Optional[Action]:
    if not ctx.focus:
        return None
    focus = ctx.focus
    return Action(f"Rename workspace {focus.workspace + 1} to “{name}”", "Until komorebi restarts", "rename",
                  [kc("workspace-name", focus.monitor, focus.workspace, name)], priority=200)


def go_actions(windows: List[Window], namer: Optional[Callable[[int, str], str]] = None) -> List[Action]:
    """One "Go to" action per app; `namer` turns (hwnd, exe) into a friendly name."""
    actions, seen = [], set()
    for window in windows:
        if window.exe in seen:
            continue
        seen.add(window.exe)
        name = (namer or appinfo.display_name)(window.hwnd, window.exe)
        actions.append(Action(f"Go to {name}", f"Workspace {window.workspace} · {window.title}", "focus",
                              [kc("eager-focus", window.exe)], f"go focus {window.exe_name} {window.title}", 85))
    return actions
