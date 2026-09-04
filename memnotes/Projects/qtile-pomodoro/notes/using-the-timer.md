---
type: Consumer Guide
title: Using the Qtile Pomodoro Timer
status: stable
audience: usage
tags: [qtile, pomodoro, controls]
---

# Using the Qtile Pomodoro Timer

Install the package into the Python environment that runs Qtile. Configure intervals in `~/.config/qtile-pomodoro/config.toml`; after changing it, invoke the reload control.

The Qtile bar shows the active phase, remaining time, and progress toward a Long Break. `Mod+p` starts or resumes focus, `Mod+Shift+p` pauses, `Mod+Ctrl+p` resets, and `Mod+Alt+p` opens the text statistics report.

A completed Focus Session opens an all-screen X11 Break Overlay. Its bottom control skips the Break; a completed Break presents a Resume Gate that accepts Space.
