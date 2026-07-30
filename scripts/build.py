"""Build a standalone Timed Leet executable for the current operating system."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "Timed Leet",
        "--collect-all",
        "pyttsx3",
        str(ROOT / "timed_leet" / "__main__.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    print(f"\nBuild complete: {ROOT / 'dist'}")


if __name__ == "__main__":
    main()

