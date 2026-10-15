---
project_id: qtile-pomodoro
subproject_id: manual-breaks-and-timer-control-panel
record_kind: epic
local_id: "001"
status: approved
created: 2026-10-15
updated: 2026-10-15
linked_prd: ../prd.md
linked_architecture: ../architecture.md
linked_stories:
  - ../stories/story-001.md
  - ../stories/story-002.md
  - ../stories/story-003.md
  - ../stories/story-004.md
---

# Epic 001: Manual Breaks and Timer Control Panel

## Description

Deliver manual short/long breaks that preserve unfinished focus progress, plus
a responsive Qtile-native control panel for timer actions and persistent settings.
The complete value is one usable panel backed by the existing authoritative
Timer Service, with correct accounting, recovery and all-workspace overlays.

Parents: [approved PRD](../prd.md) and [approved architecture](../architecture.md).
The user approved this epic. Its four allocated story records remain draft and
require implementation approval; epic approval alone does not authorize code.

## Scope

### In Scope

- Persist held focus and original focus duration; preserve fractional remaining
  time, exact-once completed-focus accounting, deadline precedence and one-step
  recovery across manual breaks and daemon replacement.
- Manual short/long break commands available from CLI and panel; reject attempts
  during an existing running/paused break. Natural completion waits at the gate;
  explicit skip returns to held focus or starts a fresh interval.
- Four-field settings editor backed by a lossless TOMLKit save, strict validation,
  permissions and durable atomic replacement. Report partial/unknown outcomes
  honestly and preserve unrelated TOML/Todoist values without exposing secrets.
- Shared nonblocking socket client and Qtile controller; cached status rendering,
  one in-flight request, stale-daemon detection, guarded existing self-heal and
  no automatic resubmission of uncertain state-changing actions.
- Bar-click panel, native keyboard/mouse editing, state-appropriate actions,
  explicit Controls access during breaks/gates, coordinated focus/stacking,
  monitor/workspace reconciliation and complete finalization cleanup.
- Existing CLI controls, task/Todoist behavior, timer history and active-session
  deployment invariants remain intact. Update consumer/development knowledge
  and prove the changed paths before completing the epic.

### Out of Scope

- Standalone GUI, Wayland, another daemon, task-feature changes or scheduling.
- Custom one-off break lengths, automatic work restart or editing old history.
- A full typed-operation framework, plugin system, event sourcing, external-editor
  file watching, or new optimistic concurrency/retry machinery.
- Source/configuration/runtime changes before the corresponding story is approved.

## Implementation Stories

Canonical records were allocated after epic approval. The dependencies below
define implementation order; all four stories still require approval before coding.

| Story | Delivered behavior | Dependency |
|---|---|---|
| [001: Manual-break state, accounting and recovery](../stories/story-001.md) | CLI manual breaks, held-focus recovery and atomic accounting. | Approved parents |
| [002: Durable timer-settings persistence](../stories/story-002.md) | Validated, lossless, durable settings saves for future phases. | 001 |
| [003: Asynchronous client and Qtile controller](../stories/story-003.md) | Shared nonblocking CLI/bar/overlay transport and lifecycle. | 001, 002 |
| [004: Native control panel and delivery](../stories/story-004.md) | Controls/settings UI, full integration, knowledge and safe deployment. | 001, 002, 003 |

### Cross-story contracts

- Story001 owns real held-focus/state/accounting command results; Story002 owns
  real settings/save-outcome payloads. Document stable snapshot field names at
  dependency completion before Story003 begins; do not add dummy future payloads.
- Story003 owns the `protocol_version: 2` marker and shared client/controller
  cutover, including overlay hooks and deferred-restack cleanup. Story004 extends
  that same owner for the panel, without a second hook/controller infrastructure.
- Successor implementation starts after predecessor acceptance/receipt, not just
  predecessor approval. Earlier slices remain usable at their own service/CLI or
  bar/overlay seam; the whole feature is deployed only after integration is ready.
- Story001 produces `held_focus`, `focus_original_seconds` and meaningful service-
  derived `available_commands`. Story002 produces `settings.saved/applied/outcome`
  and extends real action availability. Story003 consumes those frozen names and
  adds only the protocol marker; no field producer is delegated to the panel.

### Slice Acceptance to Carry into Stories

**Manual-break state, accounting and recovery**

- Preserve running/paused/gated focus without a new deadline while held. Repeated
  manual breaks from a held gate retain the same checkpoint; requests during a
  running/paused break cannot replace it.
- Original focus duration and remaining survive settings changes, skip/reset,
  natural break completion and persisted recovery. A focus finishing afterward
  counts once; manual-break time is excluded and cycle count is not reset.
- Atomically commit completion/state and publish memory/notification afterward;
  rollback cannot duplicate history. Acquire single-writer ownership before
  state loading/migration/recovery. Preserve legacy history/deadlines and the
  architecture's explicit assumption for missing legacy original-duration data.
- Preserve current CLI commands; expose manual break commands through the service.

**Durable timer-settings persistence**

- Add the approved non-GUI TOMLKit dependency with a supported locked version.
  Positive whole-number validation rejects bool, partial payloads and unknown
  timer keys before mutation; invalid input cannot trigger expiry settlement.
- Preserve unrelated fields/comments and token secrecy on success and error.
  Flush/fsync temporary content before replacement, then synchronize directory
  entries before claiming a durable save; preserve permissions.
- Distinguish rejected, applied, saved-not-applied and unknown/post-replacement
  durability states; no blind rollback or automatic retry after uncertainty.
- Running/paused/held intervals and original accounting duration remain unchanged;
  fresh phases use current saved/applied settings, including long-break cadence.

**Asynchronous timer client and Qtile controller**

- Extract one shared asynchronous Unix-socket request path and remove obsolete
  blocking subprocess polling. Keep drawing and event handling on Qtile's loop.
- Preserve supported CLI shapes; add settings payloads and protocol-version/error
  handling. An old daemon cannot falsely report a new action as successful.
- All bars, the panel and full-screen surfaces use the same snapshots. Closing
  UI cannot duplicate, cancel as if undone, or silently resubmit accepted actions.
- Discard late callbacks and release controller tasks/hooks after final ownership
  ends; absence/refusal may trigger one guarded revival, not timeout/protocol errors.

**Native control panel and end-to-end delivery**

- Current state/countdown/held-focus progress remain live while dirty setting
  fields stay untouched by status refresh. Save is explicit; closing discards
  unsaved edits, not active service state.
- All requested actions are usable and valid-state gated, with clear phase-specific
  Reset meaning. Controls can be deliberately opened above active break/gate
  surfaces without leaving stale panels or stealing focus unexpectedly.
- Screen reconfiguration disposes removed/changed resources and recreates correct
  geometry from cached state. Workspace/current-screen changes restore the
  approved foreground order without waiting for the next poll.
- Exercise actual Qtile surfaces against an isolated timer/store; observe rendered
  output, input/focus and occupied-workspace stacking. Do not reset/shorten the
  user's active session. Report unavailable multi-monitor checks explicitly.

## Success Criteria

- [ ] All allocated implementation stories satisfy their full acceptance criteria,
  focused regression checks and convergent code review before completion.
- [ ] Starting a manual break with 25 minutes left in a 35-minute focus holds that
  progress. Break completion waits; resume continues at 25 minutes; eventual
  completion records exactly one 35-minute focus and excludes the break.
- [ ] Manual long break, paused focus, held gate, invalid repeated break, break
  reset and explicit skip preserve the approved timer/counter invariants.
- [ ] Settings validate/save durably and survive restart, without retiming active,
  paused or held work or exposing/modifying unrelated configuration.
- [ ] The actual panel, break and resume surfaces are verified in Qtile, including
  controls during breaks, keyboard/mouse input, occupied-workspace stacking and
  screen lifecycle behavior where the environment permits.
- [ ] Whole-feature tests and integrated service/client/UI checks pass; existing
  timer, task/Todoist and overlay regressions remain covered.
- [ ] Consumer/development docs, knowledge and safe deployment evidence are current;
  both daemon and Qtile load the implemented version without resetting user work.

## Verification and Delivery Rules

Permanent tests cover consumer-visible transitions, boundaries, persistence,
precedence and errors—not mock forwarding echoes or source text. Use real
SQLite/temp configuration and actual local sockets at the correct seams.
Exercise the actual Qtile UI; tests alone do not establish visible stacking or
usable input. Do not claim source/runtime behavior from architecture reviews.

No silent scope reduction: a passing core helper is not a delivered control
panel, and a popup without persistence/recovery is not a completed epic.

## Progress

- Stories: 4 allocated; 0 approved; 0 implemented.
- Epic: approved; stories: draft, awaiting implementation approval.
- Last updated: 2026-10-15.

## Story-Bundle Pre-Approval Review

All four story records remain draft. Independent Standards and Spec reviewers
examined their planning contracts; focused round-2 re-review found all findings
resolved. This is not an implementation test, code-review receipt or story approval.

| Axis finding | Resolution |
|---|---|
| STORY-SPEC-001 | Backend producers assigned: 001 supplies held-focus/original interval/action availability; 002 supplies settings outcomes and extends actions; 003 consumes the frozen contract and adds the protocol marker. |
| STORY-SPEC-002 | Focus Reset clears the checkpoint; Break Reset preserves it; natural completion records the original interval before releasing metadata. |
| STORY-SPEC-003 / STORY-STD-002 | Known post-replacement sync failure and lost client reply are distinct; a lost reply cannot imply old runtime settings. Read-only reconciliation, no automatic rollback/resubmission. |
| STORY-SPEC-004 | Structural/payload validation precedes time settlement; valid actions reconcile one expired phase before state-legality checks. |
| STORY-STD-001 | Unknown Save request keys are rejected; additional config-file keys are preserved rather than newly rejected. |

Clarifications also distinguish a running break deadline from the deadline-free
held checkpoint and expired-focus history from expired-break gate transitions.
PRD feature scope and the four-story order are unchanged. Implementation remains
blocked on explicit approval of these story records.
