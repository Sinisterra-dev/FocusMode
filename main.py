from __future__ import annotations

from pathlib import Path
import tkinter.messagebox as messagebox

from config import ConfigManager
from hosts_manager import HostsManager
from ui import build_app
from utils import SingleInstanceLock, relaunch_as_admin


def main() -> None:
    relaunch_as_admin()

    config_manager = ConfigManager()
    lock = SingleInstanceLock(config_manager.data_dir / "focusmode.lock")

    if not lock.acquire():
        messagebox.showwarning(
            "Focus Mode",
            "Ya existe una instancia en ejecución.\nSi hay una sesión activa, se mantiene en la instancia actual.",
        )
        return

    try:
        hosts_manager = HostsManager()
        run_app = build_app(config_manager=config_manager, hosts_manager=hosts_manager)
        run_app()
    finally:
        lock.release()


if __name__ == "__main__":
    main()
