---
project_id: qtile-pomodoro
subproject_id: null
record_kind: quick-task
local_id: 2026-09-09-break-overlay-diagnostics
status: approved
created: 2026-09-09
updated: 2026-10-12
related_notes:
  - ../../notes/using-the-timer.md
related_specs:
  - ../architecture.md
related_files:
  - ../../../../../src/qtile_pomodoro/qtile.py
consumer_interface_change: true
proposal_required: false
routine_edge_change: false
routine_decision_required: false
routine_proposals: []
review_base: 5b6f1ddb76cb7bb030412abab07c970750b4c3a4
review_round: 0
acceptance_evidence: []
review_record: ""
evidence_packs: []
---

# Quick Task: Break Overlay Failure Diagnostics

## Request

Capture a deterministic trace for the user-reported condition: a timed break
begins on Qtile group 2, the normal desktop remains visible, and keyboard input
stops responding.

## Scope

- Normalize this legacy, active Quick Task's identity metadata under the
  user-approved migration; leave unrelated feature specifications in place.
- Repair X11 break-popup stacking in `BreakOverlays.sync()` and maintain it
  when switching between occupied workspaces.
- Deploy the corrected package and replace the stale timer daemon using its
  persisted state, without resetting focus or manufacturing session history.
- Add a regression check, verify real X11 stacking, and document deployment
  requirements. No configuration or task-data changes.

## Out of Scope

- Permanent telemetry, new persistence, or changes to break behavior before a
  red trace identifies the cause.

## Acceptance Criteria

- [ ] Expired focus produces a running break rather than `focus/running/0s`.
- [ ] The break popup stacks above clients on occupied workspaces after switches.
- [ ] A non-expired focus deadline survives daemon replacement unchanged.
- [ ] No debug scaffolding or unrelated feature changes remain.
- [ ] Regression checks, live verification, review, and knowledge updates pass.

## Implementation Notes

Captured recurrence: Qtile polls normally; the socket-owning daemon predates
the installed transition fix and returns an overdue focus at zero. X11's reused
break popup is below clients in root stacking order. Qtile 0.37 skips raising
group-less Internal windows through `change_layer()`, including Popup's
`place(above=True)` call.

User approved the bounded work-record migration and both fixes on 2026-10-12.
The prior diagnostic baseline was `f9a9354`; this recurrence pins the new base
listed above without claiming the earlier work completed.

## Verification

- Pending user reproduction.

## Links

- Related note: [Using the Qtile Pomodoro Timer](../../notes/using-the-timer.md)
- Related file: `src/qtile_pomodoro/qtile.py`

## Review

- [ ] Diff reviewed against scope.
- [ ] Acceptance criteria satisfied.
- [ ] Status set to `done` only after verification passes.
