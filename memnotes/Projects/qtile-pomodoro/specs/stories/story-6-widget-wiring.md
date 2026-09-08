---
status: approved
created: 2026-09-08
updated: 2026-09-08
---

# Story 3: Widget wiring and live smoke

Parent: [Epic 2](../epics/epic-2-todoist-sync.md) | [Architecture](../architecture-todoist-sync.md)

## User Story

As the user, opening the overlay shows live Todoist state within
seconds, my actions reach Todoist, and pending/offline state is visible
(`↻N`), with `r` to force a refresh.

## Tasks

- [ ] Wire `task_widget.py`: refresh-on-open with revision-guarded
  redraw; `↻N` / `!` header indicator; `r` force-refresh key; token
  loaded from `config.toml [tasks] todoist_api_token`.
- [ ] Route overlay mutations through `engine.enqueue` when a token is
  configured; direct local mutation otherwise.
- [ ] Deploy to the Qtile venv, restart Qtile.
- [ ] Live smoke with the user: add in overlay ↔ appears in Todoist web;
  complete in overlay ↔ gone from Todoist; `r` pulls web-side changes;
  offline drill (network cut → add+complete → reconnect → `r` → verify
  in Todoist web).

## Acceptance Criteria

- [ ] Full test suite passes.
- [ ] Live smoke items above verified by the user.
- [ ] Code review round passes.

## Notes

(none yet)

## Notes (partial)

- Wiring + review complete (7f6d745). Live smoke pending user token.

## Live smoke results (2026-09-08)

- Token delivered via `TODOIST_API_TOKEN` exported in ~/.bashrc (user
  preference; never pasted or stored). Loader order: env → config.toml →
  one-shot interactive-bash fallback (Qtile doesn't inherit bashrc).
- Refresh-on-open: revision 1 after first open; Todoist Inbox was empty
  of open items and nothing due today — local tasks correctly survived.
- Write-through: overlay-path adds reached Todoist (origin local→todoist
  via temp-id mapping); completes sent item_close; queue drained;
  verified against live API (no open smoke items remain).
- Offline drill covered at unit level (network-failure tests); live
  network-cut drill left to user discretion.
