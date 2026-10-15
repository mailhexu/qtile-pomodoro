---
project_id: qtile-pomodoro
subproject_id: null
record_kind: quick-task
local_id: 2026-10-15-legacy-feature-spec-migration
status: done
created: 2026-10-15
updated: 2026-10-15
consumer_interface_change: false
proposal_required: false
routine_edge_change: false
routine_decision_required: false
routine_proposals: []
review_base: 2d3bacbdec27eaf2af89732a709a77ef2b3b41da
review_round: 1
acceptance_evidence:
  - specs/migration-plans/2026-10-15-owner-layout-acceptance.json
review_record: specs/migration-plans/2026-10-15-owner-layout-review.json
registration_root: /home/hexu/projects/qtile_pomodoro
registration_outputs:
  - .kosmic/working-directories.json
  - worktree:.kosmic/workdir.json
---

# Quick Task: Legacy feature specification migration

## Request and Authority

The user explicitly approved moving and relinking the 16 legacy task-overlay,
Todoist-sync and undo feature specifications into owner-local directories,
normalizing ancestry/shared metadata, and registering this working directory.
Application source, installed Kosmic tooling, runtime configuration, timer state,
and task data are out of scope.

This is a bounded migration bootstrap record. The installed CLI can create a
new PRD owner, but its catalog guard prevents both derived records and normal
Quick Task creation while any legacy flat feature specs remain. Its documented
flat Quick Task bootstrap resolver authorizes the migration work. This record
is established under the explicit approved migration rather than reopening a
completed repair record or disabling a catalog guard.

## Scope

- Move six task-overlay feature records to owner `minimal-qtile-task-overlay`,
  six Todoist records to `prd-todoist-client-sync`, and four undo records to
  `prd-undo-task-completion-and-move`.
- Use canonical `specs/stories/`, not the planner's erroneous `storys/` output.
  Preserve titles, body requirements, existing approval/lifecycle states and
  historical verification; normalize identity, ancestry, and relative links.
- Create each owner's SubprojectEntry and specifications index; update current
  discovery links. Keep shared knowledge, skills, mathdocs and Quick Tasks at
  the Project root; normalize legacy Quick Task identity where absent.
- Preserve the already receipted break-overlay repair record, its receipt and
  acceptance/review/log artifacts byte-for-byte. Old path mentions inside
  immutable historical evidence are provenance, not active aliases; record
  their mapping rather than editing hashes or inventing fresh approvals.
- Register `/home/hexu/projects/qtile_pomodoro` and bind its STATUS output.
- Preserve the approved manual-breaks PRD and its reserved owner. After migration,
  retry architecture creation through the normal CLI; architecture remains draft.

## Out of Scope

- Application implementation, behavior changes, daemon restarts or installation.
- Modifying user-authored skills or installed Kosmic implementation.
- Turning old checkboxes into new acceptance claims, changing historical statuses,
  or fabricating review/receipt evidence for previously unreceipted work.

## Acceptance Criteria

- [x] All 16 feature records have one canonical owner-local identity and valid ancestry; no flat feature specs or runtime aliases remain.
- [x] Requirements, lifecycle states and immutable repair evidence are preserved.
- [x] Active relative links resolve to migrated records/shared knowledge; historical path references have an explicit retained mapping.
- [x] Catalog loading, directory registration and STATUS generation succeed without suppressing guards.
- [x] No application source, installed tooling, runtime configuration, timer state or task data changed.
- [x] Independent migration review passes and observed acceptance evidence is recorded.

## Routine Decision

This is a one-time metadata relocation, not a new reusable execution procedure.
No reusable routine edge is added or materially changed.

## Verification

- Integrated catalog/link/body/status/immutable-hash check passed for all16 moves.
- Supported registration and STATUS generation passed; actual dashboard inspected.
- Normal owner-local architecture creation now succeeds without guard bypass.
- Independent Standards and Spec reviews approved round1 with no findings.
- Details and retained hashes: [migration observations](../../log/qtile-pomodoro-2026-10-15-spec-migration.md).
- Completion is published only by work finish; no terminal status is assigned manually.
