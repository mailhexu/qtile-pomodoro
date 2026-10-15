---
project_id: "qtile-pomodoro"
subproject_id: "manual-breaks-and-timer-control-panel"
status: "draft"
record_kind: "story"
local_id: "004"
linked_prd: "../prd.md"
linked_epic: "../epics/epic-001.md"
linked_architecture: "../architecture.md"
depends_on: ["001", "002", "003"]
created: 2026-10-15
updated: 2026-10-15
related_notes:
  - ../../../../notes/using-the-timer.md
  - ../../../../notes/qtile-integration.md
consumer_interface_change: true
proposal_required: false
routine_edge_change: false
routine_decision_required: false
routine_proposals: []
review_base: ""
review_round: 0
acceptance_evidence: []
review_record: ""
---

# Story 4: Native Control Panel and End-to-End Delivery

## User Story

As a Qtile pomodoro user,
I want a native panel opened by clicking the Pomodoro bar, and an explicit Controls action while a break or resume gate covers the bar,
So that I can run state-appropriate actions and edit settings without memorizing bindings, while held focus and overlays stay authoritative.

## Scope

**In scope:** new `timer_panel.py` (native popup, numeric draft fields, action callbacks); bar-click toggle; Controls buttons on break/Resume Gate surfaces; state-gated actions; settings Save flow and errors; keyboard/mouse input; geometry/focus/stacking lifecycle; workspace and screen hooks; finalization cleanup; integration verification, consumer docs, safe deployment.

**Non-goals:** a second timer or persisted GUI state; new GUI toolkit or Wayland; task/Todoist changes; service transitions/accounting (001), TOML mechanics (002), transport/controller (003); custom one-off durations; automatic restart.

**Source outputs:** `qtile.py` controller entry points/stacking/hooks, new `timer_panel.py`, knowledge/doc updates, deployment evidence. Depends on 001, 002, 003; implementation starts only after this story's approval.

## Acceptance Criteria

- [ ] AC-1 (FR-001): Clicking the bar toggles exactly one panel on the current screen; Escape closes it; reopening never duplicates windows or callbacks.
- [ ] AC-2 (FR-002): In any service state the panel renders live phase, integer remaining countdown, cycle progress and held-focus summary from controller snapshots, and keeps no timer of its own.
- [ ] AC-3 (FR-003): Only actions valid per state among Start/Resume, Pause, Reset, Start Short/Long Break, Skip Break are enabled; Reset carries a phase-specific label; CLI/keybinding behavior still works.
- [ ] AC-4 (FR-004): From idle/ready/running/paused focus a manual short/long break starts immediately with the configured duration and normal overlay; during a running or paused break manual-break actions are unavailable and a stale-panel request is rejected without discarding saved focus or restarting the break.
- [ ] AC-5 (FR-005): With 25 minutes left of a 35-minute focus, the break freezes exactly those 25; nothing elapses during break or gate; from paused focus it preserves without first running it.
- [ ] AC-6 (FR-006): A manual break reaching zero waits at the resume gate; explicit resume continues at 25 (not 35); with no held focus resume starts a fresh focus at then-current settings.
- [ ] AC-7 (FR-007): Skip resumes held focus immediately or starts fresh; break Reset ends at the gate retaining held focus; focus Reset aborts uncounted; automatic-break skip/reset semantics stay intact.
- [ ] AC-8 (FR-008): When the resumed focus finishes, exactly one 35-minute history row is recorded excluding break time; the manual break never increments or resets the cycle counter.
- [ ] AC-9 (FR-009): Daemon replacement mid-break or at the gate preserves held focus, never duplicates history, never auto-starts focus; an overdue manual break settles to the gate.
- [ ] AC-10 (FR-010): All four fields edit via keyboard/mouse; explicit Save persists; closing with dirty edits discards only the draft and changes no configuration.
- [ ] AC-11 (FR-011): Invalid input (zero/negative/fractional/boolean/empty) yields an actionable error, leaving file, applied daemon settings, active state and history unchanged, without expiry settlement.
- [ ] AC-12 (FR-012): A valid save affects future phases only; active/paused deadline and remaining, and held remaining/original interval, stay untouched; unrelated TOML and the Todoist token survive unexposed.
- [ ] AC-13 (FR-013): applied, saved-not-applied, rejected and unknown outcomes are reported distinctly; daemon absence errors clearly without freezing the panel or spawning duplicate daemons.
- [ ] AC-14 (FR-014, ADR-014): During an active break/gate covering the bar, its explicit Controls button opens the panel above that overlay (explicit X11 `StackMode.Above`) with live state; the overlay stays authoritative; no stale panel obscures a break without deliberate request.
- [ ] AC-15: Workspace switch or view-mode change closes the panel and restacks the authoritative overlay immediately, not at the next poll; pause/resume within one break keeps a deliberately opened panel.
- [ ] AC-16 (ARCH-UI-001): `screens_reconfigured` disposes resources on removed/changed screens, rebuilds geometry from cached state and restores stacking/current-screen focus; `current_screen_change` closes the panel and coalesces a deferred restack after Qtile's own focus work; finalization unsubscribes all hooks and disposes every popup/layout.
- [ ] AC-17: Status refreshes leave dirty field drafts untouched; opening or closing the panel cannot reset or otherwise mutate service state.
- [ ] AC-18: Permanent regressions exercise consumer-visible behavior — rendered snapshots, enabled/disabled actions, error text, stacking outcomes — through real store/socket/controller/panel seams, never mock-forwarding echoes or source-text assertions.
- [ ] AC-19: Actual isolated Qtile smoke covers panel buttons/fields/Save, focus→break→gate→resume, Controls above an active overlay, occupied-workspace stacking, screen reconfiguration and current-screen focus; multi-monitor checks run where the environment permits, otherwise are reported unavailable; no step resets or shortens the user's real session.
- [ ] AC-20: Deployment installs the implemented package into Qtile's interpreter, replaces both daemon and Qtile module cache preserving state, and verifies the actually loaded code (protocol/snapshot) — never via resets, shortened timers or fabricated history.

## Tasks

### Phase 1: Research

- [ ] RESEARCH-001: Re-read ADR-013/ADR-014 and delivered 001–003 contracts: snapshot fields, commands, error codes, controller task/hook ownership.
- [ ] RESEARCH-002: Map existing dedicated-layout popup and break/resume overlay patterns, geometry/hit-region and keyboard conventions in `qtile.py`; confirm Qtile 0.37 hook semantics.
- [ ] RESEARCH-003: Verify isolated smoke options (temp config/store, local socket, display); document multi-monitor availability honestly.

### Phase 2: Behavior-First Regressions

- [ ] TEST-001: State-gated action matrix (idle/ready/running/paused/break/gate): rendered enabled sets and service rejection of stale-panel requests.
- [ ] TEST-002: Held-focus lifecycle via panel actions: 25-of-35 hold, gate wait, resume-at-25, skip, break reset, focus reset, repeated manual break from held gate, exactly-once 35-minute history.
- [ ] TEST-003: Panel settings save: valid save future-only; each invalid class rejected; applied/saved-not-applied/rejected/unknown distinct; unrelated sections and token preserved.
- [ ] TEST-004: Panel lifecycle: open/close/reopen without duplicates; dirty fields across refreshes; closed-panel callback discard; complete finalization cleanup.
- [ ] TEST-005: Screen/workspace behavior at the controller seam: reconfiguration reconciliation, deferred current-screen restack, overlay/panel ordering.

### Phase 3: Implementation

- [ ] IMPL-001: `timer_panel.py`: native popup layout, numeric draft/edit fields, Tab/Shift-Tab, digits/Backspace, Enter, Escape; one geometry source for draw and hit regions.
- [ ] IMPL-002: Bar-click toggle; Controls buttons on break/gate surfaces; controller-owned stacking/focus order (overlays, then panel, then focus); workspace/view-mode close and restack; the three lifecycle hooks.
- [ ] IMPL-003: Action and Save callbacks via controller only; outcome/error rendering; enabled/disabled sync from snapshots.
- [ ] IMPL-004: Update `using-the-timer.md` and `qtile-integration.md` consumer/developer knowledge.

### Phase 4: Review and Completion

- [ ] Actual Qtile smoke per AC-19 against isolated data/service; record any unavailable surface.
- [ ] Independent two-axis review; pin `review_base` before approved implementation.
- [ ] Safe deployment evidence per AC-20; fill `acceptance_evidence`/`review_record`; human gate flips status.

## Routine Decision

No reusable deterministic procedure mechanics are introduced or materially changed; this story consumes the contracts delivered by stories 001–003.

## Technical Notes

Existing dedicated-layout popup and break/resume overlays in `qtile.py` are the pattern base; retain explicit X11 `StackMode.Above` because Internal `place(above=True)` alone is ineffective. Use `screens_reconfigured` (after `_process_screens`), `current_screen_change` and workspace-change hooks; coalesce the deferred restack on the Qtile main loop, suppressed after finalization. The panel owns only display state and unsaved field text; settings mechanics live in `settings.py` (002), transport in `client.py`, transitions/accounting in the Timer Service (001). Focus is shared between overlay and panel: verify usable input after the Qtile loop presents the surface, not from mapped flags alone.

## Assumptions & Verification

| Assumption | Verified? | Source |
|------------|-----------|--------|
| Qtile 0.37 emits `screens_reconfigured` after `_process_screens` | ⬜ | ADR-014; confirm Phase 1 |
| 003 controller snapshots include held-focus summary, saved/applied settings, commands, protocol version | ⬜ | ADR-013; confirm at 003 completion |
| Dedicated-layout pattern supports per-screen ownership and disposal | ⬜ | `qtile.py`; confirm Phase 1 |
| Isolated display/socket environment supports actual smoke | ⬜ | Phase 1 |

## Definition of Done

- [ ] All acceptance criteria met with recorded `acceptance_evidence`.
- [ ] Focused regressions pass at behavior seams, not forwarding echoes.
- [ ] Actual Qtile smoke documented, including explicitly limited/unavailable checks.
- [ ] Consumer and developer knowledge notes updated.
- [ ] Independent two-axis review completed against a pinned `review_base`.
- [ ] Safe deployment proven without resetting user state or fabricating history.

## Progress Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-10-15 | Created | Initial draft from approved PRD, architecture and Epic 001 |
