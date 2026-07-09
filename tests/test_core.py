from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from config import ConfigManager, FocusConfig, FocusSession
from hosts_manager import HostsManager
from timer import format_seconds


class FocusCoreTests(unittest.TestCase):
    def test_generate_variants(self) -> None:
        manager = HostsManager(hosts_path=Path("/tmp/hosts"), backup_path=Path("/tmp/hosts.bak"))
        variants = manager.generate_variants("https://www.facebook.com/feed")
        self.assertEqual(sorted(variants), ["facebook.com", "m.facebook.com", "www.facebook.com"])

    def test_format_seconds(self) -> None:
        self.assertEqual(format_seconds(2833), "00:47:13")

    def test_config_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            manager = ConfigManager(config_path=config_path)
            payload = FocusConfig(
                blocked_sites=["youtube.com"],
                last_duration_seconds=3600,
                strict_mode=True,
                session=FocusSession(
                    active=True,
                    start_time=datetime.now().isoformat(timespec="seconds"),
                    end_time=(datetime.now() + timedelta(hours=1)).isoformat(timespec="seconds"),
                    duration_seconds=3600,
                ),
            )
            manager.save(payload)
            loaded = manager.load()
            self.assertEqual(loaded.blocked_sites, ["youtube.com"])
            self.assertEqual(loaded.last_duration_seconds, 3600)
            self.assertTrue(loaded.strict_mode)
            self.assertTrue(loaded.session.active)


if __name__ == "__main__":
    unittest.main()
