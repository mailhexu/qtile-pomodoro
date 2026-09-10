---
status: in_progress
created: 2026-09-09
updated: 2026-09-09
related_notes:
  - ../../notes/using-the-timer.md
related_specs:
  - ../architecture.md
related_files:
  - ../../../../../src/qtile_pomodoro/qtile.py
consumer_interface_change: false
review_base: f9a9354
review_round: 0
evidence_packs: []
---

# Quick Task: Break Overlay Failure Diagnostics

## Request

Capture a deterministic trace for the user-reported condition: a timed break
begins on Qtile group 2, the normal desktop remains visible, and keyboard input
stops responding.

## Scope

- Add temporary, tagged transition diagnostics to `BreakOverlays.sync()`.
- Deploy them to the running Qtile session.
- Remove all diagnostics after one failing trace and then fix the demonstrated
  cause.

## Out of Scope

- Permanent telemetry, new persistence, or changes to break behavior before a
  red trace identifies the cause.

## Acceptance Criteria

- [ ] One tagged trace captures the failure.
- [ ] Diagnostics are removed before completion.
- [ ] Root cause is reproduced, fixed, and verified.

## Implementation Notes

Log only break/gate transitions and group changes: timer status, command,
current group, popup geometry/hidden state, and X input-focus ID.

## Verification

- Pending user reproduction.

## Links

- Related note: [Using the Qtile Pomodoro Timer](../../notes/using-the-timer.md)
- Related file: `src/qtile_pomodoro/qtile.py`

## Review

- [ ] Diff reviewed against scope.
- [ ] Acceptance criteria satisfied.
- [ ] Status set to `done` only after verification passes.
