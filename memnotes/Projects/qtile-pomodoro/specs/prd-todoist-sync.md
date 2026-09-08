---
status: approved
created: 2026-09-08
updated: 2026-09-08
---

# PRD: Todoist Client Sync

## Problem

The task overlay's local JSON store is isolated: tasks created in Todoist
(phone, web, other clients) never appear in the overlay, and overlay actions
never reach Todoist. The user maintains two disjoint task lists.

## Goal

Make the overlay a real Todoist client: Todoist is authoritative, the overlay
shows live Todoist state, and overlay actions write through to Todoist —
while remaining instant and usable offline.

## Non-Goals

- Wayland support.
- Todoist projects beyond Inbox and due-today tasks (no project browser,
  no labels/filters/priorities UI).
- Background/periodic sync daemon (sync is user-initiated + on-write).
- Migrating the Pomodoro timer store (unchanged, SQLite, orthogonal).

## Users & Use Cases

Primary: the owner (single user, single machine, existing Todoist account).

1. Capture on desktop: type a task in the overlay → appears in Todoist
   Inbox (or Today if that's the add-target) within seconds.
2. Plan from phone, execute at desktop: tasks added/scheduled in Todoist
   show in the overlay's Today/Inbox on next open (or refresh).
3. Complete at desktop: `d` in the overlay closes the Todoist task; the
   Done section reflects real Todoist completions.
4. Work offline: overlay opens instantly from cache; mutations queue and
   replay to Todoist when connectivity returns.

## Functional Requirements

- **FR1 Auth**: Todoist REST API token read from
  `config.toml` (`[tasks] todoist_api_token`). Absent token → feature
  disabled, overlay works on the local store exactly as today.
- **FR2 Mapping**: Today = Todoist tasks with `due.date` = today (local
  timezone); Inbox = tasks in Todoist's Inbox project. Done = recently
  completed tasks (most recent first).
- **FR3 Read sync**: on overlay open and on explicit refresh, fetch mapped
  tasks from Todoist REST API and refresh the local cache. Fetch is
  asynchronous — overlay renders from cache immediately, updates on arrival.
- **FR4 Write-through**: add / complete / move in the overlay issue the
  corresponding Todoist REST calls (create task, close task, set/clear
  due date). Success updates the cache; failure queues the mutation for
  replay (next open/refresh retries the queue in order).
- **FR5 Offline queue**: pending mutations persisted in the cache file,
  shown as a `↻N` indicator in the overlay header; applied oldest-first;
  idempotency guarded (completing an already-closed task is a no-op).
- **FR6 Conflict rule**: last-write-wins per task; Todoist state wins on
  refresh unless a local pending mutation touches that task.
- **FR7 UX unchanged**: keys, layout, Done section, bar counter behavior
  identical to the current overlay. Bar counter counts Today from cache.

## Success Criteria

- Task added in Todoist web appears in the overlay within one refresh.
- Task completed via `d` disappears from Todoist Today/Inbox.
- Kill network → overlay still opens, edits queue, reconnect → edits replay
  and Todoist reflects them.
- No token configured → current local-only behavior, zero regressions
  (all 20 existing tests still pass).

## Risks & Assumptions

- **Assumes** Todoist REST API v2 (token auth, `POST /rest/v2/tasks`,
  `POST /rest/v2/tasks/:id/close`, due-date filters client-side) and the
  Sync API for recent completions; rate limits are generous for this
  call pattern (a handful per interaction).
- Qtile process must never block on network: all HTTP off-thread; UI
  always renders cache.
- Single-writer assumption preserved: only the Qtile process writes the
  cache file (offline replay ordering is local).

## Dependencies

- `urllib.request` (stdlib) for HTTP — or `requests` if already present in
  the Qtile venv (checked during architecture).
- Todoist personal API token (user-provided).

## Decision Log

- 2026-09-08 — Local cache + sync (not full replacement): user values
  instant offline-capable UI. API token in config (not OAuth). Due-date /
  Inbox mapping (not named projects). Full read/write (not read-only).
