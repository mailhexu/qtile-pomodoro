---
project_id: "qtile-pomodoro"
subproject_id: "manual-breaks-and-timer-control-panel"
status: "draft"
record_kind: "story"
local_id: "003"
created: 2026-10-15
updated: 2026-10-15
linked_prd: "../prd.md"
linked_epic: "../epics/epic-001.md"
linked_architecture: "../architecture.md"
related_notes:
  - ../../../../notes/using-the-timer.md
  - ../../../../notes/qtile-integration.md
consumer_interface_change: true
depends_on: ["001", "002"]
proposal_required: false
routine_edge_change: false
routine_decision_required: false
routine_proposals: []
review_base: ""
review_round: 0
acceptance_evidence: []
review_record: ""
---

# Story 3: Asynchronous Timer Client and Qtile Controller

Depends on story-001 (state snapshots, manual-break commands) and story-002 (settings
snapshots, `save-settings`). Parents: [PRD](../prd.md), [architecture](../architecture.md)
(ADR-013; ADR-014 hook ownership), [Epic 001](../epics/epic-001.md).

## User Story

As a Qtile user,
I want the bar, break/resume overlays and later surfaces to share one nonblocking timer
transport and controller,
So that timer interaction never freezes the window manager, actions cannot double-fire,
and a stale daemon is reported honestly instead of silently doing nothing.

## Bounded Scope

- Extract the async Unix-socket request (`cli.py:8-15`) into `client.py`, shared by CLI
  and Qtile; closure in `finally`; keep the `ok/result/error` envelope, add
  machine-readable error codes.
- One controller per Qtile instance serving cached snapshots (timer fields, held-focus
  summary, `settings.saved/applied/outcome`, `available_commands`, `protocol_version: 2`) to bars and break/resume
  overlays: one-second poll, at most one request in flight, actions precede the next
  poll, duplicate submissions refused during a mutation; drawing and input stay on
  Qtile's loop.
- Remove the bar's blocking `check_output` status path and per-click/key `Popen`
  spawning; commands route through the controller; a protocol-2-less daemon gets
  explicit upgrade-required, never false success; self-heal becomes one guarded launch
  on absent/refused socket only.
- Controller-owned lifecycle: owner refcount, task cancellation, late-callback discard,
  hook subscription/cleanup for bar and overlays; story-004's panel reuses this owner.
  No panel stubs here.

## Non-Goals

Native panel widget and panel focus/stacking policy (004); manual-break state semantics
(001); settings validation and TOML writing (002); new GUI toolkit, retry machinery,
file watching, Wayland; daemon behavior beyond the status payload's protocol marker.

## Source Outputs

- `src/qtile_pomodoro/client.py` (new): shared async client.
- `src/qtile_pomodoro/qtile.py`: controller, cached rendering, overlay command routing;
  obsolete synchronous polling/transport deleted.
- `src/qtile_pomodoro/cli.py`: consumes `client.py`; existing commands kept.
- `src/qtile_pomodoro/core.py`: `protocol_version` marker in the status payload (this
  story owns the transport contract; snapshot fields come from 001/002).
- `tests/` protocol/controller regressions; notes `using-the-timer.md`,
  `qtile-integration.md` updated.

## Acceptance Criteria

- [ ] AC-1: Given a running daemon, CLI and controller requesting concurrently through
  `client.py` share one implementation with `finally` closure; no second socket path
  remains (ADR-013).
- [ ] AC-2: The bar draws its integer countdown each second from the cached snapshot on
  Qtile's loop; no blocking `check_output`/`Popen` transport remains in `qtile.py`
  (NFR-002, FR-002).
- [ ] AC-3: During an in-flight mutation another submission is refused, not queued; due
  polls coalesce; a successful action's snapshot applies before the next poll.
- [ ] AC-4: A timed-out or lost reply surfaces unknown, keeps the last snapshot marked
  stale, disables state-changing actions, and triggers no resubmission, duplicate
  mutation or spawn (FR-013, ADR-013).
- [ ] AC-5: An old daemon lacking protocol 2 gets upgrade-required with a
  machine-readable code and no mutation (ADR-013).
- [ ] AC-6: On absent/refused socket, revival launches exactly one guarded daemon;
  timeouts and stale-protocol errors never spawn.
- [ ] AC-7: On finalization of the last owner or closure mid-request, tasks cancel,
  hooks unsubscribe, late callbacks are discarded; a service-accepted action is never
  reported undone.
- [ ] AC-8: With occupied workspaces, controller-driven overlays keep above-application
  stacking, input and close behavior unchanged (NFR-004); visible stacking is proven by
  Phase 4 Qtile smoke.
- [ ] AC-9: Consume Story001's real `held_focus`, `focus_original_seconds` and `available_commands`, plus Story002's real `settings.saved/applied/outcome` unchanged under their frozen contract; never expose unrelated TOML/tokens. Story003 adds only the protocol marker, not dummy producer values or a duplicate timer/action-state implementation.
- [ ] AC-10: Phase 2 tests use a real local socket and event loop — no mock transports
  or forwarding echoes.

## Tasks

### Phase 1: Research

- [ ] Search memnotes (`qtile-pomodoro-development`, `qtile-integration.md`) for widget,
  overlay and self-heal conventions; map every transport callsite (`cli.py` request;
  `qtile.py` status/click/keypress/self-heal) and consumers; confirm the one-second
  `InLoopPollText` cadence.
- [ ] Verify Qtile 0.37 hook names (`screens_reconfigured`, `current_screen_change`,
  workspace events) against the installed environment.
- [ ] Fix the protocol-2 status payload and error-code set from 001/002 snapshots.
- [ ] Document findings; ask the human only if a hook contract is genuinely ambiguous.

### Phase 2: Tests (behavior-first regressions)

- [ ] TEST-001: Real-socket single-flight — second submit refused during a mutation;
  due poll coalesced; action snapshot precedes next poll.
- [ ] TEST-002: Timeout/lost reply — unknown result, stale snapshot, disabled actions,
  no resubmission, duplicate mutation, or spawn.
- [ ] TEST-003: Legacy daemon without protocol 2 → upgrade-required, no false success.
- [ ] TEST-004: Absent/refused socket → exactly one guarded launch; timeout or
  stale-protocol failure → none.
- [ ] TEST-005: Last-owner finalize cancels tasks, unsubscribes hooks, discards late
  callbacks.
- [ ] TEST-006: Existing break-overlay and CLI suites pass with controller-driven
  commands and the shared client.

### Phase 3: Implementation

- [ ] IMPL-001: Extract `client.py` (typed request, timeout, envelope, error codes,
  `finally` closure); migrate `cli.py`; delete the inline request.
- [ ] IMPL-002: Add `protocol_version` to the status payload; legacy envelope otherwise.
- [ ] IMPL-003: Controller: cached snapshots, one-second poll, single-flight gate,
  action precedence, stale marking, guarded revival, owner refcount with cancellation/
  callback discard, hook subscription/cleanup.
- [ ] IMPL-004: Cut bar/overlays to the controller; delete `check_output`/`Popen` paths
  and `_daemon_spawned`; render from cache.
- [ ] IMPL-005: Update tests, docs, knowledge notes; clean cutover, no aliases.

### Phase 4: Review

- [ ] Actual CLI/local-socket smoke on an isolated timer service/data directory; never
  reset or shorten the user's session.
- [ ] Qtile-loop smoke of bar/overlay rendering on occupied workspaces; record
  unavailable surfaces (e.g. multi-monitor) explicitly.
- [ ] Independent two-axis review (requirements/spec, code/quality) from a review base
  pinned before approval; consumer knowledge and docs match shipped behavior.
- [ ] All acceptance criteria checked with recorded evidence; completion logged.

## Routine Decision

No reusable deterministic procedure mechanics are introduced or materially changed.

## Technical Notes

Read-only inspection, 2026-10-15: extraction source `cli.py:8-15`; envelope written at
`core.py:187-190` (server `core.py:193`). `qtile.py:22` blocks the loop with
`subprocess.check_output(..., timeout=2.0)` each `InLoopPollText` poll; `qtile.py:117,121`
spawn CLI subprocesses per click/key; `qtile.py:144-146` self-heals via `_daemon_spawned`
plus `Popen` whenever status returns None — including timeouts, which the guard must
narrow to absent/refused. Commands today: `daemon, status, start, pause, reset, skip,
reload, stats` (`cli.py:19`); additions ride the line-JSON envelope. No qtile pin in
`pyproject.toml`; Qtile 0.37 comes from the deployment interpreter.

Edge cases: the controller is architecture alternative 3's presentation seam — never a
second timer, no persisted state; the service still validates every action. A lost
mutation reply triggers a read-only refresh, never resubmission; late replies drop via
per-owner generation tokens. Finalization: unsubscribe hooks → cancel tasks → discard
callbacks; the `current_screen_change` deferred-restack guard protects overlays now,
the panel in story-004.

## Assumptions & Verification

| Assumption | Verified? | Source |
|------------|-----------|--------|
| `cli.py` request is the only client-side socket code | ✅ | inspection |
| Bar status polling blocks Qtile's loop | ✅ | `qtile.py:22` |
| Self-heal fires on any status failure | ✅ | `qtile.py:144-146` |
| Envelope is line-JSON `ok/result/error` | ✅ | `core.py:187-190` |
| Qtile 0.37 emits the needed hooks | ⬜ | Phase 1 |
| 001/002 snapshot fields exist before 003 starts | ⬜ | depends_on chain |

## Definition of Done

- [ ] All acceptance criteria met with real socket/scheduler evidence; focused CLI,
  widget and overlay regressions pass with no legacy transport remnants.
- [ ] Consumer knowledge notes updated; docs match shipped commands.
- [ ] Independent two-axis review completed from a pinned review base.
- [ ] Safe-behavior proof: daemon and Qtile load the new module without resetting user
  state (production deployment lands with story-004).

## Progress Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-10-15 | Created | Initial draft |
