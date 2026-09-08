# macOS Port — Development Handoff

Target: a native macOS app with the full functionality of this repo
(`qtile-pomodoro`), which today runs as an X11/Qtile Linux setup. This
document is self-contained: contracts, semantics, UX, and hard-won
pitfalls. Reference source: https://github.com/mailhexu/qtile-pomodoro
(read `src/qtile_pomodoro/` alongside this doc; the four stdlib-only
modules port nearly verbatim).

## 1. Product summary

Two subsystems, deliberately decoupled:

1. **Pomodoro timer** — a background daemon with a Unix-socket CLI,
   SQLite state, wall-clock-accurate phases, break overlays on every
   screen, and completion notifications.
2. **Task overlay** — a lightweight Todoist client: Today/Inbox lists,
   a bar/menu-bar counter, and a keyboard-first popup summoned by a
   global hotkey. Local JSON cache; writes through to Todoist; fully
   usable offline with a replay queue.

Key architectural rule the Linux version enforces and the port must
keep: **the timer is a daemon (survives the UI), the tasks are
in-process (no task daemon)**. Task interactions are always
user-initiated; nothing about tasks needs to outlive the UI host.

## 2. What ports as-is vs what needs rewriting

| Module | Portability | Notes |
|---|---|---|
| `core.py` (timer daemon, config, SQLite store, socket protocol) | **~verbatim** | stdlib only; swap Unix-socket path constants and config/data dir conventions |
| `tasks.py` (TaskStore, JSON persistence) | **~verbatim** | stdlib only; path convention swap |
| `task_model.py` (pure overlay interaction model) | **verbatim** | no I/O, no UI toolkit; drives any frontend |
| `todoist.py` (TodoistClient + SyncEngine) | **verbatim** | stdlib + threads only |
| `cli.py` (argparse CLI: daemon/status/start/pause/reset/skip/reload/stats) | ~verbatim | |
| `qtile.py` (break overlays, bar widget) | **rewrite** | macOS: full-screen NSPanel per display + menu-bar item |
| `task_widget.py` (bar counter + task popup) | **rewrite** | macOS: NSStatusItem counter + NSPanel/popover |

Recommended stack: **Python + PyObjC** (keeps the four stdlib modules
importable unchanged, single codebase), or Swift for the UI shell with
the Python core behind a small XPC/subprocess bridge. If the agent
prefers full Swift, the contract sections below define behavior
precisely enough to reimplement.

## 3. Timer subsystem contract

### Config

TOML at a platform-appropriate path (Linux used
`~/.config/qtile-pomodoro/config.toml`; on macOS use
`~/Library/Application Support/<app>/config.toml`, keep TOML format):

```toml
[timer]
focus_minutes = 25        # all four keys positive ints; defaults shown
short_break_minutes = 5
long_break_minutes = 15
long_break_after = 4      # completed focus sessions per long break

[tasks]
todoist_api_token = "…"   # OPTIONAL; absent → purely local tasks
```

`reload` re-reads config; changes apply to future phases only.

### State machine

- Phases: `focus → short_break → focus …`; every
  `long_break_after`-th completed focus yields `long_break`.
- Statuses: `idle`, `running`, `paused`, and the completion surfaces.
- `start` resumes or starts focus. `pause` preserves remaining time.
  `reset` aborts the current focus to idle (breaks are not "reset").
  `skip` ends the current phase early.
- **Wall-clock semantics**: elapsed time follows real time — sleep,
  suspend, and daemon restart included. Persist `end_at` (epoch) and on
  daemon start recover: if `end_at` passed while away, process only the
  interrupted phase transition (complete the focus, enter the break).
  Never rely on the daemon staying alive to keep time.
- A focus interval counts in stats **only if it reached zero**.
- Notifications fire **only when a focus or a break completes**.

### Daemon & CLI

- One daemon per user, addressed via a Unix-domain socket
  (`$XDG_RUNTIME_DIR` on Linux; `$TMPDIR` on macOS) guarded by uid.
  Stale-socket handling: probe-connect; dead socket → unlink; live →
  refuse to double-start.
- CLI subcommands: `daemon | status | start | pause | reset | skip |
  reload | stats`. `status` returns phase/status/remaining; `stats`
  returns local-day minutes, ISO-week minutes, and retained history.
- SQLite (Linux path `~/.local/share/qtile-pomodoro/timer.sqlite3`):
  - `state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT)` —
    payload is the JSON state object (phase, status, end_at, remaining,
    completed_in_cycle).
  - `sessions (completed_at TEXT, seconds INTEGER)` — one row per
    completed focus session (local-time ISO timestamp).
- Launch on login: **LaunchAgent plist** (`~/Library/LaunchAgents/…plist`,
  `RunAtLoad`, keep-alive) replaces the Linux startup hook. Log
  somewhere inspectable (`~/Library/Logs/<app>/`).

### Break overlay & notifications

- When a break starts: a full-screen, top-most, per-display window with
  the remaining time and a single **Skip Break** control (starts focus
  immediately). When focus starts from Ready-to-work, pressing Space on
  the resume surface also starts. On macOS: borderless `NSPanel` at
  `NSStatusLevel` (or above) one per `NSScreen`, `canBecomeKey` for the
  skip button.
- Notifications via `osascript -e 'display notification …'` or
  UserNotifications framework; content: phase completed, what's next.

## 4. Task subsystem contract

### Data (JSON cache)

```json
{
  "version": 1,
  "today":     [{"id": "…", "title": "…", "created_at": "ISO",
                 "completed_at": null, "origin": "local|todoist"}],
  "inbox":     [ …same shape… ],
  "completed": [ …same shape, completed_at set… ],
  "sync": {"queue": [...], "token": "…|null", "revision": 7}
}
```

- **Atomic writes only**: temp file + `os.replace`. Single writer (the
  UI process).
- **Lenient load**: unknown/missing keys → defaults; a file written by
  older builds must load with every task intact. Quarantine (rename
  `.corrupt`) **only** for unreadable JSON — never for schema reasons.
- `sync` is omitted from output while untouched (no engine attached).
- Done list = append-only local log of overlay completions (capped
  display at 5).

### Overlay UX (exact contract — users are muscle-bound to it)

- Lists: **Today (N)** then **Inbox (N)** then dimmed **Done (N)**.
- **Selection highlight bar** across the row; `j`/`k` move it across
  both lists, reaching the last **visible** row; navigation must clamp
  to visible rows when the list is truncated (never act on hidden
  rows). Truncation shows `… N more`.
- **`d` completes** the selected task. **Space is NOT a completion
  key** (single-key completion caused accidental removals — a hard
  product decision). Space is inert in nav mode.
- `m` moves the selected task between Today and Inbox.
- **Type-to-add**: any printable key in nav mode begins the input line
  immediately; Backspace edits; `Enter` commits to the Tab-selected
  target (`Tab` toggles Today↔Inbox; target shown in the input
  prefix). Letters `j k m d i r` are reserved for navigation in nav
  mode — `i` or `Enter` on an empty line enters input mode for titles
  beginning with those letters.
- `r` forces a Todoist refresh (nav mode only).
- **Esc backs out of input mode first**, then closes (nav mode);
  the global hotkey toggles open/close.
- Click a row → completes it. Done rows are display-only.
- Header indicator: `↻N` = N queued (unsynced) writes; `!` = queue
  overflow (cap 100, newest dropped).
- Hint line at the bottom, verbatim from the Linux build:
  `type to add  Tab:target  j/k:select  d:done  m:move  r:refresh  Esc:close/back`
- Menu-bar counter `Tasks:N` (N = open Today count), click opens the
  overlay. Updates within ~1s of any change.
- Global hotkey (Linux used Mod+N): on macOS register a system
  hotkey (Carbon `RegisterEventHotKey` via PyObjC, or a
  user-configurable ⌘-combo) to toggle the overlay.

### Todoist sync engine (behavioral contract)

All HTTP through **Unified API v1**: `POST
https://api.todoist.com/api/v1/sync`, Bearer token, form-encoded body.
REST v2 / Sync v9 are sunset (2026-02-10) — do not use them.

- **Reads**: full sync only — form fields `sync_token="*"`,
  `resource_types=["items","user"]`. Response gives `items[]` (id,
  content, project_id, checked, is_deleted, due{date,string,…},
  added_at), `user.inbox_project_id`, and a new sync_token (unused — we
  always full-sync; refreshes are user-initiated and accounts are
  small).
- **Writes**: one batch per drain — `commands: [{type, uuid,
  [temp_id], args}]`. Types used: `item_add` (args `{content,
  due:{"string":"today"}?}`; omit project_id to land in the Todoist
  Inbox), `item_close` (args `{id}`), `item_update` (args `{id, due}`
  where due is `{"string":"today"}` or `null`). **Due-date semantics
  verified live**: `due.date` in responses is a *full RFC3339 UTC
  timestamp* — compare only `[:10]`.
- **Command UUID idempotency**: every queued write keeps a stable
  client-generated UUID; retries resend the same UUID and are safe.
  Creates use `temp_id` = the local task id; the response's
  `temp_id_mapping` resolves it — rewrite the task id AND any later
  queued args referencing it.
- **Queue-as-retry**: no in-place retries. Failed batches persist and
  replay next refresh. Per-command server error (`sync_status`
  non-"ok") → retry up to 3 refreshes, then drop that entry. Network
  errors keep the whole batch. Batch success removes only the sent
  UUIDs (entries enqueued mid-flight survive).
- **Reconcile** (after each read): fetched items replace
  `origin:"todoist"` entries — Inbox = items with
  `project_id == user.inbox_project_id`; Today = items with
  `due.date[:10] <= today` (overdue included, Todoist Today-view
  semantics). Items `checked` or `is_deleted` are excluded and dropped.
  **Local-origin tasks and tasks under pending writes always survive**
  (kept in their original list) until replayed or completed.
- **Threading**: all HTTP on a single worker thread; UI renders only
  the cache; worker completion reaches the UI thread via a main-thread
  dispatch (`call_soon_threadsafe` equivalent:
  `performSelectorOnMainThread` / `DispatchQueue.main.async`). Locks
  guard memory+file only — never span a network call. Single-flight
  refreshes (one worker max; concurrent requests register callbacks the
  running worker fires). After the worker's read fails (offline),
  re-check the dirty flag before sleeping — an enqueue that arrived
  mid-flight must not strand the queue.
- **Write-through on mutation**: every add/complete/move applies
  locally first (UI stays instant), queues the command, persists, and
  kicks the worker. Overlay open and `r` also trigger refreshes.
- **Token resolution order** (do NOT paste secrets into chats/configs
  unless the user chooses to): `TODOIST_API_TOKEN` env var →
  config.toml → one-shot interactive-shell fallback. On macOS prefer
  Keychain as an additional first-class source, keeping env-var
  compatibility. Never log the token.
- **Done section** = local completion log only. v1 has **no
  completed-items listing** (verified); tasks completed in other
  clients vanish from lists on refresh (correct) but don't join Done.

### Overlay rendering pitfalls ( generalize beyond Qtile)

- Give every text section its own layout/attributed-string object
  created once and re-drawn per pass; mutating one shared layout object
  per line silently renders nothing on some toolkits.
- One geometry function (`_visible_rows`) is the single source for
  drawing AND hit-testing; derive truncation, selection clamping, and
  click targets from it.
- Budget popup height explicitly: reserve fixed rows for headers,
  input line, hint, and the Done section before computing how many
  task rows fit.
- Clamp `chr(keysym)`-style conversions to the Unicode range (media
  keys crash naive conversions).

## 5. Testing & acceptance

- The repo's 40 tests are UI-free and must port with the modules
  (store persistence/migration/corrupt-recovery, model keymap,
  client request shapes against a stubbed transport, engine
  queue/replay/reconcile). Keep "no network in unit tests".
- Live acceptance checklist (user-facing):
  1. Timer: focus completes → notification + break overlay on every
     display; skip works; pause survives; stats day/week correct;
     daemon survives logout-less relogin; time survives sleep.
  2. Tasks no-token: overlay opens instantly, add/complete/move/persist
     across app restart; hint line matches §4 verbatim.
  3. Tasks with Todoist: web-side add appears on open/`r`; overlay
     add/complete/move reach Todoist; offline add+complete replays
     correctly after reconnect (temp-id remap); `↻N` shows pending.
  4. Pre-existing tasks.json from the Linux build loads with all tasks
     intact (schema is additive; migration is lenient).

## 6. Suggested project layout (macOS)

```
pomodoro_mac/
  core/        # ported: timer core, tasks store, model, todoist sync
  ui/          # PyObjC: menu bar item, overlay panel, break panels, hotkey
  cli.py       # ported CLI (daemon control via socket)
  LaunchAgent.plist
  tests/       # ported 40 tests + UI-free additions
```

Deliver as a launch-on-login app (LaunchAgent for the daemon; the UI
host can be a menu-bar app `LSUIElement=true`).
