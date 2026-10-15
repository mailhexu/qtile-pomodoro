# 2026-10-15: Manual breaks and timer control panel planning

Governing draft: [Manual Breaks and Timer Control Panel PRD](../subprojects/manual-breaks-and-timer-control-panel/specs/prd.md).
Qualified identity: `qtile-pomodoro/manual-breaks-and-timer-control-panel/prd/prd`.

- Request: manually start a break and provide a control panel.
- User decision: preserve unfinished focus time during a manual break; wait for
  explicit resume after natural break completion rather than restarting work.
- User decision: panel includes controls and saved timer settings.
- Draft scope: bar-click Qtile popup; live timer state; Start/Resume, Pause,
  Reset, short/long manual break, Skip Break; persistent editing of configured
  focus/short-break/long-break minutes and long-break interval.
- Manual breaks do not count as completed focus or reset the cycle. Held focus
  survives daemon replacement; settings affect future phases, not the active
  countdown or held focus. Preserve unrelated TOML settings, including Todoist.
- `spec-create --kind prd` reserved and published immutable subproject
  `manual-breaks-and-timer-control-panel`, operation
  `d158540a52544a5c97a591b64b6b7ba4`.
- PRD populated and linked from owner-local/project specs indexes. It remains
  draft pending user approval; no architecture/story approval or implementation
  is inferred from these product choices.
- Spec-event `generate-status` was attempted with the qualified draft record;
  it refused `STATUS_ROOT_UNBOUND`. No working-directory binding or dashboard
  was silently created or claimed updated.
- Read-only checks confirmed existing timer/accounting/overlay contracts and
  required procedure-skill availability. This is planning-only: no source,
  runtime timer state, settings, or user tasks were changed; no behavioral test
  or live timer operation was needed for this draft.

## PRD Approval and Architecture Proposal

- User approved the PRD; its status is now approved, not an implementation grant.
- Three read-only interface designs compared a minimal command facade, typed
  phase/operation variants, and a shared asynchronous presentation controller.
- Selected the smaller daemon command facade plus one shared async Qtile
  controller. Draft covers persisted held focus/original duration, transactional
  completion, durable settings saves and one coordinated panel/overlay focus owner.
- Proposed one new non-GUI dependency, TOMLKit, based on primary documentation;
  no dependency or application-specific preservation behavior was installed/tested.
- Explicit Controls access during breaks/gates keeps pause/settings reachable
  without allowing stale panels to obscure the authoritative full-screen surface.
- Independent core/UI preflight reviewers found two design gaps: file/directory
  synchronization and screen-reconfiguration resource reconciliation. Both were
  corrected and approved in focused round-2 documentary re-review.
- The separate, user-approved full spec migration completed with its own
  evidence, reviews and receipt. Working-directory STATUS is now bound/generated;
  application source and the prior timer-repair proof artifacts remained unchanged.
- Architecture remains draft; epics/stories/code/deployment await their gates.
- After migration completion, a spec-event STATUS refresh using the draft
  architecture identity was refused as WORK_PHASE_DENIED (the installed helper
  accepts implementation records, despite the documented planning workflow).
  Reported through automated QA; did not reopen a terminal record or change
  installed tooling. The successful migration finish had already regenerated
  STATUS with the approved PRD, draft architecture/research and completed migration.

## Architecture Approval and Delivery Epic

- User approved the architecture; its status and approval narrative now reflect
  that decision. Approval does not grant implementation or deployment authority.
- Reserved canonical draft epic `manual-breaks-and-timer-control-panel/epic/001`
  through the normal CLI, linked to the approved architecture and PRD.
- Proposed four story slices: manual-break state/accounting/recovery; durable
  settings persistence; async client/shared Qtile controller; native panel and
  full integration/deployment. Dependencies and full acceptance are in the epic.
- No story records were created: the current workflow requires epic approval
  first, followed by approval of the allocated story records before coding.
- Read-only catalog check confirmed draft epic, two approved ancestors, valid
  owner-local Markdown links and zero prematurely allocated stories.
- The required STATUS event was attempted with the epic identity and refused
  WORK_PHASE_DENIED, consistent with the already reported planning-authority
  guard mismatch. No terminal migration record was reopened to bypass it;
  current canonical records/indexes are authoritative for this approval gate.
- No application source, dependencies, runtime state or settings were changed.

## Epic Approval and Story Approval Bundle

- User approved Epic001. Reserved canonical story001..004 under the same owner
  through the normal CLI; all four remain draft, with no fictional approval or
  implementation evidence. Four disjoint author agents populated their records.
- Dependencies are 001 -> 002 -> 003 -> 004 (003 requires001/002;004requiresall);
  predecessor acceptance/receipt is required before successor implementation.
- 001ownsreal held-focus/original-duration/action snapshots;002ownssettings/save
  outcomes;003ownsprotocol_version2,sharedasyncclient/controller/hookinfrastructure;
  004reusesitfornativepanelandend-to-enddelivery. No future UI/backend stubs.
- Catalog/link check passed: four correct IDs, each draft with three approved
  ancestors, exact dependency lists, valid active links and no application changes.
  The first checker compared catalog tuples to lists; correcting that harness
  representation resolved the check without any record mutation.
- Independent story Standards/Spec review found bounded planning contradictions:
  missing command-availability producer, focus-reset preservation wording, invalid
  payload/time-settlement order, and conflated lost-reply versus known sync-failure
  outcomes. Unknown file-key rejection also exceeded the requested validation scope.
- Corrected all findings, including the narrow ADR-012 outcome clarification:
  reply loss may follow successful save/application, so old defaults cannot be
  inferred. No requested functionality or accepted scope was removed.
- Focused round2 reviewers marked STORY-SPEC-001..004 and STORY-STD-001..002
  resolved/ready; review was documentary only. Per-story review_base/evidence fields
  stay empty until real implementation research, tests, smoke and review occur.
- STATUS generation with draftStory001 was attempted and rejected as draft not
  authorizing implementation (known planning-authority guard issue). Canonical
  records/indexes remain authoritative; no unrelated approved/terminal record was
  selected to bypass it. Story approval will provide normal implementation authority.
- No application code, dependencies, tests, configuration or live timer were changed.
