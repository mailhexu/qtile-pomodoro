---
project_id: "qtile-pomodoro"
subproject_id: "manual-breaks-and-timer-control-panel"
status: "draft"
record_kind: "story"
local_id: "001"
linked_prd: "../prd.md"
linked_epic: "../epics/epic-001.md"
linked_architecture: "../architecture.md"
depends_on: []
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

# Story 001: Manual-Break State, Accounting and Recovery

## User Story

As a pomodoro user,
I want to start a manual short or long break at any moment without losing unfinished focus progress,
So that I can rest now and resume exactly where I stopped, with history, cycle counts and daemon restarts staying truthful (FR-004..FR-009).

## Scope

In scope: state v2 codec/migration; held-focus and original-duration snapshots; command precedence; atomic state/history transaction with exact-once accounting; single-writer ownership; `short-break`/`long-break` service commands plus CLI with existing meanings intact; regressions in `tests/test_core.py` plus targeted service tests; docs/knowledge for changed behavior. Non-goals: settings writer, TOMLKit, shared client/controller, panel/overlays, task features (stories 002–004).

## Acceptance Criteria

- [ ] AC-001: Persist `schema_version: 2`, `focus_original_seconds`, and `held_focus {remaining_seconds: float, original_seconds: int} | null` (ADR-010). Active and held focus metadata are never simultaneously owned. The held checkpoint has no deadline; `State.end_at` belongs only to the running current phase, so a running manual break retains its own break deadline. Idle, paused and gated phases have no current-phase deadline.
- [ ] AC-002: Given a legacy v1 payload, when upgraded, then migration happens in the same transaction as the settling write, old history is untouched, a missing original duration initializes from the configuration loaded at upgrade (documented assumption, not reconstructed history), and an unsupported newer version fails clearly instead of loading as legacy/default.
- [ ] AC-003: A fresh focus captures its original interval at start and preserves it while unfinished across manual-break skip, break reset, settings changes and recovery. Natural focus completion records that original interval once and releases the checkpoint; focus reset clears it without counting the aborted focus (FR-007/008).
- [ ] AC-004: Starting a manual break from running focus freezes fractional focus remaining (e.g. 1499.5 s) without a held-focus deadline, while the manual break receives its own running deadline. Preserve fractional seconds internally and integer public countdown fields (ADR-010).
- [ ] AC-005: Given a paused focus, when a manual break starts, then its frozen remaining is held without running it first (FR-005).
- [ ] AC-006: Given a gate already holding focus, when another manual break is requested, then the identical checkpoint (remaining, original seconds) is retained (FR-004/FR-006).
- [ ] AC-007: Given a running or paused break, when a manual-break command arrives, then it is rejected explicitly and neither break nor held focus is replaced or restarted (FR-004).
- [ ] AC-008: Given idle or a fresh gate, when a manual break runs to its gate and the user skips/starts, then a fresh focus begins at then-current settings, no focus history row is added, and the cycle counter is neither incremented nor reset (FR-006, FR-008).
- [ ] AC-009: Given a held 25-minute remainder of a 35-minute focus, when the break ends and work resumes, then it continues at 25 minutes and finishing records exactly one 35-minute focus excluding break/gate time (FR-008).
- [ ] AC-010: First reject structurally invalid requests/payloads without settling time, including Story002's invalid Save input. For a structurally valid timer action, settle at most one expired phase, then validate action legality in the resulting state: manual break at a focus deadline is rejected after one focus completion and its automatic break. Status reads retain lazy expiry reconciliation (ADR-010/012).
- [ ] AC-011: Break reset enters the Resume Gate preserving held focus. Focus reset, including a gate that holds unfinished focus, clears both active/held original-duration and remaining checkpoints and aborts uncounted; automatic-break skip/reset semantics stay unchanged (FR-007).
- [ ] AC-012: Given a focus completion, when persisted, then the history insert and state write commit in one SQLite transaction via `commit(state, completed_focus_seconds=None)`; a persistence failure rolls back leaving no duplicate/partial history and the prior in-memory state; notification and in-memory publication happen only after commit (ADR-011, NFR-003).
- [ ] AC-013: Given a daemon launch, when Timer construction, state loading, migration or recovery runs, then a per-user advisory lock is already held; a duplicate launch exits before any such write while the existing live-socket check is retained (ADR-011).
- [ ] AC-014: Given daemon replacement, then a non-expired phase keeps its deadline exactly; an overdue focus completes once into one fresh automatic break; an overdue manual break enters the Resume Gate with held focus intact, never an automatically running focus (FR-009).
- [ ] AC-015: Given the current CLI, when `daemon/status/start/pause/reset/skip/reload/stats` run, then meanings, output shape and the `ok/result/error` envelope are unchanged, and `short-break`/`long-break` work through the same service path with explicit invalid-state errors (ADR-013).
- [ ] AC-016: Service status publishes `held_focus`, `focus_original_seconds`, and server-derived `available_commands` for meaningful timer controls in the reconciled state, preserving existing integer countdown fields. Manual-break actions are offered in eligible focus/idle/gated states, not running/paused breaks. The service revalidates requests; UI affordances do not replace validation or alter existing idempotent CLI behavior. Document/freeze these fields before Story003; no future settings/panel stubs.

## Tasks

### Phase 1: Research

- [ ] Search notes (`using-the-timer.md`, `qtile-integration.md`), `docs/adr/0002`, epic-001, ADR-010/011/013.
- [ ] Verify seams: `State`, `Store.save`/`complete_focus` split commits, `Timer.finish` counting `duration("focus")`, recovery inside `Timer.__init__`, ticker via `command("status")`, CLI envelope.
- [ ] Verify `tests/test_core.py` fixtures (temp SQLite, monkeypatched clock, suppressed notify); document findings plus the legacy-migration assumption source.

### Phase 2: Behavior-First Regressions (extend `tests/test_core.py`; service-level only where meaningful)

- [ ] TEST-001: running focus suspension preserves float remaining in a deadline-free checkpoint while the manual break owns a fresh deadline and counts down independently; TEST-002: paused focus suspension never runs the held focus.
- [ ] TEST-003: manual break from a held gate keeps the identical checkpoint; TEST-004: manual break during running/paused break rejected, state and held focus unchanged.
- [ ] TEST-005: idle manual break — no history row, no held focus; skip/start begins fresh focus at current settings.
- [ ] TEST-006: resume counts once with original seconds, break time excluded, cycle untouched, settings change does not retime it.
- [ ] TEST-007: expired focus plus manual-break request yields one completion, an automatic break, and a rejected request.
- [ ] TEST-008: injected persistence failure at commit — no history row, prior state retained, no notification.
- [ ] TEST-009: v1→v2 migration preserves history and a non-expired legacy deadline, initializing missing original duration from config; TEST-010: unsupported newer version fails clearly with no writes.
- [ ] TEST-011: recovery matrix — non-expired restart keeps deadline; overdue focus completes once into a fresh automatic break; overdue manual break reaches the gate with held focus.
- [ ] TEST-012: duplicate daemon launch exits before any state/migration write; live-socket refusal preserved.
- [ ] TEST-013: break reset → gate preserving held focus; focus reset aborts uncounted.
- [ ] TEST-014 (service seam): `short-break`/`long-break` through the request envelope return the new state or an explicit error.
- [ ] TEST-015: real service snapshots and command results across idle/focus/paused/break/gated states expose accurate held-focus/original-duration values and state-sensitive `available_commands`, including rejection of stale manual-break actions.

### Phase 3: Implementation

- [ ] IMPL-001: state v2 codec — new fields, float-internal/integer-public remaining, legacy upgrade in the settling transaction, clear failure on newer versions.
- [ ] IMPL-002: centralized transitions with structural/payload validation before time settlement, then settle-one-phase/state-legality validation; capture original focus at start and hold/restore it across running/paused/gated states; reject manual breaks during breaks.
- [ ] IMPL-003: `Store.commit(state, completed_focus_seconds=None)` transactional interface; migrate actual callers; remove the obsolete separate-commit path cleanly (no aliases).
- [ ] IMPL-004: per-user advisory lock before `Timer()`/Store load/recovery; duplicate launch exits pre-write.
- [ ] IMPL-005: one-step recovery, service dispatch and manual-break CLI; publish real `held_focus`, `focus_original_seconds` and meaningful `available_commands` fields while preserving existing public status semantics. Story002 extends settings/actions; Story003 owns the protocol-version marker.
- [ ] IMPL-006: update affected callers/tests; docs/knowledge for actual behavior.

### Phase 4: Review and Completion

- [ ] Focused regressions green; no unrelated test churn.
- [ ] Actual CLI and local-socket smoke against isolated data/service (own `XDG_*` paths); never reset or shorten the user's session.
- [ ] Update `using-the-timer.md` and `qtile-integration.md` only for real changed behavior.
- [ ] Pin `review_base`, run independent two-axis (standards + spec) review, record `acceptance_evidence` and `review_record`; safe-proof that no step edits history or user state.

## Routine Decision

No reusable deterministic procedure mechanics are introduced or materially changed.

## Technical Notes

- `Store.save`/`Store.complete_focus` commit separately (`core.py:83-89`): a crash between them can count a completion without state — replaced by ADR-011's single transaction.
- `Timer.finish` records `duration("focus")` from current config (`core.py:128-143`); exact-once accounting must read the captured interval instead.
- Recovery runs in `Timer.__init__` before any lock (`core.py:115-119`); ownership must precede it.
- Public `remaining` is already integer-rounded in `status()`; v2 keeps that contract with floats internally.
- Held focus is distinct from machine suspend and from pausing the displayed break.

## Assumptions & Verification

| Assumption | Verified? | Source |
|------------|-----------|--------|
| Existing CLI meanings/envelope unchanged | ✅ | `cli.py`, ADR-013 |
| State is a single-row JSON payload (`state` id=1) | ✅ | `core.py` Store |
| Ticker and status share the transition path | ✅ | `serve()`/`command()` |
| Advisory-lock primitive (e.g. `fcntl.flock` on a runtime lock file) | ⬜ pending | ADR-011 pins ownership timing, not the primitive |
| v1 durations are integer minutes | ✅ | `State` defaults, `load_config` |

## Definition of Done

- [ ] All acceptance criteria met with real results in `acceptance_evidence`.
- [ ] Focused behavior regressions pass (consumer-visible states/errors, not source/mock echoes).
- [ ] Consumer knowledge updated (`using-the-timer.md`, `qtile-integration.md`) for actual behavior.
- [ ] Independent two-axis review with pinned `review_base`; decision in `review_record`.
- [ ] Safe proof: isolated-data smoke only; no session reset, history edit or destructive step.

## Progress Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-10-15 | Created | Initial draft from approved epic/architecture |
