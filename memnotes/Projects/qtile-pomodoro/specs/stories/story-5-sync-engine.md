---
status: approved
created: 2026-09-08
updated: 2026-09-08
---

# Story 2: SyncEngine, storage migration, queue/reconcile

Parent: [Epic 2](../epics/epic-2-todoist-sync.md) | [Architecture](../architecture-todoist-sync.md)

## User Story

As the user, my overlay renders instantly from a local cache while a
background worker keeps it coherent with Todoist — including offline
mutation replay — and my existing tasks.json upgrades losslessly.

## Tasks

- [ ] Write `tests/test_todoist.py` engine tests first (fake client, no
  network): lenient load of pre-migration files **with task survival**;
  batch drain in queue order; temp-id mapping rewrites remaining queued
  args referencing the local id; permanent-vs-transient command errors
  (close-on-closed = success; unknown-id dropped; network error keeps
  batch); dirty-flag chained refresh; reconcile set-replacement with
  `checked`/`is_deleted` exclusion, local-origin survival, pending-op
  shielding; queue cap at 100.
- [ ] Extend `tasks.py`: additive `sync` block (queue/token/revision),
  lenient loader, `origin` field, save-omits-untouched-sync.
- [ ] Implement `SyncEngine` in `todoist.py` (worker thread, lock
  discipline, `call_soon_threadsafe` callback, alive-guard, queue cap).
- [ ] Run the full test suite (new + existing 20).

## Acceptance Criteria

- [ ] All engine unit tests pass.
- [ ] Existing 20 tests pass unmodified (no-token contract).
- [ ] Migration regression test proves pre-migration tasks survive load.

## Notes

(none yet)
