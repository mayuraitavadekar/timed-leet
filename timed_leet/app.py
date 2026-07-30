"""Tkinter desktop interface for Timed Leet."""

from __future__ import annotations

import math
import sys
import time
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from timed_leet.session import (
    ALL_PHASES,
    BRUTE_FORCE,
    DECISION_PROMPT,
    END,
    Phase,
    Route,
    Session,
)
from timed_leet.speech import SpeechService


COLORS = {
    "background": "#0B1020",
    "surface": "#141B2D",
    "surface_high": "#1B2540",
    "primary": "#8B5CF6",
    "primary_light": "#A78BFA",
    "cyan": "#22D3EE",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "border": "#2B3652",
    "success": "#34D399",
    "warning": "#FBBF24",
    "danger": "#FB7185",
}


def format_time(seconds: float) -> str:
    whole = max(0, int(seconds))
    minutes, secs = divmod(whole, 60)
    return f"{minutes:02d}:{secs:02d}"


class FlatButton(ttk.Button):
    """A real button with platform-consistent colors.

    Using a label as a button made click handling unreliable on some Tk/macOS
    versions.  The ``clam`` ttk theme honors these colors while preserving the
    native button command and keyboard behavior.
    """

    def __init__(
        self,
        parent: tk.Misc,
        *,
        text: str,
        command: Callable[[], None],
        bg: str,
        fg: str = COLORS["text"],
        hover_bg: str = COLORS["primary_light"],
        font: tuple[str, int] | tuple[str, int, str] = (
            "TkDefaultFont",
            10,
            "bold",
        ),
        width: int | None = None,
        anchor: str = "center",
        padx: int = 16,
        pady: int = 10,
    ) -> None:
        self._style_name = f"Flat{id(self)}.TButton"
        self._style = ttk.Style(parent)
        self._font = font
        self._anchor = anchor
        self._padx = padx
        self._pady = pady
        self._base_bg = bg
        self._hover_bg = hover_bg
        self._foreground = fg
        self._configure_palette()
        super().__init__(
            parent,
            text=text,
            command=command,
            width=width,
            takefocus=True,
            cursor="hand2",
            style=self._style_name,
        )

    def set_palette(self, *, bg: str, fg: str, hover_bg: str) -> None:
        self._base_bg = bg
        self._hover_bg = hover_bg
        self._foreground = fg
        self._configure_palette()

    def _configure_palette(self) -> None:
        self._style.configure(
            self._style_name,
            background=self._base_bg,
            foreground=self._foreground,
            font=self._font,
            anchor=self._anchor,
            padding=(self._padx, self._pady),
            borderwidth=1,
            relief="flat",
        )
        self._style.map(
            self._style_name,
            background=[
                ("disabled", self._base_bg),
                ("pressed", self._hover_bg),
                ("active", self._hover_bg),
            ],
            foreground=[
                ("disabled", COLORS["muted"]),
                ("!disabled", self._foreground),
            ],
        )


class TimedLeetApp(tk.Tk):
    TICK_MS = 100

    def __init__(self) -> None:
        super().__init__()
        self.title("Timed Leet")
        self.geometry("1100x720")
        self.minsize(900, 640)
        self.configure(bg=COLORS["background"])

        self.session = Session()
        self.running = False
        self.has_started = False
        self._last_tick = time.monotonic()
        self._phase_buttons: dict[str, FlatButton] = {}
        self._speech = SpeechService(self._queue_speech_error)
        self._speech_error: str | None = None

        self._configure_styles()
        self._build_ui()
        self._bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(self.TICK_MS, self._tick)
        self._render()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Timed.Horizontal.TProgressbar",
            troughcolor=COLORS["border"],
            background=COLORS["primary"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["primary"],
            darkcolor=COLORS["primary"],
            thickness=8,
        )

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=COLORS["background"], padx=32, pady=24)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=COLORS["background"])
        header.pack(fill="x", pady=(0, 20))
        tk.Label(
            header,
            text="TIMED LEET",
            font=("TkDefaultFont", 20, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"],
        ).pack(side="left")
        tk.Label(
            header,
            text="INTERVIEW PRACTICE",
            font=("TkDefaultFont", 10, "bold"),
            fg=COLORS["cyan"],
            bg=COLORS["background"],
        ).pack(side="left", padx=14, pady=(7, 0))
        self.route_label = tk.Label(
            header,
            font=("TkDefaultFont", 10),
            fg=COLORS["muted"],
            bg=COLORS["background"],
        )
        self.route_label.pack(side="right", pady=(7, 0))

        content = tk.Frame(outer, bg=COLORS["background"])
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=7)
        content.grid_columnconfigure(1, weight=4)
        content.grid_rowconfigure(0, weight=1)

        self.main_card = tk.Frame(
            content,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=34,
            pady=28,
        )
        self.main_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        sidebar = tk.Frame(
            content,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        self.phase_kicker = tk.Label(
            self.main_card,
            text="CURRENT PHASE",
            font=("TkDefaultFont", 10, "bold"),
            fg=COLORS["primary_light"],
            bg=COLORS["surface"],
        )
        self.phase_kicker.pack()
        self.phase_name = tk.Label(
            self.main_card,
            font=("TkDefaultFont", 24, "bold"),
            fg=COLORS["text"],
            bg=COLORS["surface"],
            wraplength=570,
            justify="center",
        )
        self.phase_name.pack(pady=(8, 18))

        self.timer_canvas = tk.Canvas(
            self.main_card,
            width=230,
            height=230,
            bg=COLORS["surface"],
            highlightthickness=0,
        )
        self.timer_canvas.pack()

        self.elapsed_label = tk.Label(
            self.main_card,
            font=("TkDefaultFont", 11),
            fg=COLORS["muted"],
            bg=COLORS["surface"],
        )
        self.elapsed_label.pack(pady=(10, 2))
        self.phase_remaining_label = tk.Label(
            self.main_card,
            font=("TkDefaultFont", 10),
            fg=COLORS["muted"],
            bg=COLORS["surface"],
        )
        self.phase_remaining_label.pack()

        self.guidance = tk.Label(
            self.main_card,
            font=("TkDefaultFont", 11),
            fg=COLORS["muted"],
            bg=COLORS["surface_high"],
            padx=18,
            pady=14,
            wraplength=570,
            justify="center",
        )
        self.guidance.pack(fill="x", pady=(20, 18))

        self.decision_frame = tk.Frame(self.main_card, bg=COLORS["surface"])
        tk.Label(
            self.decision_frame,
            text="Do you want to write the brute force code?",
            font=("TkDefaultFont", 12, "bold"),
            fg=COLORS["text"],
            bg=COLORS["surface"],
        ).pack(side="left", padx=(0, 16))
        self._make_button(
            self.decision_frame,
            "Yes · +6 min",
            lambda: self._choose_code(True),
            COLORS["primary"],
        ).pack(side="left", padx=4)
        self._make_button(
            self.decision_frame,
            "No · Optimize",
            lambda: self._choose_code(False),
            COLORS["surface_high"],
        ).pack(side="left", padx=4)

        controls = tk.Frame(self.main_card, bg=COLORS["surface"])
        controls.pack(side="bottom", pady=(12, 0))
        self.start_button = self._make_button(
            controls, "Start", self._toggle_running, COLORS["primary"], width=14
        )
        self.start_button.pack(side="left", padx=5)
        self.reset_button = self._make_button(
            controls, "Reset", self._reset, COLORS["surface_high"], width=10
        )
        self.reset_button.pack(side="left", padx=5)
        self.voice_button = self._make_button(
            controls, "Replay Voice", self._replay_voice, COLORS["surface_high"], width=12
        )
        self.voice_button.pack(side="left", padx=5)

        tk.Label(
            sidebar,
            text="PHASES",
            font=("TkDefaultFont", 11, "bold"),
            fg=COLORS["text"],
            bg=COLORS["surface"],
        ).pack(anchor="w", pady=(0, 12))

        phase_list = tk.Frame(sidebar, bg=COLORS["surface"])
        phase_list.pack(fill="both", expand=True)
        for index, phase in enumerate(ALL_PHASES, start=1):
            label = f"{index:02d}   {phase.name}"
            if phase.optional:
                label += "  (+6)"
            button = FlatButton(
                phase_list,
                text=label,
                command=lambda key=phase.key: self._jump_to(key),
                anchor="w",
                font=("TkDefaultFont", 10),
                padx=12,
                pady=9,
                bg=COLORS["surface"],
                hover_bg=COLORS["surface_high"],
            )
            button.pack(fill="x", pady=2)
            self._phase_buttons[phase.key] = button

        self.progress_bar = ttk.Progressbar(
            sidebar,
            style="Timed.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
        )
        self.progress_bar.pack(fill="x", pady=(12, 7))
        self.progress_label = tk.Label(
            sidebar,
            font=("TkDefaultFont", 9),
            fg=COLORS["muted"],
            bg=COLORS["surface"],
        )
        self.progress_label.pack(anchor="e")

        self.status_label = tk.Label(
            outer,
            text="Ready. Press Space or click Start.",
            font=("TkDefaultFont", 9),
            fg=COLORS["muted"],
            bg=COLORS["background"],
        )
        self.status_label.pack(fill="x", pady=(12, 0))

    def _make_button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        color: str,
        width: int | None = None,
    ) -> FlatButton:
        return FlatButton(
            parent,
            text=text,
            command=command,
            width=width,
            font=("TkDefaultFont", 10, "bold"),
            fg=COLORS["text"],
            bg=color,
            hover_bg=COLORS["primary_light"],
            padx=16,
            pady=10,
        )

    def _bind_shortcuts(self) -> None:
        self.bind("<space>", lambda _event: self._toggle_running())
        self.bind("<Command-r>", lambda _event: self._reset())
        self.bind("<Control-r>", lambda _event: self._reset())

    def _toggle_running(self) -> None:
        if self.session.finished:
            self._reset()
        if self.session.awaiting_code_decision:
            return
        self.running = not self.running
        self._last_tick = time.monotonic()
        if self.running and not self.has_started:
            self.has_started = True
            self._speech.say(self.session.current_phase.prompt)
        self.status_label.configure(
            text=(
                f"{self.session.current_phase.name} started."
                if self.running
                else "Timer paused."
            ),
            fg=COLORS["muted"],
        )
        self._render()

    def _reset(self) -> None:
        self.running = False
        self.has_started = False
        self.session.reset()
        self._speech.stop()
        self._last_tick = time.monotonic()
        self.status_label.configure(text="Reset. Press Space or click Start.")
        self._render()

    def _jump_to(self, phase_key: str) -> None:
        phase = self.session.jump_to(phase_key)
        self.has_started = True
        self.running = phase is not END
        self._last_tick = time.monotonic()
        self._speech.say(phase.prompt)
        self.status_label.configure(text=f"Jumped to {phase.name}. Timer reset to phase start.")
        self._render()

    def _choose_code(self, should_write: bool) -> None:
        phase = self.session.choose_brute_force_code(should_write)
        self.running = True
        self.has_started = True
        self._last_tick = time.monotonic()
        self._speech.say(phase.prompt)
        self.status_label.configure(
            text="51-minute route selected." if should_write else "45-minute route selected."
        )
        self._render()

    def _replay_voice(self) -> None:
        prompt = (
            DECISION_PROMPT
            if self.session.awaiting_code_decision
            else self.session.current_phase.prompt
        )
        self._speech.say(prompt)
        self.status_label.configure(text="Replaying voice guidance.")

    def _tick(self) -> None:
        now = time.monotonic()
        delta = now - self._last_tick
        self._last_tick = now

        if self.running:
            previous_phase = self.session.current_phase
            events = self.session.advance(delta)
            if "decision" in events:
                self.running = False
                self._speech.say(DECISION_PROMPT)
                self.status_label.configure(text="Choose whether to write brute force code.")
            elif "phase" in events:
                self._speech.say(self.session.current_phase.prompt)
                if "finished" in events:
                    self.running = False
                    self.status_label.configure(text="Session complete. Great work!")
                else:
                    self.status_label.configure(
                        text=f"{previous_phase.name} complete. Next phase started."
                    )
        self._render()
        self._show_queued_speech_error()
        self.after(self.TICK_MS, self._tick)

    def _draw_timer(self) -> None:
        canvas = self.timer_canvas
        canvas.delete("all")
        pad = 14
        bounds = (pad, pad, 230 - pad, 230 - pad)
        canvas.create_oval(*bounds, outline=COLORS["border"], width=12)

        phase = self.session.current_phase
        if phase.duration_seconds:
            phase_progress = min(1.0, self.session.phase_elapsed / phase.duration_seconds)
        else:
            phase_progress = 1.0
        canvas.create_arc(
            *bounds,
            start=90,
            extent=-359.9 * phase_progress,
            style="arc",
            outline=COLORS["cyan"] if self.running else COLORS["primary"],
            width=12,
        )
        canvas.create_text(
            115,
            104,
            text=format_time(self.session.total_elapsed),
            fill=COLORS["text"],
            font=("TkDefaultFont", 34, "bold"),
        )
        state = "ELAPSED"
        if self.session.finished:
            state = "COMPLETE"
        elif self.session.awaiting_code_decision:
            state = "DECISION"
        elif self.running:
            state = "RUNNING"
        elif self.has_started:
            state = "PAUSED"
        canvas.create_text(
            115,
            142,
            text=state,
            fill=COLORS["cyan"] if self.running else COLORS["muted"],
            font=("TkDefaultFont", 9, "bold"),
        )

    def _render(self) -> None:
        phase = self.session.current_phase
        self.phase_name.configure(text=phase.name)
        self.guidance.configure(text=phase.prompt)
        self.elapsed_label.configure(
            text=f"Total elapsed · {format_time(self.session.total_elapsed)}"
            f" / {format_time(self.session.total_duration)}"
        )
        remaining = "Complete" if phase is END else f"{format_time(self.session.phase_remaining)} left in phase"
        self.phase_remaining_label.configure(text=remaining)
        self.route_label.configure(
            text=(
                "51 MIN · BRUTE FORCE CODE INCLUDED"
                if self.session.route == Route.WITH_BRUTE_FORCE_CODE
                else "45 MIN · STANDARD ROUTE"
            )
        )
        self.progress_bar["value"] = self.session.progress * 100
        self.progress_label.configure(
            text=f"{math.floor(self.session.progress * 100):d}% of session"
        )
        self.start_button.configure(
            text=(
                "Start Again"
                if self.session.finished
                else "Pause"
                if self.running
                else "Resume"
                if self.has_started
                else "Start"
            ),
            state="disabled" if self.session.awaiting_code_decision else "normal",
        )

        if self.session.awaiting_code_decision:
            if not self.decision_frame.winfo_ismapped():
                self.decision_frame.pack(before=self.guidance, pady=(0, 14))
        elif self.decision_frame.winfo_ismapped():
            self.decision_frame.pack_forget()

        current_key = phase.key
        route_keys = {item.key for item in self.session.phases}
        for key, button in self._phase_buttons.items():
            if key == current_key:
                button.set_palette(
                    bg=COLORS["primary"],
                    fg=COLORS["text"],
                    hover_bg=COLORS["primary_light"],
                )
            elif key not in route_keys:
                button.set_palette(
                    bg=COLORS["surface"],
                    fg=COLORS["muted"],
                    hover_bg=COLORS["surface_high"],
                )
            else:
                button.set_palette(
                    bg=COLORS["surface"],
                    fg=COLORS["text"],
                    hover_bg=COLORS["surface_high"],
                )
        self._draw_timer()

    def _queue_speech_error(self, message: str) -> None:
        self._speech_error = message

    def _show_queued_speech_error(self) -> None:
        if self._speech_error:
            self.status_label.configure(
                text=f"{self._speech_error} The visual timer will continue.",
                fg=COLORS["warning"],
            )
            self._speech_error = None

    def _on_close(self) -> None:
        self._speech.close()
        self.destroy()


def main() -> None:
    try:
        app = TimedLeetApp()
        app.mainloop()
    except tk.TclError as exc:
        print(f"Timed Leet could not open a desktop window: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
