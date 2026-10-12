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

### Upgrading without losing an active timer

An install replaces files, not code already loaded in memory. Upgrade into
Qtile's interpreter, then replace **both** the Qtile module cache and the
long-lived Timer Service process. A config reload does not clear Qtile's
module cache, and restarting Qtile alone does not replace a surviving daemon.

1. Record `/path/to/qtile/bin/python -m qtile_pomodoro.cli status --json`
   and `/path/to/qtile/bin/python -m qtile_pomodoro.cli stats`, using the
   interpreter into which the package was installed. Identify
   the sole listening owner of `$XDG_RUNTIME_DIR/qtile-pomodoro-<uid>.sock`
   (`/tmp` if `XDG_RUNTIME_DIR` is unset) with `ss -xlpn`, and inspect that
   exact PID with `ps -p PID -o pid,lstart,args`. Stop if ownership is ambiguous.
2. Install with the interpreter above and restart Qtile with
   `qtile cmd-obj -o cmd -f restart`; do not substitute a config reload.
3. Recheck the socket owner and process identity. If the known old daemon
   still owns it, terminate **only that verified PID** with `kill -TERM PID`.
   The widget's next poll normally starts the replacement with Qtile's
   interpreter. Check for a new sole socket owner and a working status
   response; do not launch another daemon alongside it. If automatic launch
   is deliberately disabled, wait for the old process to exit and confirm
   there is no listener before starting one daemon using
   `/path/to/qtile/bin/python -m qtile_pomodoro.cli daemon`.
4. Check status/history again. Before expiry, the original deadline, cycle
   counter and history are preserved. If focus is already overdue, recovery
   records exactly one completion and starts a fresh break at recovery time;
   it does not begin a fresh focus or catch up through multiple phases.

Do **not** issue `reset` or `start`, delete the store, or rewrite history as
part of an upgrade. See [development deployment notes](docs/DEVELOPMENT.md)
for the stale-runtime incident and restart details.

## Qtile integration

Add this to `config.py`:

```python
import subprocess
import sys
from libqtile import hook, widget
from qtile_pomodoro.qtile import Pomodoro
from qtile_pomodoro.task_widget import TaskCount, TaskOverlay

@hook.subscribe.startup_once
def start_pomodoro():
    subprocess.Popen([sys.executable, "-m", "qtile_pomodoro.cli", "daemon"])

# Add Pomodoro() and TaskCount() to a bar's widgets list; bind Mod+N:
Key([mod], "n", lazy.function(lambda qtile: TaskOverlay.toggle(qtile)))
```

The widget is display-only. Bind Qtile keys to these commands:

```text
qtile-pomodoro start | pause | reset | skip | reload | stats
```

`start` resumes or starts focus. A completed focus interval starts a break and shows a full-screen overlay on every X11 screen. Clicking its single **Skip Break** control starts focus immediately. A completed or reset break enters **Ready to work**; press Space in the resume surface or invoke `qtile-pomodoro start`.

## Task overlay

A daemonless, Qtile-native task list: `Mod+N` (or clicking `Tasks:N` in the
bar) opens a centered popup with **Today** and **Inbox** lists.

- Type to add; `Tab` picks the target list; `Enter` commits.
- `j`/`k` move the highlight, `d` completes, `m` moves between lists;
  clicking a row completes it.
- A dimmed **Done (N)** section shows the 5 most recent completions.
- `Esc` backs out of typing, then closes.

Tasks persist in `$XDG_DATA_HOME/qtile-pomodoro/tasks.json`; completions are
retained (hidden) as history. Independent of the Pomodoro daemon.

**Todoist sync** (optional): add a Todoist API token to the config:

```toml
[tasks]
todoist_api_token = "…"
```

The overlay then becomes a Todoist client — Today = tasks due today
(overdue included), Inbox = the Todoist Inbox project, with add /
complete / move writing through to Todoist. The JSON file is a cache:
the overlay opens instantly offline and queued changes replay on
reconnect (`↻N` shows pending writes; `r` forces a refresh). Without a
token, everything stays purely local.

## Semantics

- Only focus intervals reaching zero count in statistics.
- Notifications are emitted only when a focus or break completes.
- Pausing preserves remaining time; resetting focus aborts it to Idle.
- Timer elapsed time follows wall-clock time, including suspend and service restart. Recovery processes only the interrupted phase transition.
- `qtile-pomodoro stats` reports local-day and ISO-week totals plus retained local history.
