---
project_id: "qtile-pomodoro"
subproject_id: "manual-breaks-and-timer-control-panel"
status: "draft"
record_kind: "story"
local_id: "002"
created: 2026-10-15
updated: 2026-10-15
linked_prd: "../prd.md"
linked_epic: "../epics/epic-001.md"
linked_architecture: "../architecture.md"
depends_on: ["001"]
consumer_interface_change: true
related_notes:
  - ../../../../notes/using-the-timer.md
  - ../../../../notes/qtile-integration.md
proposal_required: false
routine_edge_change: false
routine_decision_required: false
routine_proposals: []
review_base: ""
review_round: 0
acceptance_evidence: []
review_record: ""
---

# Story 002: Durable Timer-Settings Persistence

## User Story

As a Pomodoro user,
I want validated focus/break durations and the long-break interval saved durably into my existing config.toml without altering anything else in it,
So that future timer phases use my settings across daemon restarts while my active session, history, and Todoist configuration stay untouched.

**Bounded scope**: new `src/qtile_pomodoro/settings.py` (typed four-field settings, strict validation, document-preserving TOMLKit save with durability sequencing); daemon `save-settings` command; CLI `save-settings` with four explicit flags; phase-stable snapshots and the applied/saved_not_applied/rejected/unknown outcome taxonomy; `tomlkit` declared and locked; migration of the timer's actual config-loading callers. Depends on Story 001's state seam (settle at most one expired phase, then validate the action).

**Non-goals**: no Qtile widget/controller/panel or shared async-client work (Stories 003/004); no held-focus semantics (Story 001); no new GUI dependency; no custom one-off break lengths, schedules, history editing, file watching, optimistic revision tracking, or automatic retry machinery; task/Todoist modules behaviorally unchanged.

**Source outputs**: [PRD](../prd.md) FR-010–FR-013, NFR-002/003/005; [Architecture](../architecture.md) ADR-012 and the module/cutover plan; [research memo](../research/2026-10-15-toml-settings.md) "Required Implementation Evidence"; [Epic 001](../epics/epic-001.md) "Durable timer-settings persistence" slice acceptance.

## Acceptance Criteria

- [ ] **AC-1** Given a save payload, when any of the four values is not a positive whole number (bool `true`/`false`, 0, negative, float, string), or a key is missing or unknown, then `save-settings` returns `rejected` naming the offending field, with no expiry settlement, file write, state change, or history row (FR-011, ADR-012).
- [ ] **AC-2** Given an expired phase deadline, when an invalid save is submitted, then the expired phase is not settled — no completion counted, no automatic break started, phase/status unchanged — because validation precedes settlement (ADR-010/ADR-012).
- [ ] **AC-3** Given an expired focus and a valid Save payload, settle it once using previous settings (one focus history row and the old long-break cadence), then apply defaults only to future phases. An expired break instead enters its gate with held focus intact and no new focus history. Never retime the phase just started by settlement (ADR-012).
- [ ] **AC-4** Given a valid save, when it succeeds, then the outcome is `applied`: the rendered document was validated, written to a same-directory temporary file, flushed and fsynced, atomically replaced, and the containing directory fsynced — before success is reported (ADR-012).
- [ ] **AC-5** Given each pre-replacement failure seam — unreadable existing file, invalid TOML, unwritable directory/permissions, temp write or replace failure — then the outcome is `rejected`, the original file bytes and permissions are unchanged, and messages name field or file location without echoing TOML source text or any credential value, including malformed-token cases (FR-013, ADR-012).
- [ ] **AC-6** A service-detected post-replacement directory-sync failure yields `unknown`: retain old applied defaults, do not claim the old file is unchanged, and do not roll back/retry; visible file contents alone do not prove durability. Separately, a lost reply yields an unknown client outcome even if the service already durably saved/applied the new settings. Do not assume old defaults or undo it; reconcile authoritative current state read-only without automatic resubmission (ADR-012).
- [ ] **AC-7** Given a durable replacement whose daemon application then fails, then the outcome is `saved_not_applied`, and the service result, snapshot, and CLI reporting distinguish it from `applied` and from errors (FR-013).
- [ ] **AC-8** Given a config containing comments, whitespace/order, quoted keys, dotted keys, inline tables, multiline strings, and unrelated sections including `tasks.todoist_api_token`, when a valid save rewrites it, then unrelated bytes and structure survive losslessly and no outcome, error, or snapshot ever contains the token or full TOML (FR-012; research memo evidence list).
- [ ] **AC-9** Saving during non-expired running focus/break, paused focus/break or a held gate preserves current remaining/deadline, held remaining, original focus interval, counter and history. Already-expired phases follow AC-3 settlement rather than an impossible unchanged-state guarantee (FR-012/008).
- [ ] **AC-10** Given saved valid settings, when fresh phases start (idle/resume/skip, manual breaks, automatic break cadence), then they use current applied settings without daemon restart; absent config still yields `DEFAULTS`; the existing `reload` command re-applies the saved document and keeps its meaning (FR-012, ADR-012).
- [ ] **AC-11** Preserve existing file permissions and create new files owner-only. Loading validates positive integer values (not bool) for the four owned timer keys. Retain additional file keys, including inside `[timer]`, rather than rejecting them solely for unknown names; strict missing/unknown-key rejection applies to the incoming Save payload, not unrelated file content (FR-011/012).
- [ ] **AC-12** Given any outcome, the CLI reports exactly that outcome, exits nonzero unless it is `applied`, never auto-retries, and `--json` exposes a machine-readable outcome field; `unknown` is never presented as success or as "original file unchanged" (FR-013).
- [ ] **AC-13** Config-loading ownership lives only in `settings.py`: `core.py` no longer parses TOML, `load_config`/deprecated aliases are gone, actual callers (`Timer.__init__`, `reload`, duration/cadence reads) and their tests are migrated, and `pyproject.toml`/lock declare a compatible locked `tomlkit` (ADR-012 cutover plan).
- [ ] **AC-14** The service publishes timer-only `settings.saved`, `settings.applied` and `settings.outcome`, extending Story001's `available_commands` with the actually implemented settings action. Represent absent/uncertain data honestly, not as invented durable success; document/freeze names and nullable meanings for Story003. No full TOML or credential values enter the snapshot.

## Tasks

### Phase 1: Research

- [ ] Confirm seams: `core.py` `DEFAULTS`/`config_path`/`load_config` (tomllib), `Timer.__init__` and `reload` callers, snapshot consumers, and the `tests/test_core.py` monkeypatch pattern.
- [ ] Read the research memo; treat its TOMLKit claims as documentation, not local proof; select a Python ≥3.11-compatible `tomlkit` version and lock it during implementation.
- [ ] Record current loader behavior deltas (today booleans pass `isinstance(value, int)`; unknown `[timer]` keys are validated).
- [ ] Document findings in Technical Notes.

### Phase 2: Tests (behavior first; real temp files and temp SQLite)

- [ ] TEST-001 strict validation matrix (bool/0/negative/float/str/missing/unknown) → `rejected`, nothing settled or written (AC-1, AC-2).
- [ ] TEST-002: valid Save at an expired focus completes once under old settings; at an expired break it enters the held gate without history. New defaults affect only later phases (AC-3).
- [ ] TEST-003 durable sequence: tomllib-validated render → temp write → fsync → replace → dir fsync → `applied` (AC-4).
- [ ] TEST-004 pre-replacement failure matrix on real files: invalid TOML, unreadable file, unwritable directory → `rejected`, original bytes/permissions intact, secret-free messages (AC-5).
- [ ] TEST-005a: detected post-replacement dir-sync failure keeps old applied defaults and uncertain durability; TEST-005b: discard a reply after real durable save/application, require unknown client outcome with new service settings retained, read-only reconciliation and no rollback/retry (AC-6/12).
- [ ] TEST-006 application failure after durable replace → `saved_not_applied` in result, snapshot, and CLI rendering (AC-7).
- [ ] TEST-007 lossless round trip: comments, quoted/dotted keys, multiline strings, inline tables, unrelated sections and token preserved; no token in errors/snapshots (AC-8).
- [ ] TEST-008 phase stability with real temp SQLite: save during running/paused/held leaves state, original interval, and history unchanged (AC-9).
- [ ] TEST-009 fresh phases, manual-break durations, long-break cadence, absent-config defaults, reload re-application (AC-10).
- [ ] TEST-010: permissions/new-file mode and strict validation of four owned file values; existing additional `[timer]` keys remain loadable/preserved while unknown Save payload keys are rejected (AC-11).
- [ ] TEST-011 CLI save-settings: four flags, outcome-accurate text/exit status, `--json` outcome field (AC-12).
- [ ] TEST-012: real service snapshots reflect known saved/applied/outcome semantics, absent config defaults and actually supported actions; no credential leak or fabricated future payload (AC-14).

### Phase 3: Implementation

- [ ] IMPL-001 `settings.py`: typed settings dataclass, strict validation, fresh-read load, TOMLKit read/modify/write with the durability sequence, outcome/error taxonomy without source or secret echo.
- [ ] IMPL-002 Migrate `core.py` callers; delete `load_config`/tomllib ownership and any aliases; migrate test monkeypatch seams.
- [ ] IMPL-003: validate payload -> settle at most one expired phase -> durable write -> future defaults -> outcome; expose `settings.saved/applied/outcome` and extend real `available_commands`, freezing the snapshot contract before003.
- [ ] IMPL-004 CLI `save-settings` with four explicit flags and outcome rendering; declare and lock `tomlkit`.

### Phase 4: Smoke, review, docs, completion

- [ ] Actual CLI smoke against a real daemon in an isolated `XDG_CONFIG_HOME`/`XDG_DATA_HOME`/`XDG_RUNTIME_DIR` environment, exercising applied, saved_not_applied, rejected, and unknown paths over the real socket; the user's live session is never touched.
- [ ] All permanent tests pass; nothing claimed that was not executed.
- [ ] Independent two-axis review (Task 7): pin `review_base` before implementation, run Standards and Spec axes, record the round.
- [ ] Update `notes/using-the-timer.md` (save-settings usage/outcomes) and the development reference; add only real Progress Log rows.

## Routine Decision

No reusable deterministic procedure mechanics are introduced or materially changed; the durability sequencing is application logic defined by ADR-012, not a compiled routine.

## Technical Notes

Verified seams (2026-10-15): `core.py::load_config` merges `DEFAULTS` over `[timer]` via `tomllib`; actual callers are `Timer.__init__` and `command("reload")`; `duration`/`finish`/`status` read the loaded mapping and `qtile.py` consumes only snapshot fields. `task_widget.py::_todoist_token()` performs its own independent `tasks.todoist_api_token` read — it is not a timer-config caller and stays behaviorally unchanged. Tests monkeypatch `qtile_pomodoro.core.config_path`; that seam moves with ownership to `settings.py`.

Validation-before-settlement reuses Story 001's single transition seam: a valid save settles at most one expired phase under previously applied settings, then swaps future-phase defaults; invalid input returns before any settlement (AC-2 locks this order).

Filesystem replacement and SQLite are not one transaction. Before replacement, failures preserve original bytes. A detected directory-sync failure after replacement retains old runtime defaults but has uncertain file durability. A lost reply can follow successful application: the client cannot infer old defaults, and refresh reports current service state without rollback, retry or claiming mere file visibility proves durability.

| Assumption | Verified? | Source |
|------------|-----------|--------|
| TOMLKit preserves unrelated TOML in this repo's real files | ⬜ pending — requires TEST-007, docs are not proof | Research memo |
| A `tomlkit` version compatible with Python ≥3.11 exists | ⬜ pending — locked at implementation | ADR-012 |
| Directory fsync behaves on the deployed filesystem | ⬜ pending — exercised in TEST-003/005 | ADR-012 |

## Definition of Done

- [ ] All acceptance criteria met with real-file/temp-SQLite evidence recorded in `acceptance_evidence`.
- [ ] Focused regressions pass: existing timer/CLI/store tests green after the settings cutover, no aliases retained.
- [ ] Consumer knowledge updated (`using-the-timer.md`); development reference reflects `settings.py` ownership.
- [ ] Independent two-axis review completed and pinned in `review_record`.
- [ ] Safe proof: smoke ran in isolated config/data/runtime dirs; the user's session and real config were never modified.

## Progress Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-10-15 | Created | Initial draft; awaiting story approval |
