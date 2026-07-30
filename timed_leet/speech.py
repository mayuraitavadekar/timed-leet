"""Non-blocking text-to-speech service."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable


class SpeechService:
    """Runs pyttsx3 in its own thread so speech never freezes the interface."""

    def __init__(self, on_error: Callable[[str], None] | None = None) -> None:
        self._messages: queue.Queue[str | None] = queue.Queue()
        self._on_error = on_error
        self._thread = threading.Thread(
            target=self._worker, name="timed-leet-speech", daemon=True
        )
        self._thread.start()

    def say(self, text: str) -> None:
        self.stop()
        self._messages.put(text)

    def stop(self) -> None:
        while True:
            try:
                self._messages.get_nowait()
            except queue.Empty:
                break

    def close(self) -> None:
        self.stop()
        self._messages.put(None)

    def _worker(self) -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
        except Exception as exc:  # platform audio failures should not stop the timer
            self._report_error(f"Voice guidance is unavailable: {exc}")
            return

        while True:
            message = self._messages.get()
            if message is None:
                try:
                    engine.stop()
                finally:
                    return
            try:
                engine.say(message)
                engine.runAndWait()
            except Exception as exc:
                self._report_error(f"Could not play voice guidance: {exc}")

    def _report_error(self, message: str) -> None:
        if self._on_error:
            self._on_error(message)

