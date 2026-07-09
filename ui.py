from __future__ import annotations

from datetime import datetime, timedelta
import tkinter.messagebox as messagebox
from typing import Callable

import customtkinter as ctk

from config import ConfigManager, FocusConfig, FocusSession
from hosts_manager import HostsManager
from timer import FocusTimer, format_seconds
from utils import append_strict_log


class FocusModeApp(ctk.CTk):
    PRESET_OPTIONS = {
        "15 minutos": 15 * 60,
        "30 minutos": 30 * 60,
        "45 minutos": 45 * 60,
        "1 hora": 60 * 60,
        "2 horas": 2 * 60 * 60,
        "3 horas": 3 * 60 * 60,
        "Personalizado": None,
    }

    def __init__(self, config_manager: ConfigManager, hosts_manager: HostsManager) -> None:
        super().__init__()
        self.title("Focus Mode")
        self.geometry("1024x700")
        self.minsize(900, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.config_manager = config_manager
        self.hosts_manager = hosts_manager
        self.config_data: FocusConfig = self.config_manager.load()
        self.timer = FocusTimer()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._site_rows: list[ctk.CTkLabel] = []
        self._build_ui()
        self._refresh_sites_ui()
        self._resume_active_session_if_needed()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, corner_radius=12)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        left = ctk.CTkFrame(container, corner_radius=10)
        right = ctk.CTkFrame(container, corner_radius=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        title = ctk.CTkLabel(left, text="🧠 Focus Mode", font=ctk.CTkFont(size=30, weight="bold"))
        title.pack(anchor="w", padx=20, pady=(20, 12))

        self.countdown_var = ctk.StringVar(value="00:00:00")
        self.countdown_label = ctk.CTkLabel(
            left,
            textvariable=self.countdown_var,
            font=ctk.CTkFont(size=72, weight="bold"),
            text_color="#f8fafc",
        )
        self.countdown_label.pack(anchor="center", pady=30)

        options_frame = ctk.CTkFrame(left)
        options_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.duration_var = ctk.StringVar(value=self._option_for_seconds(self.config_data.last_duration_seconds))
        self.duration_menu = ctk.CTkOptionMenu(options_frame, values=list(self.PRESET_OPTIONS.keys()), variable=self.duration_var)
        self.duration_menu.pack(side="left", padx=10, pady=10)

        self.custom_minutes = ctk.StringVar(value="90")
        self.custom_entry = ctk.CTkEntry(options_frame, textvariable=self.custom_minutes, width=120, placeholder_text="Minutos")
        self.custom_entry.pack(side="left", padx=10, pady=10)

        self.strict_mode_var = ctk.BooleanVar(value=self.config_data.strict_mode)
        strict_switch = ctk.CTkSwitch(options_frame, text="Modo Estricto", variable=self.strict_mode_var)
        strict_switch.pack(side="left", padx=10, pady=10)

        self.start_button = ctk.CTkButton(
            left,
            text="▶ Iniciar Focus",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=56,
            command=self._start_focus,
        )
        self.start_button.pack(fill="x", padx=20, pady=(0, 20))

        right_title = ctk.CTkLabel(right, text="Sitios bloqueados", font=ctk.CTkFont(size=24, weight="bold"))
        right_title.pack(anchor="w", padx=20, pady=(20, 12))

        self.domain_var = ctk.StringVar()
        domain_input = ctk.CTkEntry(right, textvariable=self.domain_var, placeholder_text="ej. facebook.com")
        domain_input.pack(fill="x", padx=20, pady=(0, 10))

        actions = ctk.CTkFrame(right)
        actions.pack(fill="x", padx=20, pady=(0, 10))

        add_button = ctk.CTkButton(actions, text="➕ Agregar sitio", height=42, command=self._add_site)
        add_button.pack(side="left", padx=(8, 8), pady=8, fill="x", expand=True)

        delete_button = ctk.CTkButton(actions, text="🗑 Eliminar sitio", height=42, fg_color="#7f1d1d", hover_color="#991b1b", command=self._remove_selected_site)
        delete_button.pack(side="left", padx=(8, 8), pady=8, fill="x", expand=True)

        self.site_list = ctk.CTkScrollableFrame(right)
        self.site_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.selected_site_var = ctk.StringVar(value="")

    def _refresh_sites_ui(self) -> None:
        for row in self._site_rows:
            row.destroy()
        self._site_rows.clear()

        for site in self.config_data.blocked_sites:
            row = ctk.CTkRadioButton(self.site_list, text=site, value=site, variable=self.selected_site_var)
            row.pack(anchor="w", padx=8, pady=6)
            self._site_rows.append(row)

    def _add_site(self) -> None:
        value = self.domain_var.get().strip().lower()
        clean = value.replace("https://", "").replace("http://", "").split("/")[0].removeprefix("www.")
        if not clean:
            return
        if clean not in self.config_data.blocked_sites:
            self.config_data.blocked_sites.append(clean)
            self.config_data.blocked_sites.sort()
            self.config_manager.save(self.config_data)
            self._refresh_sites_ui()
        self.domain_var.set("")

    def _remove_selected_site(self) -> None:
        selected = self.selected_site_var.get()
        if not selected:
            return
        self.config_data.blocked_sites = [site for site in self.config_data.blocked_sites if site != selected]
        self.selected_site_var.set("")
        self.config_manager.save(self.config_data)
        self._refresh_sites_ui()

    def _duration_in_seconds(self) -> int:
        selected = self.duration_var.get()
        preset = self.PRESET_OPTIONS.get(selected)
        if preset is not None:
            return preset
        try:
            minutes = int(self.custom_minutes.get())
        except ValueError:
            minutes = 90
        return max(1, minutes) * 60

    def _option_for_seconds(self, seconds: int) -> str:
        for key, value in self.PRESET_OPTIONS.items():
            if value == seconds:
                return key
        return "Personalizado"

    def _set_focus_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.start_button.configure(state=state)
        self.duration_menu.configure(state=state)
        self.custom_entry.configure(state=state)

    def _start_focus(self) -> None:
        if not self.config_data.blocked_sites:
            messagebox.showwarning("Focus Mode", "Agrega al menos un sitio para bloquear.")
            return

        duration = self._duration_in_seconds()
        end_time = datetime.now() + timedelta(seconds=duration)

        self.config_data.last_duration_seconds = duration
        self.config_data.strict_mode = self.strict_mode_var.get()
        self.config_data.session = FocusSession(
            active=True,
            start_time=self.config_manager.now_iso(),
            end_time=end_time.isoformat(timespec="seconds"),
            duration_seconds=duration,
        )

        try:
            self.hosts_manager.block_domains(self.config_data.blocked_sites)
            self.config_manager.save(self.config_data)
            self._set_focus_controls_enabled(False)
            self._launch_timer(end_time)
        except Exception as error:
            self.hosts_manager.restore_hosts()
            self.config_data.session = FocusSession()
            self.config_manager.save(self.config_data)
            messagebox.showerror("Focus Mode", f"No se pudo activar el bloqueo:\n{error}")

    def _launch_timer(self, end_time: datetime) -> None:
        def safe_tick(remaining: int) -> None:
            self.after(0, lambda: self.countdown_var.set(format_seconds(remaining)))

        def safe_complete() -> None:
            self.after(0, self._on_timer_completed)

        self.timer.start(end_time=end_time, on_tick=safe_tick, on_complete=safe_complete)

    def _on_timer_completed(self) -> None:
        try:
            self.hosts_manager.restore_hosts()
        finally:
            self.timer.reset()
            self.config_data.session = FocusSession()
            self.config_manager.save(self.config_data)
            self.countdown_var.set("00:00:00")
            self._set_focus_controls_enabled(True)
            messagebox.showinfo("Focus Mode", "¡Sesión finalizada! Sitios desbloqueados.")

    def _resume_active_session_if_needed(self) -> None:
        session = self.config_data.session
        end_time = self.config_manager.parse_iso(session.end_time)
        if not session.active or end_time is None:
            return

        now = datetime.now()
        if end_time <= now:
            self._on_timer_completed()
            return

        self._set_focus_controls_enabled(False)
        self._launch_timer(end_time)

    def _on_close(self) -> None:
        session_active = self.config_data.session.active
        strict = self.strict_mode_var.get()

        if session_active:
            text = "El modo Focus está activo.\nNo puedes cerrar la aplicación hasta que finalice el temporizador."
            messagebox.showwarning("Focus Mode", text)
            if strict:
                append_strict_log(self.config_manager.data_dir / "strict_mode.log", "Intento de cierre bloqueado")
                self.iconify()
            return

        self.timer.reset()
        self.destroy()


def build_app(config_manager: ConfigManager, hosts_manager: HostsManager) -> Callable[[], None]:
    app = FocusModeApp(config_manager=config_manager, hosts_manager=hosts_manager)
    return app.mainloop
