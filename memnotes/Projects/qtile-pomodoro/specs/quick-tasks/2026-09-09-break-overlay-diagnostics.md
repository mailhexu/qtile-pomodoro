---
project_id: qtile-pomodoro
subproject_id: null
record_kind: quick-task
local_id: 2026-09-09-break-overlay-diagnostics
status: done
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
review_round: 2
acceptance_evidence:
  - specs/quick-tasks/2026-10-12-break-overlay-acceptance.json
review_record: specs/quick-tasks/2026-10-12-break-overlay-review.json
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

- [x] Expired focus produces a running break rather than `focus/running/0s`.
- [x] The break popup stacks above clients on occupied workspaces after switches.
- [x] A non-expired focus deadline survives daemon replacement unchanged.
- [x] No debug scaffolding or unrelated feature changes remain.
- [x] Regression checks, live verification, review, and knowledge updates pass.

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

- Full suite with actual Qtile dependencies: 70 passed.
- Live stale-daemon replacement: one recovered focus, break 300s, count 230.
- Actual X11 switches on occupied groups 1/2/4/9: popup viewable, focused,
  and above every client without another polling cycle.
- Live non-expired daemon replacement preserved deadline 1791792364.3931727,
  cycle count 230, and history 231.
- Actual presented screenshot: full dark BREAK 02:03 plus skip control.
- Details: [recurrence repair observations](../../log/qtile-pomodoro-2026-10-12.md).

## Links

- Related note: [Using the Qtile Pomodoro Timer](../../notes/using-the-timer.md)
- Related file: `src/qtile_pomodoro/qtile.py`

## Review

- [x] Diff reviewed against scope.
- [x] Acceptance criteria satisfied.
- [ ] Status set to `done` only after verification passes.

Independent Standards and Spec reviewers approved round 2. Standards finding
STD-001 (README upgrade checks must use Qtile's interpreter) is resolved.
Lifecycle stays `in_progress` until `work finish` writes the completion receipt:
the installed tool rejects `review` as implementation authority despite its
documented lifecycle. No terminal status is assigned by hand.
