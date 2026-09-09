---
status: done
created: 2026-09-09
updated: 2026-09-09
related_notes:
  - ../../notes/using-the-task-overlay.md
related_specs:
  - ../architecture.md
related_files:
  - ../../../../../src/qtile_pomodoro/task_widget.py
consumer_interface_change: true
review_base: 32e6870c367d54186a1c29a61beb9920a80c7334
review_round: 2
evidence_packs: []
---

# Quick Task: Left-align and wrap task text

## Request

Task text in the overlay is visually misaligned. It must be left-aligned and
long titles must wrap rather than run past the available column.

## Scope

- Render all overlay layouts with Pango left alignment.
- Remove leading padding from active task titles.
- Derive bounded wrapped visual lines once in `_visible_rows()`.
- Use visual-row heights for drawing, selection highlight, click hit-testing,
  and visible-row truncation.
- Keep the Done group display-only; its checkmark remains its prefix.

## Out of Scope

- Changing task data, keyboard bindings, completion behavior, or popup size.

## Acceptance Criteria

- [x] Every active title and its continuation begins at the same left edge.
- [x] A long title wraps to at most two lines inside the task column.
- [x] Selection and clicking use every wrapped line of one logical task.
- [x] Done rows remain dimmed, display-only, and do not overlap active content.
- [x] Unit tests and live verification pass.
- [x] Log updated.
- [x] Durable knowledge unchanged; no note update required.
- [x] Specs index updated.

## Implementation Notes

Qtile's `TextLayout` defaults to centered Pango alignment. The overlay now
sets each layout to Pango left alignment. `_visible_rows()` derives bounded
wrapped lines, attaches visual height to task rows, and reserves that same
height for rendering, selection, and hit testing.

## Verification

- `PYTHONPATH=src /home/hexu/projects/myenvs/mydev/bin/python -m pytest tests/ -q`
  — 40 passed.
- Qtile package import with `PYTHONPATH=src` — `TaskOverlay` imports.
- Deployed through the Qtile UV environment and inspected a live screenshot:
  active text was flush-left, the long Summarize task wrapped, the selected row
  was intact, and Done rows did not overlap.

## Links

- Related notes: [Using the Task Overlay](../../notes/using-the-task-overlay.md)
- Related specs: [Task Overlay Architecture](../architecture.md)
- Related files: `src/qtile_pomodoro/task_widget.py`

## Code Review

**Review Base**: `32e6870c367d54186a1c29a61beb9920a80c7334`
**Current Round**: 2

### Standards

| ID | Disposition | Evidence | Required Resolution | Introduced | Status |
|----|-------------|----------|---------------------|------------|--------|
| STD-001 | Blocking | Task 0 requires `template-quick-task.md`; the initial record lacked its metadata and review sections. | Restore the template structure and record verification/review evidence. | Round 1 | resolved |

### Spec

| ID | Disposition | Evidence | Required Resolution | Introduced | Status |
|----|-------------|----------|---------------------|------------|--------|
| SPEC-001 | Blocking | Character-count wrapping does not guarantee a proportional Pango line fits the task column. | Measure rendered Pango width for wrapping and ellipsis. | Round 1 | resolved |

### Re-review History

| Round | Reviewed Revision | Findings Checked | New REG/LATE Evidence | Decision |
|-------|-------------------|------------------|-----------------------|----------|
| 1 | `43d1f7f` | Complete two-axis inventory | n/a | changes requested |
| 2 | `d10f86c` | STD-001 and SPEC-001 | none | approved |

## Review

- [x] Diff reviewed against scope.
- [x] Acceptance criteria satisfied.
- [x] Status set to `done` after verification and review pass.
