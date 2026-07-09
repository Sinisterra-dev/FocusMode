from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any


def _default_data_dir() -> Path:
    appdata = Path.home()
    if "APPDATA" in os.environ:
        appdata = Path(os.environ["APPDATA"])
    return appdata / "FocusMode"


@dataclass(slots=True)
class FocusSession:
    active: bool = False
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: int = 1800


@dataclass(slots=True)
class FocusConfig:
    blocked_sites: list[str] = field(default_factory=list)
    last_duration_seconds: int = 1800
    strict_mode: bool = False
    session: FocusSession = field(default_factory=FocusSession)


class ConfigManager:
    def __init__(self, config_path: Path | None = None) -> None:
        self.data_dir = _default_data_dir()
        self.config_path = config_path or self.data_dir / "config.json"

    def load(self) -> FocusConfig:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            default_config = FocusConfig()
            self.save(default_config)
            return default_config

        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            default_config = FocusConfig()
            self.save(default_config)
            return default_config

        session_data = raw.get("session", {})
        session = FocusSession(
            active=bool(session_data.get("active", False)),
            start_time=session_data.get("start_time"),
            end_time=session_data.get("end_time"),
            duration_seconds=int(session_data.get("duration_seconds", raw.get("last_duration_seconds", 1800))),
        )

        blocked_sites = [site.strip().lower() for site in raw.get("blocked_sites", []) if str(site).strip()]
        return FocusConfig(
            blocked_sites=blocked_sites,
            last_duration_seconds=int(raw.get("last_duration_seconds", 1800)),
            strict_mode=bool(raw.get("strict_mode", False)),
            session=session,
        )

    def save(self, config: FocusConfig) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = asdict(config)
        self.config_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def parse_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
