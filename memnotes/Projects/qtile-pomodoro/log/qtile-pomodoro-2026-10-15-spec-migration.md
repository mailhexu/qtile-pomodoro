# 2026-10-15: Approved legacy feature specification migration

Governing record: [Migration Quick Task](../specs/quick-tasks/2026-10-15-legacy-feature-spec-migration.md).
Identity: `qtile-pomodoro/quick-task/2026-10-15-legacy-feature-spec-migration`.

## Authority and Scope

The user separately approved the full legacy specification migration after
architecture creation for the approved manual-breaks PRD was refused. The prior
repair approval had covered only bounded Quick Task/knowledge normalization;
it was not reused as authority for this work.

A new approved flat Quick Task was established under the migration bootstrap
exception; `work start` accepted it before substantive relocation. Three agents
owned disjoint feature hierarchies. No installed tooling or application source
was modified.

## Publication

- Moved 16 feature records into three canonical owners: six task-overlay, six
  Todoist-sync and four undo records. Added owner entries and local indexes.
- Used `stories/`, not the planner's incorrect `storys/`; restored missing
  Todoist ancestry from its existing body Parent links. Preserved historical
  statuses, requirements, unchecked criteria, Notes and existing review history.
- Normalized the two unreceipted shared Quick Task identities and active links;
  did not invent missing historical receipts or fresh completion decisions.
- Kept the completed break-overlay repair record, receipt, acceptance/review
  JSON and observed-results log byte-for-byte unchanged. Historical old-path
  mentions remain provenance, with the retained source-to-target map in
  [the migration manifest](../specs/migration-plans/2026-10-15-owner-layout.json).
- Updated discovery links; kept shared notes, skills, mathdocs and Quick Tasks
  at Project root. The approved manual-breaks owner was not relocated.
- Added ignore rules only for managed scratch and transient Kosmic lock files.
- Registered the exact working directory `/home/hexu/projects/qtile_pomodoro`
  through `workdir-register`, then bound STATUS with the supported migration
  command. Refreshed generated Project skill metadata, not installed skills.

## Observed Acceptance

The integrated read-only check loaded the catalog with **21 records** before
creating the new architecture. It verified all **16 relocations** against Git
baseline `2d3bacbdec27eaf2af89732a709a77ef2b3b41da`:

- Every target is catalogued with the expected ancestry depth.
- Historical lifecycle statuses match; body text matches after removing only
  Markdown link destinations, so requirements/prose were not rewritten.
- All active metadata/Markdown links checked resolve. No original alias files
  remain. Immutable historical proof paths are explicitly mapped, not edited.
- All **five immutable repair artifacts** match their recorded SHA-256 hashes.
- Application fingerprint remains
  `825f5c285abf739b53a6e5d69ed472d088cf37e5de7e53bd95d243dc0979beba`
  for tracked source/tests/README/docs/CONTEXT/pyproject/lock files.

`workdir-register` observed directory ID `wd-41a626016dfea1bf`, constrained to
this Project but not a fixed subproject. `generate-status` successfully wrote
root `STATUS.md`; inspection shows canonical owner-local links and truthfully
marks historic done records without receipts as receipt pending.

The formerly blocked ordinary `spec-create --kind architecture` then published
`qtile-pomodoro/manual-breaks-and-timer-control-panel/architecture/architecture`
as **draft**. This is the actual planning-workflow smoke test; no guard was
suppressed and no raw architecture record bypass was used.

No tests or application were launched, installed, restarted or reset for this
metadata operation. No timer settings/state or task data were written.

## Independent Review

- `MigrationStandardsReview`: approved; no blocking or nonblocking findings.
- `MigrationSpecReview`: approved; no findings. The reviewer distinguished
  supplied integrated observations from its own static inspection.

Both reviewers covered metadata relocation/provenance/registration, not the
separate still-draft feature architecture or an implementation approval.
