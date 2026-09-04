---
status: done
created: 2026-09-04
updated: 2026-09-04
linked_epic: ../epics/epic-1-task-overlay.md
linked_architecture: ../architecture.md
linked_prd: ../prd.md
related_notes: [../../notes/qtile-integration.md]
consumer_interface_change: false
review_base: ""
review_round: 0
---

# Story 1: TaskStore with JSON persistence

## User Story

As a Qtile user,
I want my Inbox and Today tasks persisted in a local JSON file,
So that my tasks survive Qtile restarts and are never sent anywhere.

## Acceptance Criteria

- [ ] Given a fresh store, when `add(title, "today")` and `add(title, "inbox")` are called, then `tasks.json` exists with the tasks under the correct lists and `today_count` reflects only Today.
- [ ] Given a store with a Today task, when `complete(task_id)` is called, then the task leaves Today, appears in `completed` with a non-null `completed_at`, and `today_count` decrements.
- [ ] Given a store with an Inbox task, when `move(task_id)` is called, then the task appears in Today and vice versa.
- [ ] Given a persisted store, when a new `TaskStore` is constructed on the same path, then all lists round-trip exactly.
- [ ] Given a corrupted or missing `tasks.json`, when the store loads, then it starts empty (renaming the corrupt file aside) instead of raising.
- [ ] Every mutation writes atomically (temp file + `os.replace`); no intermediate partial file is ever the canonical path.

## Tasks

### Phase 1: Research

- [ ] Search memnotes for relevant knowledge
- [ ] Review `qtile_pomodoro/core.py` for XDG path conventions
- [ ] Document findings in Technical Notes

### Phase 2: Tests (TDD - Write First!)

- [ ] TEST-001: add to inbox/today persists and counts
- [ ] TEST-002: complete hides from list, retains in completed with timestamp
- [ ] TEST-003: move swaps lists
- [ ] TEST-004: save/load round-trip
- [ ] TEST-005: corrupted-file recovery starts empty

### Phase 3: Implementation

- [ ] IMPL-001: `Task` dataclass and `TaskStore` in `qtile_pomodoro/tasks.py` (pure stdlib, no Qtile imports)
- [ ] IMPL-002: atomic JSON save with `version: 1` schema

### Phase 4: Review

- [ ] All tests pass
- [ ] Code review completed
- [ ] Knowledge notes updated

## Technical Notes

Store path: reuse the package's `data_path()` convention but a sibling file `tasks.json` under `$XDG_DATA_HOME/qtile-pomodoro/`. IDs: `uuid4().hex[:12]`. Timestamps: local-time ISO-8601, matching the Pomodoro session-history convention.

## Assumptions & Verification

| Assumption | Verified? | Source |
|------------|-----------|--------|
| Single writer is the Qtile process | ⬜ | Architecture ADR-002 |
| pytest available in mydev env | ⬜ | to verify |

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
