---
status: draft
created: 2026-09-09
updated: 2026-09-09
linked_prd: ../prd-task-undo.md
linked_architecture: ../architecture-task-undo.md
linked_epic: ../epics/epic-3-local-task-undo.md
---

# Story 7: One-step local task undo

## User Story

As a Task Overlay user, I want to reverse my most recent accidental completion
or move with one key (`u`), so that I never lose a task to a mis-press.

## Requirements

- `TaskStore.complete()`/`move()` return an in-memory `UndoAction`
  (`kind`, `task_id`, `source`) on local success; `undo(action)` reverses it
  atomically and returns success. Engine path returns no action.
- `OverlayModel` keeps only the latest local action, clears it after a
  successful undo, and keeps `u` inert with no action or with sync enabled.
- Both `d` and mouse completion go through one model completion method.
- `u` appears in the on-screen hint; the hint marks undo local-only while
  sync is enabled.
- Consumer guide `notes/using-the-task-overlay.md` documents undo.

## Acceptance Criteria

- [ ] Unit: undoing a completion restores the task to its pre-completion list
      with `completed_at` cleared and the Done entry removed.
- [ ] Unit: undoing a move restores the task to its pre-move list.
- [ ] Unit: `u` with no action or with sync enabled mutates nothing.
- [ ] Unit: a new completion/move replaces the retained action.
- [ ] Unit: undoing a stale/absent task returns failure without mutation.
- [ ] Live smoke: `d` then `u` and `m` then `u` restore state in Qtile; bar
      counter and overlay redraw; hint mentions undo.
- [ ] Existing tests pass; consumer note updated.

## Technical Notes

- `UndoAction` dataclass lives in `tasks.py`; never serialized.
- Keep `_visible_rows()` clamp behavior unchanged.

## Out of Scope

- Redo, multi-step history, cross-restart undo, any Todoist command changes.

## Definition of Done

- Tests written first (TDD) and passing; live smoke verified.
- Code review (Task 7) converged; story status `done`; log updated.
