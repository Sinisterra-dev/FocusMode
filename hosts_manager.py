from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Iterable

BLOCK_IP = "127.0.0.1"


class HostsManager:
    def __init__(self, hosts_path: Path | None = None, backup_path: Path | None = None) -> None:
        self.hosts_path = hosts_path or Path(r"C:\Windows\System32\drivers\etc\hosts")
        backup_default = self.hosts_path.with_suffix(".focusmode.bak")
        self.backup_path = backup_path or backup_default
        self.start_marker = "# >>> FOCUS_MODE_START >>>"
        self.end_marker = "# <<< FOCUS_MODE_END <<<"

    def generate_variants(self, domain: str) -> list[str]:
        clean = domain.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
        clean = clean.removeprefix("www.")
        if not clean:
            return []

        variants = {clean, f"www.{clean}", f"m.{clean}"}
        return sorted(variants)

    def _build_block_section(self, domains: Iterable[str]) -> str:
        lines = [self.start_marker]
        for domain in domains:
            for variant in self.generate_variants(domain):
                lines.append(f"{BLOCK_IP} {variant}")
        lines.append(self.end_marker)
        return "\n".join(lines)

    def backup_hosts(self) -> None:
        original = self.hosts_path.read_text(encoding="utf-8")
        self.backup_path.write_text(original, encoding="utf-8")

    @staticmethod
    def _flush_dns_cache() -> None:
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=False, capture_output=True, text=True)
        except OSError:
            return

    def block_domains(self, domains: list[str]) -> None:
        if not domains:
            return
        original_content = self.hosts_path.read_text(encoding="utf-8")
        block_section = self._build_block_section(domains)

        if self.start_marker in original_content and self.end_marker in original_content:
            self.restore_hosts()
            original_content = self.hosts_path.read_text(encoding="utf-8")

        self.backup_hosts()

        updated = original_content.rstrip() + "\n\n" + block_section + "\n"
        try:
            self.hosts_path.write_text(updated, encoding="utf-8")
            self._flush_dns_cache()
        except Exception:
            self.restore_hosts()
            raise

    def restore_hosts(self) -> None:
        if self.backup_path.exists():
            restored = self.backup_path.read_text(encoding="utf-8")
            self.hosts_path.write_text(restored, encoding="utf-8")
            self._flush_dns_cache()
            return

        current = self.hosts_path.read_text(encoding="utf-8")
        if self.start_marker in current and self.end_marker in current:
            start = current.index(self.start_marker)
            end = current.index(self.end_marker) + len(self.end_marker)
            updated = (current[:start] + current[end:]).strip() + "\n"
            self.hosts_path.write_text(updated, encoding="utf-8")
            self._flush_dns_cache()
