from __future__ import annotations

from datetime import datetime
import threading
import time
from typing import Callable

TickCallback = Callable[[int], None]
CompleteCallback = Callable[[], None]


class FocusTimer:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._end_time: datetime | None = None

    @property
    def running(self) -> bool:
        return self._running

    def start(self, end_time: datetime, on_tick: TickCallback, on_complete: CompleteCallback) -> None:
        if self._running:
            return
        self._running = True
        self._end_time = end_time
        self._stop_event.clear()

        def run() -> None:
            try:
                while not self._stop_event.is_set():
                    if self._end_time is None:
                        break
                    remaining = int((self._end_time - datetime.now()).total_seconds())
                    if remaining <= 0:
                        on_tick(0)
                        on_complete()
                        break
                    on_tick(remaining)
                    time.sleep(1)
            finally:
                self._running = False

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def reset(self) -> None:
        self._stop_event.set()
        self._running = False


def format_seconds(total_seconds: int) -> str:
    clamped = max(total_seconds, 0)
    hours, remainder = divmod(clamped, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"
