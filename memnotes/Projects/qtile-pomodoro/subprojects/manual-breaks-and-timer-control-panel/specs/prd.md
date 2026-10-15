---
project_id: qtile-pomodoro
subproject_id: manual-breaks-and-timer-control-panel
record_kind: prd
local_id: prd
status: draft
created: 2026-10-15
updated: 2026-10-15
linked_research: []
linked_epics: []
---

# Manual Breaks and Timer Control Panel

## Problem Statement

The timer currently offers CLI/keybinding controls and automatic breaks, but
no single graphical surface for operating it or changing its settings. A user
cannot intentionally start a short or long break while preserving an unfinished
focus session. Editing TOML or remembering individual bindings is inconvenient.

## Goals

- Provide a compact Qtile-native timer control panel, opened by clicking the
  Pomodoro bar widget; existing keybindings and CLI controls remain usable.
- Start a short or long break manually using the configured durations.
- Preserve unfinished focus progress through a manual break, then wait for an
  explicit resume rather than automatically restarting work.
- Edit and save focus/break durations and the long-break interval from the panel.
- Preserve timer history, cycle accounting, recovery behavior, and the repaired
  all-workspace break-overlay stacking.

## Non-Goals

- A standalone desktop application, Wayland support, or a new GUI dependency.
- Changing Todoist/task behavior, adding schedules, or editing past session history.
- Custom one-off break durations, automatic focus restart, or resetting the
  current countdown merely because future-phase settings were saved.

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001 | Clicking the Pomodoro bar widget toggles one Qtile-native control panel on the current screen. The panel supports mouse and keyboard operation, closes with Escape, and can be reopened without duplicate windows or callbacks. | must |
| FR-002 | The panel shows live phase/status, remaining time, cycle progress, and any focus time held for resumption after a manual break. It does not maintain an independent timer. | must |
| FR-003 | Provide Start/Resume, Pause, Reset, Start Short Break, Start Long Break, and Skip Break actions. Enable only actions valid for the current state and give Reset a phase-specific label or explanation. Keep current CLI/keybinding behavior available. | must |
| FR-004 | Manual short/long breaks are available from idle, ready-to-work, running-focus, and paused-focus states. They begin immediately with the corresponding configured duration and the normal full-screen break overlay. While already in an active or paused break, another manual-break action is unavailable and must not discard saved focus or silently restart the break. | must |
| FR-005 | Starting a manual break during unfinished focus preserves the exact remaining focus time. Focus time does not elapse during the break or while waiting at the subsequent resume gate. A paused focus is preserved without first running it. | must |
| FR-006 | When a manual break reaches zero, show the normal resume gate and wait. An explicit resume continues the saved focus time; if there was no unfinished focus, it starts a fresh focus using the then-current settings. | must |
| FR-007 | Explicitly skipping a manual break resumes the saved focus immediately, or starts a fresh focus when none was suspended. Resetting a break ends it at the resume gate without discarding saved focus. Resetting focus aborts that unfinished focus without counting it. Existing automatic-break skip/reset semantics remain intact. | must |
| FR-008 | Manual breaks neither increment nor reset the completed-focus cycle counter and do not add a completed-focus history entry. A suspended-and-resumed focus counts exactly once when its remaining focus time finishes; its history duration excludes the break and reflects its original configured focus interval. | must |
| FR-009 | Persist both the active phase and the focus held for resumption. Daemon replacement/reboot must not lose held focus, duplicate a completion, or turn an overdue manual break into an automatically running focus. Existing wall-clock handling applies to the running break, not the held focus. | must |
| FR-010 | The panel edits the configured focus duration, short-break duration, long-break duration, and number of completed focus sessions before a long break. Show an explicit Save action; closing without saving does not change configuration. | must |
| FR-011 | Validate all four settings as positive whole numbers before saving; durations are minutes. Invalid input displays an actionable error and leaves the file, daemon configuration, active state, and history unchanged. | must |
| FR-012 | Save valid timer settings persistently and apply them to future phases without requiring a Qtile/daemon restart. Do not alter an active/paused phase's deadline or remaining time, or a suspended focus's remaining time/original interval. Preserve unrelated TOML sections, including Todoist configuration; never expose its token in the panel. | must |
| FR-013 | Distinguish successful save/application from errors. If valid settings were saved but the daemon could not load them, show that they are saved but not yet applied; do not falsely report full success. Unavailable-daemon errors must not freeze the panel or create duplicate daemons. | must |
| FR-014 | Manual breaks and settings updates are owned by the Timer Service, not the popup; retain the existing service/CLI integration pattern. Opening or closing the panel cannot reset the timer. The full-screen break/resume surfaces remain authoritative and must not be obscured by a stale control panel. | must |

## Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-001 | Remain X11/Qtile-native, lightweight, and compatible with the deployed Qtile 0.37 Python environment; no additional long-lived process or GUI toolkit. | must |
| NFR-002 | Timer/service I/O must not block normal Qtile interaction; the panel must remain dismissible and show failures clearly. | must |
| NFR-003 | Configuration and state writes must not leave partial files/state on failure. Existing stored state must upgrade without losing timer history or task data. | must |
| NFR-004 | Active break and resume overlays remain visible above application windows across occupied workspaces. Panel/overlay hooks and resources are cleaned up on close/finalization/reconfiguration. | must |
| NFR-005 | Regression tests cover transitions, accounting, persistence, validation, and settings precedence; verify the actual panel and break/resume surfaces in Qtile. No live verification may reset or shorten the user's active session. | must |

## Success Criteria

- [ ] Clicking the bar opens a usable panel showing current state; Start/Resume,
  Pause, Reset, manual short/long break, and Skip Break produce the stated
  state-dependent behavior without duplicate panels.
- [ ] With 25 minutes left in an unfinished 35-minute focus, a manual short break
  holds those 25 minutes. Natural break completion waits at the resume gate;
  explicit resume continues at 25 minutes, not 35. No focus completion is
  recorded until those remaining focus minutes finish, then exactly one
  35-minute focus is recorded.
- [ ] A manual long break, a break entered from paused focus, repeated manual-break
  attempts during a break, break reset, and explicit skip all preserve the
  specified focus/counter invariants.
- [ ] Starting a manual break from idle/ready with no suspended focus creates no
  focus history entry and waits for an explicit fresh-focus start afterward.
- [ ] Replacing the daemon during a manual break or at its resume gate preserves
  held focus and avoids duplicate history or automatic work restart.
- [ ] All four settings save, survive restart, and take effect on future phases.
  Editing them during running/paused/suspended focus or an active break leaves
  the current interval unchanged. Unrelated TOML settings survive.
- [ ] Invalid settings and daemon/file errors are visible and never masquerade
  as a successful update; invalid input changes neither config nor timer state.
- [ ] Actual Qtile smoke verifies panel operation plus break/resume surfaces
  above applications on occupied workspaces, with the user's active session
  unchanged by the verification procedure.

## Decisions and Gate

- User decision: keep unfinished focus progress across a manual break.
- User decision: control panel includes controls and persistent settings editing.
- Proposed default: bar-click Qtile popup; configured short/long break durations;
  explicit resume after natural break completion; existing skip behavior remains
  an explicit request to return to work immediately.
- This PRD is a draft. PRD approval precedes architecture and story approval;
  it does not authorize implementation or deployment.

## Open Questions

None blocking PRD review. Exact popup layout, keyboard shortcuts, service command
shapes, persisted suspended-focus representation, and configuration-writing
mechanics belong to the architecture gate.
