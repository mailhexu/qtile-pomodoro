# Development Notes

Practical findings from building and deploying this service, recorded so the
next change doesn't rediscover them. For the domain language see
[CONTEXT.md](../CONTEXT.md); for architecture decisions see the
[ADR index](./adr/).

## Qtile environment is UV-managed Python 3.12

The running Qtile (0.37.0) is **not** the system Python. It lives in a
`uv`-managed tool environment:

```text
/home/hexu/.local/share/uv/tools/qtile/bin/python   (Python 3.12)
```

Consequences:

- Install/upgrade the package into that exact interpreter, or the widget
  import fails with `ModuleNotFoundError`:

  ```bash
  uv pip install --python ~/.local/share/uv/tools/qtile/bin/python .
  ```

- That venv has **no pip** (`python -m pip` fails), hence `uv pip`.
- `pipx install` puts the CLI in its own isolated venv: the CLI would work,
  but `config.py` (loaded by Qtile's interpreter) cannot import the widget.
  This is why installation targets Qtile's environment (see README).
- Invoke the daemon with that interpreter and `-m qtile_pomodoro.cli`.
  A `qtile-pomodoro` script on `PATH` can have an old/system-Python shebang;
  do not assume the script uses the environment just upgraded.

## Qtile 0.37 widget API gotchas

- `base.ThreadPoolText` **no longer exists**. Deriving from it kills config
  reload with `AttributeError` and the bar silently keeps the old layout.
  Use `base.InLoopPollText` (runs `poll()` in the event loop — keep it
  non-blocking) or `base.BackgroundPoll` (thread-backed) instead.
- `Popup` takes **`fontsize`**, not `font_size`. The wrong name is silently
  ignored via `Configurable` defaults, so text renders at 14pt instead of the
  requested size — no error anywhere.
- Package upgrades require replacing **two** in-memory copies: restart Qtile
  (`qtile cmd-obj -o cmd -f restart`) to clear its module cache, and replace
  the long-lived Timer Service process as described below. Config reload
  re-imports `config.py`, but leaves `qtile_pomodoro` cached; a Qtile restart
  alone leaves a surviving daemon's cached `core` unchanged.

## Popup text rendering

`Popup.draw_text()` draws its single `self.layout` at the given offset. To
render the overlay's large countdown and the smaller bottom hint
independently, create a second `drawer.textlayout(...)`. Both layouts draw
onto the popup's drawer before `popup.draw()` flushes it:

```python
popup.timer_layout = popup.drawer.textlayout(...)
popup.button_layout = popup.drawer.textlayout(...)
popup.clear()
popup.timer_layout.draw(cx, screen.height // 3)
popup.button_layout.draw(cx, screen.height * 2 // 3)
popup.draw(); popup.place(); popup.unhide(); popup.win.focus()
```

`win.focus()` matters: without it the popup never receives key presses
(`process_key_press`) — which is why Space at the resume gate initially
did nothing.

## Verification recipes

- Live widget/bar state without reading pixels:

  ```bash
  qtile cmd-obj -o screen 0 bar bottom -f info
  ```

  Returns every widget's name/text/length — this is how the missing
  `Pomodoro` widget was detected.
- Config type-check (needs the package visible to mypy's Python; a missing
  `py.typed` marker surfaces here):

  ```bash
  qtile check -c ~/.config/qtile/config.py
  ```
- Qtile's own errors (failed reloads land here and nowhere else):

  ```text
  ~/.local/share/qtile/qtile.log
  ```
- Rapid overlay tests may use one-minute focus in an isolated test store.
  Do not change the user's config or run `reset`/`start` against an active
  saved timer to verify an upgrade; that would abort or alter its phase.

## Runtime state on this workstation

- Config: `~/.config/qtile-pomodoro/config.toml` (focus 35 min)
- Store: `~/.local/share/qtile-pomodoro/timer.sqlite3`
- Socket: `$XDG_RUNTIME_DIR/qtile-pomodoro-<uid>.sock`
- Daemon is spawned by Qtile's `startup_once` hook; it survives config
  reloads and Qtile restarts (duplicate-start is refused by probing the
  socket).

### Daemon launch must use Qtile's interpreter

`startup_once` originally spawned `~/.local/bin/qtile-pomodoro`, whose
`#!/usr/bin/python3` shebang cannot import the package (user site-packages
disabled via `PYTHONNOUSERSITE=1`). The daemon died instantly on every
login; the bug surfaced only after a full gdm3 reboot killed the manually
spawned daemon. Every launch site in `~/.config/qtile/config.py` now uses
`sys.executable -m qtile_pomodoro.cli` instead.

As a second line of defense, the widget self-heals: if `poll()` finds no
service it spawns the daemon once (`start_new_session=True`) and re-arms
the guard whenever the service answers again.

- Integration in `~/.config/qtile/config.py`: widget import, `startup_once`
  daemon launch, and `mod+p` / `mod+shift+p` / `mod+ctrl+p` /
  `mod+ctrl+shift+p` / `mod+alt+p` keybindings.

### State-preserving package deployment

Follow the [README upgrade sequence](../README.md#upgrading-without-losing-an-active-timer).
Use the same Qtile interpreter, XDG environment and store for the replacement;
do not copy an empty database over the existing one.

- Capture status and history before replacement with the target interpreter:

  ```bash
  ~/.local/share/uv/tools/qtile/bin/python -m qtile_pomodoro.cli status --json
  ~/.local/share/uv/tools/qtile/bin/python -m qtile_pomodoro.cli stats
  ss -xlpn
  ```

  Locate the exact socket path from the workstation notes above (using the
  same `XDG_RUNTIME_DIR`, or `/tmp` when unset). Confirm one listening owner,
  its command line and its start time with `ps -p PID -o pid,lstart,args`.
  If there are multiple or unidentifiable owners, stop and resolve ownership;
  never use a broad process-name kill.
- Install into Qtile's interpreter and restart Qtile, not just its config.
  Inspect the socket owner again. An old daemon may survive; only send
  `kill -TERM PID` after rechecking that PID is the known old socket owner.
  Do not stop a replacement that already started.
- The widget automatically launches a replacement when it observes the
  missing service. Prefer that single launch owner, then confirm the new
  socket owner's process start time and status response. Do not combine it
  with a manual launch. A manual launch is appropriate only when automatic
  launching is disabled, the old process has exited and no listener remains:
  use the Qtile interpreter with `-m qtile_pomodoro.cli daemon`.
- Preserve the original SQLite store and saved deadline. Do not issue
  `reset`, `start`, `skip` or rewrite session history for deployment.
  An unexpired running focus resumes with the **original** deadline and
  counter/history, not a new full interval. An overdue focus is completed
  once by the current daemon's recovery and enters a fresh break whose
  deadline starts at recovery time. Recovery never silently catches up
  through more phases; compare post-upgrade status/history accordingly.

### Stale daemon incident: focus running at zero

The observed CLI and normally polling Qtile both reported `focus`, `running`,
`0s` with an expired deadline. The daemon had started at 15:12:33, before the
status-expiry fix was installed at 15:48, and still held the old implementation
in memory. Installing the fix and restarting only Qtile did not update it.
The current `Timer.status()` completes an expired phase even without a live
ticker. The timeout diagnosis was disproven by successful status responses and
normal widget polling; increasing the polling timeout is not the remedy for
this stale-runtime failure. The old daemon's ticker was no longer advancing,
but why it stopped was not captured and remains unknown.

`tests/test_core.py` covers status expiry without a ticker and replacement
before/after expiry using the real temporary SQLite store and a controlled
clock. It never opens the user's state or launches desktop notifications.

## Known limitations (accepted in design)

- X11 only; overlays are not guaranteed to cover layer-shell surfaces on
  Wayland (ADR-0003).
- Statistics count only focus sessions that reach zero; skipped/reset
  sessions are not recorded.
- Wall-clock timing: recovery processes exactly one phase transition and
  starts the next phase at recovery time.
