"""Non-blocking text-to-speech service."""

from __future__ import annotations

import queue
import subprocess
import sys
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
        while True:
            message = self._messages.get()
            if message is None:
                return
            try:
                self._speak(message)
            except Exception as exc:
                self._report_error(f"Could not play voice guidance: {exc}")

    def _speak(self, message: str) -> None:
        if sys.platform == "darwin":
            # pyttsx3's macOS driver uses an AppKit run loop. Running that next
            # to Tk can eventually make the interface unresponsive, so use the
            # built-in speech command in the isolated worker process instead.
            subprocess.run(
                ["/usr/bin/say", "-r", "175", message],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.say(message)
            engine.runAndWait()
            engine.stop()
        except Exception:
            # Re-raise so the worker can report the failure without dying.
            raise

    def _report_error(self, message: str) -> None:
        if self._on_error:
            self._on_error(message)
