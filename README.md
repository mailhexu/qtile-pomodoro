# Qtile Pomodoro

A Qtile-specific X11 Pomodoro service: persistent timer state, Qtile bar status, all-screen break overlays, local history, and CLI controls.

## Install

Install into the Python environment that launches Qtile so `config.py` can import the widget. For a UV-managed Qtile installation:

```bash
uv pip install --python /path/to/qtile/bin/python .
```

On this workstation the interpreter is:

```bash
uv pip install --python ~/.local/share/uv/tools/qtile/bin/python .
```

This is deliberately not a `pipx` installation: pipx isolates its packages from Qtile's Python environment.

The desktop must provide `notify-send` (libnotify). Create `~/.config/qtile-pomodoro/config.toml` to override defaults:

```toml
[timer]
focus_minutes = 25
short_break_minutes = 5
long_break_minutes = 15
long_break_after = 4
```

State and completed-session history live in `$XDG_DATA_HOME/qtile-pomodoro/timer.sqlite3`. The configuration reload command changes only future phases.

## Qtile integration

Add this to `config.py`:

```python
import subprocess
from libqtile import hook, widget
from qtile_pomodoro.qtile import Pomodoro

@hook.subscribe.startup_once
def start_pomodoro():
    subprocess.Popen(["qtile-pomodoro", "daemon"])

# Add Pomodoro() to a bar's widgets list.
```

The widget is display-only. Bind Qtile keys to these commands:

```text
qtile-pomodoro start | pause | reset | skip | reload | stats
```

`start` resumes or starts focus. A completed focus interval starts a break and shows a full-screen overlay on every X11 screen. Clicking its single **Skip Break** control starts focus immediately. A completed or reset break enters **Ready to work**; press Space in the resume surface or invoke `qtile-pomodoro start`.

## Semantics

- Only focus intervals reaching zero count in statistics.
- Notifications are emitted only when a focus or break completes.
- Pausing preserves remaining time; resetting focus aborts it to Idle.
- Timer elapsed time follows wall-clock time, including suspend and service restart. Recovery processes only the interrupted phase transition.
- `qtile-pomodoro stats` reports local-day and ISO-week totals plus retained local history.
