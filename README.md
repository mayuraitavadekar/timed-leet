# Timed Leet

Timed Leet is a cross-platform desktop coach for practicing LeetCode-style
interviews. It guides you through a structured **45-minute session**, or a
**51-minute session** when you choose to write the brute force solution.

## Features

- Voice prompt at the beginning of every phase
- Total elapsed time in `mm:ss`
- Phase countdown and visual progress
- Yes/no decision after the brute force discussion
- Click any phase to jump there and reset elapsed time to that phase's start
- Pause, resume, reset, and replay voice guidance
- Native desktop UI for macOS, Windows, and Linux

## Run from source

Python 3.9 or newer is required.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install and run:

```bash
python -m pip install .
timed-leet
```

You can also launch it with:

```bash
python -m timed_leet
```

On some Linux distributions, install Tk and eSpeak first:

```bash
# Ubuntu / Debian
sudo apt install python3-tk espeak-ng
```

## Build an installable standalone app

Build on each target operating system to produce its native artifact. A Windows
executable must be built on Windows, a macOS app on macOS, and a Linux binary
on Linux.

```bash
python -m pip install ".[dev]"
python scripts/build.py
```

Artifacts are written to `dist/`:

- macOS: `dist/Timed Leet.app`
- Windows: `dist/Timed Leet/Timed Leet.exe`
- Linux: `dist/Timed Leet/Timed Leet`

The built app includes Python and the required packages, so the recipient does
not need Python installed. Linux users still need a working speech engine such
as `espeak-ng`.

## Keyboard shortcuts

- `Space`: start, pause, or resume
- `Cmd+R` (macOS) / `Ctrl+R` (Windows/Linux): reset

## Session timeline

| Phase | Duration |
| --- | ---: |
| Problem Understanding | 4 min |
| Identify Constraints and Pattern | 3 min |
| Brute Force Solution | 4 min |
| Write Brute Force Code (optional) | 6 min |
| Optimization | 7 min |
| Code | 21 min |
| Dry Run, Edge Cases and End | 6 min |

The standard route totals 45 minutes. Including brute force code totals 51
minutes.
