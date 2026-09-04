---
status: done
created: 2026-09-04
updated: 2026-09-04
---

# Quick Task: Done section in task overlay

## Request

Show finished tasks in the overlay so completed work is visible.

## Scope

- Add a display-only **Done (N)** section below Inbox: most recent completions first, dimmed with a `✓` prefix, capped at 5 rows with `…N more`.
- Done rows are not selectable and not clickable (no accidental mutations).
- Popup height 420→520 to keep open-task capacity.

## Verification

- Live screenshot shows Done section with previously completed tasks.
- Existing 20 unit tests unchanged and passing (model untouched).

## Outcome

Implemented in task_widget.py; deployed and verified 2026-09-04.
