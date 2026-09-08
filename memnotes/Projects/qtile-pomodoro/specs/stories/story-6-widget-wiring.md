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
