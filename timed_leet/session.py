"""Pure timing and phase-transition logic for Timed Leet."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Route(str, Enum):
    STANDARD = "standard"
    WITH_BRUTE_FORCE_CODE = "with_brute_force_code"


@dataclass(frozen=True)
class Phase:
    key: str
    name: str
    short_name: str
    duration_seconds: int
    prompt: str
    optional: bool = False


PROBLEM_UNDERSTANDING = Phase(
    "understanding",
    "Problem Understanding",
    "Understand",
    4 * 60,
    "Read the problem loudly. Understand the problem. Restate it in your own "
    "words. Understand what is input and the shape of input, and what is output.",
)
IDENTIFY_CONSTRAINTS = Phase(
    "constraints",
    "Identify Constraints and Pattern",
    "Constraints",
    3 * 60,
    "Understand constraints. Ask if constraints are not given. Identify the pattern.",
)
BRUTE_FORCE = Phase(
    "brute_force",
    "Brute Force Solution",
    "Brute Force",
    4 * 60,
    "Think and describe the naive solution. Explain why it works. State time and "
    "space complexity. Ask the interviewer before you start writing code. Don't "
    "write code unless asked.",
)
BRUTE_FORCE_CODE = Phase(
    "brute_force_code",
    "Write Brute Force Code",
    "Brute Code",
    6 * 60,
    "Okay. Write your brute force solution. Narrate decisions while writing code. "
    "Do not explain code line by line while writing.",
    optional=True,
)
OPTIMIZATION = Phase(
    "optimization",
    "Optimization",
    "Optimize",
    7 * 60,
    "Identify the bottleneck. Explain repeated work. Try to introduce the optimal "
    "idea. State time and space complexity before coding. Don't ask until asked.",
)
CODE = Phase(
    "code",
    "Code",
    "Code",
    21 * 60,
    "Code while narrating key decisions. Don't explain every line.",
)
DRY_RUN = Phase(
    "dry_run",
    "Dry Run, Edge Cases and End",
    "Dry Run",
    6 * 60,
    "Walk through one example and test edge cases. Mention optimized time and "
    "space complexity.",
)
END = Phase(
    "end",
    "End",
    "End",
    0,
    "It was great interviewing with you. Thanks for using Timed Leet. See you later.",
)

DECISION_PROMPT = "Do you want to write code?"

ALL_PHASES = (
    PROBLEM_UNDERSTANDING,
    IDENTIFY_CONSTRAINTS,
    BRUTE_FORCE,
    BRUTE_FORCE_CODE,
    OPTIMIZATION,
    CODE,
    DRY_RUN,
    END,
)


def phases_for(route: Route) -> tuple[Phase, ...]:
    if route == Route.WITH_BRUTE_FORCE_CODE:
        return ALL_PHASES
    return tuple(phase for phase in ALL_PHASES if not phase.optional)


class Session:
    """Tracks elapsed time and transitions through the selected interview route."""

    def __init__(self) -> None:
        self.route = Route.STANDARD
        self.phase_index = 0
        self.phase_elapsed = 0.0
        self.awaiting_code_decision = False
        self.finished = False

    @property
    def phases(self) -> tuple[Phase, ...]:
        return phases_for(self.route)

    @property
    def current_phase(self) -> Phase:
        return self.phases[self.phase_index]

    @property
    def total_duration(self) -> int:
        return sum(phase.duration_seconds for phase in self.phases)

    @property
    def total_elapsed(self) -> float:
        return sum(
            phase.duration_seconds for phase in self.phases[: self.phase_index]
        ) + self.phase_elapsed

    @property
    def phase_remaining(self) -> float:
        return max(0.0, self.current_phase.duration_seconds - self.phase_elapsed)

    @property
    def progress(self) -> float:
        if self.total_duration == 0:
            return 1.0
        return min(1.0, self.total_elapsed / self.total_duration)

    def reset(self) -> None:
        self.route = Route.STANDARD
        self.phase_index = 0
        self.phase_elapsed = 0.0
        self.awaiting_code_decision = False
        self.finished = False

    def choose_brute_force_code(self, should_write: bool) -> Phase:
        if should_write:
            self.route = Route.WITH_BRUTE_FORCE_CODE
            target = BRUTE_FORCE_CODE
        else:
            self.route = Route.STANDARD
            target = OPTIMIZATION
        self.awaiting_code_decision = False
        self.finished = False
        self.phase_index = self.phases.index(target)
        self.phase_elapsed = 0.0
        return target

    def jump_to(self, phase_key: str) -> Phase:
        target = next((p for p in ALL_PHASES if p.key == phase_key), None)
        if target is None:
            raise ValueError(f"Unknown phase: {phase_key}")

        if target.optional:
            self.route = Route.WITH_BRUTE_FORCE_CODE

        self.phase_index = self.phases.index(target)
        self.phase_elapsed = 0.0
        self.awaiting_code_decision = False
        self.finished = target is END
        return target

    def advance(self, seconds: float) -> list[str]:
        """Advance time and return transition events.

        Events are ``decision`` when user input is needed, ``phase`` when a new
        phase begins, and ``finished`` when the End phase is reached.
        """
        if seconds < 0:
            raise ValueError("seconds cannot be negative")
        if self.awaiting_code_decision or self.finished:
            return []

        events: list[str] = []
        remaining_tick = seconds
        while remaining_tick > 0 and not self.awaiting_code_decision and not self.finished:
            phase = self.current_phase
            available = phase.duration_seconds - self.phase_elapsed

            if remaining_tick < available:
                self.phase_elapsed += remaining_tick
                break

            remaining_tick -= max(0.0, available)
            self.phase_elapsed = float(phase.duration_seconds)

            if phase is BRUTE_FORCE:
                self.awaiting_code_decision = True
                events.append("decision")
                break

            self.phase_index += 1
            self.phase_elapsed = 0.0
            if self.current_phase is END:
                self.finished = True
                events.extend(("phase", "finished"))
                break
            events.append("phase")

        return events
