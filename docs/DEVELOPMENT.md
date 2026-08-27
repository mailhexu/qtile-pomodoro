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
- The `qtile-pomodoro` console script lands in `~/.local/bin`, which is on
  `PATH`; shebang points into the uv venv, so it works from any shell.

## Qtile 0.37 widget API gotchas

- `base.ThreadPoolText` **no longer exists**. Deriving from it kills config
  reload with `AttributeError` and the bar silently keeps the old layout.
  Use `base.InLoopPollText` (runs `poll()` in the event loop — keep it
  non-blocking) or `base.BackgroundPoll` (thread-backed) instead.
- `Popup` takes **`fontsize`**, not `font_size`. The wrong name is silently
  ignored via `Configurable` defaults, so text renders at 14pt instead of the
  requested size — no error anywhere.
- After any package change you must restart Qtile
  (`qtile cmd-obj -o cmd -f restart`), not merely reload config: config
  reload re-imports `config.py`, but the previously imported
  `qtile_pomodoro` module stays cached in Qtile's process.

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
- Rapid overlay test: set `focus_minutes = 1`, `reload`, `reset`, `start`;
  restore afterwards. An aborted focus session is not counted in stats.

## Runtime state on this workstation

- Config: `~/.config/qtile-pomodoro/config.toml` (focus 35 min)
- Store: `~/.local/share/qtile-pomodoro/timer.sqlite3`
- Socket: `$XDG_RUNTIME_DIR/qtile-pomodoro-<uid>.sock`
- Daemon is spawned by Qtile's `startup_once` hook; it survives config
  reloads and Qtile restarts (duplicate-start is refused by probing the
  socket).
- Integration in `~/.config/qtile/config.py`: widget import, `startup_once`
  daemon launch, and `mod+p` / `mod+shift+p` / `mod+ctrl+p` /
  `mod+ctrl+shift+p` / `mod+alt+p` keybindings.

## Known limitations (accepted in design)

- X11 only; overlays are not guaranteed to cover layer-shell surfaces on
  Wayland (ADR-0003).
- Statistics count only focus sessions that reach zero; skipped/reset
  sessions are not recorded.
- Wall-clock timing: recovery processes exactly one phase transition and
  starts the next phase at recovery time.
