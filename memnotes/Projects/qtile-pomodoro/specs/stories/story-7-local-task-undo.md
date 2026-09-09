---
status: review
created: 2026-09-09
updated: 2026-09-09
linked_prd: ../prd-task-undo.md
linked_architecture: ../architecture-task-undo.md
linked_epic: ../epics/epic-3-local-task-undo.md
related_notes:
  - ../../notes/using-the-task-overlay.md
consumer_interface_change: true
review_base: a00a406447ac67956ab416587c666149cf893d51
review_round: 2
evidence_packs: []
---

# Story 7: One-step local task undo

## Approval Record

Approved by the user on 2026-09-09 through the explicit story-approval gate
before implementation began. The `draft → approved → in_progress` transition
was applied in the working tree together with the first implementation commit
(`c296e16`) instead of a separate preceding commit — recorded here (STD-001)
rather than rewriting published history.

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

- [x] Unit: undoing a completion restores the task to its pre-completion list
      with `completed_at` cleared and the Done entry removed.
- [x] Unit: undoing a move restores the task to its pre-move list.
- [x] Unit: `u` with no action or with sync enabled mutates nothing.
- [x] Unit: a new completion/move replaces the retained action.
- [x] Unit: undoing a stale/absent task returns failure without mutation.
- [x] Live smoke: `d` then `u` and `m` then `u` restore state in Qtile; bar
      counter and overlay redraw; hint mentions undo.
- [x] Existing tests pass; consumer note updated.

## Technical Notes

- `UndoAction` dataclass lives in `tasks.py`; never serialized.
- Keep `_visible_rows()` clamp behavior unchanged.

## Out of Scope

- Redo, multi-step history, cross-restart undo, any Todoist command changes.

## Verification

- `PYTHONPATH=src /home/hexu/projects/myenvs/mydev/bin/python -m pytest tests/ -q`
  — 60 passed (15 Story 7 tests).
- Live Qtile smoke with sync temporarily detached: `d`/`u` and `m`/`u`
  net-zero on `tasks.json` (35 ids before and after), overlay redraw, hint
  shows `u:undo`; sync engine restored afterwards.
- Usage skill pair regenerated from the updated consumer note and validated.

## Definition of Done

- Tests written first (TDD) and passing; live smoke verified.
- Code review (Task 7) converged; story status `done`; log updated.

## Code Review

**Review Base**: `a00a406447ac67956ab416587c666149cf893d51`
**Current Round**: 2

### Standards

| ID | Disposition | Evidence | Required Resolution | Introduced | Status |
|----|-------------|----------|---------------------|------------|--------|
| STD-001 | Blocking | Story went draft→in_progress in the implementation commit; approval gate untraceable. | Record the explicit user approval (Approval Record; commits not rewritten). | Round 1 | resolved |
| STD-002 | Blocking | Story frontmatter lacked `review_base`/`review_round`. | Pin base `a00a406447a` and round. | Round 1 | resolved |
| STD-003 | Blocking | Criteria unchecked, status not advanced, log/index stale. | Check criteria, advance story/epic/index to review, log implementation. | Round 1 | resolved |
| STD-004 | Blocking | `consumer_interface_change` and `related_notes` missing. | Declare both in frontmatter. | Round 1 | resolved |
| STD-005 | Blocking | Architecture/epic `linked_stories: []`; epic row unlinked. | Add reciprocal links. | Round 1 | resolved |
| STD-006 | Blocking | `apply_undo()` ignored a sync engine enabled after the action was retained (ADR-009). | Guard on `store.engine`, drop retained action. | Round 1 | resolved |
| STD-007 | Blocking | Consumed move action (task already in source) returned `True` without applying. | Return `False` when already home. | Round 1 | resolved |
| STD-008 | Non-blocking | Consumer note still said only `j/k/m/d/i` are reserved prefixes. | Add `u`; regenerate usage skill. | Round 1 | resolved |

### Spec

| ID | Disposition | Evidence | Required Resolution | Introduced | Status |
|----|-------------|----------|---------------------|------------|--------|
| SPEC-001 | Blocking | PRD Must 6: `u` must be a safe no-op whenever sync is enabled; retained action still executed. | Same engine guard as STD-006. | Round 1 | resolved |
| SPEC-002 | Blocking | Stale move undo reported success without mutation. | Same fix as STD-007. | Round 1 | resolved |
| SPEC-003 | Non-blocking | PRD Should 1: no feedback after undo. | `undo_status` shown in the hint until the next key. | Round 1 | resolved |
| SPEC-004 | Non-blocking | PRD Should 2: selection jumped to the restored task. | Reselect the previously selected task when still visible, else clamp. | Round 1 | resolved |
| SPEC-005 | Non-blocking | Reserved-prefix guidance missed `u`. | Same fix as STD-008. | Round 1 | resolved |

### Re-review History

| Round | Reviewed Revision | Findings Checked | New REG/LATE Evidence | Decision |
|-------|-------------------|------------------|-----------------------|----------|
| 1 | `c296e16` | complete two-axis inventory | n/a | changes requested |
| 2 | fixes after `c296e16` | STD-001..008, SPEC-001..005 | pending verification round | pending |
