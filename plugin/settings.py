"""User settings, as defined in SettingsTemplate.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _as_str(value: Any) -> str:
    return str(value).strip().strip('"') if value is not None else ""


@dataclass(frozen=True)
class Settings:
    komorebic_path: str = ""
    komorebi_config_path: str = ""
    whkdrc_path: str = ""
    editor_path: str = ""
    start_whkd: bool = True
    start_bar: bool = False
    zen_workspace_padding: int = 80
    zen_container_padding: int = 15
    action_delay_ms: int = 600
    show_apps_in_search: bool = True

    @classmethod
    def from_dict(cls, raw: Optional[Mapping[str, Any]]) -> Settings:
        raw = raw or {}
        defaults = cls()
        return cls(
            komorebic_path=_as_str(raw.get("komorebic_path")),
            komorebi_config_path=_as_str(raw.get("komorebi_config_path")),
            whkdrc_path=_as_str(raw.get("whkdrc_path")),
            editor_path=_as_str(raw.get("editor_path")),
            start_whkd=_as_bool(raw.get("start_whkd"), defaults.start_whkd),
            start_bar=_as_bool(raw.get("start_bar"), defaults.start_bar),
            zen_workspace_padding=_as_int(raw.get("zen_workspace_padding"), defaults.zen_workspace_padding),
            zen_container_padding=_as_int(raw.get("zen_container_padding"), defaults.zen_container_padding),
            action_delay_ms=_as_int(raw.get("action_delay_ms"), defaults.action_delay_ms),
            show_apps_in_search=_as_bool(raw.get("show_apps_in_search"), defaults.show_apps_in_search),
        )

    @property
    def start_flags(self) -> list:
        """Flags for `komorebic start` / `komorebic stop`."""
        flags = []
        if self.start_whkd:
            flags.append("--whkd")
        if self.start_bar:
            flags.append("--bar")
        return flags
