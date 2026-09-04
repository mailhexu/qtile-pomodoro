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

# Story 3: Keyboard-driven TaskOverlay popup

## User Story

- [ ] Given the overlay is open and focused, typing printable characters starts the input line immediately and builds on it; Backspace deletes; Enter adds the task to the Tab-selected target (Inbox↔Today) and clears the input. Letters j/k/m/d/i are reserved for navigation in nav mode; i or Enter enters input mode to type titles beginning with those letters.
- [ ] Given tasks are listed, `j`/`k` move the selection across Today and Inbox including the last visible row (with a filled highlight bar), `d` (with empty input) completes the selected task, and `m` moves it between lists; navigation never targets rows hidden by truncation. Space is deliberately not a completion key: single-key completion caused accidental task removal (user decision 2026-09-04).
- [ ] Given the overlay is open, `Esc` from input mode returns to nav; `Esc` from nav (or Mod+N) closes and kills the popup; reopening shows persisted state.
- [ ] Mouse clicks on list rows complete the row's task; a click on the input hint focuses input (best-effort).

## Tasks

### Phase 1: Research

- [ ] Search memnotes for relevant knowledge
- [ ] Review Break Overlay popup construction and `process_key_press`/`process_button_click` handling in `qtile_pomodoro/qtile.py`
- [ ] Verify keysym values delivered by X11 `process_key_press` for printable keys, Backspace, Tab, Escape
- [ ] Document findings in Technical Notes

### Phase 2: Tests (TDD - Write First!)

- [ ] TEST-001: input-line editor state machine as a pure function (feed key strings → buffer, commit)
- [ ] TEST-002: selection navigation over a synthetic list model
- [ ] TEST-003: overlay action mapping (Space/m/Tab/Esc dispatch)

### Phase 3: Implementation

- [ ] IMPL-001: pure interaction model (input editor + selection + dispatch) in `qtile_pomodoro/task_widget.py`
- [ ] IMPL-002: popup rendering (dual textlayouts: lists, input line) and event wiring
- [ ] IMPL-003: `TaskOverlay.toggle` close path (kill popup, release focus)

### Phase 4: Review

- [ ] All tests pass
- [ ] Live smoke: full add → complete → move → close → reopen cycle via Mod+N
- [ ] Code review completed
- [ ] Knowledge notes updated

## Technical Notes

Reuse the proven popup recipe: `Popup(qtile, x, y, w, h)` + custom `textlayout`s + `place()/unhide()/win.focus()`. X11 `handle_KeyPress` maps state-shifted keysyms before `process_key_press(keysym)` — decode via a keysym→char table, not `chr()`. Overlay renders on `qtile.current_screen` only. Long lists truncate to visible rows with an ellipsis (minimalist scope: no scrolling in v1).

## Assumptions & Verification

| Assumption | Verified? | Source |
|------------|-----------|--------|
| Internal windows receive key events after `win.focus()` | ✅ | Break Overlay resume gate (working) |
| Keysyms arrive as X11 numeric symbols | ⬜ | verify in Phase 1 |
| Popup on current screen suffices on multi-monitor | ⬜ | Architecture risk table |

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
