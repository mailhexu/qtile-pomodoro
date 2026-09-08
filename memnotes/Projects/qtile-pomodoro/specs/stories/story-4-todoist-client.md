---
status: approved
created: 2026-09-08
updated: 2026-09-08
---

# Story 1: TodoistClient + live API probe

Parent: [Epic 2](../epics/epic-2-todoist-sync.md) | [Architecture](../architecture-todoist-sync.md)

## User Story

As the developer, I need a thin, fully-tested stdlib HTTP client for
`POST /api/v1/sync` and a pinned record of real v1 response shapes, so
the sync engine can be built against verified facts.

## Tasks

- [ ] Write `tests/test_todoist.py` client tests first (stubbed
  `urllib.request`): request shape (URL, Bearer header, form-encoded
  `sync_token`/`resource_types`/`commands`), JSON parsing, timeout,
  `TodoistError` mapping (network / non-2xx / bad JSON), batch
  `send()` returning `temp_id_mapping` + `sync_status`,
  `CommandError(uuid)` for per-command `"error"` status.
- [ ] Implement `src/qtile_pomodoro/todoist.py` class `TodoistClient`
  (`read()`, `send(commands)`), stdlib only.
- [ ] Run the unit tests.
- [ ] Live probe with the user's token (read-only first, then one
  scratch `item_add` + `item_close` + `item_update` on it): pin the
  exact `item_add` due-object shape, `item_update` due/clear args,
  `items[]` field names (`due.date`, `project_id`, `checked`,
  `is_deleted`), and `user.inbox_project_id`. Record findings in this
  story's Notes.

## Acceptance Criteria

- [ ] All client unit tests pass; no network in unit tests.
- [ ] Probe results recorded: exact arg shapes and response fields used
  by stories 2–3, with a sample response excerpt (token redacted).
- [ ] Scratch task cleaned up (closed + archived state left tidy).

## Notes

(to be filled by the probe)
