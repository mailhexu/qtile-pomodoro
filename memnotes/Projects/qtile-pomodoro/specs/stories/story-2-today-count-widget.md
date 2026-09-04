---
status: done
created: 2026-09-04
updated: 2026-09-04
linked_epic: ../epics/epic-1-task-overlay.md
linked_architecture: ../architecture.md
linked_prd: ../prd.md
related_notes: [../../notes/qtile-integration.md]
consumer_interface_change: true
review_base: ""
review_round: 0
---

# Story 2: TaskCount bar widget and config wiring

## User Story

As a Qtile user,
I want a bar widget showing my incomplete Today count that opens the task overlay on click,
So that task status is always glanceable and one click away.

## Acceptance Criteria

- [ ] Given tasks exist, the bar renders `Tasks:N` with N = incomplete Today count within one poll interval of any mutation.
- [ ] Given no tasks file exists, the widget renders `Tasks:0` without error.
- [ ] Given a click on the widget, the TaskOverlay opens (stubbed toggle in this story; full behavior in story 3).
- [ ] Given the Pomodoro Timer Service is stopped, the task widget still renders its count.
- [ ] `~/.config/qtile/config.py` gains `TaskCount()` in the bar and a `Mod+N` keybinding that toggles the overlay, and `qtile check` passes.

## Tasks

### Phase 1: Research

- [ ] Search memnotes for relevant knowledge
- [ ] Review `Pomodoro` widget polling pattern in `qtile_pomodoro/qtile.py`
- [ ] Document findings in Technical Notes

### Phase 2: Tests (TDD - Write First!)

- [ ] TEST-001: unit-test the count formatting helper (pure function, no Qtile)
- [ ] TEST-002: mtime-based reload triggers only when the file changed

### Phase 3: Implementation

- [ ] IMPL-001: `TaskCount(base.InLoopPollText)` in `qtile_pomodoro/task_widget.py` sharing a module-level `TaskStore`
- [ ] IMPL-002: button-press opens overlay; config.py wiring (widget + Mod+N)

### Phase 4: Review

- [ ] All tests pass
- [ ] Live smoke: `qtile cmd-obj -o screen 0 bar bottom -f info` shows `Tasks:N`
- [ ] Code review completed
- [ ] Knowledge notes updated

## Technical Notes

Follow the verified `InLoopPollText` pattern (see [Qtile Integration Constraints](../../notes/qtile-integration.md)); never use `ThreadPoolText`. Poll reads must not raise when the JSON is briefly mid-replace (atomic replace makes this a non-issue; still guard with try/except). Config changes require Qtile restart, not reload.

## Assumptions & Verification

| Assumption | Verified? | Source |
|------------|-----------|--------|
| `mod+n` unbound in current config | ⬜ | to verify in config.py |
| 1 s poll of file mtime is negligible cost | ⬜ | stat() is cheap; verify no visible CPU |

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests pass
- [ ] Code reviewed and approved
- [ ] Knowledge notes updated
- [ ] No regressions introduced

## Progress Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-09-04 | Created | Initial draft |
