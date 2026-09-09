---
status: review
created: 2026-09-09
updated: 2026-09-09
consumer_interface_change: true
related_notes:
  - ../../notes/using-the-task-overlay.md
review_base: 32e6870c367d54186a1c29a61beb9920a80c7334
review_round: 0
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

- Every active title and its continuation begins at the same left edge.
- A long title wraps to at most two lines inside the task column.
- Selection and clicking cover every wrapped line of one logical task.
- Done rows remain dimmed, display-only, and do not overlap active content.

## Verification

- `PYTHONPATH=src /home/hexu/projects/myenvs/mydev/bin/python -m pytest tests/ -q`
  — 40 passed.
- Deployed into Qtile and inspected a live screenshot: active text was
  flush-left, the long Summarize task wrapped, the selected row was intact,
  and Done rows did not overlap.
