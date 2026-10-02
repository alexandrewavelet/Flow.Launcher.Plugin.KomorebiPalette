"""The Flow Launcher plugin class."""

from __future__ import annotations

import json
import os
import webbrowser
from pathlib import Path
from typing import Any, Dict, List

from flowlauncher import FlowLauncher

from plugin import actions, clipboard, executor, komorebi
from plugin.actions import Action, Context
from plugin.matching import match_score, tokenize
from plugin.settings import Settings

PLUGIN_DIR = Path(__file__).parent.parent
DEFAULT_KEYWORD = "k"
DOCS_URL = "https://lgug2z.github.io/komorebi/cli/{}.html"
REPO_URL = "https://github.com/alexandrewavelet/Flow.Launcher.Plugin.KomorebiPalette"


def _plugin_id() -> str:
    try:
        return json.loads((PLUGIN_DIR / "plugin.json").read_text(encoding="utf-8"))["ID"]
    except (OSError, ValueError, KeyError):
        return ""


def _action_keyword() -> str:
    """The keyword the user set for this plugin in Flow (used in query hints)."""
    candidates = [Path(os.environ.get("APPDATA", "")) / "FlowLauncher", PLUGIN_DIR.parent.parent]
    for root in candidates:
        try:
            flow_settings = json.loads((root / "Settings" / "Settings.json").read_text(encoding="utf-8"))
            keywords = flow_settings["PluginSettings"]["Plugins"][_plugin_id()]["ActionKeywords"]
            if keywords and keywords[0] != "*":
                return keywords[0]
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return DEFAULT_KEYWORD


class KomorebiPalette(FlowLauncher):

    # ------------------------------------------------------------------
    # Flow entry points
    # ------------------------------------------------------------------

    def query(self, query: str) -> List[Dict[str, Any]]:
        settings = Settings.from_dict(self.rpc_request.get("settings") or self.rpc_request.get("Settings"))
        ctx = self._context(settings)
        raw = query.strip()
        tokens = tokenize(raw)
        head = tokens[0] if tokens else ""

        # Always shown, whatever the query
        alerts = [actions.not_responding_action(settings)] if ctx.state is None else []

        if head == "rename" and len(raw.split(None, 1)) > 1:
            rename = actions.rename_action(ctx, raw.split(None, 1)[1])
            items, tokens = [rename] if rename else [], []
        elif head == "send":
            number = next((int(t) for t in tokens[1:] if t.isdigit()), None)
            items, tokens = actions.send_actions(ctx, number), []
        elif head == "go":
            items, tokens = actions.go_actions(komorebi.get_windows(ctx.state)), tokens[1:]
        else:
            items = actions.catalogue(ctx)
            if tokens and settings.show_apps_in_search:
                items += actions.go_actions(komorebi.get_windows(ctx.state))

        return self._results(alerts, [], ctx) + self._results(items, tokens, ctx)

    def context_menu(self, data: List[str]) -> List[Dict[str, Any]]:
        command, subcommand = (data + ["", ""])[:2]
        menu = []
        if command:
            menu.append(self._menu_item("Copy command", command, "config", "copy_to_clipboard", [command]))
        if subcommand:
            menu.append(self._menu_item("Open komorebic documentation", f"komorebic {subcommand}", "icon",
                                        "open_url", [DOCS_URL.format(subcommand)]))
        menu.append(self._menu_item("Report an issue or suggest a feature", REPO_URL, "icon",
                                    "open_url", [REPO_URL + "/issues"]))
        return menu

    # ------------------------------------------------------------------
    # JsonRPCAction methods
    # ------------------------------------------------------------------

    def run(self, payload: Dict[str, Any]) -> None:
        executor.spawn(payload)

    def copy_to_clipboard(self, text: str) -> None:
        clipboard.copy(text)

    def open_url(self, url: str) -> None:
        webbrowser.open(url)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _context(self, settings: Settings) -> Context:
        komorebic = komorebi.find_komorebic(settings.komorebic_path)
        state = komorebi.get_state(komorebic)
        config_file = komorebi.config_path(settings.komorebi_config_path)
        return Context(
            settings=settings,
            komorebic=komorebic,
            keyword=_action_keyword(),
            state=state,
            focus=komorebi.get_focus(state),
            config=komorebi.load_config(config_file),
            config_file=config_file,
            whkdrc_file=komorebi.whkdrc_path(settings.whkdrc_path),
        )

    def _results(self, items: List[Action], tokens: List[str], ctx: Context) -> List[Dict[str, Any]]:
        results = []
        for item in items:
            score = match_score(tokens, item.search_text)
            if score:
                results.append(self._to_result(item, score * 10 + item.priority, ctx))
        return results

    @staticmethod
    def _to_result(item: Action, score: int, ctx: Context) -> Dict[str, Any]:
        if item.change_query is not None:
            rpc = {"method": "Flow.Launcher.ChangeQuery", "parameters": [item.change_query, True],
                   "dontHideAfterAction": True}
            context: List[str] = []
        else:
            payload = {"komorebic": ctx.komorebic, "editor": ctx.settings.editor_path,
                       "delay": ctx.settings.action_delay_ms / 1000, "steps": item.steps}
            rpc = {"method": "run", "parameters": [payload]}
            context = _context_data(item)
        return {
            "Title": item.title,
            "SubTitle": item.subtitle,
            "IcoPath": f"Images\\{item.icon}.png",
            "JsonRPCAction": rpc,
            "ContextData": context,
            "Score": score,
        }

    @staticmethod
    def _menu_item(title: str, subtitle: str, icon: str, method: str, parameters: list) -> Dict[str, Any]:
        return {"Title": title, "SubTitle": subtitle, "IcoPath": f"Images\\{icon}.png",
                "JsonRPCAction": {"method": method, "parameters": parameters}}


def _context_data(item: Action) -> List[str]:
    """[shell command, first komorebic subcommand] for the context menu."""
    commands = [step for step in item.steps if step and step[0] == "komorebic"]
    if not commands:
        return []
    text = " ; ".join(" ".join(_quote(part) for part in step) for step in commands)
    return [text, commands[0][1]]


def _quote(part: str) -> str:
    return f'"{part}"' if " " in part else part
