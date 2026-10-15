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
